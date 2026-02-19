from fastapi import FastAPI, APIRouter, HTTPException
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
from image_generator import generate_image
from seo_assistant import analyze_article_seo, chat_about_seo
from content_templates import get_all_templates

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


@api_router.get("/health")
async def health():
    return {"status": "healthy"}


# --- Article Generation ---

@api_router.post("/articles/generate")
async def generate_article_endpoint(request: ArticleGenerateRequest):
    """Generate a new SEO-optimized article."""
    try:
        article_data = await generate_article(
            topic=request.topic,
            primary_keyword=request.primary_keyword,
            secondary_keywords=request.secondary_keywords,
            target_length=request.target_length,
            tone=request.tone
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
            "topic": request.topic,
            "primary_keyword": request.primary_keyword,
            "secondary_keywords": request.secondary_keywords,
            "target_length": request.target_length,
            "tone": request.tone,
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
async def list_articles():
    """List all articles."""
    articles = await db.articles.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [{**serialize_doc(a)} for a in articles]


@api_router.get("/articles/{article_id}")
async def get_article(article_id: str):
    """Get a single article by ID."""
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return serialize_doc(article)


@api_router.put("/articles/{article_id}")
async def update_article(article_id: str, request: ArticleUpdateRequest):
    """Update an existing article."""
    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.articles.update_one(
        {"id": article_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return serialize_doc(article)


@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    """Delete an article."""
    result = await db.articles.delete_one({"id": article_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
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
async def get_stats():
    """Get dashboard statistics."""
    total_articles = await db.articles.count_documents({})
    
    # Average SEO score
    pipeline = [
        {"$match": {"seo_score.percentage": {"$exists": True}}},
        {"$group": {"_id": None, "avg_score": {"$avg": "$seo_score.percentage"}}}
    ]
    avg_result = await db.articles.aggregate(pipeline).to_list(1)
    avg_score = round(avg_result[0]["avg_score"]) if avg_result else 0
    
    # Articles needing improvement (score < 70)
    needs_improvement = await db.articles.count_documents(
        {"seo_score.percentage": {"$lt": 70}}
    )
    
    return {
        "total_articles": total_articles,
        "avg_seo_score": avg_score,
        "needs_improvement": needs_improvement
    }


# --- Image Generation ---

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "hero"  # hero, section, infographic, custom
    article_id: Optional[str] = None

@api_router.post("/images/generate")
async def generate_image_endpoint(request: ImageGenerateRequest):
    """Generate an image using Gemini Nano Banana model."""
    try:
        result = await generate_image(
            prompt=request.prompt,
            style=request.style
        )
        
        # Save image to DB
        image_id = str(uuid.uuid4())
        image_doc = {
            "id": image_id,
            "prompt": request.prompt,
            "style": request.style,
            "article_id": request.article_id,
            "mime_type": result["mime_type"],
            "data": result["data"],  # base64
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
        {"_id": 0, "data": 0}  # Exclude base64 data from list for performance
    ).sort("created_at", -1).to_list(50)
    return images


@api_router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """Delete an image."""
    result = await db.images.delete_one({"id": image_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"message": "Image deleted", "id": image_id}


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
