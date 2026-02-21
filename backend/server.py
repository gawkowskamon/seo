from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json

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
from wordpress_service import publish_to_wordpress, generate_wordpress_plugin
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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'seo_article_writer')]

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
    result = []
    for u in users:
        if isinstance(u.get("created_at"), datetime):
            u["created_at"] = u["created_at"].isoformat()
        # Count articles for this user
        article_count = await db.articles.count_documents({"user_id": u["id"]})
        u["article_count"] = article_count
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
    return {"status": "healthy"}


# --- Article Generation ---

import asyncio

# Background job storage
_generation_jobs = {}

async def _run_generation_job(job_id: str, request_data: dict, user: dict):
    """Background task for article generation."""
    try:
        _generation_jobs[job_id]["status"] = "generating"
        _generation_jobs[job_id]["stage"] = 1
        
        article_data = await generate_article(
            topic=request_data["topic"],
            primary_keyword=request_data["primary_keyword"],
            secondary_keywords=request_data["secondary_keywords"],
            target_length=request_data["target_length"],
            tone=request_data["tone"],
            template=request_data["template"]
        )
        
        _generation_jobs[job_id]["stage"] = 3
        
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
        
        await db.articles.insert_one(article_doc)
        
        _generation_jobs[job_id]["status"] = "completed"
        _generation_jobs[job_id]["stage"] = 4
        _generation_jobs[job_id]["article_id"] = article_id
        _generation_jobs[job_id]["article"] = serialize_doc(article_doc)
        
    except Exception as e:
        logging.error(f"Background generation error: {e}")
        _generation_jobs[job_id]["status"] = "failed"
        _generation_jobs[job_id]["error"] = str(e)


@api_router.post("/articles/generate")
async def generate_article_endpoint(request: ArticleGenerateRequest, user: dict = Depends(get_current_user)):
    """Start async article generation - returns job ID immediately."""
    job_id = str(uuid.uuid4())
    
    _generation_jobs[job_id] = {
        "status": "queued",
        "stage": 0,
        "article_id": None,
        "article": None,
        "error": None,
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    request_data = {
        "topic": request.topic,
        "primary_keyword": request.primary_keyword,
        "secondary_keywords": request.secondary_keywords,
        "target_length": request.target_length,
        "tone": request.tone,
        "template": request.template
    }
    
    asyncio.create_task(_run_generation_job(job_id, request_data, user))
    
    return {"job_id": job_id, "status": "queued"}


@api_router.get("/articles/generate/status/{job_id}")
async def get_generation_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check article generation job status."""
    job = _generation_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job nie znaleziony")
    if job["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    result = {
        "job_id": job_id,
        "status": job["status"],
        "stage": job["stage"]
    }
    
    if job["status"] == "completed":
        result["article_id"] = job["article_id"]
        result["article"] = job["article"]
        # Cleanup
        del _generation_jobs[job_id]
    elif job["status"] == "failed":
        result["error"] = job["error"]
        del _generation_jobs[job_id]
    
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


@api_router.get("/articles/{article_id}")
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    """Get a single article by ID (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    return serialize_doc(article)


@api_router.put("/articles/{article_id}")
async def update_article(article_id: str, request: ArticleUpdateRequest, user: dict = Depends(get_current_user)):
    """Update an existing article (owner or admin)."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if not user.get("is_admin") and article.get("user_id") and article["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Brak dostepu")
    
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
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
    reference_image: Optional[ReferenceImageData] = None

@api_router.get("/image-styles")
async def list_image_styles():
    """Return all available image styles."""
    return get_all_image_styles()

@api_router.post("/images/generate")
async def generate_image_endpoint(request: ImageGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate an image using Gemini Nano Banana model."""
    try:
        # Validate reference image if provided
        ref_image_data = None
        if request.reference_image:
            allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku. Dozwolone: PNG, JPG, WEBP")
            # Check size (base64 is ~4/3 of original, limit to ~5MB original = ~6.7MB base64)
            if len(request.reference_image.data) > 7_000_000:
                raise HTTPException(status_code=400, detail="Plik jest zbyt duzy. Maksymalny rozmiar: 5MB")
            ref_image_data = {
                "data": request.reference_image.data,
                "mime_type": request.reference_image.mime_type
            }

        # Get article context if article_id provided
        article_context = None
        if request.article_id:
            article = await db.articles.find_one({"id": request.article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article
        
        # Generate main or variant
        if request.variation_type:
            result = await generate_image_variant(
                original_prompt=request.prompt,
                style=request.style,
                variation_type=request.variation_type,
                article_context=article_context,
                reference_image=ref_image_data
            )
        else:
            result = await generate_image(
                prompt=request.prompt,
                style=request.style,
                article_context=article_context,
                reference_image=ref_image_data
            )
        
        # Save image to DB
        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id,
            "user_id": user["id"],
            "prompt": request.prompt,
            "style": request.style,
            "article_id": request.article_id,
            "variation_type": request.variation_type,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "has_reference": ref_image_data is not None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.images.insert_one(image_doc)
        
        return {
            "id": image_id,
            "prompt": request.prompt,
            "style": request.style,
            "mime_type": result["mime_type"],
            "data": result["data"],
            "created_at": image_doc["created_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            reference_image=source_data
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
    reference_image: Optional[ReferenceImageData] = None

@api_router.post("/images/generate-batch")
async def generate_batch_endpoint(request: MultiVariantRequest, user: dict = Depends(get_current_user)):
    """Generate multiple image variants at once."""
    import asyncio
    
    if request.num_variants < 1 or request.num_variants > 4:
        raise HTTPException(status_code=400, detail="Liczba wariantow musi byc od 1 do 4")
    
    try:
        ref_image_data = None
        if request.reference_image:
            allowed_mime = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
            if request.reference_image.mime_type not in allowed_mime:
                raise HTTPException(status_code=400, detail="Nieobslugiwany format pliku")
            ref_image_data = {"data": request.reference_image.data, "mime_type": request.reference_image.mime_type}
        
        article_context = None
        if request.article_id:
            article = await db.articles.find_one({"id": request.article_id}, {"_id": 0, "topic": 1, "primary_keyword": 1})
            if article:
                article_context = article
        
        # Generate variants with slight prompt modifications
        variant_suffixes = [
            "",
            " Create a different composition with alternative layout.",
            " Use a warmer, more inviting color palette.",
            " Make it more minimalist and clean with extra white space."
        ]
        
        async def gen_one(suffix):
            modified_prompt = request.prompt + suffix
            return await generate_image(
                prompt=modified_prompt,
                style=request.style,
                article_context=article_context,
                reference_image=ref_image_data
            )
        
        tasks = [gen_one(variant_suffixes[i]) for i in range(request.num_variants)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        saved = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                saved.append({"error": str(result), "variant_index": i})
                continue
            image_id = str(uuid.uuid4())
            image_doc = {
                "id": image_id,
                "user_id": user["id"],
                "prompt": request.prompt,
                "style": request.style,
                "article_id": request.article_id,
                "variation_type": f"batch_{i}",
                "mime_type": result["mime_type"],
                "data": result["data"],
                "tags": ["batch"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.images.insert_one(image_doc)
            saved.append({
                "id": image_id,
                "prompt": request.prompt,
                "style": request.style,
                "variant_index": i,
                "mime_type": result["mime_type"],
                "data": result["data"],
                "created_at": image_doc["created_at"]
            })
        
        return {"variants": saved, "total": len(saved)}
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
    await db.settings.update_one(
        {"key": "wordpress"},
        {"$set": {
            "key": "wordpress",
            "wp_url": request.wp_url.rstrip("/"),
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
            raise HTTPException(status_code=502, detail=result.get("error", "Blad publikacji na WordPress"))
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"WordPress publish error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wordpress/plugin")
async def download_wordpress_plugin(user: dict = Depends(get_current_user)):
    """Generate and download the WordPress plugin file."""
    # Use the current API base URL
    api_base = os.environ.get("API_BASE_URL", "")
    if not api_base:
        # Try to construct from request context
        api_base = "https://content-craft-ai-4.preview.emergentagent.com/api"
    
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

@api_router.post("/articles/{article_id}/seo-assistant")
async def seo_assistant_endpoint(article_id: str, request: SEOAssistantRequest):
    """AI SEO Assistant - analyze article or chat about improvements."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        if request.mode == "chat" and request.message:
            result = await chat_about_seo(
                article=article,
                user_message=request.message,
                conversation_history=request.history or []
            )
        else:
            result = await analyze_article_seo(article=article)
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logging.error(f"SEO Assistant error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

@api_router.post("/seo-audit")
async def run_audit(request: SEOAuditRequest, user: dict = Depends(get_current_user)):
    """Run SEO audit on a URL."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    try:
        result = await run_seo_audit(request.url, emergent_key)
        
        audit_id = str(uuid.uuid4())
        audit_doc = {
            "id": audit_id,
            "user_id": user["id"],
            "url": request.url,
            "result": result,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.seo_audits.insert_one(audit_doc)
        
        return {"id": audit_id, **result}
    except Exception as e:
        logging.error(f"SEO audit error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@api_router.post("/competition/analyze")
async def analyze_comp(request: CompetitionRequest, user: dict = Depends(get_current_user)):
    """Analyze competition for an article."""
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="Brak klucza AI")
    
    article = await db.articles.find_one({"id": request.article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Artykul nie znaleziony")
    
    try:
        result = await analyze_competition(article, request.competitor_url, emergent_key)
        return result
    except Exception as e:
        logging.error(f"Competition analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    base_url = os.environ.get("APP_BASE_URL", "https://content-craft-ai-4.preview.emergentagent.com")
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


# Include the router in the main app
app.include_router(api_router)

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
    """Ensure admin user exists on every startup."""
    admin_email = "monika.gawkowska@kurdynowski.pl"
    admin_password = "MonZuz8180!"
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "full_name": "Monika Gawkowska",
            "workspace_id": str(uuid.uuid4()),
            "is_admin": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        await db.users.insert_one(admin_doc)
        logger.info(f"Admin user created: {admin_email}")
    else:
        # Ensure admin flag and active status are set correctly
        if not existing.get("is_admin") or not existing.get("is_active", True):
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {"is_admin": True, "is_active": True}}
            )
            logger.info(f"Admin user flags updated: {admin_email}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
