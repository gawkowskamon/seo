from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env FIRST before any other imports
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.responses import Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import asyncio
import re

from article_generator import generate_article, suggest_topics
from seo_scorer import compute_seo_score
from export_service import (
    generate_facebook_post,
    generate_google_business_post,
    generate_full_html,
    generate_pdf_bytes
)
from image_generator import generate_image, generate_image_variant, get_all_image_styles
from seo_assistant import analyze_article_seo, chat_about_seo
from content_templates import get_all_templates
from wordpress_service import publish_to_wordpress, generate_wordpress_plugin, build_styled_wordpress_content
from tpay_service import get_all_plans, get_plan, create_tpay_transaction, calculate_subscription_end
from auth import (
    register_user, authenticate_user, get_user_by_id,
    create_access_token, decode_access_token
)
from series_generator import generate_series_outline
from content_calendar_service import generate_content_calendar
from import_service import scrape_article_from_url, import_from_wordpress, optimize_imported_article
from linkbuilding_service import analyze_internal_links
from seo_audit_service import run_seo_audit
from competition_service import analyze_competition
from auto_update_service import check_articles_for_updates
from chat_assistant_service import chat_with_assistant, clear_chat_session


# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise RuntimeError("MONGO_URL environment variable is required")
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
db = client[os.environ.get('DB_NAME', 'seo_article_writer')]

# Validate EMERGENT_LLM_KEY at startup
_llm_key = os.environ.get('EMERGENT_LLM_KEY')
if _llm_key:
    logging.info(f"EMERGENT_LLM_KEY loaded: {_llm_key[:12]}...")
else:
    logging.warning("EMERGENT_LLM_KEY NOT FOUND in environment! AI features will not work.")

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ============ Pydantic Models ============

class ArticleGenerateRequest(BaseModel):
    topic: str
    primary_keyword: str
    secondary_keywords: List[str] = []
    target_length: int = 1500
    tone: str = "profesjonalny"
    template: str = "standard"

class ArticleUpdateRequest(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    faq: Optional[List[Dict[str, str]]] = None
    toc: Optional[List[Dict[str, str]]] = None
    internal_link_suggestions: Optional[List[Dict[str, str]]] = None
    sources: Optional[List[Dict[str, str]]] = None
    html_content: Optional[str] = None

class ScoreRequest(BaseModel):
    primary_keyword: str
    secondary_keywords: List[str] = []

class TopicSuggestRequest(BaseModel):
    category: str = "ogólne"
    context: str = "aktualne tematy podatkowe i księgowe w Polsce"

class ExportRequest(BaseModel):
    format: str  # "facebook", "google_business", "html", "pdf"

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str


# ============ Auth Helper ============

async def get_current_user_optional(authorization: Optional[str] = Header(None)):
    """Get current user from token if present, otherwise return None."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = await get_user_by_id(db, user_id)
    return user

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from token. Raises 401 if not authenticated."""
    user = await get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Wymagane logowanie")
    return user


# ============ Helper Functions ============

def serialize_doc(doc: dict) -> dict:
    """Serialize MongoDB document for JSON response."""
    if doc is None:
        return None
    if "_id" in doc:
        del doc["_id"]
    # Convert datetime objects
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


# ============ API Routes ============

@api_router.get("/")
async def root():
    return {"message": "SEO Article Writer API", "status": "running"}


# ============ Auth Routes ============

@api_router.post("/auth/register")
async def api_register(request: RegisterRequest):
    """Register a new user."""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Haslo musi miec minimum 6 znakow")
    if "@" not in request.email:
        raise HTTPException(status_code=400, detail="Nieprawidlowy adres email")
    try:
        user = await register_user(db, request.email, request.password, request.full_name)
        token = create_access_token(data={"sub": user["id"], "email": user["email"]})
        return {"user": user, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/auth/login")
async def api_login(request: LoginRequest):
    """Login and get JWT token."""
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Nieprawidlowy email lub haslo")
    token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    return {"user": user, "token": token}

@api_router.get("/auth/me")
async def api_get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


# ============ Admin Routes ============

class AdminCreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    is_admin: bool = False

class AdminUpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

async def require_admin(user: dict = Depends(get_current_user)):
    """Require admin role."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Wymagane uprawnienia administratora")
    return user

@api_router.get("/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)."""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(200)
    # Batch count articles per user
    counts_cursor = db.articles.aggregate([{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}])
    counts = {doc["_id"]: doc["count"] async for doc in counts_cursor}
    result = []
    for u in users:
        if isinstance(u.get("created_at"), datetime):
            u["created_at"] = u["created_at"].isoformat()
        u["article_count"] = counts.get(u["id"], 0)
        result.append(u)
    return result

@api_router.post("/admin/users")
async def admin_create_user(request: AdminCreateUserRequest, admin: dict = Depends(require_admin)):
    """Create a new user (admin only)."""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Haslo musi miec minimum 6 znakow")
    if "@" not in request.email:
        raise HTTPException(status_code=400, detail="Nieprawidlowy adres email")
    try:
        user = await register_user(db, request.email, request.password, request.full_name)
        # Update admin flag if set
        if request.is_admin:
            await db.users.update_one({"id": user["id"]}, {"$set": {"is_admin": True}})
            user["is_admin"] = True
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, request: AdminUpdateUserRequest, admin: dict = Depends(require_admin)):
    """Update user role/permissions (admin only)."""
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="Uzytkownik nie znaleziony")
    
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.is_admin is not None:
        update_data["is_admin"] = request.is_admin
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if isinstance(updated.get("created_at"), datetime):
        updated["created_at"] = updated["created_at"].isoformat()
    return updated

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Deactivate a user (admin only). Cannot deactivate yourself."""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Nie mozesz dezaktywowac wlasnego konta")
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="Uzytkownik nie znaleziony")
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "Uzytkownik dezaktywowany", "id": user_id}


@api_router.get("/health")
async def health():
    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    return {
        "status": "healthy",
        "llm_key_configured": bool(llm_key),
        "llm_key_prefix": llm_key[:12] + "..." if llm_key else None
    }


# --- Article Generation ---

import asyncio


def _sync_run_generation_job(job_id: str, request_data: dict, user: dict):
    """Run article generation in a separate thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "generating", "stage": 1}}
        )

        loop = asyncio.new_event_loop()
        try:
            article_data = loop.run_until_complete(generate_article(
                topic=request_data["topic"],
                primary_keyword=request_data["primary_keyword"],
                secondary_keywords=request_data["secondary_keywords"],
                target_length=request_data["target_length"],
                tone=request_data["tone"],
                template=request_data["template"]
            ))
        finally:
            loop.close()

        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"stage": 3}}
        )

        seo_score = compute_seo_score(
            article_data,
            request_data["primary_keyword"],
            request_data["secondary_keywords"]
        )

        article_id = str(uuid.uuid4())
        article_doc = {
            "id": article_id,
            "user_id": user["id"],
            "workspace_id": user.get("workspace_id", user["id"]),
            "topic": request_data["topic"],
            "primary_keyword": request_data["primary_keyword"],
            "secondary_keywords": request_data["secondary_keywords"],
            "target_length": request_data["target_length"],
            "tone": request_data["tone"],
            "template": request_data["template"],
            "title": article_data.get("title", ""),
            "slug": article_data.get("slug", ""),
            "meta_title": article_data.get("meta_title", ""),
            "meta_description": article_data.get("meta_description", ""),
            "toc": article_data.get("toc", []),
            "sections": article_data.get("sections", []),
            "faq": article_data.get("faq", []),
            "internal_link_suggestions": article_data.get("internal_link_suggestions", []),
            "sources": article_data.get("sources", []),
            "seo_score": seo_score,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        sync_db.articles.insert_one(article_doc)

        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {
                "status": "completed",
                "stage": 4,
                "article_id": article_id
            }}
        )

    except Exception as e:
        err_msg = str(e)
        if "budget" in err_msg.lower() or "exceeded" in err_msg.lower():
            err_msg = "Budzet Universal Key wyczerpany. Doladuj w Profile > Universal Key > Add Balance."
        elif "502" in err_msg or "bad gateway" in err_msg.lower():
            err_msg = "Usluga AI tymczasowo niedostepna (blad 502). Sprawdz saldo Universal Key lub sprobuj za chwile."
        elif "429" in err_msg or "rate" in err_msg.lower():
            err_msg = "Przekroczono limit zapytan AI. Sprobuj za kilka minut."
        elif "401" in err_msg or "auth" in err_msg.lower():
            err_msg = "Blad autoryzacji klucza AI. Skontaktuj sie z administratorem."
        logging.error(f"Background generation error: {e}")
        sync_db.generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": err_msg}}
        )
    finally:
        sync_client.close()


@api_router.post("/articles/generate")
async def generate_article_endpoint(request: ArticleGenerateRequest, user: dict = Depends(get_current_user)):
    """Start async article generation - returns job ID immediately."""
    job_id = str(uuid.uuid4())
    
    job_doc = {
        "job_id": job_id,
        "status": "queued",
        "stage": 0,
        "article_id": None,
        "error": None,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.generation_jobs.insert_one(job_doc)
    
    request_data = {
        "topic": request.topic,
        "primary_keyword": request.primary_keyword,
        "secondary_keywords": request.secondary_keywords,
        "target_length": request.target_length,
        "tone": request.tone,
        "template": request.template
    }
    
    asyncio.get_event_loop().run_in_executor(
        None, _sync_run_generation_job, job_id, request_data, user
    )
    
    return {"job_id": job_id, "status": "queued"}


@api_router.get("/articles/generate/status/{job_id}")
async def get_generation_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check article generation job status."""
    job = await db.generation_jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    # Detect stale jobs: if generating for more than 5 minutes, mark as failed
    if job["status"] == "generating":
        from datetime import datetime as dt
        created = dt.fromisoformat(job["created_at"].replace("Z", "+00:00")) if isinstance(job["created_at"], str) else job["created_at"]
        elapsed = (datetime.now(timezone.utc) - created).total_seconds()
        if elapsed > 180:
            await db.generation_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": "failed", "error": "Generowanie przekroczylo limit czasu (3 min)"}}
            )
            job["status"] = "failed"
            job["error"] = "Generowanie przekroczylo limit czasu (3 min)"
    
    result = {
        "job_id": job_id,
        "status": job["status"],
        "stage": job.get("stage", 0)
    }
    
    if job["status"] == "completed":
        result["article_id"] = job.get("article_id")
        # Load article from DB
        if job.get("article_id"):
            article = await db.articles.find_one({"id": job["article_id"]}, {"_id": 0})
            if article:
                result["article"] = serialize_doc(article)
        # Cleanup old job
        await db.generation_jobs.delete_one({"job_id": job_id})
    elif job["status"] == "failed":
        result["error"] = job.get("error", "Nieznany blad")
        await db.generation_jobs.delete_one({"job_id": job_id})
    
    return result


# --- Scheduled Articles (must be before /articles/{article_id}) ---

@api_router.get("/articles/scheduled")
async def list_scheduled_articles(user: dict = Depends(get_current_user)):
    """List all scheduled articles."""
    articles = await db.articles.find(
        {"user_id": user["id"], "schedule_status": "scheduled"},
        {"_id": 0, "id": 1, "title": 1, "scheduled_at": 1, "scheduled_wp": 1}
    ).sort("scheduled_at", 1).to_list(50)
    return articles

@api_router.post("/articles/check-updates")
async def check_updates(user: dict = Depends(get_current_user)):
    """Check all articles for needed updates."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    articles = await db.articles.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).to_list(20)
    
    if not articles:
        return {"articles_needing_update": [], "up_to_date_articles": [], "summary": "Brak artykulow do sprawdzenia."}
    
    try:
        result = await check_articles_for_updates(articles, emergent_key)
        
        await db.update_checks.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    except Exception as e:
        logging.error(f"Auto-update check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Article CRUD ---

@api_router.get("/articles")
async def list_articles(user: dict = Depends(get_current_user)):
    """List articles scoped to user (admin sees all)."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    articles = await db.articles.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [{**serialize_doc(a)} for a in articles]

# NOTE: All /articles/STATIC_PATH routes must be placed BEFORE /articles/{article_id}
# to avoid FastAPI treating the static path as an article_id.

@api_router.get("/articles/categories-list")
async def list_categories_safe(user: dict = Depends(get_current_user)):
    """Get all unique categories (safe path to avoid conflict)."""
    pipeline = [
        {"$match": {"category": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.articles.aggregate(pipeline).to_list(50)
    return [r["_id"] for r in result]


@api_router.get("/articles/{article_id}")
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    """Get a single article by ID (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    return serialize_doc(article)


def _slugify(text: str) -> str:
    """Create a URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r'[ąàáâãäå]', 'a', text)
    text = re.sub(r'[ćçč]', 'c', text)
    text = re.sub(r'[ęèéêë]', 'e', text)
    text = re.sub(r'[łl]', 'l', text)
    text = re.sub(r'[ńñ]', 'n', text)
    text = re.sub(r'[óòôõö]', 'o', text)
    text = re.sub(r'[śšş]', 's', text)
    text = re.sub(r'[żźž]', 'z', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text[:80].strip('-')


def _parse_html_to_sections(html: str) -> list:
    """Parse HTML content from the visual editor back into structured sections."""
    if not html or not html.strip():
        return []
    
    # Split HTML by h2 tags to get sections
    # Pattern: find all h2 and content between them
    parts = re.split(r'(<h2[^>]*>.*?</h2>)', html, flags=re.IGNORECASE | re.DOTALL)
    
    sections = []
    current_section = None
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Check if this is an h2 heading
        h2_match = re.match(r'<h2[^>]*(?:id="([^"]*)")?[^>]*>(.*?)</h2>', part, re.IGNORECASE | re.DOTALL)
        if h2_match:
            # Save previous section
            if current_section:
                sections.append(current_section)
            
            heading_text = re.sub(r'<[^>]+>', '', h2_match.group(2)).strip()
            anchor = h2_match.group(1) or _slugify(heading_text)
            current_section = {
                "heading": heading_text,
                "anchor": anchor,
                "content": "",
                "subsections": []
            }
        elif current_section is not None:
            # Process content within current section - split by h3
            h3_parts = re.split(r'(<h3[^>]*>.*?</h3>)', part, flags=re.IGNORECASE | re.DOTALL)
            current_subsection = None
            
            for h3_part in h3_parts:
                h3_part = h3_part.strip()
                if not h3_part:
                    continue
                
                h3_match = re.match(r'<h3[^>]*(?:id="([^"]*)")?[^>]*>(.*?)</h3>', h3_part, re.IGNORECASE | re.DOTALL)
                if h3_match:
                    if current_subsection:
                        current_section["subsections"].append(current_subsection)
                    
                    sub_heading = re.sub(r'<[^>]+>', '', h3_match.group(2)).strip()
                    sub_anchor = h3_match.group(1) or _slugify(sub_heading)
                    current_subsection = {
                        "heading": sub_heading,
                        "anchor": sub_anchor,
                        "content": ""
                    }
                elif current_subsection is not None:
                    current_subsection["content"] += h3_part
                else:
                    current_section["content"] += h3_part
            
            if current_subsection:
                current_section["subsections"].append(current_subsection)
    
    # Don't forget the last section
    if current_section:
        sections.append(current_section)
    
    # Clean up content - trim whitespace
    for section in sections:
        section["content"] = section["content"].strip()
        for sub in section.get("subsections", []):
            sub["content"] = sub["content"].strip()
    
    return sections


@api_router.put("/articles/{article_id}")
async def update_article(article_id: str, request: ArticleUpdateRequest, user: dict = Depends(get_current_user)):
    """Update an existing article (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    
    # Sync html_content back to sections so SEO scorer has updated data
    html_to_parse = update_data.get("html_content", "")
    if html_to_parse:
        logging.info(f"Parsing html_content ({len(html_to_parse)} chars) to sections")
        parsed_sections = _parse_html_to_sections(html_to_parse)
        logging.info(f"Parsed {len(parsed_sections)} sections from html_content")
        if parsed_sections:
            update_data["sections"] = parsed_sections
            # Also extract title from H1 if present
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_to_parse, re.IGNORECASE | re.DOTALL)
            if title_match:
                new_title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip()
                if new_title:
                    update_data["title"] = new_title
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Save version history before updating
    version_doc = {
        "id": str(uuid.uuid4()),
        "article_id": article_id,
        "user_id": user.get("id", ""),
        "version_data": {k: v for k, v in article.items() if k not in ("_id",)},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.article_versions.insert_one(version_doc)
    
    await db.articles.update_one({"id": article_id}, {"$set": update_data})
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return serialize_doc(article)


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    """Delete an article (owner or admin)."""
    article = await db.articles.find_one({"id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    await db.articles.delete_one({"id": article_id})
    return {"message": "Article deleted", "id": article_id}


# --- SEO Scoring ---

@api_router.post("/articles/{article_id}/score")
async def score_article(article_id: str, request: ScoreRequest):
    """Compute SEO score for an article."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    score = compute_seo_score(article, request.primary_keyword, request.secondary_keywords)
    
    # Update score in DB
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {"seo_score": score, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return score


# --- Export ---

@api_router.post("/articles/{article_id}/export")
async def export_article(article_id: str, request: ExportRequest):
    """Export article in various formats."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if request.format == "facebook":
        content = generate_facebook_post(article)
        return {"format": "facebook", "content": content}
    
    elif request.format == "google_business":
        content = generate_google_business_post(article)
        return {"format": "google_business", "content": content}
    
    elif request.format == "html":
        html = generate_full_html(article)
        return {"format": "html", "content": html}
    
    elif request.format == "wordpress":
        styled_content = build_styled_wordpress_content(article)
        return {"format": "wordpress", "content": styled_content}
    
    elif request.format == "pdf":
        pdf_bytes = generate_pdf_bytes(article)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={article.get('slug', 'article')}.pdf"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown format: {request.format}")



# --- Regeneration ---

class RegenerateRequest(BaseModel):
    section: str  # "faq", "meta"

@api_router.post("/articles/{article_id}/regenerate")
async def regenerate_section(article_id: str, request: RegenerateRequest):
    """Regenerate a specific section of the article using AI."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        from article_generator import ARTICLE_SYSTEM_PROMPT
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise ValueError("EMERGENT_LLM_KEY not configured")
        
        topic = article.get("topic", "")
        primary_keyword = article.get("primary_keyword", "")
        
        if request.section == "faq":
            prompt = f"""Na podstawie artykułu o temacie: "{topic}" (słowo kluczowe: "{primary_keyword}"), wygeneruj 6-8 pytań FAQ ze szczegółowymi odpowiedziami.

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown):
{{
  "faq": [
    {{
      "question": "Pytanie FAQ (naturalne, jak w wyszukiwarce)",
      "answer": "Szczegółowa odpowiedź (minimum 30 słów, konkretna i merytoryczna)"
    }}
  ]
}}"""
        elif request.section == "meta":
            prompt = f"""Na podstawie artykułu o temacie: "{topic}" (słowo kluczowe: "{primary_keyword}"), wygeneruj nowy meta tytuł i meta opis zoptymalizowane pod SEO.

Odpowiedz WYŁĄCZNIE w formacie JSON (bez markdown):
{{
  "meta_title": "Meta tytuł SEO (max 60 znaków, zawiera słowo kluczowe)",
  "meta_description": "Meta opis SEO (120-160 znaków, zachęcający do kliknięcia, zawiera słowo kluczowe)"
}}"""
        else:
            raise HTTPException(status_code=400, detail=f"Unknown section: {request.section}")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"regen-{article_id}-{request.section}",
            system_message="Jesteś ekspertem SEO od księgowości w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )
        chat.with_model("openai", "gpt-4.1-mini")
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        import re
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = re.sub(r'^```(?:json)?\s*', '', clean_response)
            clean_response = re.sub(r'\s*```$', '', clean_response)
        
        result = json.loads(clean_response)
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# --- Topic Suggestions ---

@api_router.post("/topics/suggest")
async def suggest_topics_endpoint(request: TopicSuggestRequest):
    """Get AI-powered topic suggestions."""
    try:
        result = await suggest_topics(
            category=request.category,
            context=request.context
        )
        return result
    except Exception as e:
        logging.error(f"Topic suggestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Dashboard Stats ---

@api_router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics scoped to user (admin sees all)."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    total_articles = await db.articles.count_documents(query)
    
    # Average SEO score
    match_query = {**query, "seo_score.percentage": {"$exists": True}}
    pipeline = [
        {"$match": match_query},
        {"$group": {"_id": None, "avg_score": {"$avg": "$seo_score.percentage"}}}
    ]
    avg_result = await db.articles.aggregate(pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg_score"]) if avg_result else 0
    
    # Articles needing improvement (score < 70)
    needs_query = {**query, "seo_score.percentage": {"$lt": 70}}
    needs_improvement = await db.articles.count_documents(needs_query)
    
    return {
        "total_articles": total_articles,
        "avg_seo_score": avg_score,
        "needs_improvement": needs_improvement
    }


# --- Image Generation ---

class ReferenceImageData(BaseModel):
    data: str  # base64 encoded image
    mime_type: str  # e.g. "image/png", "image/jpeg"
    name: Optional[str] = None

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "hero"
    article_id: Optional[str] = None
    variation_type: Optional[str] = None  # color, composition, mood, simplify
    reference_image: Optional[ReferenceImageData] = None  # backward compat (single)
    reference_images: Optional[List[ReferenceImageData]] = None  # multiple attachments

@api_router.get("/image-styles")
async def list_image_styles():
    """Return all available image styles."""
    return get_all_image_styles()

def _sync_generate_image(job_id: str, user_id: str, prompt: str, style: str, article_id: str,
                          variation_type: str, ref_images_data: list):
    """Run image generation in a separate thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        article_context = None
        if article_id:
            article = sync_db.articles.find_one({"id": article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article

        loop = asyncio.new_event_loop()
        try:
            if variation_type:
                result = loop.run_until_complete(generate_image_variant(
                    original_prompt=prompt, style=style, variation_type=variation_type,
                    article_context=article_context, reference_images=ref_images_data
                ))
            else:
                result = loop.run_until_complete(generate_image(
                    prompt=prompt, style=style, article_context=article_context,
                    reference_images=ref_images_data
                ))
        finally:
            loop.close()

        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id, "user_id": user_id, "prompt": prompt, "style": style,
            "article_id": article_id, "variation_type": variation_type,
            "mime_type": result["mime_type"], "data": result["data"],
            "has_reference": ref_images_data is not None,
            "num_references": len(ref_images_data) if ref_images_data else 0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        sync_db.images.insert_one(image_doc)

        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "result": {
                "id": image_id, "prompt": prompt, "style": style,
                "mime_type": result["mime_type"], "data": result["data"],
                "created_at": image_doc["created_at"]
            }, "updated_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        logging.error(f"Image generation job {job_id} failed: {e}")
        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now(timezone.utc)}}
        )
    finally:
        sync_client.close()


@api_router.post("/images/generate")
async def generate_image_endpoint(request: ImageGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate an image using Gemini Nano Banana model (async with polling)."""
    try:
        allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        ref_images_list = []
        if request.reference_images:
            for ref in request.reference_images:
                if ref.mime_type not in allowed_mime:
                    raise HTTPException(status_code=400, detail=f"Nieobslugiwany format pliku: {ref.mime_type}. Dozwolone: PNG, JPG, WEBP")
                if len(ref.data) > 7_000_000:
                    raise HTTPException(status_code=400, detail="Jeden z plikow jest zbyt duzy. Maksymalny rozmiar: 5MB")
                ref_images_list.append({"data": ref.data, "mime_type": ref.mime_type})
        elif request.reference_image:
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku. Dozwolone: PNG, JPG, WEBP")
            if len(request.reference_image.data) > 7_000_000:
                raise HTTPException(status_code=400, detail="Plik jest zbyt duzy. Maksymalny rozmiar: 5MB")
            ref_images_list.append({"data": request.reference_image.data, "mime_type": request.reference_image.mime_type})

        ref_images_data = ref_images_list if ref_images_list else None
        job_id = str(uuid.uuid4())
        await db.image_generation_jobs.insert_one({
            "job_id": job_id, "status": "processing",
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        })

        asyncio.get_event_loop().run_in_executor(
            None, _sync_generate_image, job_id, user["id"], request.prompt, request.style,
            request.article_id, request.variation_type, ref_images_data
        )
        return {"job_id": job_id, "status": "processing"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/images/generate/status/{job_id}")
async def image_generation_status(job_id: str):
    """Poll image generation job status."""
    job = await db.image_generation_jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "completed":
        await db.image_generation_jobs.delete_one({"job_id": job_id})
        return {"status": "completed", "result": job.get("result", {})}
    if job["status"] == "failed":
        await db.image_generation_jobs.delete_one({"job_id": job_id})
        return {"status": "failed", "error": job.get("error", "Unknown error")}
    return {"status": "processing"}


@api_router.get("/images/{image_id}")
async def get_image(image_id: str):
    """Get a single image by ID."""
    image = await db.images.find_one({"id": image_id}, {"_id": 0})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "id": image["id"],
        "prompt": image.get("prompt", ""),
        "style": image.get("style", ""),
        "mime_type": image.get("mime_type", ""),
        "data": image.get("data", ""),
        "article_id": image.get("article_id"),
        "created_at": image.get("created_at")
    }


@api_router.get("/articles/{article_id}/images")
async def get_article_images(article_id: str):
    """Get all images for a specific article."""
    images = await db.images.find(
        {"article_id": article_id}, 
        {"_id": 0, "data": 0}
    ).sort("created_at", -1).to_list(50)
    return images


@api_router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image."""
    result = await db.images.delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted", "id": image_id}


# --- Image Library ---

@api_router.get("/library/images")
async def library_list_images(
    q: Optional[str] = None,
    style: Optional[str] = None,
    tag: Optional[str] = None,
    article_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: dict = Depends(get_current_user)
):
    """List all images for current user (admin sees all). Supports filtering."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    
    if q:
        query["prompt"] = {"$regex": q, "$options": "i"}
    if style:
        query["style"] = style
    if tag:
        query["tags"] = tag
    if article_id:
        query["article_id"] = article_id
    
    # Get total count
    total = await db.images.count_documents(query)
    
    # Fetch images - include data for thumbnails
    images = await db.images.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
    
    # Mark all as having data
    for img in images:
        img["has_data"] = bool(img.get("data"))
    
    return {
        "images": images,
        "total": total,
        "limit": limit,
        "offset": offset
    }


class ImageTagsRequest(BaseModel):
    tags: List[str] = []

@api_router.put("/images/{image_id}/tags")
async def update_image_tags(image_id: str, request: ImageTagsRequest, user: dict = Depends(get_current_user)):
    """Update tags on an image."""
    image = await db.images.find_one({"id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    if not user.get("is_admin") and image.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    # Clean tags
    clean_tags = [t.strip().lower() for t in request.tags if t.strip()]
    await db.images.update_one(
        {"id": image_id},
        {"$set": {"tags": clean_tags, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"id": image_id, "tags": clean_tags}


@api_router.get("/library/tags")
async def library_list_tags(user: dict = Depends(get_current_user)):
    """List all unique tags for current user's images."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    pipeline = [
        {"$match": {**query, "tags": {"$exists": True, "$ne": []}}},
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 50}
    ]
    tags = await db.images.aggregate(pipeline).to_list(50)
    return [{"tag": t["_id"], "count": t["count"]} for t in tags]


# --- AI Image Editing ---

class ImageEditRequest(BaseModel):
    mode: str  # "inpaint", "background", "style_transfer", "enhance"
    prompt: str
    image_id: Optional[str] = None  # existing image to edit
    source_image: Optional[ReferenceImageData] = None  # or send directly

@api_router.post("/images/edit")
async def edit_image_endpoint(request: ImageEditRequest, user: dict = Depends(get_current_user)):
    """AI-powered image editing: inpaint, background change, style transfer."""
    try:
        # Get source image
        source_data = None
        if request.image_id:
            img_doc = await db.images.find_one({"id": request.image_id})
            if not img_doc:
                raise HTTPException(status_code=404, detail="Obraz zrodlowy nie znaleziony")
            source_data = {"data": img_doc["data"], "mime_type": img_doc["mime_type"]}
        elif request.source_image:
            source_data = {"data": request.source_image.data, "mime_type": request.source_image.mime_type}
        
        if not source_data:
            raise HTTPException(status_code=400, detail="Wymagany obraz zrodlowy (image_id lub source_image)")
        
        # Build edit prompt based on mode
        mode_instructions = {
            "inpaint": f"Modify this image based on the following instruction: {request.prompt}. Keep the overall composition but make the requested changes. Maintain professional quality.",
            "background": f"Change the background of this image: {request.prompt}. Keep the main subject/foreground elements intact but replace the background as described.",
            "style_transfer": f"Transform the style of this image: {request.prompt}. Keep the content and composition but apply the described artistic style.",
            "enhance": f"Enhance this image: {request.prompt}. Improve quality, colors, and details while maintaining the original content."
        }
        
        edit_prompt = mode_instructions.get(request.mode, mode_instructions["enhance"])
        
        result = await generate_image(
            prompt=edit_prompt,
            style="custom",
            reference_images=[source_data]
        )
        
        # Save edited image
        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id,
            "user_id": user["id"],
            "prompt": request.prompt,
            "style": f"edit_{request.mode}",
            "article_id": None,
            "variation_type": None,
            "edit_mode": request.mode,
            "source_image_id": request.image_id,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "tags": [request.mode, "edycja"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.images.insert_one(image_doc)
        
        return {
            "id": image_id,
            "prompt": request.prompt,
            "mode": request.mode,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "created_at": image_doc["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image edit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Multi-variant Generation ---

class MultiVariantRequest(BaseModel):
    prompt: str
    style: str = "hero"
    article_id: Optional[str] = None
    num_variants: int = 4
    reference_image: Optional[ReferenceImageData] = None  # backward compat
    reference_images: Optional[List[ReferenceImageData]] = None  # multiple attachments

def _sync_generate_batch(job_id: str, user_id: str, prompt: str, style: str,
                          article_id: str, num_variants: int, ref_images_data: list):
    """Run batch image generation in a separate thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        article_context = None
        if article_id:
            article = sync_db.articles.find_one({"id": article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article

        variant_suffixes = [
            "",
            " Create a different composition with alternative layout.",
            " Use a warmer, more inviting color palette.",
            " Make it more minimalist and clean with extra white space."
        ]

        saved = []
        for i in range(num_variants):
            modified_prompt = prompt + variant_suffixes[i]
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(generate_image(
                    prompt=modified_prompt, style=style,
                    article_context=article_context, reference_images=ref_images_data
                ))
            except Exception as e:
                saved.append({"error": str(e), "variant_index": i})
                continue
            finally:
                loop.close()

            image_id = str(uuid.uuid4())
            image_doc = {
                "id": image_id, "user_id": user_id, "prompt": prompt, "style": style,
                "article_id": article_id, "variation_type": f"batch_{i}",
                "mime_type": result["mime_type"], "data": result["data"],
                "tags": ["batch"], "created_at": datetime.now(timezone.utc).isoformat()
            }
            sync_db.images.insert_one(image_doc)
            saved.append({
                "id": image_id, "prompt": prompt, "style": style, "variant_index": i,
                "mime_type": result["mime_type"], "data": result["data"],
                "created_at": image_doc["created_at"]
            })
            # Update progress
            sync_db.image_generation_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"progress": i + 1, "updated_at": datetime.now(timezone.utc)}}
            )

        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "result": {"variants": saved, "total": len(saved)}, "updated_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        logging.error(f"Batch generation job {job_id} failed: {e}")
        sync_db.image_generation_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now(timezone.utc)}}
        )
    finally:
        sync_client.close()


@api_router.post("/images/generate-batch")
async def generate_batch_endpoint(request: MultiVariantRequest, user: dict = Depends(get_current_user)):
    """Generate multiple image variants at once (async with polling)."""
    if request.num_variants < 1 or request.num_variants > 4:
        raise HTTPException(status_code=400, detail="Liczba wariantow musi byc od 1 do 4")

    try:
        allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
        ref_images_list = []
        if request.reference_images:
            for ref in request.reference_images:
                if ref.mime_type not in allowed_mime:
                    raise HTTPException(status_code=400, detail=f"Nieobslugiwany format pliku: {ref.mime_type}")
                ref_images_list.append({"data": ref.data, "mime_type": ref.mime_type})
        elif request.reference_image:
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku")
            ref_images_list.append({"data": request.reference_image.data, "mime_type": request.reference_image.mime_type})
        ref_images_data = ref_images_list if ref_images_list else None

        job_id = str(uuid.uuid4())
        await db.image_generation_jobs.insert_one({
            "job_id": job_id, "status": "processing", "progress": 0,
            "total": request.num_variants,
            "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)
        })
        asyncio.get_event_loop().run_in_executor(
            None, _sync_generate_batch, job_id, user["id"], request.prompt, request.style,
            request.article_id, request.num_variants, ref_images_data
        )
        return {"job_id": job_id, "status": "processing", "total": request.num_variants}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Content Templates ---

@api_router.get("/templates")
async def list_templates():
    """Return all available content templates."""
    return get_all_templates()


# --- WordPress Integration ---

class WordPressSettingsRequest(BaseModel):
    wp_url: str
    wp_user: str
    wp_app_password: str

@api_router.get("/settings/wordpress")
async def get_wordpress_settings(user: dict = Depends(require_admin)):
    """Get WordPress settings (admin only)."""
    settings = await db.settings.find_one({"key": "wordpress"}, {"_id": 0})
    if not settings:
        return {"configured": False}
    return {
        "configured": True,
        "wp_url": settings.get("wp_url", ""),
        "wp_user": settings.get("wp_user", ""),
        "has_password": bool(settings.get("wp_app_password"))
    }

@api_router.post("/settings/wordpress")
async def save_wordpress_settings(request: WordPressSettingsRequest, user: dict = Depends(require_admin)):
    """Save WordPress settings (admin only)."""
    # Normalize URL - add https:// if missing
    wp_url = request.wp_url.strip().rstrip("/")
    if not wp_url.startswith("http://") and not wp_url.startswith("https://"):
        wp_url = f"https://{wp_url}"
    
    await db.settings.update_one(
        {"key": "wordpress"},
        {"$set": {
            "key": "wordpress",
            "wp_url": wp_url,
            "wp_user": request.wp_user,
            "wp_app_password": request.wp_app_password,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": user["id"]
        }},
        upsert=True
    )
    return {"message": "Ustawienia WordPress zapisane", "configured": True}

@api_router.post("/articles/{article_id}/publish-wordpress")
async def publish_article_to_wordpress(article_id: str, user: dict = Depends(get_current_user)):
    """Publish an article to WordPress as a draft."""
    # Get WordPress settings
    wp_settings = await db.settings.find_one({"key": "wordpress"})
    if not wp_settings or not wp_settings.get("wp_url"):
        raise HTTPException(status_code=400, detail="WordPress nie jest skonfigurowany. Przejdz do ustawien admina.")
    
    # Get article
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    # Check ownership
    if not user.get("is_admin") and article.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu do artykulu")
    
    try:
        result = await publish_to_wordpress(
            wp_url=wp_settings["wp_url"],
            wp_user=wp_settings["wp_user"],
            wp_app_password=wp_settings["wp_app_password"],
            article=article
        )
        
        if result.get("success"):
            # Save WP post reference
            await db.articles.update_one(
                {"id": article_id},
                {"$set": {
                    "wp_post_id": result.get("post_id"),
                    "wp_post_url": result.get("post_url"),
                    "wp_published_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            return result
        else:
            raise HTTPException(status_code=422, detail=result.get("error", "Blad publikacji na WordPress"))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WordPress publish error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wordpress/plugin")
async def download_wordpress_plugin(user: dict = Depends(get_current_user), request: object = None):
    """Generate and download the WordPress plugin file."""
    from starlette.requests import Request
    api_base = os.environ.get("API_BASE_URL", "")
    if not api_base:
        api_base = os.environ.get("REACT_APP_BACKEND_URL", "") + "/api"
    
    plugin_code = generate_wordpress_plugin(api_base)
    
    return Response(
        content=plugin_code.encode('utf-8'),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "attachment; filename=kurdynowski-importer.php"
        }
    )


# --- Article Series ---

class SeriesRequest(BaseModel):
    topic: str
    primary_keyword: str
    num_parts: int = 4
    source_text: str = ""

@api_router.post("/series/generate")
async def generate_series(request: SeriesRequest, user: dict = Depends(get_current_user)):
    """Generate a multi-part article series outline."""
    try:
        result = await generate_series_outline(
            topic=request.topic,
            primary_keyword=request.primary_keyword,
            num_parts=request.num_parts,
            source_text=request.source_text
        )
        
        # Save series to DB
        series_doc = {
            **result,
            "user_id": user["id"],
            "workspace_id": user.get("workspace_id", user["id"]),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "outline"
        }
        await db.series.insert_one(series_doc)
        
        return result
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI zwrocilo nieprawidlowy JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Series generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/series")
async def list_series(user: dict = Depends(get_current_user)):
    """List all series for current user."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    series = await db.series.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return series


# --- SEO Assistant ---

class SEOAssistantRequest(BaseModel):
    mode: str = "analyze"  # "analyze" or "chat"
    message: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

def _sync_seo_assistant(job_id: str, article_id: str, mode: str, message: str = None, history: list = None):
    """Run SEO assistant in a separate thread (sync) to avoid blocking event loop.
    litellm.completion() is synchronous, so it must run in a thread pool."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        article = sync_db.articles.find_one({"id": article_id}, {"_id": 0})
        if not article:
            sync_db.seo_assistant_jobs.update_one(
                {"job_id": job_id},
                {"$set": {"status": "failed", "error": "Article not found", "updated_at": datetime.now(timezone.utc)}}
            )
            return
        loop = asyncio.new_event_loop()
        try:
            if mode == "chat" and message:
                result = loop.run_until_complete(chat_about_seo(article=article, user_message=message, conversation_history=history or []))
            else:
                result = loop.run_until_complete(analyze_article_seo(article=article))
        finally:
            loop.close()
        sync_db.seo_assistant_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "completed", "result": result, "updated_at": datetime.now(timezone.utc)}}
        )
    except Exception as e:
        logging.error(f"SEO Assistant job {job_id} failed: {e}")
        sync_db.seo_assistant_jobs.update_one(
            {"job_id": job_id},
            {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now(timezone.utc)}}
        )
    finally:
        sync_client.close()

@api_router.post("/articles/{article_id}/seo-assistant")
async def seo_assistant_endpoint(article_id: str, request: SEOAssistantRequest):
    """AI SEO Assistant - starts async analysis or chat job."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    job_id = str(uuid.uuid4())
    await db.seo_assistant_jobs.insert_one({
        "job_id": job_id,
        "article_id": article_id,
        "mode": request.mode,
        "status": "processing",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    })
    asyncio.get_event_loop().run_in_executor(
        None, _sync_seo_assistant, job_id, article_id, request.mode, request.message, request.history
    )
    return {"job_id": job_id, "status": "processing"}

@api_router.get("/seo-assistant/status/{job_id}")
async def seo_assistant_status(job_id: str):
    """Poll SEO assistant job status."""
    job = await db.seo_assistant_jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job["status"] == "completed":
        await db.seo_assistant_jobs.delete_one({"job_id": job_id})
        return {"status": "completed", "result": job.get("result", {})}
    if job["status"] == "failed":
        await db.seo_assistant_jobs.delete_one({"job_id": job_id})
        return {"status": "failed", "error": job.get("error", "Unknown error")}
    return {"status": "processing"}


# --- Content Calendar ---

class CalendarRequest(BaseModel):
    period: str = "miesiac"  # miesiac, kwartal, polrocze

@api_router.post("/content-calendar/generate")
async def generate_calendar(request: CalendarRequest, user: dict = Depends(get_current_user)):
    """Generate AI content calendar."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    # Get existing article titles to avoid duplicates
    existing = await db.articles.find(
        {"user_id": user["id"]}, {"_id": 0, "title": 1}
    ).to_list(50)
    existing_titles = [a.get("title", "") for a in existing]
    
    now = datetime.now(timezone.utc)
    
    try:
        result = await generate_content_calendar(
            period=request.period,
            current_month=now.month,
            current_year=now.year,
            existing_titles=existing_titles,
            emergent_key=emergent_key
        )
        
        # Save calendar
        cal_id = str(uuid.uuid4())
        cal_doc = {
            "id": cal_id,
            "user_id": user["id"],
            "period": request.period,
            "plan": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.content_calendars.insert_one(cal_doc)
        
        return {"id": cal_id, **result}
    except Exception as e:
        logging.error(f"Content calendar error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/content-calendar/latest")
async def get_latest_calendar(user: dict = Depends(get_current_user)):
    """Get the most recent content calendar."""
    cal = await db.content_calendars.find_one(
        {"user_id": user["id"]},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    if not cal:
        return None
    return cal

@api_router.get("/content-calendar/list")
async def list_calendars(user: dict = Depends(get_current_user)):
    """List all content calendars."""
    cals = await db.content_calendars.find(
        {"user_id": user["id"]}, {"_id": 0, "id": 1, "period": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(20)
    return cals


# --- Article Import ---

class ImportUrlRequest(BaseModel):
    url: str
    optimize: bool = True

@api_router.post("/import/url")
async def import_article_from_url(request: ImportUrlRequest, user: dict = Depends(get_current_user)):
    """Import and optionally optimize an article from a URL."""
    try:
        scraped = await scrape_article_from_url(request.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Nie udalo sie pobrac artykulu: {str(e)}")
    
    if request.optimize:
        emergent_key = os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            raise HTTPException(status_code=500, detail="Brak klucza AI")
        
        try:
            optimized = await optimize_imported_article(
                title=scraped["title"],
                content_html=scraped["content_html"],
                emergent_key=emergent_key
            )
        except Exception as e:
            logging.error(f"Import optimization error: {e}")
            # Fall back to raw import
            optimized = {
                "title": scraped["title"],
                "sections": [{"heading": "Tresc", "anchor": "tresc", "content": scraped["content_html"][:5000], "subsections": []}],
                "primary_keyword": "",
                "secondary_keywords": [],
                "meta_title": scraped["title"][:60],
                "meta_description": scraped.get("meta_description", "")[:160],
                "faq": [],
                "toc": [],
                "sources": [],
                "internal_link_suggestions": []
            }
    else:
        optimized = {
            "title": scraped["title"],
            "sections": [{"heading": "Tresc", "anchor": "tresc", "content": scraped["content_html"][:5000], "subsections": []}],
            "primary_keyword": "",
            "secondary_keywords": [],
            "meta_title": scraped["title"][:60],
            "meta_description": scraped.get("meta_description", "")[:160],
            "faq": [],
            "toc": [],
            "sources": [],
            "internal_link_suggestions": []
        }
    
    # Save as article
    article_id = str(uuid.uuid4())
    article_doc = {
        "id": article_id,
        "user_id": user["id"],
        "workspace_id": user.get("workspace_id", user["id"]),
        "title": optimized.get("title", scraped["title"]),
        "slug": optimized.get("slug", ""),
        "primary_keyword": optimized.get("primary_keyword", ""),
        "secondary_keywords": optimized.get("secondary_keywords", []),
        "meta_title": optimized.get("meta_title", ""),
        "meta_description": optimized.get("meta_description", ""),
        "sections": optimized.get("sections", []),
        "faq": optimized.get("faq", []),
        "toc": optimized.get("toc", []),
        "sources": optimized.get("sources", []),
        "internal_link_suggestions": optimized.get("internal_link_suggestions", []),
        "source_url": request.url,
        "imported": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seo_score": {"percentage": 0}
    }
    
    await db.articles.insert_one(article_doc)
    article_doc.pop("_id", None)
    
    return article_doc

class ImportWordPressRequest(BaseModel):
    wp_url: str
    wp_user: str = ""
    wp_password: str = ""
    limit: int = 20

@api_router.post("/import/wordpress")
async def import_from_wp(request: ImportWordPressRequest, user: dict = Depends(get_current_user)):
    """List available articles from WordPress for import."""
    try:
        articles = await import_from_wordpress(
            wp_url=request.wp_url,
            wp_user=request.wp_user or None,
            wp_password=request.wp_password or None,
            limit=request.limit
        )
        return {"articles": articles, "count": len(articles)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Blad importu z WordPress: {str(e)}")


# --- Internal Linkbuilding ---

@api_router.post("/articles/{article_id}/linkbuilding")
async def suggest_internal_links(article_id: str, user: dict = Depends(get_current_user)):
    """AI-powered internal linkbuilding suggestions."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    # Get current article
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    # Get all user's articles
    all_articles = await db.articles.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "sections": 1}
    ).to_list(50)
    
    if len(all_articles) < 2:
        return {"outgoing_links": [], "incoming_links": [], "summary": "Potrzebujesz minimum 2 artykulow do linkowania wewnetrznego."}
    
    try:
        result = await analyze_internal_links(article, all_articles, emergent_key)
        
        # Save suggestions to article
        await db.articles.update_one(
            {"id": article_id},
            {"$set": {"linkbuilding_suggestions": result}}
        )
        
        return result
    except Exception as e:
        logging.error(f"Linkbuilding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# --- AI Chat Assistant ---

class ChatMessage(BaseModel):
    message: str
    article_id: str = ""

@api_router.post("/chat/message")
async def send_chat_message(request: ChatMessage, user: dict = Depends(get_current_user)):
    """Send a message to AI assistant."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    article_context = {}
    if request.article_id:
        article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
        if article:
            article_context = article
    
    session_id = f"chat-{user['id']}-{request.article_id or 'general'}"
    
    try:
        response = await chat_with_assistant(session_id, request.message, article_context, emergent_key)
        return {"response": response}
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/chat/clear")
async def clear_chat(user: dict = Depends(get_current_user)):
    """Clear chat session."""
    session_id = f"chat-{user['id']}-general"
    clear_chat_session(session_id)
    return {"status": "cleared"}


# --- Scheduled Publishing ---

class SchedulePublishRequest(BaseModel):
    scheduled_at: str  # ISO datetime string
    publish_to_wordpress: bool = True

@api_router.post("/articles/{article_id}/schedule")
async def schedule_article_publish(article_id: str, request: SchedulePublishRequest, user: dict = Depends(get_current_user)):
    """Schedule an article for future WordPress publishing."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    if not user.get("is_admin") and article.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    await db.articles.update_one(
        {"id": article_id},
        {"$set": {
            "scheduled_at": request.scheduled_at,
            "scheduled_wp": request.publish_to_wordpress,
            "schedule_status": "scheduled"
        }}
    )
    
    return {
        "message": f"Artykul zaplanowany na {request.scheduled_at}",
        "article_id": article_id,
        "scheduled_at": request.scheduled_at,
        "publish_to_wordpress": request.publish_to_wordpress
    }

@api_router.delete("/articles/{article_id}/schedule")
async def cancel_scheduled_publish(article_id: str, user: dict = Depends(get_current_user)):
    """Cancel a scheduled publication."""
    await db.articles.update_one(
        {"id": article_id},
        {"$unset": {"scheduled_at": "", "scheduled_wp": "", "schedule_status": ""}}
    )
    return {"message": "Planowana publikacja anulowana"}



# --- SEO Audit ---

class SEOAuditRequest(BaseModel):
    url: str

# Background job storage for SEO audit
_seo_audit_jobs = {}

def _sync_run_seo_audit(job_id: str, url: str, emergent_key: str, user_id: str):
    """Run SEO audit in thread to avoid blocking event loop."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _seo_audit_jobs[job_id]["status"] = "running"
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(run_seo_audit(url, emergent_key))
        finally:
            loop.close()
        audit_id = str(uuid.uuid4())
        sync_db.seo_audits.insert_one({
            "id": audit_id, "user_id": user_id, "url": url,
            "result": result, "created_at": datetime.now(timezone.utc).isoformat()
        })
        _seo_audit_jobs[job_id]["status"] = "completed"
        _seo_audit_jobs[job_id]["result"] = {"id": audit_id, **result}
    except Exception as e:
        logging.error(f"SEO audit background error: {e}")
        _seo_audit_jobs[job_id]["status"] = "failed"
        _seo_audit_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/seo-audit")
async def run_audit(request: SEOAuditRequest, user: dict = Depends(get_current_user)):
    """Start async SEO audit on a URL - returns job_id for polling."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    job_id = str(uuid.uuid4())
    _seo_audit_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "user_id": user["id"]
    }
    
    asyncio.get_event_loop().run_in_executor(None, _sync_run_seo_audit, job_id, request.url, emergent_key, user["id"])
    
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/seo-audit/status/{job_id}")
async def get_audit_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll SEO audit job status."""
    job = _seo_audit_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    result = {"job_id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _seo_audit_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _seo_audit_jobs[job_id]
    
    return result

@api_router.get("/seo-audit/history")
async def get_audit_history(user: dict = Depends(get_current_user)):
    """Get user's audit history."""
    audits = await db.seo_audits.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "url": 1, "created_at": 1, "result.overall_score": 1, "result.grade": 1}
    ).sort("created_at", -1).to_list(20)
    return audits


# --- Competition Analysis ---

class CompetitionRequest(BaseModel):
    article_id: str
    competitor_url: str

# Background job storage for competition analysis
_competition_jobs = {}

def _sync_run_competition(job_id: str, article: dict, competitor_url: str, emergent_key: str, user_id: str):
    """Run competition analysis in thread."""
    try:
        _competition_jobs[job_id]["status"] = "running"
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(analyze_competition(article, competitor_url, emergent_key))
        finally:
            loop.close()
        _competition_jobs[job_id]["status"] = "completed"
        _competition_jobs[job_id]["result"] = result
    except Exception as e:
        logging.error(f"Competition analysis background error: {e}")
        _competition_jobs[job_id]["status"] = "failed"
        _competition_jobs[job_id]["error"] = str(e)

@api_router.post("/competition/analyze")
async def analyze_comp(request: CompetitionRequest, user: dict = Depends(get_current_user)):
    """Start async competition analysis - returns job_id for polling."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    job_id = str(uuid.uuid4())
    _competition_jobs[job_id] = {
        "status": "queued",
        "result": None,
        "error": None,
        "user_id": user["id"]
    }
    
    asyncio.get_event_loop().run_in_executor(None, _sync_run_competition, job_id, article, request.competitor_url, emergent_key, user["id"])
    
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/competition/status/{job_id}")
async def get_competition_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll competition analysis job status."""
    job = _competition_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    result = {"job_id": job_id, "status": job["status"]}
    
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _competition_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _competition_jobs[job_id]
    
    return result


# --- Keyword Analytics ---

class KeywordAnalyticsRequest(BaseModel):
    keywords: List[str] = []
    industry: str = "rachunkowość i podatki"

_keyword_analytics_jobs = {}

def _sync_run_keyword_analytics(job_id: str, keywords: list, industry: str, emergent_key: str, user_id: str):
    """Run keyword analytics in thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _keyword_analytics_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"kw-analytics-{job_id[:8]}",
            system_message="Jesteś ekspertem SEO i analityki słów kluczowych w Polsce. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )
        
        kw_list = ", ".join(keywords[:10]) if keywords else "ulgi podatkowe, VAT 2026, ZUS, PIT, CIT, księgowość online, biuro rachunkowe, faktury elektroniczne"
        
        prompt = f"""Jesteś ekspertem SEO w branży: {industry}.
Przeanalizuj poniższe słowa kluczowe i wygeneruj dane analityczne w formacie JSON.

Słowa kluczowe: {kw_list}

Dla każdego słowa kluczowego podaj:
- keyword: nazwa
- monthly_searches: szacunkowa miesięczna liczba wyszukiwań (realistyczna dla polskiego rynku)
- difficulty: trudność 1-100
- trend: "rosnący", "stabilny" lub "malejący"
- trend_data: tablica 6 wartości (ostatnie 6 miesięcy, np. [80,85,90,88,95,100])
- cpc_pln: szacunkowy koszt za klik w PLN
- season_peak: miesiąc szczytowy (1-12)
- related_topics: lista 3 powiązanych tematów na artykuły
- opportunity_score: wynik szansy 1-100 (wysoki = łatwe do pozycjonowania + dużo wyszukiwań)

Odpowiedz TYLKO prawidłowym JSON: {{"keywords": [...]}}"""
        
        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        
        import json as json_mod
        data = json_mod.loads(text)
        
        _keyword_analytics_jobs[job_id]["status"] = "completed"
        _keyword_analytics_jobs[job_id]["result"] = data
        
        sync_db.keyword_analytics.insert_one({
            "id": job_id, "user_id": user_id, "keywords": keywords,
            "result": data, "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Keyword analytics error: {e}")
        _keyword_analytics_jobs[job_id]["status"] = "failed"
        _keyword_analytics_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/keyword-analytics/analyze")
async def analyze_keywords(request: KeywordAnalyticsRequest, user: dict = Depends(get_current_user)):
    """Start async keyword analytics."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    job_id = str(uuid.uuid4())
    _keyword_analytics_jobs[job_id] = {"status": "queued", "result": None, "error": None, "user_id": user["id"]}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_keyword_analytics, job_id, request.keywords, request.industry, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/keyword-analytics/status/{job_id}")
async def get_keyword_analytics_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll keyword analytics job status."""
    job = _keyword_analytics_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _keyword_analytics_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _keyword_analytics_jobs[job_id]
    return result

@api_router.get("/keyword-analytics/history")
async def get_keyword_analytics_history(user: dict = Depends(get_current_user)):
    """Get keyword analytics history."""
    docs = await db.keyword_analytics.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return docs


# --- AI Rewriter ---

class RewriteRequest(BaseModel):
    text: str
    style: str = "profesjonalny"
    article_id: str = ""

_rewrite_jobs = {}

def _sync_run_rewrite(job_id: str, text: str, style: str, emergent_key: str):
    """Run rewrite in thread."""
    try:
        _rewrite_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"rewrite-{job_id[:8]}",
            system_message="Jesteś ekspertem od pisania treści w języku polskim. Przepisuj tekst zgodnie z instrukcjami."
        )
        
        style_prompts = {
            "profesjonalny": "Przepisz tekst w profesjonalnym, eksperckim tonie. Używaj fachowej terminologii podatkowej i księgowej. Zachowaj precyzję i powagę.",
            "przystępny": "Przepisz tekst prostym, przystępnym językiem. Wyjaśniaj trudne terminy. Używaj przykładów z życia. Pisz jak do osoby bez wiedzy podatkowej.",
            "ekspercki": "Przepisz tekst w tonie autorytetu branżowego. Cytuj przepisy prawne, dodawaj kontekst historyczny i porównania. Pisz jak doradca podatkowy z 20-letnim doświadczeniem.",
            "seo": "Przepisz tekst z optymalizacją pod SEO. Używaj naturalnie słów kluczowych, twórz krótkie akapity, dodaj pytania retoryczne i wezwania do działania.",
            "skrócony": "Skróć tekst zachowując najważniejsze informacje. Usuń powtórzenia i zbędne słowa. Maks 50% oryginalnej długości.",
            "rozszerzony": "Rozszerz tekst o dodatkowe szczegóły, przykłady, dane liczbowe i kontekst prawny. Dodaj minimum 50% więcej treści."
        }
        
        instruction = style_prompts.get(style, style_prompts["profesjonalny"])
        
        prompt = f"""{instruction}

ORYGINALNY TEKST:
{text[:8000]}

WAŻNE:
- Zachowaj formatowanie HTML jeśli występuje
- Nie dodawaj komentarzy, zwróć TYLKO przepisany tekst
- Zachowaj wszystkie dane liczbowe i faktograficzne"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()
        _rewrite_jobs[job_id]["status"] = "completed"
        _rewrite_jobs[job_id]["result"] = {"rewritten_text": response.strip(), "style": style}
    except Exception as e:
        logging.error(f"Rewrite error: {e}")
        _rewrite_jobs[job_id]["status"] = "failed"
        _rewrite_jobs[job_id]["error"] = str(e)

@api_router.post("/rewrite")
async def rewrite_text(request: RewriteRequest, user: dict = Depends(get_current_user)):
    """Start async text rewrite."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Brak tekstu do przepisania")
    
    job_id = str(uuid.uuid4())
    _rewrite_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_rewrite, job_id, request.text, request.style, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/rewrite/status/{job_id}")
async def get_rewrite_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll rewrite job status."""
    job = _rewrite_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _rewrite_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _rewrite_jobs[job_id]
    return result


# --- Newsletter Generator ---

class NewsletterRequest(BaseModel):
    title: str = ""
    article_ids: List[str] = []
    style: str = "informacyjny"

@api_router.post("/newsletter/generate")
async def generate_newsletter(request: NewsletterRequest, user: dict = Depends(get_current_user)):
    """Generate newsletter from selected articles."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    # Get articles
    if request.article_ids:
        articles = await db.articles.find({"id": {"$in": request.article_ids}, "user_id": user["id"]}, {"_id": 0}).to_list(20)
    else:
        articles = await db.articles.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    if not articles:
        raise HTTPException(status_code=400, detail="Brak artykułów do newslettera")
    
    articles_summary = ""
    for a in articles:
        articles_summary += f"\n- Tytuł: {a.get('title','')}\n  Meta opis: {a.get('meta_description','')}\n  SEO: {a.get('seo_score',{}).get('percentage',0)}%\n"
    
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat = LlmChat(
        api_key=emergent_key,
        session_id=f"newsletter-{uuid.uuid4().hex[:8]}",
        system_message="Jesteś ekspertem od email marketingu dla biur rachunkowych w Polsce. Tworzysz profesjonalne newslettery w HTML."
    )
    
    title = request.title or "Cotygodniowy newsletter podatkowy"
    
    prompt = f"""Wygeneruj profesjonalny newsletter email w HTML dla biura rachunkowego Kurdynowski.
Tytuł: {title}
Styl: {request.style}

Artykuły do uwzględnienia:
{articles_summary}

Wygeneruj:
1. Nagłówek newslettera z logo tekstowym "Kurdynowski"
2. Krótkie powitanie (2-3 zdania)
3. Dla każdego artykułu: tytuł, krótki opis (2-3 zdania), przycisk "Czytaj więcej"
4. Sekcja "Ważne terminy" z najbliższymi datami podatkowymi
5. Stopka z danymi kontaktowymi

Format: kompletny HTML email z inline CSS. Kolory: #04389E (główny), #0B1220 (tekst), #F7F8FA (tło).
Zwróć TYLKO kod HTML."""
    
    response = await chat.send_message(UserMessage(text=prompt))
    html = response.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1].rsplit("```", 1)[0]
    
    newsletter_id = str(uuid.uuid4())
    await db.newsletters.insert_one({
        "id": newsletter_id,
        "user_id": user["id"],
        "title": title,
        "html": html,
        "article_ids": [a["id"] for a in articles],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"id": newsletter_id, "title": title, "html": html}

@api_router.get("/newsletter/list")
async def list_newsletters(user: dict = Depends(get_current_user)):
    """List generated newsletters."""
    docs = await db.newsletters.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return docs

@api_router.get("/newsletter/{newsletter_id}")
async def get_newsletter(newsletter_id: str, user: dict = Depends(get_current_user)):
    """Get a specific newsletter."""
    doc = await db.newsletters.find_one({"id": newsletter_id, "user_id": user["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Newsletter nie znaleziony")
    return doc


# --- Subscriptions & Payments ---

@api_router.get("/subscription/plans")
async def list_subscription_plans():
    """Return all available subscription plans."""
    return get_all_plans()

class SubscriptionCheckoutRequest(BaseModel):
    plan_id: str

@api_router.post("/subscription/checkout")
async def create_checkout(request: SubscriptionCheckoutRequest, user: dict = Depends(get_current_user)):
    """Create a tpay checkout session for the selected plan."""
    plan = get_plan(request.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Nieznany plan subskrypcji")
    
    # Get base URL for callbacks
    base_url = os.environ.get("APP_BASE_URL", os.environ.get("REACT_APP_BACKEND_URL", ""))
    callback_url = f"{base_url}/api/subscription/webhook"
    return_url = f"{base_url}/cennik"
    
    result = await create_tpay_transaction(
        plan_id=request.plan_id,
        user=user,
        callback_url=callback_url,
        return_url=return_url
    )
    
    if result.get("success"):
        # Save pending subscription
        sub_id = str(uuid.uuid4())
        sub_doc = {
            "id": sub_id,
            "user_id": user["id"],
            "plan_id": request.plan_id,
            "plan_name": plan["name"],
            "price_netto": plan["price_netto"],
            "price_brutto": plan["price_brutto"],
            "transaction_id": result.get("transaction_id"),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(sub_doc)
        
        return {
            "subscription_id": sub_id,
            "transaction_url": result.get("transaction_url"),
            "plan": plan
        }
    else:
        error_msg = result.get("error", "Blad tworzenia platnosci")
        if result.get("demo"):
            raise HTTPException(status_code=503, detail=error_msg)
        raise HTTPException(status_code=502, detail=error_msg)

@api_router.post("/subscription/webhook")
async def tpay_webhook(request_data: dict):
    """Handle tpay payment notification."""
    tx_id = request_data.get("tr_id") or request_data.get("transactionId")
    status = request_data.get("tr_status") or request_data.get("status")
    
    if not tx_id:
        raise HTTPException(status_code=400, detail="Missing transaction ID")
    
    # Find subscription
    sub = await db.subscriptions.find_one({"transaction_id": str(tx_id)})
    if not sub:
        logging.warning(f"Subscription not found for tx: {tx_id}")
        return {"status": "ok"}
    
    if status in ("TRUE", "paid", "correct"):
        # Payment confirmed
        end_date = calculate_subscription_end(sub["plan_id"])
        
        await db.subscriptions.update_one(
            {"id": sub["id"]},
            {"$set": {
                "status": "active",
                "paid_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": end_date.isoformat()
            }}
        )
        
        # Update user subscription status
        await db.users.update_one(
            {"id": sub["user_id"]},
            {"$set": {
                "subscription_plan": sub["plan_id"],
                "subscription_active": True,
                "subscription_expires": end_date.isoformat()
            }}
        )
        
        logging.info(f"Subscription activated: user={sub['user_id']}, plan={sub['plan_id']}")
    elif status in ("FALSE", "failed", "error"):
        await db.subscriptions.update_one(
            {"id": sub["id"]},
            {"$set": {"status": "failed"}}
        )
    
    return {"status": "ok"}

@api_router.get("/subscription/status")
async def get_subscription_status(user: dict = Depends(get_current_user)):
    """Get current user's subscription status."""
    # Check latest active subscription
    sub = await db.subscriptions.find_one(
        {"user_id": user["id"], "status": "active"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0, "subscription_plan": 1, "subscription_active": 1, "subscription_expires": 1})
    
    return {
        "has_subscription": bool(sub),
        "plan": sub.get("plan_id") if sub else None,
        "plan_name": sub.get("plan_name") if sub else None,
        "expires_at": sub.get("expires_at") if sub else None,
        "status": sub.get("status") if sub else "none",
        "user_subscription": user_data
    }


# --- AI Article Suggestions (Smart) ---

class AIArticleSuggestionsRequest(BaseModel):
    count: int = 6
    focus: str = ""  # optional focus area

_ai_suggestions_jobs = {}

def _sync_run_ai_suggestions(job_id: str, existing_articles: list, focus: str, count: int, emergent_key: str, user_id: str):
    """Run AI article suggestions in thread."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _ai_suggestions_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"ai-suggestions-{job_id[:8]}",
            system_message="Jesteś ekspertem SEO i content strategistą dla polskiej branży księgowej i podatkowej. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        existing_titles = [a.get("title", "") for a in existing_articles[:20]]
        existing_keywords = list(set([a.get("primary_keyword", "") for a in existing_articles[:20] if a.get("primary_keyword")]))
        titles_str = "\n".join([f"- {t}" for t in existing_titles]) if existing_titles else "Brak artykułów"
        keywords_str = ", ".join(existing_keywords[:15]) if existing_keywords else "brak"
        focus_str = f"\nSkup się szczególnie na: {focus}" if focus else ""

        prompt = f"""Przeanalizuj istniejące artykuły na blogu biura rachunkowego i zaproponuj {count} NOWYCH tematów artykułów, które uzupełnią luki w treści i przyciągną ruch.

Istniejące artykuły:
{titles_str}

Użyte słowa kluczowe: {keywords_str}
{focus_str}

Dla każdej sugestii podaj:
- title: tytuł artykułu (przyciągający, SEO-friendly, po polsku)
- primary_keyword: główne słowo kluczowe (2-4 słowa)
- secondary_keywords: lista 3-5 dodatkowych słów kluczowych
- description: krótki opis artykułu (2-3 zdania)
- rationale: dlaczego warto napisać ten artykuł (uzupełnia lukę, sezonowość, trending, itp.)
- estimated_traffic: szacunkowy miesięczny ruch (np. "500-1000")
- difficulty: "łatwa", "średnia", "trudna"
- priority: "wysoki", "średni", "niski"
- content_type: "poradnik", "analiza", "case study", "lista", "aktualności"
- seasonal: true/false (czy temat jest sezonowy)

Odpowiedz TYLKO prawidłowym JSON: {{"suggestions": [...]}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text)

        _ai_suggestions_jobs[job_id]["status"] = "completed"
        _ai_suggestions_jobs[job_id]["result"] = data

        sync_db.ai_suggestions.insert_one({
            "id": job_id, "user_id": user_id,
            "result": data, "focus": focus,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"AI suggestions error: {e}")
        _ai_suggestions_jobs[job_id]["status"] = "failed"
        _ai_suggestions_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/articles/ai-suggestions")
async def ai_article_suggestions(request: AIArticleSuggestionsRequest, user: dict = Depends(get_current_user)):
    """Start async AI article suggestions based on existing content."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    existing = await db.articles.find(query, {"_id": 0, "title": 1, "primary_keyword": 1, "seo_score": 1}).sort("created_at", -1).limit(20).to_list(20)

    job_id = str(uuid.uuid4())
    _ai_suggestions_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_ai_suggestions, job_id, existing, request.focus, request.count, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/articles/ai-suggestions/status/{job_id}")
async def ai_suggestions_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll AI suggestions job status."""
    job = _ai_suggestions_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _ai_suggestions_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _ai_suggestions_jobs[job_id]
    return result

@api_router.get("/articles/ai-suggestions/history")
async def ai_suggestions_history(user: dict = Depends(get_current_user)):
    """Get AI suggestions history."""
    docs = await db.ai_suggestions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    return docs


# --- Performance Dashboard ---

@api_router.get("/performance/dashboard")
async def performance_dashboard(user: dict = Depends(get_current_user)):
    """Get comprehensive performance metrics."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Dostęp tylko dla administratorów")

    now = datetime.now(timezone.utc)

    # Total users
    total_users = await db.users.count_documents({})

    # Active users in last 24h (DAU) - based on articles created/updated
    from datetime import timedelta
    day_ago = (now - timedelta(days=1)).isoformat()
    week_ago = (now - timedelta(days=7)).isoformat()
    month_ago = (now - timedelta(days=30)).isoformat()

    # DAU - unique users who created/updated articles in last 24h
    dau_pipeline = [
        {"$match": {"$or": [
            {"created_at": {"$gte": day_ago}},
            {"updated_at": {"$gte": day_ago}}
        ]}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]
    dau_result = await db.articles.aggregate(dau_pipeline).to_list(1)
    dau = dau_result[0]["count"] if dau_result else 0

    # MAU - unique users who created/updated articles in last 30 days
    mau_pipeline = [
        {"$match": {"$or": [
            {"created_at": {"$gte": month_ago}},
            {"updated_at": {"$gte": month_ago}}
        ]}},
        {"$group": {"_id": "$user_id"}},
        {"$count": "count"}
    ]
    mau_result = await db.articles.aggregate(mau_pipeline).to_list(1)
    mau = mau_result[0]["count"] if mau_result else 0

    # Total articles
    total_articles = await db.articles.count_documents({})

    # Articles created in last 7 days
    articles_this_week = await db.articles.count_documents({"created_at": {"$gte": week_ago}})

    # Articles created in last 30 days
    articles_this_month = await db.articles.count_documents({"created_at": {"$gte": month_ago}})

    # Average SEO score
    seo_pipeline = [
        {"$match": {"seo_score.percentage": {"$exists": True}}},
        {"$group": {"_id": None, "avg": {"$avg": "$seo_score.percentage"}, "max": {"$max": "$seo_score.percentage"}, "min": {"$min": "$seo_score.percentage"}}}
    ]
    seo_result = await db.articles.aggregate(seo_pipeline).to_list(1)
    avg_seo = round(seo_result[0]["avg"]) if seo_result else 0
    max_seo = round(seo_result[0]["max"]) if seo_result else 0
    min_seo = round(seo_result[0]["min"]) if seo_result else 0

    # Articles by SEO score range
    high_seo = await db.articles.count_documents({"seo_score.percentage": {"$gte": 80}})
    medium_seo = await db.articles.count_documents({"seo_score.percentage": {"$gte": 50, "$lt": 80}})
    low_seo = await db.articles.count_documents({"seo_score.percentage": {"$lt": 50, "$exists": True}})
    no_seo = await db.articles.count_documents({"$or": [{"seo_score": {"$exists": False}}, {"seo_score.percentage": {"$exists": False}}]})

    # Top 5 articles by SEO score
    top_articles = await db.articles.find(
        {"seo_score.percentage": {"$exists": True}},
        {"_id": 0, "id": 1, "title": 1, "seo_score": 1, "primary_keyword": 1, "created_at": 1}
    ).sort("seo_score.percentage", -1).limit(5).to_list(5)

    # Recent articles (last 5)
    recent_articles = await db.articles.find(
        {}, {"_id": 0, "id": 1, "title": 1, "seo_score": 1, "created_at": 1, "user_id": 1}
    ).sort("created_at", -1).limit(5).to_list(5)

    # Articles created per day (last 14 days)
    articles_per_day = []
    for i in range(13, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = (now - timedelta(days=i)).replace(hour=23, minute=59, second=59, microsecond=999999)
        count = await db.articles.count_documents({
            "created_at": {"$gte": day_start.isoformat(), "$lte": day_end.isoformat()}
        })
        articles_per_day.append({
            "date": day_start.strftime("%d.%m"),
            "count": count
        })

    # Total images generated
    total_images = await db.images.count_documents({})

    # Total newsletters
    total_newsletters = await db.newsletters.count_documents({})

    # WordPress published count
    wp_published = await db.articles.count_documents({"wordpress_published": True})

    # Active subscriptions
    active_subs = await db.subscriptions.count_documents({"status": "active"})

    return {
        "users": {
            "total": total_users,
            "dau": dau,
            "mau": mau,
        },
        "articles": {
            "total": total_articles,
            "this_week": articles_this_week,
            "this_month": articles_this_month,
            "per_day": articles_per_day,
        },
        "seo": {
            "average": avg_seo,
            "max": max_seo,
            "min": min_seo,
            "high": high_seo,
            "medium": medium_seo,
            "low": low_seo,
            "no_score": no_seo,
        },
        "top_articles": top_articles,
        "recent_articles": recent_articles,
        "content": {
            "images": total_images,
            "newsletters": total_newsletters,
            "wp_published": wp_published,
        },
        "subscriptions": {
            "active": active_subs,
        }
    }


# --- Plagiarism Checker ---

class PlagiarismCheckRequest(BaseModel):
    article_id: str

_plagiarism_jobs = {}

def _sync_run_plagiarism_check(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Run plagiarism check in thread using AI analysis."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _plagiarism_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        # Extract text content from sections
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(section.get("heading", ""))
            content = section.get("content", "")
            clean = re.sub(r'<[^>]+>', '', content)
            text_parts.append(clean)
            for sub in section.get("subsections", []):
                text_parts.append(sub.get("heading", ""))
                sub_content = sub.get("content", "")
                clean_sub = re.sub(r'<[^>]+>', '', sub_content)
                text_parts.append(clean_sub)

        full_text = "\n".join(text_parts)
        # Limit to ~3000 words for analysis
        words = full_text.split()
        if len(words) > 3000:
            full_text = " ".join(words[:3000])

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"plagiarism-{job_id[:8]}",
            system_message="Jesteś ekspertem od analizy treści i wykrywania plagiatu. Analizujesz tekst pod kątem oryginalności. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        prompt = f"""Przeanalizuj poniższy tekst artykułu pod kątem oryginalności i potencjalnego plagiatu.

Tytuł: {article_data.get("title", "")}
Słowo kluczowe: {article_data.get("primary_keyword", "")}

Tekst artykułu:
{full_text}

Wykonaj następujące analizy:
1. Sprawdź czy tekst wygląda na oryginalny czy skopiowany
2. Zidentyfikuj fragmenty które mogą być popularnymi frazami lub szablonami
3. Oceń unikalność stylu pisania
4. Sprawdź czy są fragmenty które brzmią jak typowe treści AI bez personalizacji
5. Oceń jakość i oryginalność treści

Odpowiedz TYLKO prawidłowym JSON:
{{
    "overall_score": 85,
    "verdict": "oryginalny" lub "podejrzany" lub "prawdopodobny plagiat",
    "summary": "Krótkie podsumowanie analizy (2-3 zdania)",
    "details": {{
        "originality": 85,
        "style_uniqueness": 80,
        "ai_detection_risk": 20,
        "template_phrases_detected": 10
    }},
    "flagged_sections": [
        {{
            "text": "Fragment tekstu...",
            "reason": "Powód oznaczenia",
            "risk_level": "niski" lub "średni" lub "wysoki"
        }}
    ],
    "recommendations": [
        "Sugestia poprawy 1",
        "Sugestia poprawy 2"
    ]
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _plagiarism_jobs[job_id]["status"] = "completed"
        _plagiarism_jobs[job_id]["result"] = data

        sync_db.plagiarism_checks.insert_one({
            "id": job_id,
            "user_id": user_id,
            "article_id": article_data.get("id", ""),
            "result": data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Plagiarism check error: {e}")
        _plagiarism_jobs[job_id]["status"] = "failed"
        _plagiarism_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/plagiarism/check")
async def check_plagiarism(request: PlagiarismCheckRequest, user: dict = Depends(get_current_user)):
    """Start async plagiarism check for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")

    job_id = str(uuid.uuid4())
    _plagiarism_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_plagiarism_check, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/plagiarism/status/{job_id}")
async def plagiarism_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll plagiarism check status."""
    job = _plagiarism_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _plagiarism_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _plagiarism_jobs[job_id]
    return result

@api_router.get("/plagiarism/history/{article_id}")
async def plagiarism_history(article_id: str, user: dict = Depends(get_current_user)):
    """Get plagiarism check history for an article."""
    docs = await db.plagiarism_checks.find(
        {"article_id": article_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    return docs


# --- User Activity Tracking ---

@api_router.post("/activity/track")
async def track_activity(user: dict = Depends(get_current_user)):
    """Track user activity for DAU/MAU calculations."""
    await db.user_activity.update_one(
        {"user_id": user["id"], "date": datetime.now(timezone.utc).strftime("%Y-%m-%d")},
        {"$set": {
            "user_id": user["id"],
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "last_active": datetime.now(timezone.utc).isoformat()
        }, "$inc": {"actions": 1}},
        upsert=True
    )
    return {"status": "ok"}


# --- Content Verification (Fact-Check) ---

class ContentVerifyRequest(BaseModel):
    article_id: str

_verification_jobs = {}

def _sync_run_content_verification(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Run content verification/fact-check in thread using AI analysis."""
    import pymongo
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _verification_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        # Extract text content from sections
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(f"## {section.get('heading', '')}")
            content = section.get("content", "")
            clean = re.sub(r'<[^>]+>', ' ', content)
            text_parts.append(clean)
            for sub in section.get("subsections", []):
                text_parts.append(f"### {sub.get('heading', '')}")
                sub_content = sub.get("content", "")
                clean_sub = re.sub(r'<[^>]+>', ' ', sub_content)
                text_parts.append(clean_sub)

        full_text = "\n".join(text_parts)
        words = full_text.split()
        if len(words) > 3000:
            full_text = " ".join(words[:3000])

        sources_str = ""
        for s in article_data.get("sources", []):
            sources_str += f"- {s.get('name', '')}: {s.get('url', '')}\n"

        faq_str = ""
        for f in article_data.get("faq", []):
            faq_str += f"Q: {f.get('question','')}\nA: {f.get('answer','')[:150]}\n\n"

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"verify-{job_id[:8]}",
            system_message="Jesteś doświadczonym BIEGŁYM REWIDENTEM i doradcą podatkowym w Polsce. Weryfikujesz treści pod kątem zgodności z obowiązującym prawem podatkowym i księgowym (stan na 2026 r.). Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        prompt = f"""Zweryfikuj poniższy artykuł blogowy z zakresu księgowości/podatków pod kątem RZETELNOŚCI MERYTORYCZNEJ.

Tytuł: {article_data.get("title", "")}
Słowo kluczowe: {article_data.get("primary_keyword", "")}

Treść artykułu:
{full_text}

Źródła podane w artykule:
{sources_str or "Brak źródeł"}

FAQ:
{faq_str or "Brak FAQ"}

SPRAWDŹ:
1. Czy cytowane przepisy prawne istnieją i są aktualne (art., ust., Dz.U.)?
2. Czy podane kwoty, stawki, terminy są prawidłowe (stan na 2026 r.)?
3. Czy twierdzenia są zgodne z obowiązującym prawem?
4. Czy źródła są wiarygodne i prowadzą do oficjalnych instytucji?
5. Czy FAQ zawiera poprawne informacje?
6. Czy brakuje istotnych zastrzeżeń prawnych (disclaimerów)?
7. Czy artykuł mógłby wprowadzić czytelnika w błąd?

Odpowiedz TYLKO prawidłowym JSON:
{{
    "overall_reliability_score": 85,
    "verdict": "rzetelny" lub "wymaga poprawek" lub "nierzetelny",
    "summary": "Krótkie podsumowanie weryfikacji (2-3 zdania)",
    "legal_accuracy": {{
        "score": 80,
        "verified_references": [
            {{
                "reference": "art. X ust. Y ustawy o ...",
                "status": "poprawny" lub "nieaktualny" lub "błędny" lub "nie do zweryfikowania",
                "note": "Komentarz"
            }}
        ]
    }},
    "factual_accuracy": {{
        "score": 85,
        "verified_facts": [
            {{
                "claim": "Twierdzenie z artykułu",
                "status": "poprawne" lub "nieprecyzyjne" lub "błędne" lub "nieaktualne",
                "correction": "Poprawna informacja (jeśli błędne)",
                "source": "Źródło poprawnej informacji"
            }}
        ]
    }},
    "completeness": {{
        "score": 75,
        "missing_info": [
            "Brakująca istotna informacja 1",
            "Brakująca istotna informacja 2"
        ],
        "missing_disclaimers": [
            "Brakujące zastrzeżenie prawne"
        ]
    }},
    "sources_quality": {{
        "score": 80,
        "assessment": "Ocena jakości źródeł",
        "missing_sources": ["Sugestia brakującego źródła"]
    }},
    "recommendations": [
        {{
            "priority": "wysoki" lub "średni" lub "niski",
            "area": "przepisy" lub "kwoty" lub "terminy" lub "źródła" lub "disclaimery" lub "kompletność",
            "description": "Konkretna rekomendacja poprawy",
            "suggested_text": "Proponowany tekst do wstawienia (jeśli dotyczy)"
        }}
    ]
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _verification_jobs[job_id]["status"] = "completed"
        _verification_jobs[job_id]["result"] = data

        sync_db.content_verifications.insert_one({
            "id": job_id,
            "user_id": user_id,
            "article_id": article_data.get("id", ""),
            "result": data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logging.error(f"Content verification error: {e}")
        _verification_jobs[job_id]["status"] = "failed"
        _verification_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/verify/check")
async def verify_content(request: ContentVerifyRequest, user: dict = Depends(get_current_user)):
    """Start async content verification for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")

    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")

    job_id = str(uuid.uuid4())
    _verification_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_content_verification, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/verify/status/{job_id}")
async def verification_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll content verification status."""
    job = _verification_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _verification_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _verification_jobs[job_id]
    return result

@api_router.get("/verify/history/{article_id}")
async def verification_history(article_id: str, user: dict = Depends(get_current_user)):
    """Get verification history for an article."""
    docs = await db.content_verifications.find(
        {"article_id": article_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    return docs


# --- Auto Competition Analysis (Top Google Results) ---

class AutoCompetitionRequest(BaseModel):
    article_id: str

_auto_competition_jobs = {}

def _sync_run_auto_competition(job_id: str, article_data: dict, emergent_key: str, user_id: str):
    """Scrape top search results for keyword, extract content, compare with article via AI."""
    import pymongo
    import httpx as httpx_sync
    from bs4 import BeautifulSoup
    sync_client = pymongo.MongoClient(os.environ.get('MONGO_URL'), serverSelectionTimeoutMS=5000)
    sync_db = sync_client[os.environ.get('DB_NAME', 'seo_article_writer')]
    try:
        _auto_competition_jobs[job_id]["status"] = "running"

        keyword = article_data.get("primary_keyword", "")
        my_title = article_data.get("title", "")
        my_sections = [s.get("heading", "") for s in article_data.get("sections", [])]
        my_word_count = 0
        my_text = ""
        for section in article_data.get("sections", []):
            text = re.sub(r'<[^>]+>', ' ', section.get("content", ""))
            my_text += " " + text
            for sub in section.get("subsections", []):
                my_text += " " + re.sub(r'<[^>]+>', ' ', sub.get("content", ""))
        my_word_count = len(my_text.split())

        # Scrape search results using DuckDuckGo HTML (no API key needed)
        search_url = f"https://html.duckduckgo.com/html/?q={keyword.replace(' ', '+')}+poradnik+polska"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

        competitors = []
        try:
            import httpx
            with httpx.Client(timeout=20.0, follow_redirects=True, verify=False) as client:
                resp = client.get(search_url, headers=headers)
                soup = BeautifulSoup(resp.text, "html.parser")
                results = soup.select(".result__a")
                urls = []
                from urllib.parse import unquote, urlparse, parse_qs
                for r in results[:8]:
                    href = r.get("href", "")
                    if not href:
                        continue
                    # Extract actual URL from DDG redirect first
                    if "uddg=" in href:
                        try:
                            parsed = parse_qs(urlparse(href).query)
                            href = unquote(parsed.get("uddg", [href])[0])
                        except Exception:
                            continue
                    # Skip DDG internal and ad URLs
                    if "duckduckgo" in href or not href.startswith("http"):
                        continue
                    urls.append(href)
                urls = urls[:5]

                # Scrape each competitor
                for url in urls:
                    try:
                        page = client.get(url, headers=headers, timeout=10.0)
                        page_soup = BeautifulSoup(page.text, "html.parser")
                        page_title = page_soup.find("title")
                        page_title_text = page_title.get_text(strip=True) if page_title else ""
                        meta_desc = ""
                        md = page_soup.find("meta", attrs={"name": "description"})
                        if md:
                            meta_desc = md.get("content", "")
                        headings = []
                        for tag in ["h1", "h2", "h3"]:
                            for h in page_soup.find_all(tag)[:10]:
                                headings.append(f"{tag.upper()}: {h.get_text(strip=True)}")
                        for tag in page_soup(["script", "style", "nav", "footer", "header", "aside"]):
                            tag.decompose()
                        article_el = page_soup.find("article") or page_soup.find("main") or page_soup.find("body")
                        content = article_el.get_text(separator=" ", strip=True)[:2000] if article_el else ""
                        competitors.append({
                            "url": url,
                            "title": page_title_text[:200],
                            "meta_desc": meta_desc[:300],
                            "headings": headings[:12],
                            "word_count": len(content.split()),
                            "content_sample": content[:1500]
                        })
                    except Exception:
                        continue
        except Exception as e:
            logging.warning(f"Search scraping failed: {e}")

        # AI analysis
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"auto-comp-{job_id[:8]}",
            system_message="Jesteś ekspertem SEO. Analizujesz artykuły konkurencji i wskazujesz luki w treści. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        comp_str = ""
        for i, c in enumerate(competitors[:5], 1):
            comp_str += f"\n--- KONKURENT {i} ---\n"
            comp_str += f"URL: {c['url']}\nTytuł: {c['title']}\n"
            comp_str += f"Meta opis: {c['meta_desc']}\n"
            comp_str += f"Nagłówki: {'; '.join(c['headings'][:8])}\n"
            comp_str += f"Słów: ~{c['word_count']}\n"
            comp_str += f"Fragment: {c['content_sample'][:600]}\n"

        prompt = f"""Przeanalizuj mój artykuł w porównaniu z TOP wynikami wyszukiwania dla słowa kluczowego: "{keyword}"

MÓJ ARTYKUŁ:
Tytuł: {my_title}
Sekcje: {', '.join(my_sections)}
Słów: ~{my_word_count}
Meta opis: {article_data.get('meta_description', '')}

WYNIKI KONKURENCJI:
{comp_str if comp_str else 'Nie udało się pobrać wyników konkurencji - analizuj sam artykuł.'}

Odpowiedz TYLKO prawidłowym JSON:
{{
    "competitors_found": {len(competitors)},
    "overall_position": "silniejszy" lub "porównywalny" lub "słabszy",
    "content_gaps": [
        {{
            "topic": "Temat/aspekt którego brakuje w moim artykule",
            "found_in": "URL lub 'wielu konkurentów'",
            "importance": "wysoka" lub "średnia" lub "niska",
            "suggestion": "Konkretna sugestia co dodać (1-2 zdania)",
            "suggested_heading": "Proponowany nagłówek H2/H3 do dodania"
        }}
    ],
    "keyword_opportunities": [
        {{
            "keyword": "Słowo kluczowe używane przez konkurencję",
            "frequency": "jak często występuje u konkurencji",
            "my_usage": "czy występuje w moim artykule",
            "action": "Dodaj/Wzmocnij/Ignoruj"
        }}
    ],
    "structural_comparison": {{
        "my_sections": {len(my_sections)},
        "avg_competitor_sections": 0,
        "my_word_count": {my_word_count},
        "avg_competitor_word_count": 0,
        "recommendation": "Co zmienić w strukturze"
    }},
    "strengths": ["Mocne strony mojego artykułu vs konkurencja"],
    "weaknesses": ["Słabe strony wymagające poprawy"],
    "action_plan": [
        {{
            "priority": 1,
            "action": "Konkretne działanie do podjęcia",
            "expected_impact": "wysoki" lub "średni" lub "niski"
        }}
    ],
    "summary": "Podsumowanie analizy (2-3 zdania)"
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)
        data["competitors_scraped"] = [{"url": c["url"], "title": c["title"], "word_count": c["word_count"]} for c in competitors]

        _auto_competition_jobs[job_id]["status"] = "completed"
        _auto_competition_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"Auto competition error: {e}")
        _auto_competition_jobs[job_id]["status"] = "failed"
        _auto_competition_jobs[job_id]["error"] = str(e)
    finally:
        sync_client.close()

@api_router.post("/competition/auto-analyze")
async def auto_competition_analysis(request: AutoCompetitionRequest, user: dict = Depends(get_current_user)):
    """Start auto competition analysis - scrapes top results for keyword."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _auto_competition_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_auto_competition, job_id, article, emergent_key, user["id"])
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/competition/auto-status/{job_id}")
async def auto_competition_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll auto competition analysis status."""
    job = _auto_competition_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _auto_competition_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _auto_competition_jobs[job_id]
    return result


# --- A/B Title Testing ---

class ABTitleRequest(BaseModel):
    article_id: str
    custom_variants: list = []  # optional user-provided variants

_ab_title_jobs = {}

def _sync_run_ab_title_test(job_id: str, article_data: dict, custom_variants: list, emergent_key: str):
    """Generate and evaluate title variants using AI."""
    try:
        _ab_title_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"ab-title-{job_id[:8]}",
            system_message="Jesteś ekspertem od copywritingu SEO i CTR. Generujesz i oceniasz warianty tytułów artykułów. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        current_title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        topic = article_data.get("topic", "")
        meta_desc = article_data.get("meta_description", "")

        custom_str = ""
        if custom_variants:
            custom_str = "\n\nDODATKOWE WARIANTY OD UŻYTKOWNIKA (też oceń):\n" + "\n".join([f"- {v}" for v in custom_variants])

        prompt = f"""Przeanalizuj obecny tytuł artykułu i zaproponuj 5 alternatywnych wariantów. Oceń każdy wariant.

OBECNY TYTUŁ: "{current_title}"
SŁOWO KLUCZOWE: "{keyword}"
TEMAT: "{topic}"
META OPIS: "{meta_desc}"
{custom_str}

Dla każdego wariantu (włącznie z obecnym) oceń:
1. CTR Potential (0-100) - jak bardzo tytuł zachęca do kliknięcia
2. SEO Score (0-100) - optymalizacja pod wyszukiwarki (keyword placement, length)
3. Emotional Appeal (0-100) - siła emocjonalna, ciekawość, urgency
4. Clarity (0-100) - jasność przekazu, zrozumiałość

Odpowiedz TYLKO prawidłowym JSON:
{{
    "current_title": {{
        "text": "{current_title}",
        "scores": {{
            "ctr": 70,
            "seo": 80,
            "emotion": 60,
            "clarity": 85
        }},
        "total": 74,
        "feedback": "Krótka ocena obecnego tytułu"
    }},
    "variants": [
        {{
            "text": "Nowy wariant tytułu",
            "strategy": "power_words" lub "question" lub "numbers" lub "how_to" lub "list" lub "urgency",
            "scores": {{
                "ctr": 85,
                "seo": 90,
                "emotion": 75,
                "clarity": 88
            }},
            "total": 85,
            "feedback": "Dlaczego ten wariant jest lepszy/gorszy",
            "changes_made": "Co zostało zmienione i dlaczego"
        }}
    ],
    "winner": {{
        "text": "Najlepszy wariant",
        "total": 92,
        "reason": "Dlaczego ten wariant jest najlepszy"
    }},
    "tips": [
        "Ogólna porada dotycząca tytułów w tej branży"
    ]
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)

        _ab_title_jobs[job_id]["status"] = "completed"
        _ab_title_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"A/B title test error: {e}")
        _ab_title_jobs[job_id]["status"] = "failed"
        _ab_title_jobs[job_id]["error"] = str(e)

@api_router.post("/articles/ab-title-test")
async def ab_title_test(request: ABTitleRequest, user: dict = Depends(get_current_user)):
    """Start A/B title test for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _ab_title_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_ab_title_test, job_id, article, request.custom_variants, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/articles/ab-title-status/{job_id}")
async def ab_title_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll A/B title test status."""
    job = _ab_title_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _ab_title_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _ab_title_jobs[job_id]
    return result


# --- Bulk Article Operations ---

class BulkDeleteRequest(BaseModel):
    article_ids: list

class BulkCategoryRequest(BaseModel):
    article_ids: list
    category: str

@api_router.post("/articles/bulk-delete")
async def bulk_delete_articles(request: BulkDeleteRequest, user: dict = Depends(get_current_user)):
    """Delete multiple articles at once."""
    if not request.article_ids:
        raise HTTPException(status_code=400, detail="Brak artykułów do usunięcia")
    query = {"id": {"$in": request.article_ids}}
    if not user.get("is_admin"):
        query["user_id"] = user["id"]
    result = await db.articles.delete_many(query)
    # Also delete related versions
    await db.article_versions.delete_many({"article_id": {"$in": request.article_ids}})
    return {"deleted": result.deleted_count, "requested": len(request.article_ids)}

@api_router.post("/articles/bulk-category")
async def bulk_categorize_articles(request: BulkCategoryRequest, user: dict = Depends(get_current_user)):
    """Assign category to multiple articles."""
    if not request.article_ids or not request.category:
        raise HTTPException(status_code=400, detail="Brak danych")
    query = {"id": {"$in": request.article_ids}}
    if not user.get("is_admin"):
        query["user_id"] = user["id"]
    result = await db.articles.update_many(query, {"$set": {"category": request.category, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"modified": result.modified_count, "category": request.category}

@api_router.get("/articles/categories")
async def list_categories(user: dict = Depends(get_current_user)):
    """Get all unique categories."""
    pipeline = [
        {"$match": {"category": {"$exists": True, "$ne": ""}}},
        {"$group": {"_id": "$category"}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.articles.aggregate(pipeline).to_list(50)
    return [r["_id"] for r in result]


# --- Article Version History ---

@api_router.get("/articles/{article_id}/versions")
async def list_article_versions(article_id: str, user: dict = Depends(get_current_user)):
    """List version history for an article."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0, "user_id": 1})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    if not user.get("is_admin") and article.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostępu")
    versions = await db.article_versions.find(
        {"article_id": article_id},
        {"_id": 0, "id": 1, "created_at": 1, "version_data.title": 1, "version_data.seo_score": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    return versions

@api_router.get("/articles/{article_id}/versions/{version_id}")
async def get_article_version(article_id: str, version_id: str, user: dict = Depends(get_current_user)):
    """Get a specific version of an article."""
    version = await db.article_versions.find_one({"id": version_id, "article_id": article_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Wersja nie znaleziona")
    return version

@api_router.post("/articles/{article_id}/versions/{version_id}/restore")
async def restore_article_version(article_id: str, version_id: str, user: dict = Depends(get_current_user)):
    """Restore article to a previous version."""
    version = await db.article_versions.find_one({"id": version_id, "article_id": article_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Wersja nie znaleziona")
    current = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not current:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    if not user.get("is_admin") and current.get("user_id") != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostępu")
    # Save current as version before restoring
    await db.article_versions.insert_one({
        "id": str(uuid.uuid4()), "article_id": article_id,
        "user_id": user.get("id", ""),
        "version_data": {k: v for k, v in current.items() if k != "_id"},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    # Restore
    restore_data = version.get("version_data", {})
    restore_data.pop("_id", None)
    restore_data.pop("id", None)
    restore_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.articles.update_one({"id": article_id}, {"$set": restore_data})
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return serialize_doc(article)


# --- Auto Generate Meta Tags ---

class AutoMetaRequest(BaseModel):
    article_id: str

_auto_meta_jobs = {}

def _sync_run_auto_meta(job_id: str, article_data: dict, emergent_key: str):
    """Generate optimized meta tags using AI."""
    try:
        _auto_meta_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(section.get("heading", ""))
            clean = re.sub(r'<[^>]+>', '', section.get("content", ""))
            text_parts.append(clean[:200])
        content_summary = " ".join(text_parts)[:1000]

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"auto-meta-{job_id[:8]}",
            system_message="Jesteś ekspertem SEO. Generujesz zoptymalizowane meta tagi dla artykułów o księgowości. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        prompt = f"""Wygeneruj zoptymalizowane meta tagi SEO dla artykułu:

Tytuł: {title}
Słowo kluczowe: {keyword}
Treść (fragment): {content_summary}

Wygeneruj 3 warianty meta title i 3 warianty meta description. Każdy wariant powinien być inny stylistycznie.

ZASADY:
- Meta title: 30-60 znaków, zawiera słowo kluczowe, RÓŻNY od tytułu artykułu
- Meta description: 120-160 znaków, zawiera słowo kluczowe, CTA (Sprawdź/Dowiedz się/Poznaj), zachęca do kliknięcia
- Uwzględnij rok 2026 w co najmniej jednym wariancie

Odpowiedz TYLKO prawidłowym JSON:
{{
    "meta_titles": [
        {{
            "text": "Meta title wariant 1",
            "length": 45,
            "score": 90,
            "style": "informacyjny" lub "pytanie" lub "CTA" lub "lista"
        }}
    ],
    "meta_descriptions": [
        {{
            "text": "Meta description wariant 1",
            "length": 140,
            "score": 88,
            "style": "informacyjny" lub "korzyści" lub "urgency"
        }}
    ],
    "recommended": {{
        "meta_title": "Najlepszy meta title",
        "meta_description": "Najlepsza meta description",
        "reason": "Dlaczego ten zestaw jest najlepszy"
    }}
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)
        _auto_meta_jobs[job_id]["status"] = "completed"
        _auto_meta_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"Auto meta error: {e}")
        _auto_meta_jobs[job_id]["status"] = "failed"
        _auto_meta_jobs[job_id]["error"] = str(e)

@api_router.post("/articles/auto-meta")
async def auto_generate_meta(request: AutoMetaRequest, user: dict = Depends(get_current_user)):
    """Auto-generate meta tags for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _auto_meta_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_auto_meta, job_id, article, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/articles/auto-meta/status/{job_id}")
async def auto_meta_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll auto meta generation status."""
    job = _auto_meta_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _auto_meta_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _auto_meta_jobs[job_id]
    return result


# --- Smart Publishing Schedule ---

class PublishScheduleRequest(BaseModel):
    article_id: str

_schedule_jobs = {}

def _sync_run_schedule_suggestion(job_id: str, article_data: dict, emergent_key: str):
    """AI suggests best publishing time based on industry and content type."""
    try:
        _schedule_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        category = article_data.get("category", "")
        faq_count = len(article_data.get("faq", []))
        word_count = sum(len(re.sub(r'<[^>]+>', '', s.get("content", "")).split()) for s in article_data.get("sections", []))

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"schedule-{job_id[:8]}",
            system_message="Jesteś ekspertem od content marketingu i analityki publikacji dla polskiej branży finansowej/księgowej. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        prompt = f"""Zaproponuj optymalny harmonogram publikacji dla tego artykułu na blogu biura rachunkowego.

Tytuł: {title}
Słowo kluczowe: {keyword}
Kategoria: {category or 'ogólna księgowość'}
Długość: ~{word_count} słów
FAQ: {faq_count} pytań

Uwzględnij:
1. Najlepsze dni tygodnia dla treści o podatach/księgowości w Polsce
2. Najlepsze godziny publikacji (kiedy target audience jest aktywna)
3. Sezonowość tematu (np. rozliczenia PIT w styczniu-kwietniu)
4. Optymalne platformy i kanały dystrybucji

Odpowiedz TYLKO prawidłowym JSON:
{{
    "recommended_slots": [
        {{
            "day": "wtorek",
            "time": "09:00",
            "score": 92,
            "reason": "Dlaczego ten termin jest optymalny"
        }}
    ],
    "best_slot": {{
        "day": "wtorek",
        "time": "09:00",
        "datetime_suggestion": "2026-03-25T09:00:00",
        "reason": "Główny powód"
    }},
    "seasonal_notes": "Uwagi o sezonowości tematu",
    "distribution_plan": [
        {{
            "channel": "WordPress blog",
            "timing": "Publikacja o wybranej godzinie",
            "tip": "Wskazówka"
        }},
        {{
            "channel": "Social Media",
            "timing": "2h po publikacji",
            "tip": "Wskazówka"
        }},
        {{
            "channel": "Newsletter",
            "timing": "Następny dzień rano",
            "tip": "Wskazówka"
        }}
    ],
    "avoid": ["Unikaj publikacji w ...", "Nie publikuj gdy ..."],
    "summary": "Krótkie podsumowanie rekomendacji (2-3 zdania)"
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)
        _schedule_jobs[job_id]["status"] = "completed"
        _schedule_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"Schedule suggestion error: {e}")
        _schedule_jobs[job_id]["status"] = "failed"
        _schedule_jobs[job_id]["error"] = str(e)

@api_router.post("/articles/smart-schedule")
async def smart_publish_schedule(request: PublishScheduleRequest, user: dict = Depends(get_current_user)):
    """AI suggests optimal publishing schedule."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _schedule_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_schedule_suggestion, job_id, article, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/articles/smart-schedule/status/{job_id}")
async def smart_schedule_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll schedule suggestion status."""
    job = _schedule_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _schedule_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _schedule_jobs[job_id]
    return result


# --- Social Media Post Generator ---

class SocialPostsRequest(BaseModel):
    article_id: str

_social_posts_jobs = {}

def _sync_run_social_posts(job_id: str, article_data: dict, emergent_key: str):
    """Generate social media posts for all platforms using AI."""
    try:
        _social_posts_jobs[job_id]["status"] = "running"
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        meta_desc = article_data.get("meta_description", "")
        key_points = []
        for section in article_data.get("sections", [])[:3]:
            key_points.append(section.get("heading", ""))
            clean = re.sub(r'<[^>]+>', ' ', section.get("content", ""))
            key_points.append(" ".join(clean.split()[:50]))
        content_summary = "\n".join(key_points)[:800]

        chat = LlmChat(
            api_key=emergent_key,
            session_id=f"social-{job_id[:8]}",
            system_message="Jesteś ekspertem od social media marketingu dla polskiej branży finansowej/księgowej. Tworzysz angażujące posty promujące artykuły blogowe. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."
        )

        prompt = f"""Wygeneruj posty na social media promujące artykuł blogowy biura rachunkowego.

ARTYKUŁ:
Tytuł: {title}
Słowo kluczowe: {keyword}
Meta opis: {meta_desc}
Kluczowe punkty:
{content_summary}

Wygeneruj po 3 warianty dla KAŻDEJ platformy, w 3 różnych tonach:
1. profesjonalny - merytoryczny, ekspercki
2. zachęcający - korzyści, CTA, emocjonalny
3. z pytaniem - angażujący, prowokujący dyskusję

ZASADY:
- LinkedIn: 150-300 słów, profesjonalny ton, hashtagi, emoji umiarkowanie
- Twitter/X: max 280 znaków, zwięzły, hashtagi, placeholder [LINK]
- Facebook: 100-200 słów, luźniejszy ton, emoji, pytania, CTA
- Instagram: 150-250 słów, storytelling, dużo hashtagów (15-20), emoji

Odpowiedz TYLKO prawidłowym JSON:
{{
    "linkedin": [
        {{"tone": "profesjonalny", "text": "Tekst posta LinkedIn", "hashtags": ["#księgowość"], "estimated_engagement": "wysoki"}}
    ],
    "twitter": [
        {{"tone": "profesjonalny", "text": "Tweet max 280 znaków [LINK]", "hashtags": ["#księgowość"], "estimated_engagement": "wysoki"}}
    ],
    "facebook": [
        {{"tone": "profesjonalny", "text": "Post Facebook z CTA", "estimated_engagement": "wysoki"}}
    ],
    "instagram": [
        {{"tone": "profesjonalny", "text": "Post Instagram ze storytellingiem", "hashtags": ["#księgowość"], "estimated_engagement": "wysoki"}}
    ],
    "tips": ["Porada dotycząca publikacji"]
}}"""

        loop = asyncio.new_event_loop()
        try:
            response = loop.run_until_complete(chat.send_message(UserMessage(text=prompt)))
        finally:
            loop.close()

        text_resp = response.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("\n", 1)[1].rsplit("```", 1)[0]

        import json as json_mod
        data = json_mod.loads(text_resp)
        _social_posts_jobs[job_id]["status"] = "completed"
        _social_posts_jobs[job_id]["result"] = data
    except Exception as e:
        logging.error(f"Social posts error: {e}")
        _social_posts_jobs[job_id]["status"] = "failed"
        _social_posts_jobs[job_id]["error"] = str(e)

@api_router.post("/articles/social-posts")
async def generate_social_posts(request: SocialPostsRequest, user: dict = Depends(get_current_user)):
    """Generate social media posts for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykuł nie znaleziony")
    job_id = str(uuid.uuid4())
    _social_posts_jobs[job_id] = {"status": "queued", "result": None, "error": None}
    asyncio.get_event_loop().run_in_executor(None, _sync_run_social_posts, job_id, article, emergent_key)
    return {"job_id": job_id, "status": "queued"}

@api_router.get("/articles/social-posts/status/{job_id}")
async def social_posts_status(job_id: str, user: dict = Depends(get_current_user)):
    """Poll social posts generation status."""
    job = _social_posts_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    result = {"job_id": job_id, "status": job["status"]}
    if job["status"] == "completed":
        result["result"] = job["result"]
        del _social_posts_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _social_posts_jobs[job_id]
    return result


# Include the router in the main app
app.include_router(api_router)

# Root health check for Kubernetes probes (no /api prefix)
@app.get("/health")
async def root_health():
    return {"status": "healthy"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from auth import hash_password

@app.on_event("startup")
async def seed_admin_user():
    """Ensure admin user exists on every startup with correct password."""
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
        admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
        if not admin_email or not admin_password:
            logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping admin seed")
            return
        existing = await db.users.find_one({"email": admin_email})
        if not existing:
            admin_doc = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "password_hash": hash_password(admin_password),
                "full_name": "Admin",
                "workspace_id": str(uuid.uuid4()),
                "is_admin": True,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
            await db.users.insert_one(admin_doc)
            logger.info(f"Admin user created: {admin_email}")
        else:
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {
                    "is_admin": True,
                    "is_active": True,
                    "password_hash": hash_password(admin_password)
                }}
            )
            logger.info(f"Admin user synced: {admin_email}")
    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")
        logger.warning("Application will continue without admin seeding")

@app.on_event("startup")
async def cleanup_stale_generation_jobs():
    """Mark any stuck 'generating' jobs as failed on startup (server restart recovery)."""
    try:
        result = await db.generation_jobs.update_many(
            {"status": "generating"},
            {"$set": {"status": "failed", "error": "Zadanie przerwane przez restart serwera. Sprobuj ponownie."}}
        )
        if result.modified_count > 0:
            logger.info(f"Cleaned up {result.modified_count} stale generation jobs on startup")
    except Exception as e:
        logger.error(f"Failed to cleanup stale jobs: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
