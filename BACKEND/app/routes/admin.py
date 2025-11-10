from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import os
from auth import get_current_user, get_current_active_user
from fastapi.exception_handlers import http_exception_handler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
auth_logger = logging.getLogger('admin_auth')  # Dedicated auth logger
auth_logger.setLevel(logging.DEBUG)

router = APIRouter()

# Templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Custom 403 error handler
@router.get("/admin/403", response_class=HTMLResponse)
async def admin_403_error(request: Request):
    """Serve custom 403 error page"""
    auth_logger.info("🚫 403 ERROR PAGE ACCESSED - Unauthenticated user attempted admin access")
    return templates.TemplateResponse("admin_403_error.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
@router.get("/admin/", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Serve admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.get("/admin/dashboard", response_class=HTMLResponse)
@router.get("/admin/dashboard/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user = Depends(get_current_active_user)):
    """Serve admin dashboard with new navigation system - REQUIRES AUTHENTICATION"""
    auth_logger.info(f"🎯 ADMIN DASHBOARD ACCESS - User: {current_user.username}, IP: {request.client.host}")
    return templates.TemplateResponse("admin_base.html", {"request": request, "current_user": current_user})

@router.get("/admin/contact", response_class=HTMLResponse)
@router.get("/admin/contact/", response_class=HTMLResponse)
async def admin_contact(request: Request, current_user = Depends(get_current_active_user)):
    """Serve admin contact management - REQUIRES AUTHENTICATION"""
    auth_logger.info(f"📧 ADMIN CONTACT ACCESS - User: {current_user.username}, IP: {request.client.host}")
    return templates.TemplateResponse("admin_contact.html", {"request": request, "current_user": current_user})

@router.get("/admin/{section}/{page}", response_class=HTMLResponse)
async def admin_section_page(request: Request, section: str, page: str, current_user = Depends(get_current_active_user)):
    """Serve admin section pages dynamically - REQUIRES AUTHENTICATION"""
    auth_logger.info(f"🔗 ADMIN SECTION ACCESS - User: {current_user.username}, Section: {section}, Page: {page}, IP: {request.client.host}")
    return templates.TemplateResponse("admin_base.html", {"request": request, "current_user": current_user})

# API endpoints for dynamic page loading - PROTECTED
@router.get("/templates/{template_name}")
async def get_admin_template(template_name: str, current_user = Depends(get_current_active_user)):
    """Serve admin page templates dynamically - REQUIRES AUTHENTICATION"""
    try:
        auth_logger.info(f"🗓️ TEMPLATE REQUEST - User: {current_user.username}, Template: {template_name}")
        
        # Log auth details
        auth_logger.info(f"🔐 Auth user ID: {current_user.id}, Username: {current_user.username}, is_superuser: {current_user.is_superuser}")
        
        # Log templates_dir path
        auth_logger.info(f"📁 templates_dir path: {templates_dir}")
        auth_logger.info(f"📁 templates_dir exists: {templates_dir.exists()}")
        auth_logger.info(f"📁 templates_dir absolute: {templates_dir.absolute()}")
        auth_logger.info(f"📁 Current working directory: {os.getcwd()}")
        
        # Log constructed template path
        template_path = templates_dir / template_name
        auth_logger.info(f"🔗 Constructed template path: {template_path}")
        auth_logger.info(f"🔗 Template path exists: {template_path.exists()}")
        auth_logger.info(f"🔗 Template path absolute: {template_path.absolute()}")
        
        # Check parent directories
        auth_logger.info(f"📂 Parent directory: {template_path.parent}")
        auth_logger.info(f"📂 Parent directory exists: {template_path.parent.exists()}")
        
        if template_path.exists():
            try:
                auth_logger.info(f"📖 Attempting to read file: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                auth_logger.info(f"✅ File read successfully! Content length: {len(content)} characters")
                
                auth_logger.info(f"🚀 Returning HTML response for {template_name}")
                return HTMLResponse(content=content, media_type="text/html")
                
            except Exception as e:
                auth_logger.error(f"❌ Error reading file {template_path}: {str(e)}")
                auth_logger.error(f"❌ Exception type: {type(e).__name__}")
                raise HTTPException(500, f"Error reading template file: {str(e)}")
        else:
            auth_logger.warning(f"❌ Template file not found: {template_path}")
            raise HTTPException(404, f"Template {template_name} not found")
            
    except Exception as e:
        auth_logger.error(f"💥 General error in get_admin_template: {str(e)}")
        auth_logger.error(f"💥 Exception type: {type(e).__name__}")
        raise HTTPException(500, f"Error loading template: {str(e)}")

@router.post("/admin/logout")
async def admin_logout(current_user = Depends(get_current_active_user)):
    """Handle admin logout - clear session/token"""
    from fastapi.responses import JSONResponse
    auth_logger.info(f"🚪 LOGOUT REQUEST - User: {current_user.username}, ID: {current_user.id}")
    return JSONResponse(
        content={"message": "Logged out successfully"},
        headers={
            "Set-Cookie": "access_token=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/"
        }
    )

# Add authentication check middleware-style route
@router.get("/admin/check-auth")
async def check_auth(current_user = Depends(get_current_active_user)):
    """Check if user is authenticated - used by frontend"""
    from fastapi.responses import JSONResponse
    auth_logger.info(f"✅ AUTH CHECK SUCCESS - User: {current_user.username}, ID: {current_user.id}, is_superuser: {current_user.is_superuser}")
    auth_logger.info(f"🔍 Returning auth data for user: {current_user.email}")
    return JSONResponse({
        "authenticated": True,
        "user": {
            "username": current_user.username,
            "is_superuser": current_user.is_superuser,
            "email": current_user.email
        }
    })