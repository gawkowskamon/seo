"""AI features: bulk ops, version history, auto meta tags, smart schedule, social posts."""
import os, logging, asyncio
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, serialize_doc, executor, HTTPException,
    uuid, datetime, timezone, json, re,
    BulkDeleteRequest, BulkCategoryRequest, AutoMetaRequest,
    PublishScheduleRequest, SocialPostsRequest,
    Optional, List, Dict, Any
)

router = APIRouter()

# In-memory job stores for async operations
_auto_meta_jobs = {}
_schedule_jobs = {}
_social_posts_jobs = {}

# --- Bulk Article Operations ---


@router.post("/articles/bulk-delete")
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

@router.post("/articles/bulk-category")
async def bulk_categorize_articles(request: BulkCategoryRequest, user: dict = Depends(get_current_user)):
    """Assign category to multiple articles."""
    if not request.article_ids or not request.category:
        raise HTTPException(status_code=400, detail="Brak danych")
    query = {"id": {"$in": request.article_ids}}
    if not user.get("is_admin"):
        query["user_id"] = user["id"]
    result = await db.articles.update_many(query, {"$set": {"category": request.category, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"modified": result.modified_count, "category": request.category}

@router.get("/articles/categories")
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

@router.get("/articles/{article_id}/versions")
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

@router.get("/articles/{article_id}/versions/{version_id}")
async def get_article_version(article_id: str, version_id: str, user: dict = Depends(get_current_user)):
    """Get a specific version of an article."""
    version = await db.article_versions.find_one({"id": version_id, "article_id": article_id}, {"_id": 0})
    if not version:
        raise HTTPException(status_code=404, detail="Wersja nie znaleziona")
    return version

@router.post("/articles/{article_id}/versions/{version_id}/restore")
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

def _sync_run_auto_meta(job_id: str, article_data: dict, emergent_key: str):
    """Generate optimized meta tags using AI."""
    try:
        _auto_meta_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        text_parts = []
        for section in article_data.get("sections", []):
            text_parts.append(section.get("heading", ""))
            clean = re.sub(r'<[^>]+>', '', section.get("content", ""))
            text_parts.append(clean[:200])
        content_summary = " ".join(text_parts)[:1000]

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

        text_resp = llm_chat_sync(prompt, system_message="Jesteś ekspertem SEO. Generujesz zoptymalizowane meta tagi dla artykułów o księgowości. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em.", session_id=f"auto-meta-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
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

@router.post("/articles/auto-meta")
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

@router.get("/articles/auto-meta/status/{job_id}")
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

def _sync_run_schedule_suggestion(job_id: str, article_data: dict, emergent_key: str):
    """AI suggests best publishing time based on industry and content type."""
    try:
        _schedule_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        category = article_data.get("category", "")
        faq_count = len(article_data.get("faq", []))
        word_count = sum(len(re.sub(r'<[^>]+>', '', s.get("content", "")).split()) for s in article_data.get("sections", []))

        schedule_sys = "Jesteś ekspertem od content marketingu i analityki publikacji dla polskiej branży finansowej/księgowej. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."

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

        text_resp = llm_chat_sync(prompt, system_message=schedule_sys, session_id=f"schedule-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
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

@router.post("/articles/smart-schedule")
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

@router.get("/articles/smart-schedule/status/{job_id}")
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

def _sync_run_social_posts(job_id: str, article_data: dict, emergent_key: str):
    """Generate social media posts for all platforms using AI."""
    try:
        _social_posts_jobs[job_id]["status"] = "running"
        from llm_helper import llm_chat_sync

        title = article_data.get("title", "")
        keyword = article_data.get("primary_keyword", "")
        meta_desc = article_data.get("meta_description", "")
        key_points = []
        for section in article_data.get("sections", [])[:3]:
            key_points.append(section.get("heading", ""))
            clean = re.sub(r'<[^>]+>', ' ', section.get("content", ""))
            key_points.append(" ".join(clean.split()[:50]))
        content_summary = "\n".join(key_points)[:800]

        social_sys = "Jesteś ekspertem od social media marketingu dla polskiej branży finansowej/księgowej. Tworzysz angażujące posty promujące artykuły blogowe. Odpowiadaj WYŁĄCZNIE poprawnym JSON-em."

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

        text_resp = llm_chat_sync(prompt, system_message=social_sys, session_id=f"social-{job_id[:8]}", timeout=120)
        text_resp = text_resp.strip()
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

@router.post("/articles/social-posts")
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

@router.get("/articles/social-posts/status/{job_id}")
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


