"""Email notifications system."""
import logging
from fastapi import APIRouter, Depends
from shared import db, get_current_user, HTTPException, uuid, datetime, timezone

router = APIRouter()

# ============ Email Notifications ============

@router.get("/notifications/settings")
async def get_notification_settings(user: dict = Depends(get_current_user)):
    """Get notification settings for current user."""
    settings = await db.notification_settings.find_one(
        {"user_id": user["id"]}, {"_id": 0}
    )
    if not settings:
        settings = {
            "user_id": user["id"],
            "email_enabled": True,
            "frequency": "weekly",
            "notify_seo_drop": True,
            "notify_article_age": True,
            "article_age_days": 90,
            "seo_drop_threshold": 10,
            "notify_competition": True,
        }
        await db.notification_settings.insert_one({**settings})
        settings.pop("_id", None)
    return settings


@router.put("/notifications/settings")
async def update_notification_settings(request: dict, user: dict = Depends(get_current_user)):
    """Update notification settings."""
    allowed = ["email_enabled", "frequency", "notify_seo_drop", "notify_article_age",
               "article_age_days", "seo_drop_threshold", "notify_competition"]
    updates = {k: v for k, v in request.items() if k in allowed}
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    await db.notification_settings.update_one(
        {"user_id": user["id"]},
        {"$set": updates, "$setOnInsert": {"user_id": user["id"]}},
        upsert=True
    )
    return await get_notification_settings(user=user)


@router.post("/notifications/check-updates")
async def check_article_updates(user: dict = Depends(get_current_user)):
    """Check which articles need updating based on age and SEO score changes."""
    settings = await db.notification_settings.find_one({"user_id": user["id"]}, {"_id": 0})
    age_days = (settings or {}).get("article_age_days", 90)

    articles = await db.articles.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "title": 1, "created_at": 1, "updated_at": 1, "seo_score": 1, "surfer_score": 1, "primary_keyword": 1}
    ).to_list(500)

    notifications = []
    now = datetime.now(timezone.utc)

    for art in articles:
        created = art.get("created_at") or art.get("updated_at", "")
        try:
            if isinstance(created, str):
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            else:
                created_dt = created
            days_old = (now - created_dt).days
        except Exception:
            days_old = 0

        if days_old >= age_days:
            notifications.append({
                "type": "article_age",
                "article_id": art.get("id"),
                "title": art.get("title", "Bez tytułu"),
                "message": f"Artykuł ma {days_old} dni — rozważ aktualizację treści",
                "severity": "warning" if days_old < age_days * 2 else "critical",
                "days_old": days_old,
            })

        seo_score = art.get("seo_score", {})
        surfer_score = art.get("surfer_score", {})
        pct = surfer_score.get("percentage") or seo_score.get("total_percentage", 0)
        if pct and pct < 60:
            notifications.append({
                "type": "low_seo",
                "article_id": art.get("id"),
                "title": art.get("title", "Bez tytułu"),
                "message": f"Wynik SEO: {pct}% — wymaga optymalizacji",
                "severity": "critical" if pct < 40 else "warning",
                "score": pct,
            })

    notifications.sort(key=lambda x: 0 if x["severity"] == "critical" else 1)
    return {"notifications": notifications, "total": len(notifications)}


@router.post("/notifications/send-test")
async def send_test_notification(user: dict = Depends(get_current_user)):
    """Send a test email notification (MOCK - logs instead of sending)."""
    email = user.get("email", "unknown")
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "email": email,
        "subject": "Test powiadomienia — Kurdynowski SEO",
        "body": "To jest testowe powiadomienie z systemu Kurdynowski SEO Writer. Powiadomienia email działają poprawnie.",
        "status": "sent_mock",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.notification_log.insert_one({**notification})
    notification.pop("_id", None)
    logging.info(f"[MOCK EMAIL] To: {email} | Subject: {notification['subject']}")
    return {"status": "sent_mock", "message": f"Testowe powiadomienie 'wysłane' do {email} (tryb testowy)", "notification": notification}


@router.get("/notifications/history")
async def get_notification_history(user: dict = Depends(get_current_user)):
    """Get notification history for user."""
    logs = await db.notification_log.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("sent_at", -1).to_list(50)
    return logs


