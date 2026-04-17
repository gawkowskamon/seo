"""WordPress webhook receiver routes.

Receives webhooks from WordPress sites (publish, update, delete, traffic stats)
to keep articles in sync with their published state on WP.

Setup on WordPress:
1. Install a webhook plugin (e.g., "WP Webhooks" or use custom PHP)
2. Configure webhook events:
   - post_published → POST {BACKEND}/api/wordpress/webhook
   - post_updated → POST {BACKEND}/api/wordpress/webhook
   - post_deleted → POST {BACKEND}/api/wordpress/webhook
   - (optional) daily_traffic_stats → POST {BACKEND}/api/wordpress/webhook
3. Include header: X-Webhook-Token: {user_token}
4. Payload: { "event": "...", "post_id": 123, "permalink": "...", "article_id": "emergent-art-id", ... }
"""
import secrets
import logging
from fastapi import APIRouter, Depends, Request, Header, HTTPException
from shared import db, get_current_user, uuid, datetime, timezone

router = APIRouter()

# ============================================================
# Token management
# ============================================================

@router.post("/wordpress/webhook/generate-token")
async def generate_webhook_token(user: dict = Depends(get_current_user)):
    """Generate (or regenerate) a unique webhook token for the user."""
    token = secrets.token_urlsafe(32)
    await db.wordpress_webhook_tokens.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "token": token,
            "user_id": user["id"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    return {"token": token}


@router.get("/wordpress/webhook/config")
async def get_webhook_config(request: Request, user: dict = Depends(get_current_user)):
    """Get webhook URL and token for this user."""
    doc = await db.wordpress_webhook_tokens.find_one({"user_id": user["id"]}, {"_id": 0})
    # Prefer X-Forwarded-Host (set by Kubernetes ingress) to build external URL
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    forwarded_proto = request.headers.get("x-forwarded-proto", "https")
    if forwarded_host:
        webhook_url = f"{forwarded_proto}://{forwarded_host}/api/wordpress/webhook"
    else:
        webhook_url = f"{str(request.base_url).rstrip('/')}/api/wordpress/webhook"
    return {
        "webhook_url": webhook_url,
        "token": doc.get("token") if doc else None,
        "has_token": bool(doc),
        "setup_instructions": {
            "method": "POST",
            "header_name": "X-Webhook-Token",
            "events_supported": [
                "post_published",
                "post_updated",
                "post_deleted",
                "traffic_stats"
            ],
            "example_payload_publish": {
                "event": "post_published",
                "post_id": 123,
                "permalink": "https://twojadomena.pl/artykul-url",
                "post_title": "Tytuł artykułu",
                "post_date": "2026-04-17T10:00:00Z",
                "article_id": "emergent-article-uuid"
            },
            "example_payload_traffic": {
                "event": "traffic_stats",
                "post_id": 123,
                "article_id": "emergent-article-uuid",
                "views_7d": 1250,
                "views_30d": 4800,
                "comments": 12,
                "avg_time_on_page_seconds": 180
            }
        }
    }


# ============================================================
# Webhook receiver (PUBLIC — authenticated via X-Webhook-Token)
# ============================================================

@router.post("/wordpress/webhook")
async def receive_webhook(request: Request, x_webhook_token: str = Header(None, alias="X-Webhook-Token")):
    """Receive webhooks from WordPress. Authenticates via X-Webhook-Token header."""
    if not x_webhook_token:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Token header")

    token_doc = await db.wordpress_webhook_tokens.find_one({"token": x_webhook_token}, {"_id": 0})
    if not token_doc:
        raise HTTPException(status_code=403, detail="Invalid webhook token")

    user_id = token_doc["user_id"]

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Missing 'event' field")

    # Log every webhook event for audit
    log_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "event": event,
        "payload": payload,
        "received_at": datetime.now(timezone.utc).isoformat()
    }
    await db.wordpress_webhook_events.insert_one(log_doc)

    # Find article by emergent article_id or by wp_post_id
    article_id = payload.get("article_id")
    wp_post_id = payload.get("post_id")

    article_query = None
    if article_id:
        article_query = {"id": article_id, "user_id": user_id}
    elif wp_post_id:
        article_query = {"wp_post_id": int(wp_post_id), "user_id": user_id}

    if not article_query:
        return {"status": "logged", "message": "No article_id or post_id to link"}

    article = await db.articles.find_one(article_query, {"_id": 0, "id": 1})
    if not article:
        return {"status": "logged", "message": "Article not found (but event stored)"}

    target_article_id = article["id"]
    now = datetime.now(timezone.utc).isoformat()

    # ============================================================
    # Event handlers
    # ============================================================
    if event == "post_published":
        update = {
            "wp_post_id": int(wp_post_id) if wp_post_id else None,
            "wp_permalink": payload.get("permalink"),
            "wp_published_at": payload.get("post_date") or now,
            "wp_status": "published",
            "status": "published",
            "published_at": payload.get("post_date") or now,
        }
        await db.articles.update_one({"id": target_article_id}, {"$set": update})
        return {"status": "ok", "event": event, "article_id": target_article_id}

    elif event == "post_updated":
        update = {
            "wp_updated_at": payload.get("post_modified") or now,
            "wp_permalink": payload.get("permalink") or None,
        }
        update = {k: v for k, v in update.items() if v is not None}
        await db.articles.update_one({"id": target_article_id}, {"$set": update})
        return {"status": "ok", "event": event, "article_id": target_article_id}

    elif event == "post_deleted":
        await db.articles.update_one(
            {"id": target_article_id},
            {"$set": {
                "wp_status": "deleted",
                "wp_deleted_at": now,
                "status": "draft"  # revert to draft since no longer on WP
            }}
        )
        return {"status": "ok", "event": event, "article_id": target_article_id}

    elif event == "traffic_stats":
        stats = {
            "wp_views_7d": payload.get("views_7d", 0),
            "wp_views_30d": payload.get("views_30d", 0),
            "wp_views_total": payload.get("views_total", 0),
            "wp_comments": payload.get("comments", 0),
            "wp_avg_time_on_page": payload.get("avg_time_on_page_seconds", 0),
            "wp_bounce_rate": payload.get("bounce_rate", 0),
            "wp_traffic_updated_at": now,
        }
        await db.articles.update_one({"id": target_article_id}, {"$set": stats})
        return {"status": "ok", "event": event, "article_id": target_article_id, "stats_updated": list(stats.keys())}

    else:
        logging.warning(f"Unknown WP webhook event: {event}")
        return {"status": "logged", "message": f"Unknown event type: {event}"}


# ============================================================
# Webhook events history
# ============================================================

@router.get("/wordpress/webhook/events")
async def list_webhook_events(limit: int = 50, user: dict = Depends(get_current_user)):
    """List recent webhook events received for this user."""
    events = await db.wordpress_webhook_events.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("received_at", -1).limit(min(limit, 200)).to_list(200)
    return events


@router.get("/wordpress/webhook/article-stats/{article_id}")
async def get_article_wp_stats(article_id: str, user: dict = Depends(get_current_user)):
    """Get WordPress traffic/publish stats for a specific article."""
    article = await db.articles.find_one(
        {"id": article_id, "user_id": user["id"]},
        {"_id": 0, "wp_post_id": 1, "wp_permalink": 1, "wp_published_at": 1, "wp_updated_at": 1,
         "wp_status": 1, "wp_views_7d": 1, "wp_views_30d": 1, "wp_views_total": 1,
         "wp_comments": 1, "wp_avg_time_on_page": 1, "wp_bounce_rate": 1, "wp_traffic_updated_at": 1}
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
