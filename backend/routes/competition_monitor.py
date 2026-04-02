"""Competition monitoring with AI analysis."""
import logging
from fastapi import APIRouter, Depends
from shared import db, get_current_user, HTTPException, uuid, datetime, timezone, json, re, List

router = APIRouter()

# ============ Competition Monitoring ============

@router.post("/competition/monitor")
async def add_competition_monitor(request: dict, user: dict = Depends(get_current_user)):
    """Add a keyword to competition monitoring."""
    keyword = request.get("keyword", "").strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="keyword required")

    existing = await db.competition_monitors.find_one(
        {"user_id": user["id"], "keyword": keyword}, {"_id": 0}
    )
    if existing:
        return existing

    from llm_helper import llm_chat
    prompt = f"""Przeprowadź analizę konkurencji dla frazy: "{keyword}" w Google (rynek polski, branża księgowość).

Odpowiedz WYŁĄCZNIE JSON:
{{
    "keyword": "{keyword}",
    "difficulty": 55,
    "monthly_volume": 1800,
    "top_results": [
        {{
            "position": 1,
            "title": "Tytuł artykułu",
            "url": "https://example.pl",
            "domain": "example.pl",
            "estimated_traffic": 500,
            "content_score": 78
        }}
    ],
    "content_gaps": [
        "Temat lub aspekt nieporuszony przez konkurencję"
    ],
    "recommended_actions": [
        "Konkretna rekomendacja działania"
    ]
}}
Wygeneruj 5-8 wyników w top_results, 3-5 content_gaps, 3-5 recommended_actions."""

    try:
        resp = await llm_chat(prompt, system_message="Jesteś ekspertem SEO analizującym konkurencję w SERP. Odpowiadaj WYŁĄCZNIE JSON.", session_id=f"comp-mon-{hash(keyword)%100000}", timeout=120)
        clean = resp.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        analysis = json.loads(clean)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy: {e}")

    monitor = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "keyword": keyword,
        "analysis": analysis,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_checked": datetime.now(timezone.utc).isoformat(),
    }
    await db.competition_monitors.insert_one({**monitor})
    monitor.pop("_id", None)
    return monitor


@router.get("/competition/monitors")
async def list_competition_monitors(user: dict = Depends(get_current_user)):
    """List all monitored keywords."""
    monitors = await db.competition_monitors.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return monitors


@router.delete("/competition/monitors/{monitor_id}")
async def delete_competition_monitor(monitor_id: str, user: dict = Depends(get_current_user)):
    """Remove a keyword from monitoring."""
    result = await db.competition_monitors.delete_one({"id": monitor_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"status": "deleted", "id": monitor_id}


@router.post("/competition/monitors/{monitor_id}/refresh")
async def refresh_competition_monitor(monitor_id: str, user: dict = Depends(get_current_user)):
    """Re-analyze competition for a monitored keyword."""
    monitor = await db.competition_monitors.find_one(
        {"id": monitor_id, "user_id": user["id"]}, {"_id": 0}
    )
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    keyword = monitor["keyword"]
    from llm_helper import llm_chat
    prompt = f"""Przeprowadź aktualną analizę konkurencji dla frazy: "{keyword}" w Google (rynek polski).

Odpowiedz WYŁĄCZNIE JSON:
{{
    "keyword": "{keyword}",
    "difficulty": 55,
    "monthly_volume": 1800,
    "top_results": [
        {{"position": 1, "title": "Tytuł", "url": "https://example.pl", "domain": "example.pl", "estimated_traffic": 500, "content_score": 78}}
    ],
    "content_gaps": ["Aspekt nieporuszony"],
    "recommended_actions": ["Rekomendacja"]
}}
Wygeneruj 5-8 wyników, 3-5 luk, 3-5 rekomendacji."""

    try:
        resp = await llm_chat(prompt, system_message="Ekspert SEO. Odpowiadaj WYŁĄCZNIE JSON.", session_id=f"comp-ref-{hash(keyword)%100000}", timeout=120)
        clean = resp.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```(?:json)?\s*', '', clean)
            clean = re.sub(r'\s*```$', '', clean)
        analysis = json.loads(clean)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd analizy: {e}")

    await db.competition_monitors.update_one(
        {"id": monitor_id},
        {"$set": {"analysis": analysis, "last_checked": datetime.now(timezone.utc).isoformat()}}
    )
    monitor["analysis"] = analysis
    monitor["last_checked"] = datetime.now(timezone.utc).isoformat()
    return monitor

