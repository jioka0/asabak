from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/admin", response_class=HTMLResponse)
@router.get("/admin/", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Serve admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.get("/admin/dashboard", response_class=HTMLResponse)
@router.get("/admin/dashboard/", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Serve admin dashboard with new navigation system"""
    return templates.TemplateResponse("admin_base.html", {"request": request})

@router.get("/admin/contact", response_class=HTMLResponse)
@router.get("/admin/contact/", response_class=HTMLResponse)
async def admin_contact(request: Request):
    """Serve admin contact management"""
    return templates.TemplateResponse("admin_contact.html", {"request": request})

@router.get("/admin/{section}/{page}", response_class=HTMLResponse)
async def admin_section_page(request: Request, section: str, page: str):
    """Serve admin section pages dynamically"""
    return templates.TemplateResponse("admin_base.html", {"request": request})

# API endpoints for dynamic page loading
@router.get("/templates/{template_name}")
async def get_admin_template(template_name: str):
    """Serve admin page templates dynamically"""
    try:
        logger.info(f"🔍 Request for template: {template_name}")
        
        # Log templates_dir path
        logger.info(f"📁 templates_dir path: {templates_dir}")
        logger.info(f"📁 templates_dir exists: {templates_dir.exists()}")
        logger.info(f"📁 templates_dir absolute: {templates_dir.absolute()}")
        logger.info(f"📁 Current working directory: {os.getcwd()}")
        
        # Log constructed template path
        template_path = templates_dir / template_name
        logger.info(f"🔗 Constructed template path: {template_path}")
        logger.info(f"🔗 Template path exists: {template_path.exists()}")
        logger.info(f"🔗 Template path absolute: {template_path.absolute()}")
        
        # Check parent directories
        logger.info(f"📂 Parent directory: {template_path.parent}")
        logger.info(f"📂 Parent directory exists: {template_path.parent.exists()}")
        
        if template_path.exists():
            try:
                logger.info(f"📖 Attempting to read file: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.info(f"✅ File read successfully! Content length: {len(content)} characters")
                
                logger.info(f"🚀 Returning HTML response for {template_name}")
                return HTMLResponse(content=content, media_type="text/html")
                
            except Exception as e:
                logger.error(f"❌ Error reading file {template_path}: {str(e)}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                raise HTTPException(500, f"Error reading template file: {str(e)}")
        else:
            logger.warning(f"❌ Template file not found: {template_path}")
            raise HTTPException(404, f"Template {template_name} not found")
            
    except Exception as e:
        logger.error(f"💥 General error in get_admin_template: {str(e)}")
        logger.error(f"💥 Exception type: {type(e).__name__}")
        raise HTTPException(500, f"Error loading template: {str(e)}")