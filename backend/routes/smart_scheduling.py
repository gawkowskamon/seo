"""Smart Scheduling Widget — AI-powered actionable insights for Dashboard.

Generates 4-6 personalized insights based on user's article portfolio:
- Articles needing optimization (score < 60% OR score declined)
- Draft articles ready to publish (score ≥ 70%, sitting in drafts > 7 days)
- Top article candidate for social media promotion (high score + high traffic)
- AI-suggested trending topics based on user's history
- Portfolio gaps (keywords without pillar pages)
- Best publishing day/time (from wp_published_at + wp_views or defaults)

Cached per user for 6 hours.
"""
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from shared import db, get_current_user, uuid, datetime, timezone, json

router = APIRouter()


async def _get_articles_needing_optimization(user_id, is_admin):
    """Articles with score < 60% or declining score, sorted by lowest score."""
    query = {} if is_admin else {"user_id": user_id}
    query["surfer_score.percentage"] = {"$lt": 60}
    articles = await db.articles.find(
        query,
        {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "surfer_score.percentage": 1}
    ).sort("surfer_score.percentage", 1).limit(5).to_list(5)
    return articles


async def _get_drafts_ready_to_publish(user_id, is_admin):
    """Drafts with good score sitting around too long."""
    query = {"status": {"$in": ["draft", None]}}
    if not is_admin:
        query["user_id"] = user_id
    cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    query["surfer_score.percentage"] = {"$gte": 70}
    query["created_at"] = {"$lt": cutoff}
    query["$or"] = [{"wp_status": {"$ne": "published"}}, {"wp_status": {"$exists": False}}]

    articles = await db.articles.find(
        query,
        {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "surfer_score.percentage": 1, "created_at": 1}
    ).sort("surfer_score.percentage", -1).limit(5).to_list(5)
    return articles


async def _get_top_for_social_promotion(user_id, is_admin):
    """Published article with highest score + high views for social promotion."""
    query = {"wp_status": "published"}
    if not is_admin:
        query["user_id"] = user_id

    articles = await db.articles.find(
        query,
        {"_id": 0, "id": 1, "title": 1, "primary_keyword": 1, "surfer_score.percentage": 1,
         "wp_permalink": 1, "wp_views_7d": 1, "wp_views_30d": 1}
    ).sort([("wp_views_7d", -1), ("surfer_score.percentage", -1)]).limit(3).to_list(3)
    return articles


async def _get_best_publishing_day(user_id, is_admin):
    """Analyze historical wp_published_at + wp_views to find best day of week."""
    query = {"wp_published_at": {"$exists": True, "$ne": None}}
    if not is_admin:
        query["user_id"] = user_id

    published = await db.articles.find(
        query,
        {"_id": 0, "wp_published_at": 1, "wp_views_7d": 1, "wp_views_30d": 1}
    ).to_list(100)

    # Default for accounting niche (Polish market)
    default = {"day": "wtorek", "hour_range": "9:00-11:00", "reason": "Domyślna rekomendacja dla branży księgowej"}

    if len(published) < 3:
        return default

    # Count views per weekday
    weekday_views = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    for a in published:
        try:
            pd = datetime.fromisoformat(a["wp_published_at"].replace("Z", "+00:00"))
            views = a.get("wp_views_30d") or a.get("wp_views_7d") or 0
            if views > 0:
                weekday_views[pd.weekday()].append(views)
        except Exception:
            continue

    # Average views per weekday
    avg_by_day = {d: sum(v) / len(v) for d, v in weekday_views.items() if v}
    if not avg_by_day:
        return default

    best_day = max(avg_by_day, key=avg_by_day.get)
    days_pl = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    return {
        "day": days_pl[best_day],
        "hour_range": "9:00-11:00",
        "reason": f"Oparte na danych: średnio {int(avg_by_day[best_day])} wyświetleń z artykułów publikowanych w ten dzień",
        "data_points": len(published)
    }


async def _get_content_gaps(user_id, is_admin):
    """Keywords appearing in many articles but without a pillar page (target_length >= 2500)."""
    match = {} if is_admin else {"user_id": user_id}
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$primary_keyword",
            "count": {"$sum": 1},
            "max_length": {"$max": "$target_length"},
            "has_pillar": {"$max": {"$cond": [{"$gte": ["$target_length", 2500]}, 1, 0]}}
        }},
        {"$match": {"count": {"$gte": 2}, "has_pillar": 0}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    results = await db.articles.aggregate(pipeline).to_list(5)
    return [{"keyword": r["_id"], "article_count": r["count"], "max_length": r.get("max_length", 0)} for r in results if r["_id"]]


async def _get_trending_topics_ai(user_id, is_admin):
    """Use LLM to suggest 1-2 trending topics based on user's history."""
    query = {} if is_admin else {"user_id": user_id}

    # Get recent article titles + keywords
    recent = await db.articles.find(
        query,
        {"_id": 0, "title": 1, "primary_keyword": 1, "created_at": 1}
    ).sort("created_at", -1).limit(20).to_list(20)

    if len(recent) < 3:
        return []

    import os
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return []

        titles_list = "\n".join(f"- {a.get('title','')} (słowo: {a.get('primary_keyword','')})" for a in recent[:15])
        current_month_pl = ["styczniu","lutym","marcu","kwietniu","maju","czerwcu","lipcu","sierpniu","wrześniu","październiku","listopadzie","grudniu"][datetime.now(timezone.utc).month - 1]

        prompt = f"""Jestem polskim specjalistą SEO branży księgowej. Oto ostatnie artykuły w moim portfolio:
{titles_list}

Zaproponuj 2 tematy na nowe artykuły które:
1. Są powiązane z moim portfolio (nie totalnie z innej branży)
2. Są aktualne/sezonowe w {current_month_pl} (np. zmiany przepisów, nadchodzące terminy podatkowe, nowe interpretacje)
3. Mają realny potencjał rankingowy w polskim Google

Zwróć WYŁĄCZNIE JSON tablicę o strukturze:
[{{"topic":"Krótki temat 5-8 słów","primary_keyword":"fraza kluczowa 2-4 słowa","reason":"Dlaczego ten temat, 1 zdanie"}}]
"""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"trending-{user_id[:8]}",
            system_message="Jesteś ekspertem SEO branży księgowej. Zwracasz WYŁĄCZNIE poprawny JSON (tablicę)."
        ).with_model("gemini", "gemini-2.0-flash")

        import asyncio
        response = await asyncio.wait_for(
            chat.send_message(UserMessage(text=prompt)),
            timeout=60
        )
        # Parse response
        clean = response.strip()
        if clean.startswith("```"):
            import re
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        topics = json.loads(clean)
        if isinstance(topics, list):
            return topics[:2]
    except Exception as e:
        logging.warning(f"Trending topics AI failed: {e}")
    return []


@router.get("/smart-scheduling/insights")
async def get_scheduling_insights(refresh: bool = False, user: dict = Depends(get_current_user)):
    """Get AI-powered scheduling insights. Cached 6h per user."""
    user_id = user["id"]
    is_admin = user.get("is_admin", False)

    # Check cache
    cache_key = f"smart_scheduling_{user_id}"
    if not refresh:
        cached = await db.insights_cache.find_one({"key": cache_key}, {"_id": 0})
        if cached:
            cached_at = datetime.fromisoformat(cached["cached_at"])
            if (datetime.now(timezone.utc) - cached_at).total_seconds() < 6 * 3600:
                return {**cached["data"], "cached": True, "cached_at": cached["cached_at"]}

    # Generate fresh insights
    needs_opt = await _get_articles_needing_optimization(user_id, is_admin)
    ready_to_publish = await _get_drafts_ready_to_publish(user_id, is_admin)
    social_candidates = await _get_top_for_social_promotion(user_id, is_admin)
    best_day = await _get_best_publishing_day(user_id, is_admin)
    gaps = await _get_content_gaps(user_id, is_admin)
    trending = await _get_trending_topics_ai(user_id, is_admin)

    insights_data = {
        "needs_optimization": needs_opt,
        "ready_to_publish": ready_to_publish,
        "social_promotion": social_candidates,
        "best_publishing_time": best_day,
        "content_gaps": gaps,
        "trending_topics": trending,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save cache
    await db.insights_cache.update_one(
        {"key": cache_key},
        {"$set": {
            "key": cache_key,
            "user_id": user_id,
            "data": insights_data,
            "cached_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    return {**insights_data, "cached": False}
