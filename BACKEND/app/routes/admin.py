from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import logging
import os
from auth import get_current_user, get_current_active_user
from fastapi.exception_handlers import http_exception_handler
from database import SessionLocal

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
@router.get("/admin/api/dashboard/kpi")
@router.get("/api/admin/dashboard/kpi")
async def get_dashboard_kpi(current_user = Depends(get_current_active_user)):
    """Get dashboard KPI data"""
    from sqlalchemy import func
    from models.blog import BlogPost
    from models.contact import Contact
    from models.blog import NewsletterSubscriber

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

@router.get("/api/dashboard/popular-content")
@router.get("/admin/api/dashboard/popular-content")
@router.get("/api/admin/dashboard/popular-content")
async def get_popular_content(current_user = Depends(get_current_active_user)):
    """Get popular content data"""
    from models.blog import BlogPost

    try:
        # Get top 5 posts by views (placeholder - implement real view tracking)
        popular_posts = db.query(BlogPost).order_by(BlogPost.view_count.desc()).limit(5).all()

        return [
            {
                "title": post.title,
                "category": getattr(post, "section", None) or "General",
                "publishedAt": post.published_at.isoformat() if getattr(post, "published_at", None) else None,
                "views": getattr(post, "view_count", 0) or 0  # Placeholder
            }
            for post in popular_posts
        ]
    except Exception as e:
        auth_logger.error(f"❌ Error getting popular content: {e}")
        raise HTTPException(status_code=500, detail="Failed to load popular content")

@router.get("/api/dashboard/recent-activity")
@router.get("/admin/api/dashboard/recent-activity")
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

@router.get("/api/dashboard/quick-stats")
@router.get("/admin/api/dashboard/quick-stats")
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
@router.get("/admin/api/blog/posts")
@router.get("/api/admin/blog/posts")
async def get_blog_posts(current_user = Depends(get_current_active_user)):
    """Get blog posts data for admin interface"""
    auth_logger.info("🗂️ get_blog_posts endpoint hit at /admin/api/blog/posts or /api/admin/blog/posts")
    from models.blog import BlogPost
    from sqlalchemy import func

    try:
        # Get all posts with basic info
        posts_query = db.query(BlogPost).order_by(BlogPost.published_at.desc())
        posts = posts_query.all()

        # Get stats
        total_posts = db.query(func.count(BlogPost.id)).scalar() or 0
        # Status field not present in model yet; approximate counts
        published_count = total_posts
        draft_count = 0
        scheduled_count = 0

        # Get categories with counts (using 'section' field instead of missing 'category')
        categories = db.query(
            BlogPost.section,
            func.count(BlogPost.id).label('count')
        ).filter(
            BlogPost.section.isnot(None)
        ).group_by(BlogPost.section).all()

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
                "excerpt": post.excerpt or (post.content[:100] + "...") if post.content else "No content",
                "status": "published" if getattr(post, "published_at", None) else "draft",
                "author": "NekwasaR",  # Default author
                "category": getattr(post, "section", None) or "Uncategorized",
                "categoryId": getattr(post, "section", None),  # For filtering
                "tags": [],  # Implement when you have tags
                "updatedAt": post.published_at.isoformat() if getattr(post, "published_at", None) else None,
                "createdAt": post.published_at.isoformat() if getattr(post, "published_at", None) else None,
                "contentLength": len(post.content or ""),
                "views": getattr(post, "view_count", 0) or 0
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

@router.post("/admin/api/blog/posts")
async def create_blog_post(post_data: dict, current_user = Depends(get_current_active_user)):
    """Create a new blog post"""
    from models.blog import BlogPost
    from datetime import datetime

    try:
        # Set published_at if provided, otherwise leave as None for drafts
        published_at = None
        if post_data.get("published_at"):
            try:
                published_at = datetime.fromisoformat(post_data["published_at"].replace('Z', '+00:00'))
            except:
                published_at = datetime.utcnow()

        new_post = BlogPost(
            title=post_data.get("title", ""),
            content=post_data.get("content", ""),
            excerpt=post_data.get("excerpt"),
            template_type=post_data.get("template_type"),
            featured_image=post_data.get("featured_image"),
            video_url=post_data.get("video_url"),
            tags=post_data.get("tags"),
            section=post_data.get("section", "others"),
            slug=post_data.get("slug"),
            priority=post_data.get("priority", 0),
            is_featured=post_data.get("is_featured", False),
            published_at=published_at
        )

        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return {"success": True, "post_id": new_post.id}
    except Exception as e:
        auth_logger.error(f"❌ Error creating blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create blog post")

@router.put("/admin/api/blog/posts/{post_id}")
async def update_blog_post(post_id: int, post_data: dict, current_user = Depends(get_current_active_user)):
    """Update a blog post"""
    from models.blog import BlogPost

    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Update fields
        for field in ["title", "content", "excerpt", "template_type", "featured_image", "video_url", "tags", "section", "slug", "priority", "is_featured", "published_at"]:
            if field in post_data:
                setattr(post, field, post_data[field])

        db.commit()

        return {"success": True}
    except Exception as e:
        auth_logger.error(f"❌ Error updating blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update blog post")

@router.get("/admin/api/blog/posts/{post_id}")
async def get_blog_post(post_id: int, current_user = Depends(get_current_active_user)):
    """Get a single blog post for admin interface"""
    from models.blog import BlogPost

    try:
        post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        return {
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "excerpt": post.excerpt,
            "template_type": post.template_type,
            "featured_image": post.featured_image,
            "video_url": post.video_url,
            "tags": post.tags,
            "section": post.section,
            "priority": post.priority,
            "is_featured": post.is_featured,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "author": post.author or "NekwasaR"  # Use the author field from the model
        }
    except Exception as e:
        auth_logger.error(f"❌ Error getting blog post: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blog post")

@router.delete("/admin/api/blog/posts/{post_id}")
async def delete_blog_post(post_id: int, current_user = Depends(get_current_active_user)):
    """Delete a blog post"""
    from models.blog import BlogPost

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

@router.get("/admin/api/blog/render-template/{template_name}")
@router.get("/api/admin/blog/render-template/{template_name}")
async def render_blog_template(template_name: str, current_user = Depends(get_current_active_user)):
    """Render a blog template for the editor"""
    from pathlib import Path
    import re

    try:
        auth_logger.info(f"🎨 RENDERING TEMPLATE: {template_name} for user {current_user.username}")

        # Map template names
        template_map = {
            'template1': 'template1-banner-image.html',
            'template2': 'template2-banner-video.html',
            'template3': 'template3-listing.html'
        }

        if template_name not in template_map:
            auth_logger.error(f"❌ Template {template_name} not in map")
            raise HTTPException(status_code=404, detail="Template not found")

        template_file = template_map[template_name]
        project_root = Path(__file__).resolve().parents[3]
        auth_logger.info(f"🗂️ Project root resolved: {project_root}")
        template_path = project_root / "blog" / "templates" / template_file

        auth_logger.info(f"📁 Template path: {template_path}")
        auth_logger.info(f"📁 Template exists: {template_path.exists()}")

        if not template_path.exists():
            auth_logger.error(f"❌ Template file not found: {template_path}")
            raise HTTPException(status_code=404, detail="Template file not found")

        # Read the template
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        auth_logger.info(f"📖 Template content length: {len(content)}")

        # Extract the content block (between {% block content %} and {% endblock %})
        content_match = re.search(r'{% block content %}(.*?){% endblock %}', content, re.DOTALL | re.IGNORECASE)
        if not content_match:
            auth_logger.error("❌ Could not extract template content block")
            raise HTTPException(status_code=500, detail="Could not extract template content")

        template_content = content_match.group(1).strip()
        auth_logger.info(f"✂️ Extracted content length: {len(template_content)}")

        # Extract and remove styles from content
        style_match = re.search(r'<style>(.*?)</style>', template_content, re.DOTALL | re.IGNORECASE)
        if style_match:
            template_styles = style_match.group(1).strip()
            # Remove the style tag from content
            template_content = re.sub(r'<style>.*?</style>', '', template_content, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            template_styles = ""

        auth_logger.info(f"🎨 Extracted styles length: {len(template_styles)}")
        auth_logger.info(f"📄 Final content length: {len(template_content)}")

        # Load global blog template assets (CSS/JS) so the editor can render everything
        global_styles = ""
        global_scripts = ""
        try:
            project_root = Path(__file__).resolve().parents[3]
            base_css_path = project_root / "blog" / "templates" / "css" / "blog-templates.css"
            auth_logger.info(f"🧩 Global CSS path: {base_css_path} exists: {base_css_path.exists()}")
            if base_css_path.exists():
                global_styles = base_css_path.read_text(encoding="utf-8")
                auth_logger.info(f"🧩 Global CSS length: {len(global_styles)}")
            else:
                auth_logger.warning(f"⚠️ Global CSS not found at {base_css_path}")
        except Exception as e:
            auth_logger.error(f"❌ Error reading global CSS: {e}")

        try:
            project_root = Path(__file__).resolve().parents[3]
            base_js_path = project_root / "blog" / "templates" / "js" / "blog-templates.js"
            auth_logger.info(f"🧩 Global JS path: {base_js_path} exists: {base_js_path.exists()}")
            if base_js_path.exists():
                global_scripts = base_js_path.read_text(encoding="utf-8")
                auth_logger.info(f"🧩 Global JS length: {len(global_scripts)}")
            else:
                auth_logger.warning(f"⚠️ Global JS not found at {base_js_path}")
        except Exception as e:
            auth_logger.error(f"❌ Error reading global JS: {e}")

        # Return the extracted content, template-scoped styles, and global assets
        result = {
            "html": template_content,
            "styles": template_styles,
            "globalStyles": global_styles,
            "globalScripts": global_scripts,
            "template": template_name
        }
        auth_logger.info(f"✅ Template rendered successfully for {template_name}")
        return result

    except Exception as e:
        auth_logger.error(f"💥 Error rendering template {template_name}: {str(e)}")
        auth_logger.error(f"💥 Exception type: {type(e).__name__}")
        import traceback
        auth_logger.error(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to render template: {str(e)}")

@router.get("/api/blog/posts/section/{section}")
async def get_posts_by_section(section: str, limit: int = 10):
    """Get published posts for a specific section (public API - no auth required)"""
    from models.blog import BlogPost

    try:
        # Map section names to database queries
        section_filters = {
            'latest': BlogPost.published_at.isnot(None),
            'popular': BlogPost.published_at.isnot(None),
            'featured': BlogPost.is_featured == True,
            'others': BlogPost.published_at.isnot(None)
        }

        if section not in section_filters:
            raise HTTPException(status_code=400, detail="Invalid section")

        query = db.query(BlogPost).filter(section_filters[section])

        # Order by different criteria based on section
        if section == 'latest':
            query = query.order_by(BlogPost.published_at.desc())
        elif section == 'popular':
            query = query.order_by(BlogPost.view_count.desc())
        elif section == 'featured':
            query = query.order_by(BlogPost.published_at.desc())
        else:  # others
            query = query.order_by(BlogPost.published_at.desc())

        posts = query.limit(limit).all()

        # Convert to dict format
        result = []
        for post in posts:
            result.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'author': post.author,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'featured_image': post.featured_image,
                'tags': post.tags if post.tags else [],
                'view_count': post.view_count,
                'like_count': post.like_count,
                'comment_count': post.comment_count,
                'template_type': post.template_type,
                'is_featured': post.is_featured
            })

        return {"posts": result}

    except Exception as e:
        auth_logger.error(f"❌ Error getting posts by section: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")