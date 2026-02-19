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

@api_router.post("/articles/generate")
async def generate_article_endpoint(request: ArticleGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate a new SEO-optimized article."""
    try:
        article_data = await generate_article(
            topic=request.topic,
            primary_keyword=request.primary_keyword,
            secondary_keywords=request.secondary_keywords,
            target_length=request.target_length,
            tone=request.tone,
            template=request.template
        )
        
        # Compute initial SEO score
        seo_score = compute_seo_score(
            article_data, 
            request.primary_keyword, 
            request.secondary_keywords
        )
        
        # Create article document
        article_id = str(uuid.uuid4())
        article_doc = {
            "id": article_id,
            "user_id": user["id"],
            "workspace_id": user.get("workspace_id", user["id"]),
            "topic": request.topic,
            "primary_keyword": request.primary_keyword,
            "secondary_keywords": request.secondary_keywords,
            "target_length": request.target_length,
            "tone": request.tone,
            "template": request.template,
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
        
        # Save to MongoDB
        await db.articles.insert_one(article_doc)
        
        return serialize_doc(article_doc)
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"AI returned invalid JSON: {str(e)}")
    except Exception as e:
        logging.error(f"Article generation error: {e}")
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
        api_base = "https://blog-optimizer-kit.preview.emergentagent.com/api"
    
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
    base_url = os.environ.get("APP_BASE_URL", "https://blog-optimizer-kit.preview.emergentagent.com")
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
