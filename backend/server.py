"""
SEO Article Writer - Main Application Entry Point

This is the main FastAPI application server. All API routes are organized
in the routes/ directory and imported here.

Architecture:
  server.py           - App creation, middleware, startup/shutdown events
  routes/api_routes.py - All API route handlers (117 endpoints)
  shared.py           - Shared models, DB connection, auth helpers (optional future use)
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env FIRST before any other imports
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import logging
import uuid
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="SEO Article Writer", version="2.0.0")

# Import routes
from routes.api_routes import api_router, db, client

# Include the API router
app.include_router(api_router)

# Root health check for Kubernetes probes (no /api prefix)
@app.get("/health")
async def root_health():
    return {"status": "healthy"}

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Startup Events ============

from auth import hash_password

@app.on_event("startup")
async def seed_admin_user():
    """Ensure admin user exists on every startup with correct password."""
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
        admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
        if not admin_email or not admin_password:
            logger.warning("ADMIN_EMAIL or ADMIN_PASSWORD not set, skipping admin seed")
            return
        existing = await db.users.find_one({"email": admin_email})
        if not existing:
            admin_doc = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "password_hash": hash_password(admin_password),
                "full_name": "Admin",
                "workspace_id": str(uuid.uuid4()),
                "is_admin": True,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
            await db.users.insert_one(admin_doc)
            logger.info(f"Admin user created: {admin_email}")
        else:
            await db.users.update_one(
                {"email": admin_email},
                {"$set": {
                    "is_admin": True,
                    "is_active": True,
                    "password_hash": hash_password(admin_password)
                }}
            )
            logger.info(f"Admin user synced: {admin_email}")
    except Exception as e:
        logger.error(f"Failed to seed admin user: {e}")
        logger.warning("Application will continue without admin seeding")


@app.on_event("startup")
async def cleanup_stale_generation_jobs():
    """Mark any stuck 'generating' jobs as failed on startup."""
    try:
        result = await db.generation_jobs.update_many(
            {"status": "generating"},
            {"$set": {"status": "failed", "error": "Zadanie przerwane przez restart serwera. Sprobuj ponownie."}}
        )
        if result.modified_count > 0:
            logger.info(f"Cleaned up {result.modified_count} stale generation jobs on startup")
    except Exception as e:
        logger.error(f"Failed to cleanup stale jobs: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
