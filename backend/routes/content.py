"""Content tools: templates, WordPress, series, SEO assistant, calendar, import, linkbuilding, chat, scheduling."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, require_admin, serialize_doc, executor, HTTPException,
    uuid, datetime, timezone, json, re,
    SEOAssistantRequest, CalendarRequest, ImportUrlRequest, ImportWordPressRequest,
    SchedulePublishRequest, WordPressSettingsRequest, SeriesRequest, ChatMessage,
    Response, Optional, List, Dict, Any
)
from seo_assistant import analyze_article_seo, chat_about_seo
from content_calendar_service import generate_content_calendar
from import_service import scrape_article_from_url, import_from_wordpress, optimize_imported_article
from linkbuilding_service import analyze_internal_links
from wordpress_service import publish_to_wordpress, generate_wordpress_plugin, build_styled_wordpress_content
from series_generator import generate_series_outline
from content_templates import get_all_templates
from chat_assistant_service import chat_with_assistant, clear_chat_session

router = APIRouter()

# --- Content Templates ---

@router.get("/templates")
async def list_templates():
    """Return all available content templates."""
    return get_all_templates()


# --- WordPress Integration ---


@router.get("/settings/wordpress")
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

@router.post("/settings/wordpress")
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

@router.post("/articles/{article_id}/publish-wordpress")
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

@router.get("/wordpress/plugin")
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


@router.post("/series/generate")
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

@router.get("/series")
async def list_series(user: dict = Depends(get_current_user)):
    """List all series for current user."""
    query = {} if user.get("is_admin") else {"user_id": user["id"]}
    series = await db.series.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return series


# --- SEO Assistant ---

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

@router.post("/articles/{article_id}/seo-assistant")
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

@router.get("/seo-assistant/status/{job_id}")
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


@router.post("/content-calendar/generate")
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

@router.get("/content-calendar/latest")
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

@router.get("/content-calendar/list")
async def list_calendars(user: dict = Depends(get_current_user)):
    """List all content calendars."""
    cals = await db.content_calendars.find(
        {"user_id": user["id"]}, {"_id": 0, "id": 1, "period": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(20)
    return cals


# --- Article Import ---


@router.post("/import/url")
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


@router.post("/import/wordpress")
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

@router.post("/articles/{article_id}/linkbuilding")
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


@router.post("/chat/message")
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

@router.post("/chat/clear")
async def clear_chat(user: dict = Depends(get_current_user)):
    """Clear chat session."""
    session_id = f"chat-{user['id']}-general"
    clear_chat_session(session_id)
    return {"status": "cleared"}


# --- Scheduled Publishing ---


@router.post("/articles/{article_id}/schedule")
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

@router.delete("/articles/{article_id}/schedule")
async def cancel_scheduled_publish(article_id: str, user: dict = Depends(get_current_user)):
    """Cancel a scheduled publication."""
    await db.articles.update_one(
        {"id": article_id},
        {"$unset": {"scheduled_at": "", "scheduled_wp": "", "schedule_status": ""}}
    )
    return {"message": "Planowana publikacja anulowana"}



