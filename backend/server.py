"""
SEO Article Writer - Main Application Entry Point

Architecture:
  server.py              - App creation, middleware, startup/shutdown (this file)
  shared.py              - DB connection, auth helpers, Pydantic models
  routes/
    auth.py              - Auth & Admin (9 routes)
    articles.py          - Article CRUD, generation, export, scoring (13 routes)
    surfer.py            - SurferSEO endpoints (8 routes)
    images.py            - Image generation & library (11 routes)
    content.py           - WordPress, calendar, SEO assistant, chat (19 routes)
    seo_tools.py         - SEO audit, analytics, plagiarism, verification (32 routes)
    ai_features.py       - Bulk ops, versions, meta, schedule, social posts (12 routes)
    social.py            - Social media scheduling (4 routes)
    notifications.py     - Email notifications (5 routes)
    competition_monitor.py - Competition monitoring (4 routes)
    ────────────────────────────────────────────────
    Total: 117 API endpoints
"""
from dotenv import load_dotenv
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import logging
import uuid
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="SEO Article Writer", version="2.0.0")

# Create master router with /api prefix
api_router = APIRouter(prefix="/api")

# Import and include all sub-routers
from routes.auth import router as auth_router
from routes.articles import router as articles_router
from routes.surfer import router as surfer_router
from routes.images import router as images_router
from routes.content import router as content_router
from routes.seo_tools import router as seo_tools_router
from routes.ai_features import router as ai_features_router
from routes.social import router as social_router
from routes.notifications import router as notifications_router
from routes.competition_monitor import router as competition_router

# Include sub-routers - ORDER MATTERS: specific routes before parameterized ones
# Routes with /articles/... static paths must be included BEFORE /articles/{article_id}
api_router.include_router(auth_router)
api_router.include_router(ai_features_router)    # /articles/auto-meta, /articles/social-posts etc.
api_router.include_router(seo_tools_router)       # /articles/ai-suggestions
api_router.include_router(articles_router)        # /articles/{article_id} - must be LAST
api_router.include_router(surfer_router)
api_router.include_router(images_router)
api_router.include_router(content_router)
api_router.include_router(social_router)
api_router.include_router(notifications_router)
api_router.include_router(competition_router)

app.include_router(api_router)

# Health check (no /api prefix)
@app.get("/health")
async def root_health():
    return {"status": "healthy"}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup events
from shared import db, client
from auth import hash_password

@app.on_event("startup")
async def seed_admin_user():
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
        admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
        if not admin_email or not admin_password:
            logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD not set")
            return
        existing = await db.users.find_one({"email": admin_email})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()), "email": admin_email,
                "password_hash": hash_password(admin_password),
                "full_name": "Admin", "workspace_id": str(uuid.uuid4()),
                "is_admin": True, "is_active": True,
                "created_at": datetime.now(timezone.utc),
            })
            logger.info(f"Admin user created: {admin_email}")
        else:
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {"is_admin": True, "is_active": True, "password_hash": hash_password(admin_password)}}
            )
            logger.info(f"Admin user synced: {admin_email}")
    except Exception as e:
        logger.error(f"Failed to seed admin: {e}")

@app.on_event("startup")
async def cleanup_stale_jobs():
    try:
        result = await db.generation_jobs.update_many(
            {"status": "generating"},
            {"$set": {"status": "failed", "error": "Zadanie przerwane przez restart serwera."}}
        )
        if result.modified_count > 0:
            logger.info(f"Cleaned {result.modified_count} stale jobs")
    except Exception as e:
        logger.error(f"Failed to cleanup: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
