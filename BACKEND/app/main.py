import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import hashlib
from sqlalchemy.orm import Session

from database import create_tables, SessionLocal
from routes import contacts, blogs, products, auth, admin, search, newsletter, analytics, content
from core.config import settings
from scheduler import init_scheduler, start_scheduler, stop_scheduler
from models.user import AdminUser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NekwasaR Portfolio API",
    description="Backend API for NekwasaR's portfolio website",
    version="1.0.0"
)

# Templates for admin pages
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(blogs.router, prefix="/api/blogs", tags=["blogs"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(newsletter.router, prefix="/api/newsletter", tags=["newsletter"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(content.router, prefix="/api/content", tags=["content"])
app.include_router(admin.router, tags=["admin"])

# Mount static files for admin interface
app.mount("/static", StaticFiles(directory="../../portfolio"), name="static")

def create_default_admin_user():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(AdminUser).filter(AdminUser.username == "gojominitia").first()
        
        if admin_user:
            logger.info("Admin user already exists, skipping creation")
            return
        
        # Create default admin user
        hashed_password = hashlib.sha256("gojominitiA@".encode()).hexdigest()
        default_admin = AdminUser(
            username="gojominitia",
            email="gojominitia@nekwasar.com", 
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        db.add(default_admin)
        db.commit()
        logger.info("✅ Default admin user created successfully!")
        logger.info("Username: gojominitia")
        logger.info("Password: gojominitiA@")
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {str(e)}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    """Create database tables and initialize scheduler on startup"""
    logger.info("🚀 Starting up application...")

    # Create database tables
    logger.info("📋 Creating database tables...")
    create_tables()

    # Create default admin user
    logger.info("👤 Creating default admin user...")
    create_default_admin_user()

    # Initialize scheduler
    logger.info("⏰ Initializing scheduler...")
    init_scheduler()
    start_scheduler()

    logger.info("✅ Application started successfully!")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to main portfolio site"""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0; url=http://127.0.0.1:8000" />
        </head>
        <body>
            <p>Redirecting to portfolio site...</p>
        </body>
    </html>
    """

# Fallback admin dashboard routes (ensure rendering even if router load order conflicts)
@app.get("/admin/dashboard", response_class=HTMLResponse)
@app.get("/admin/dashboard/", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})


# Production Security Features (Commented for easy enabling)
"""
# HTTPS Enforcement (Uncomment in production)
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

# Rate Limiting (Uncomment in production)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Enhanced CORS (Uncomment and configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"],  # Replace with your domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security Headers (Uncomment in production)
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "www.yourdomain.com"])

# Input Validation Enhancement (Uncomment in production)
from pydantic import validator, BaseModel

class SecureContactCreate(BaseModel):
    name: str
    email: str
    message: str

    @validator('name')
    def name_must_be_valid(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        if not all(c.isalnum() or c.isspace() or c in ".-'" for c in v):
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

# Replace ContactCreate with SecureContactCreate in routes/contacts.py
"""

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )