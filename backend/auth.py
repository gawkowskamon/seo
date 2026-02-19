"""
JWT Authentication module.
Handles user registration, login, token generation, and token verification.
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
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kurdynowski-seo-jwt-secret-key-2026-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


async def register_user(db, email: str, password: str, full_name: str = "") -> dict:
    """Register a new user."""
    # Check if user already exists
    existing = await db.users.find_one({"email": email.lower()})
    if existing:
        raise ValueError("Uzytkownik z tym adresem email juz istnieje")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "full_name": full_name,
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    
    # Return user without password
    return {
        "id": user_id,
        "email": user_doc["email"],
        "full_name": user_doc["full_name"],
        "created_at": user_doc["created_at"].isoformat()
    }


async def authenticate_user(db, email: str, password: str) -> Optional[dict]:
    """Authenticate a user and return user data if valid."""
    user = await db.users.find_one({"email": email.lower()})
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    if not user.get("is_active", True):
        return None
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user.get("full_name", ""),
        "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else str(user["created_at"])
    }


async def get_user_by_id(db, user_id: str) -> Optional[dict]:
    """Get user by ID."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if user and isinstance(user.get("created_at"), datetime):
        user["created_at"] = user["created_at"].isoformat()
    return user
