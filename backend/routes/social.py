"""Social media scheduling."""
from fastapi import APIRouter, Depends
from shared import db, get_current_user, HTTPException, uuid, datetime, timezone, List

router = APIRouter()

# ============ Social Media Scheduling ============

@router.post("/social/schedule")
async def schedule_social_post(request: dict, user: dict = Depends(get_current_user)):
    """Schedule a social media post for later publishing."""
    platform = request.get("platform", "")
    text = request.get("text", "")
    scheduled_at = request.get("scheduled_at", "")
    article_id = request.get("article_id", "")
    hashtags = request.get("hashtags", [])

    if not platform or not text or not scheduled_at:
        raise HTTPException(status_code=400, detail="platform, text, scheduled_at required")

    post = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "article_id": article_id,
        "platform": platform,
        "text": text,
        "hashtags": hashtags,
        "scheduled_at": scheduled_at,
        "status": "scheduled",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.scheduled_posts.insert_one(post)
    post.pop("_id", None)
    return post


@router.get("/social/scheduled")
async def list_scheduled_posts(user: dict = Depends(get_current_user)):
    """List all scheduled social media posts for the user."""
    posts = await db.scheduled_posts.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("scheduled_at", 1).to_list(100)
    return posts


@router.delete("/social/scheduled/{post_id}")
async def cancel_scheduled_post(post_id: str, user: dict = Depends(get_current_user)):
    """Cancel a scheduled post."""
    result = await db.scheduled_posts.delete_one({"id": post_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"status": "cancelled", "id": post_id}


@router.put("/social/scheduled/{post_id}/publish")
async def mark_post_published(post_id: str, user: dict = Depends(get_current_user)):
    """Mark a scheduled post as published."""
    result = await db.scheduled_posts.update_one(
        {"id": post_id, "user_id": user["id"]},
        {"$set": {"status": "published", "published_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"status": "published", "id": post_id}


