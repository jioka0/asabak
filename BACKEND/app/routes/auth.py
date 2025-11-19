from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.auth import authenticate_user, create_access_token, get_current_active_user, get_current_superuser
from backend.app.models.user import AdminUser as DBAdminUser
from backend.app.schemas import AdminUserCreate, AdminUser as AdminUserSchema, Token, AdminLogin
import logging

# Set up dedicated auth route logging
auth_route_logger = logging.getLogger('auth_routes')
auth_route_logger.setLevel(logging.DEBUG)

router = APIRouter()

@router.post("/register", response_model=AdminUserSchema)
async def register_admin(user: AdminUserCreate, db: Session = Depends(get_db)):
    """Register a new admin user (only for initial setup)"""
    # Check if user already exists
    db_user = db.query(DBAdminUser).filter(
        (DBAdminUser.username == user.username) | (DBAdminUser.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    # Create new admin user
    from backend.app.auth import get_password_hash
    hashed_password = get_password_hash(user.password)
    db_user = DBAdminUser(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_superuser=True  # First user is superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return AdminUserSchema(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at,
        last_login=db_user.last_login
    )

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    auth_route_logger.info("🚀 LOGIN ENDPOINT CALLED")
    auth_route_logger.info(f"📝 FORM DATA - Username: {form_data.username}, Grant type: {form_data.grant_type}")
    auth_route_logger.info(f"🔐 PASSWORD LENGTH - {len(form_data.password) if form_data.password else 0}")

    auth_route_logger.info("🔍 STARTING USER AUTHENTICATION")
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        auth_route_logger.error(f"❌ AUTHENTICATION FAILED - Username: {form_data.username}")
        auth_route_logger.error("❌ INVALID CREDENTIALS - Login rejected")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_route_logger.info("✅ USER AUTHENTICATION SUCCESSFUL")
    auth_route_logger.info(f"👤 USER DETAILS - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    auth_route_logger.info(f"🔐 USER STATUS - Active: {user.is_active}, Superuser: {user.is_superuser}")

    access_token_expires = timedelta(minutes=120)  # 2 hours
    auth_route_logger.info(f"⏰ TOKEN EXPIRATION - {access_token_expires} (2 hours)")

    auth_route_logger.info("🔐 CREATING ACCESS TOKEN")
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    auth_route_logger.info("✅ LOGIN PROCESS COMPLETED")
    auth_route_logger.info(f"🎫 TOKEN DETAILS - Length: {len(access_token)}, Type: bearer")
    auth_route_logger.info(f"🚀 RETURNING TOKEN RESPONSE - Username: {form_data.username}")

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AdminUserSchema)
async def read_users_me(current_user: DBAdminUser = Depends(get_current_active_user)):
    """Get current user info"""
    return current_user

@router.get("/users", response_model=list[AdminUserSchema])
async def get_admin_users(
    skip: int = 0,
    limit: int = 100,
    current_user: DBAdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get all admin users (superuser only)"""
    users = db.query(DBAdminUser).offset(skip).limit(limit).all()
    return users

@router.put("/users/{user_id}/activate")
async def activate_admin_user(
    user_id: int,
    current_user: DBAdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Activate/deactivate admin user (superuser only)"""
    user = db.query(DBAdminUser).filter(DBAdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}"}

@router.delete("/users/{user_id}")
async def delete_admin_user(
    user_id: int,
    current_user: DBAdminUser = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Delete admin user (superuser only)"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(DBAdminUser).filter(DBAdminUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return {"message": "User deleted"}