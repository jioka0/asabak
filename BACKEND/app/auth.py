from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db
from models.user import AdminUser
from schemas import TokenData
from core.config import settings
import logging

# Set up dedicated auth logging
auth_logger = logging.getLogger('auth_flow')
auth_logger.setLevel(logging.DEBUG)

# Security configuration
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Temporarily disable bcrypt due to compatibility issues
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Use simple hash verification for now
    import hashlib
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Use a simple hash for now to avoid bcrypt issues
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    auth_logger.info(f"🔐 JWT CREATED - User: {data.get('sub')}, Expires: {expire}, Token length: {len(encoded_jwt)}")
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate user with username and password"""
    auth_logger.info(f"🔍 AUTH ATTEMPT - Username: {username}, Time: {datetime.now()}")
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    
    if not user:
        auth_logger.warning(f"❌ AUTH FAILED - User not found: {username}")
        return False
    
    auth_logger.info(f"👤 USER FOUND - ID: {user.id}, Username: {user.username}, Active: {user.is_active}")
    
    if not verify_password(password, user.hashed_password):
        auth_logger.warning(f"❌ AUTH FAILED - Wrong password for: {username}")
        return False
    
    if not user.is_active:
        auth_logger.warning(f"❌ AUTH FAILED - User inactive: {username}")
        return False
        
    auth_logger.info(f"✅ AUTH SUCCESS - User authenticated: {username}")
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        auth_logger.info(f"🔍 JWT DECODE ATTEMPT - Token: {credentials.credentials[:50]}...")
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        auth_logger.info(f"🔍 JWT DECODED - Username from token: {username}")
        auth_logger.info(f"🔍 Token payload: {payload}")
        
        if username is None:
            auth_logger.warning(f"❌ JWT VALIDATION FAILED - No username in token")
            raise credentials_exception
        token_data = TokenData(username=username)
        auth_logger.info(f"🔑 TOKEN DATA CREATED - Username: {token_data.username}")
    except JWTError as e:
        auth_logger.error(f"❌ JWT DECODE ERROR - {e}")
        auth_logger.error(f"❌ TOKEN INVALID - Error type: {type(e).__name__}")
        raise credentials_exception

    user = db.query(AdminUser).filter(AdminUser.username == token_data.username).first()
    if user is None:
        auth_logger.error(f"❌ USER NOT FOUND - Username: {token_data.username}")
        raise credentials_exception
    
    auth_logger.info(f"✅ USER RETRIEVED - ID: {user.id}, Username: {user.username}, Active: {user.is_active}, Superuser: {user.is_superuser}")
    return user

def get_current_active_user(current_user: AdminUser = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_superuser(current_user: AdminUser = Depends(get_current_active_user)):
    """Get current superuser"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

# Production Security Features (Commented for easy enabling)
"""
# HTTPS Enforcement (Uncomment in production)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Rate Limiting (Uncomment in production)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS Settings (Uncomment and configure for production)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers (Uncomment in production)
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])

# Input Validation Enhancement (Uncomment in production)
from pydantic import validator

class SecureContactCreate(BaseModel):
    name: str
    email: str
    message: str

    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not v.replace(' ', '').isalnum():
            raise ValueError('Name contains invalid characters')
        return v.strip()

    @validator('email')
    def email_must_be_valid(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

    @validator('message')
    def message_must_be_valid(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters')
        return v.strip()
"""