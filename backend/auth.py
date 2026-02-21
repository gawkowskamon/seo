"""
JWT Authentication module.
Handles user registration, login, token generation, and token verification.
Supports workspaces (each user = one workspace) and admin role.
"""

import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or os.environ.get("SECRET_KEY") or "kurdynowski-seo-jwt-secret-" + os.environ.get("DB_NAME", "fallback")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def _serialize_user(user: dict) -> dict:
    """Serialize user for API response (exclude password, convert dates)."""
    result = {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "workspace_id": user.get("workspace_id", user["id"]),
        "is_admin": user.get("is_admin", False),
    }
    created = user.get("created_at")
    if isinstance(created, datetime):
        result["created_at"] = created.isoformat()
    elif created:
        result["created_at"] = str(created)
    return result


async def register_user(db, email: str, password: str, full_name: str = "") -> dict:
    """Register a new user with their own workspace."""
    existing = await db.users.find_one({"email": email.lower()})
    if existing:
        raise ValueError("Uzytkownik z tym adresem email juz istnieje")
    
    user_id = str(uuid.uuid4())
    workspace_id = str(uuid.uuid4())
    
    user_doc = {
        "id": user_id,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "full_name": full_name,
        "workspace_id": workspace_id,
        "is_admin": False,
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    return _serialize_user(user_doc)


async def authenticate_user(db, email: str, password: str) -> Optional[dict]:
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active", True):
        return None
    return _serialize_user(user)


async def get_user_by_id(db, user_id: str) -> Optional[dict]:
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        return None
    return _serialize_user(user)
