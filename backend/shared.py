"""
Shared dependencies for all route modules.
Contains: DB connection, auth helpers, Pydantic models, utility functions.
"""
from dotenv import load_dotenv
import os
from pathlib import Path

# Load .env FIRST
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env', override=False)

from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise RuntimeError("MONGO_URL environment variable is required")
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
db = client[os.environ.get('DB_NAME', 'seo_article_writer')]

# Thread pool for background tasks
executor = ThreadPoolExecutor(max_workers=4)

# Validate LLM key
_llm_key = os.environ.get('EMERGENT_LLM_KEY')
if _llm_key:
    logging.info(f"EMERGENT_LLM_KEY loaded: {_llm_key[:12]}...")
else:
    logging.warning("EMERGENT_LLM_KEY NOT FOUND!")


# ============ Auth Helpers ============

from auth import (
    register_user, authenticate_user, get_user_by_id,
    create_access_token, decode_access_token, hash_password
)

async def get_current_user_optional(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return await get_user_by_id(db, user_id)

async def get_current_user(authorization: Optional[str] = Header(None)):
    user = await get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Wymagane logowanie")
    return user

async def require_admin(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Wymagane uprawnienia administratora")
    return user


# ============ Utility ============

def serialize_doc(doc: dict) -> dict:
    if doc is None:
        return None
    if "_id" in doc:
        del doc["_id"]
    for key, value in doc.items():
        if isinstance(value, datetime):
            doc[key] = value.isoformat()
    return doc


# ============ Pydantic Models ============

class ArticleGenerateRequest(BaseModel):
    topic: str
    primary_keyword: str
    secondary_keywords: List[str] = []
    target_length: int = 1500
    tone: str = "profesjonalny"
    template: str = "standard"
    language: str = "pl"
    quality_preset: str = "premium"  # "draft" | "standard" | "premium"

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
    format: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class AdminCreateUserRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    is_admin: bool = False

class AdminUpdateUserRequest(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class ImageGenerateRequest(BaseModel):
    prompt: str
    style: str = "hero"
    article_id: Optional[str] = None
    variation_type: Optional[str] = None
    reference_image: Optional[Any] = None
    reference_images: Optional[List[Any]] = None

class ReferenceImageData(BaseModel):
    data: str
    mime_type: str

class ImageTagsRequest(BaseModel):
    tags: List[str] = []

class ImageEditRequest(BaseModel):
    mode: str
    prompt: str
    image_id: Optional[str] = None
    source_image: Optional[ReferenceImageData] = None

class MultiVariantRequest(BaseModel):
    prompt: str
    style: str = "hero"
    article_id: Optional[str] = None
    num_variants: int = 4
    reference_image: Optional[ReferenceImageData] = None
    reference_images: Optional[List[ReferenceImageData]] = None

class WordPressSettingsRequest(BaseModel):
    wp_url: str
    wp_user: str
    wp_app_password: str

class SeriesRequest(BaseModel):
    topic: str
    primary_keyword: str
    num_parts: int = 4
    source_text: str = ""

class SEOAssistantRequest(BaseModel):
    mode: str = "analyze"
    message: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None

class CalendarRequest(BaseModel):
    period: str = "miesiac"

class ImportUrlRequest(BaseModel):
    url: str
    optimize: bool = True

class ImportWordPressRequest(BaseModel):
    wp_url: str
    wp_user: str = ""
    wp_password: str = ""
    limit: int = 20

class SchedulePublishRequest(BaseModel):
    scheduled_at: str
    publish_to_wordpress: bool = True

class SEOAuditRequest(BaseModel):
    url: str

class CompetitionRequest(BaseModel):
    article_id: str
    competitor_url: str

class KeywordAnalyticsRequest(BaseModel):
    keywords: List[str] = []
    industry: str = "rachunkowość i podatki"

class RewriteRequest(BaseModel):
    text: str
    style: str = "profesjonalny"
    article_id: str = ""

class NewsletterRequest(BaseModel):
    title: str = ""
    article_ids: List[str] = []
    style: str = "informacyjny"

class ChatMessage(BaseModel):
    message: str
    article_id: str = ""

class RegenerateRequest(BaseModel):
    section: str = ""
    section_index: int = 0
    instructions: str = ""

class PlagiarismCheckRequest(BaseModel):
    article_id: str

class ContentVerifyRequest(BaseModel):
    article_id: str

class AutoCompetitionRequest(BaseModel):
    article_id: str

class ABTitleRequest(BaseModel):
    article_id: str
    custom_variants: List[str] = []

class BulkDeleteRequest(BaseModel):
    article_ids: List[str]

class BulkCategoryRequest(BaseModel):
    article_ids: List[str]
    category: str

class AutoMetaRequest(BaseModel):
    article_id: str

class PublishScheduleRequest(BaseModel):
    article_id: str

class SocialPostsRequest(BaseModel):
    article_id: str
