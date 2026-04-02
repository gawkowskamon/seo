"""Auth and Admin routes."""
import os
from fastapi import APIRouter, Depends
from shared import (
    db, get_current_user, require_admin, serialize_doc, HTTPException, uuid, datetime, timezone,
    RegisterRequest, LoginRequest, AdminCreateUserRequest, AdminUpdateUserRequest,
    register_user, authenticate_user, create_access_token, hash_password, List
)

router = APIRouter()

# ============ Auth Routes ============

@router.post("/auth/register")
async def api_register(request: RegisterRequest):
    """Register a new user."""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Haslo musi miec minimum 6 znakow")
    if "@" not in request.email:
        raise HTTPException(status_code=400, detail="Nieprawidlowy adres email")
    try:
        user = await register_user(db, request.email, request.password, request.full_name)
        token = create_access_token(data={"sub": user["id"], "email": user["email"]})
        return {"user": user, "token": token}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login")
async def api_login(request: LoginRequest):
    """Login and get JWT token."""
    user = await authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Nieprawidlowy email lub haslo")
    token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    return {"user": user, "token": token}

@router.get("/auth/me")
async def api_get_me(user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return user


# ============ Admin Routes ============

async def require_admin(user: dict = Depends(get_current_user)):
    """Require admin role."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Wymagane uprawnienia administratora")
    return user

@router.get("/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    """List all users (admin only)."""
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(200)
    # Batch count articles per user
    counts_cursor = db.articles.aggregate([{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}])
    counts = {doc["_id"]: doc["count"] async for doc in counts_cursor}
    result = []
    for u in users:
        if isinstance(u.get("created_at"), datetime):
            u["created_at"] = u["created_at"].isoformat()
        u["article_count"] = counts.get(u["id"], 0)
        result.append(u)
    return result

@router.post("/admin/users")
async def admin_create_user(request: AdminCreateUserRequest, admin: dict = Depends(require_admin)):
    """Create a new user (admin only)."""
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Haslo musi miec minimum 6 znakow")
    if "@" not in request.email:
        raise HTTPException(status_code=400, detail="Nieprawidlowy adres email")
    try:
        user = await register_user(db, request.email, request.password, request.full_name)
        # Update admin flag if set
        if request.is_admin:
            await db.users.update_one({"id": user["id"]}, {"$set": {"is_admin": True}})
            user["is_admin"] = True
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/admin/users/{user_id}")
async def admin_update_user(user_id: str, request: AdminUpdateUserRequest, admin: dict = Depends(require_admin)):
    """Update user role/permissions (admin only)."""
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="Uzytkownik nie znaleziony")
    
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.is_admin is not None:
        update_data["is_admin"] = request.is_admin
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if isinstance(updated.get("created_at"), datetime):
        updated["created_at"] = updated["created_at"].isoformat()
    return updated

@router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: dict = Depends(require_admin)):
    """Deactivate a user (admin only). Cannot deactivate yourself."""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Nie mozesz dezaktywowac wlasnego konta")
    target = await db.users.find_one({"id": user_id})
    if not target:
        raise HTTPException(status_code=404, detail="Uzytkownik nie znaleziony")
    await db.users.update_one({"id": user_id}, {"$set": {"is_active": False}})
    return {"message": "Uzytkownik dezaktywowany", "id": user_id}


@router.get("/health")
async def health():
    llm_key = os.environ.get("EMERGENT_LLM_KEY")
    return {
        "status": "healthy",
        "llm_key_configured": bool(llm_key),
    }

@router.get("/")
async def root():
    return {"message": "SEO Article Writer API", "status": "running"}

