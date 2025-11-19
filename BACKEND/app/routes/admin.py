from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import os
from backend.app.auth import get_current_user, get_current_active_user
from fastapi.exception_handlers import http_exception_handler
from backend.app.database import SessionLocal

# Get database session
db = SessionLocal()

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
async def admin_dashboard(request: Request):
    """Serve admin dashboard HTML page - Authentication handled by JavaScript"""
    auth_logger.info(f"📄 ADMIN DASHBOARD PAGE REQUEST - IP: {request.client.host}")
    return templates.TemplateResponse("admin_base.html", {"request": request})

@router.get("/admin/contact", response_class=HTMLResponse)
@router.get("/admin/contact/", response_class=HTMLResponse)
async def admin_contact(request: Request):
    """Serve admin contact management - Authentication handled by JavaScript"""
    auth_logger.info(f"📄 ADMIN CONTACT PAGE REQUEST - IP: {request.client.host}")
    return templates.TemplateResponse("admin_contact.html", {"request": request})

@router.get("/admin/{section}/{page}", response_class=HTMLResponse)
async def admin_section_page(request: Request, section: str, page: str):
    """Serve admin section pages dynamically - Authentication handled by JavaScript"""
    auth_logger.info(f"📄 ADMIN SECTION PAGE REQUEST - Section: {section}, Page: {page}, IP: {request.client.host}")
    return templates.TemplateResponse("admin_base.html", {"request": request})

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
async def check_auth(request: Request, current_user = Depends(get_current_active_user)):
    """Check if user is authenticated - used by frontend"""
    auth_logger.info("🚀 CHECK-AUTH ENDPOINT CALLED")
    auth_logger.info(f"🌐 REQUEST INFO - IP: {request.client.host}, Method: {request.method}, URL: {request.url}")
    auth_logger.info(f"🔍 HEADERS - Authorization: {'Bearer ***' if request.headers.get('authorization') else 'None'}")

    from fastapi.responses import JSONResponse

    auth_logger.info("✅ AUTH CHECK PASSED - User validation successful")
    auth_logger.info(f"👤 USER DETAILS - ID: {current_user.id}, Username: {current_user.username}, Email: {current_user.email}")
    auth_logger.info(f"🔐 USER STATUS - Active: {current_user.is_active}, Superuser: {current_user.is_superuser}")
    auth_logger.info(f"📅 USER TIMESTAMPS - Created: {current_user.created_at}, Last Login: {current_user.last_login}")

    response_data = {
        "authenticated": True,
        "user": {
            "username": current_user.username,
            "is_superuser": current_user.is_superuser,
            "email": current_user.email
        }
    }

    auth_logger.info(f"📤 RESPONSE DATA - {response_data}")
    auth_logger.info("✅ CHECK-AUTH COMPLETED SUCCESSFULLY")

    return JSONResponse(response_data)

# Dashboard API endpoints
@router.get("/api/admin/dashboard/kpi")
async def get_dashboard_kpi(current_user = Depends(get_current_active_user)):
    """Get dashboard KPI data"""
    from sqlalchemy import func
    from backend.app.models.blog import BlogPost
    from backend.app.models.contact import Contact
    from backend.app.models.blog import NewsletterSubscriber

    try:
        # Get total posts
        total_posts = db.query(func.count(BlogPost.id)).scalar() or 0

        # Get total comments (if you have a comments model)
        total_comments = 0  # Placeholder - implement when you have comments

        # Get total subscribers
        total_subscribers = db.query(func.count(NewsletterSubscriber.id)).scalar() or 0

        # Get total views (placeholder - implement analytics later)
        total_views = 0  # Placeholder

        # Mock change percentages (implement real calculations later)
        posts_change = 12
        comments_change = 8
        subscribers_change = 15
        views_change = 25

        return {
            "totalPosts": total_posts,
            "totalComments": total_comments,
            "totalSubscribers": total_subscribers,
            "totalViews": total_views,
            "postsChange": posts_change,
            "commentsChange": comments_change,
            "subscribersChange": subscribers_change,
            "viewsChange": views_change
        }
    except Exception as e:
        auth_logger.error(f"❌ Error getting KPI data: {e}")
        raise HTTPException(status_code=500, detail="Failed to load KPI data")

@router.get("/api/admin/dashboard/popular-content")
async def get_popular_content(current_user = Depends(get_current_active_user)):
    """Get popular content data"""
    from backend.app.models.blog import BlogPost

    try:
        # Get top 5 posts by views (placeholder - implement real view tracking)
        popular_posts = db.query(BlogPost).limit(5).all()

        return [
            {
                "title": post.title,
                "category": post.category or "General",
                "publishedAt": post.created_at.isoformat() if post.created_at else None,
                "views": getattr(post, 'views', 0) or 0  # Placeholder
            }
            for post in popular_posts
        ]
    except Exception as e:
        auth_logger.error(f"❌ Error getting popular content: {e}")
        raise HTTPException(status_code=500, detail="Failed to load popular content")

@router.get("/api/admin/dashboard/recent-activity")
async def get_recent_activity(current_user = Depends(get_current_active_user)):
    """Get recent activity data"""
    try:
        # Mock recent activity data (implement real activity tracking later)
        activities = [
            {
                "type": "post_created",
                "description": "New blog post published: 'Building the Future'",
                "timestamp": "2025-11-14T10:30:00Z"
            },
            {
                "type": "comment_added",
                "description": "New comment on 'AI Technology Trends'",
                "timestamp": "2025-11-14T09:15:00Z"
            },
            {
                "type": "user_registered",
                "description": "New newsletter subscriber joined",
                "timestamp": "2025-11-14T08:45:00Z"
            },
            {
                "type": "search_performed",
                "description": "Popular search: 'machine learning'",
                "timestamp": "2025-11-14T08:20:00Z"
            }
        ]

        return activities
    except Exception as e:
        auth_logger.error(f"❌ Error getting recent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to load recent activity")

@router.get("/api/admin/dashboard/quick-stats")
async def get_quick_stats(current_user = Depends(get_current_active_user)):
    """Get quick stats data"""
    try:
        # Mock quick stats (implement real metrics later)
        return {
            "searchQueries": 42,
            "avgResponseTime": 245,
            "uptime": 99.8,
            "dbSize": 15.7
        }
    except Exception as e:
        auth_logger.error(f"❌ Error getting quick stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to load quick stats")

# Blog management API endpoints
@router.get("/api/admin/blog/posts")
async def get_blog_posts(current_user = Depends(get_current_active_user)):
    """Get blog posts data for admin interface"""
    from backend.app.models.blog import BlogPost
    from sqlalchemy import func

    try:
        # Get all posts with basic info
        posts_query = db.query(BlogPost).order_by(BlogPost.created_at.desc())
        posts = posts_query.all()

        # Get stats
        total_posts = db.query(func.count(BlogPost.id)).scalar() or 0
        published_count = db.query(func.count(BlogPost.id)).filter(BlogPost.status == 'published').scalar() or 0
        draft_count = db.query(func.count(BlogPost.id)).filter(BlogPost.status == 'draft').scalar() or 0
        scheduled_count = db.query(func.count(BlogPost.id)).filter(BlogPost.status == 'scheduled').scalar() or 0

        # Get categories with counts
        categories = db.query(
            BlogPost.category,
            func.count(BlogPost.id).label('count')
        ).filter(
            BlogPost.category.isnot(None)
        ).group_by(BlogPost.category).all()

        # Mock tags for now (implement when you have tags model)
        tags = [
            {"id": "tech", "name": "Technology", "count": 8},
            {"id": "design", "name": "Design", "count": 5},
            {"id": "business", "name": "Business", "count": 4},
            {"id": "ai", "name": "AI", "count": 6},
            {"id": "tutorial", "name": "Tutorial", "count": 3}
        ]

        posts_data = [
            {
                "id": str(post.id),
                "title": post.title,
                "excerpt": post.excerpt or post.content[:100] + "..." if post.content else "No content",
                "status": post.status or "draft",
                "author": "NekwasaR",  # Default author
                "category": post.category or "Uncategorized",
                "categoryId": post.category,  # For filtering
                "tags": [],  # Implement when you have tags
                "updatedAt": post.updated_at.isoformat() if post.updated_at else post.created_at.isoformat(),
                "createdAt": post.created_at.isoformat(),
                "contentLength": len(post.content or ""),
                "views": getattr(post, 'views', 0) or 0
            }
            for post in posts
        ]

        return {
            "posts": posts_data,
            "stats": {
                "totalPosts": total_posts,
                "publishedCount": published_count,
                "draftCount": draft_count,
                "scheduledCount": scheduled_count
            },
            "categories": [
                {"id": cat[0], "name": cat[0], "count": cat[1]}
                for cat in categories
            ],
            "tags": tags
        }
    except Exception as e:
        auth_logger.error(f"❌ Error getting blog posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to load blog posts")

@router.post("/api/admin/blog/posts")
async def create_blog_post(post_data: dict, current_user = Depends(get_current_active_user)):
    """Create a new blog post"""
    from backend.app.models.blog import BlogPost

    try:
        new_post = BlogPost(
            title=post_data.get("title", ""),
            content=post_data.get("content", ""),
            excerpt=post_data.get("excerpt"),
            category=post_data.get("category"),
            status=post_data.get("status", "draft"),
            author_id=current_user.id
        )

        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return {"success": True, "post_id": new_post.id}
    except Exception as e:
        auth_logger.error(f"❌ Error creating blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create blog post")

@router.put("/api/admin/blog/posts/{post_id}")
async def update_blog_post(post_id: int, post_data: dict, current_user = Depends(get_current_active_user)):
    """Update a blog post"""
    from backend.app.models.blog import BlogPost

    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Update fields
        for field in ["title", "content", "excerpt", "category", "status"]:
            if field in post_data:
                setattr(post, field, post_data[field])

        post.updated_at = func.now()
        db.commit()

        return {"success": True}
    except Exception as e:
        auth_logger.error(f"❌ Error updating blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update blog post")

@router.delete("/api/admin/blog/posts/{post_id}")
async def delete_blog_post(post_id: int, current_user = Depends(get_current_active_user)):
    """Delete a blog post"""
    from backend.app.models.blog import BlogPost

    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        db.delete(post)
        db.commit()

        return {"success": True}
    except Exception as e:
        auth_logger.error(f"❌ Error deleting blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete blog post")