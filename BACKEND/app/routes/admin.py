from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import cast, String, func
from database import get_db, SessionLocal
import logging
import os
from auth import get_current_user, get_current_active_user

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
    return templates.TemplateResponse("admin_base.html", {"request": request})

@router.get("/admin/contact", response_class=HTMLResponse)
@router.get("/admin/contact/", response_class=HTMLResponse)
async def admin_contact(request: Request):
    """Serve admin contact management - Authentication handled by JavaScript"""
    return templates.TemplateResponse("admin_contact.html", {"request": request})

@router.get("/admin/blog/editor")
@router.get("/admin/blog/editor/")
async def admin_blog_editor_page(request: Request):
    """Serve standalone blog editor page - Authentication handled by JavaScript"""
    return templates.TemplateResponse("admin_blog_editor.html", {"request": request})

@router.get("/admin/blog/tags")
@router.get("/admin/blog/tags/")
async def admin_blog_tags_page(request: Request):
    """Serve blog tags management page - Authentication handled by JavaScript"""
    return templates.TemplateResponse("admin_blog_tags.html", {"request": request})

@router.get("/admin/{section}/{page}", response_class=HTMLResponse)
async def admin_section_page(request: Request, section: str, page: str):
    """Serve admin section pages dynamically - Authentication handled by JavaScript"""
    return templates.TemplateResponse("admin_base.html", {"request": request})

# API endpoints for dynamic page loading - PROTECTED
@router.get("/templates/{template_name}")
async def get_admin_template(template_name: str, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Serve admin page templates dynamically - REQUIRES AUTHENTICATION"""
    try:
        template_path = templates_dir / template_name

        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HTMLResponse(content=content, media_type="text/html")

            except Exception as e:
                raise HTTPException(500, f"Error reading template file: {str(e)}")
        else:
            raise HTTPException(404, f"Template {template_name} not found")

    except Exception as e:
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
    from fastapi.responses import JSONResponse

    response_data = {
        "authenticated": True,
        "user": {
            "username": current_user.username,
            "is_superuser": current_user.is_superuser,
            "email": current_user.email
        }
    }

    return JSONResponse(response_data)

# Dashboard API endpoints
@router.get("/admin/api/dashboard/kpi")
@router.get("/api/admin/dashboard/kpi")
async def get_dashboard_kpi(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def get_popular_content(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def get_quick_stats(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def get_blog_posts(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get blog posts data for admin interface"""
    from models.blog import BlogPost
    from sqlalchemy import func

    try:
        # Get all posts with basic info
        posts_query = db.query(BlogPost).order_by(BlogPost.published_at.desc().nullslast())
        posts = posts_query.all()

        # Get stats with proper draft counting
        total_posts = db.query(func.count(BlogPost.id)).scalar() or 0

        # Count published posts (where published_at is not None)
        published_count = db.query(func.count(BlogPost.id)).filter(BlogPost.published_at.isnot(None)).scalar() or 0

        # Count draft posts (where published_at is None) - this is the key fix
        draft_count = db.query(func.count(BlogPost.id)).filter(BlogPost.published_at.is_(None)).scalar() or 0

        scheduled_count = 0  # Placeholder for future implementation

        # Get categories with counts (using 'section' field instead of missing 'category')
        categories = db.query(
            BlogPost.section,
            func.count(BlogPost.id).label('count')
        ).filter(
            BlogPost.section.isnot(None)
        ).group_by(BlogPost.section).all()

        # Get real tags from database
        from models.blog import BlogTag
        tags_query = db.query(BlogTag).order_by(BlogTag.name.asc())
        tags_db = tags_query.all()
        
        # Calculate actual tag counts from posts
        tags = []
        for tag in tags_db:
            # Count posts that have this tag
            tag_count = db.query(func.count(BlogPost.id)).filter(
                cast(BlogPost.tags, String).like(f'%"{tag.slug}"%')
            ).scalar() or 0
            
            tags.append({
                "id": str(tag.id),
                "name": tag.name,
                "slug": tag.slug,
                "count": tag_count
            })
        
        # If no real tags exist, provide some default ones for demo
        if not tags:
            tags = [
                {"id": "tech", "name": "Technology", "count": 8},
                {"id": "design", "name": "Design", "count": 5},
                {"id": "business", "name": "Business", "count": 4},
                {"id": "ai", "name": "AI", "count": 6},
                {"id": "tutorial", "name": "Tutorial", "count": 3}
            ]

        posts_data = []
        for post in posts:
            # Determine status based on published_at field
            is_published = getattr(post, "published_at", None) is not None
            status = "published" if is_published else "draft"
            
            # For drafts, ensure they have a proper slug (may be generated during save)
            slug = getattr(post, "slug", None)
            if not is_published and not slug:
                # Generate a temporary slug for drafts that don't have one
                slug = f"draft-{post.id}"
            
            post_data = {
                "id": str(post.id),
                "title": post.title or "Untitled Draft" if not is_published else post.title,
                "excerpt": post.excerpt or (post.content[:100] + "...") if post.content else "No content",
                "status": status,
                "author": post.author or "NekwasaR",
                "category": getattr(post, "section", None) or "Uncategorized",
                "categoryId": getattr(post, "section", None),
                "tags": post.tags if post.tags else [],
                "updatedAt": post.published_at.isoformat() if getattr(post, "published_at", None) else None,
                "createdAt": getattr(post, "created_at", None) or getattr(post, "published_at", None),
                "contentLength": len(post.content or ""),
                "views": getattr(post, "view_count", 0) or 0,
                "slug": slug,
                "template_type": post.template_type,
                "isDraft": not is_published,  # Add explicit draft flag
                "publishedAt": post.published_at.isoformat() if getattr(post, "published_at", None) else None
            }
            posts_data.append(post_data)

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
        import traceback
        auth_logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Failed to load blog posts")

@router.post("/admin/api/blog/posts")
async def create_blog_post(post_data: dict, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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

        return {"success": True, "post_id": new_post.id, "slug": new_post.slug}
    except Exception as e:
        auth_logger.error(f"❌ Error creating blog post: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create blog post")

@router.post("/admin/api/blog/drafts")
async def save_blog_draft(draft_data: dict, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Save a blog post as draft"""
    from models.blog import BlogPost
    from datetime import datetime
    import uuid

    try:
        # Check if this is an update to an existing draft or a new draft
        post_id = draft_data.get("id")

        if post_id:
            # Update existing draft
            post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if not post:
                raise HTTPException(status_code=404, detail="Draft not found")
        else:
            # Create new draft
            post = BlogPost()
            db.add(post)

        # Generate a unique slug for drafts if not provided
        title = draft_data.get("title", "Untitled Draft")
        if not draft_data.get("slug"):
            # Generate a unique slug for drafts
            unique_id = str(uuid.uuid4())[:8]
            slug_base = title.lower().replace(" ", "-")[:50]
            post.slug = f"draft-{slug_base}-{unique_id}"
        else:
            post.slug = draft_data.get("slug")

        # Update draft content (always leave published_at as None for drafts)
        post.title = title
        post.content = draft_data.get("content", "")
        post.excerpt = draft_data.get("excerpt", "")
        post.template_type = draft_data.get("template_type", "template1")
        post.featured_image = draft_data.get("featured_image", "")
        post.video_url = draft_data.get("video_url", "")
        post.tags = draft_data.get("tags", [])
        post.section = draft_data.get("section", "others")
        post.priority = draft_data.get("priority", 0)
        post.is_featured = draft_data.get("is_featured", False)
        post.published_at = None  # Ensure this is a draft
        post.author = current_user.username or "NekwasaR"

        # Generate search index for better discoverability
        search_content = f"{post.title} {post.content[:500]}"
        post.search_index = search_content

        # Flush to ensure the draft is saved with None published_at
        db.flush()
        db.commit()
        db.refresh(post)

        auth_logger.info(f"✅ DRAFT SAVED SUCCESSFULLY - Post ID: {post.id}, Slug: {post.slug}")
        return {"success": True, "post_id": post.id, "slug": post.slug, "message": "Draft saved successfully"}
    except Exception as e:
        auth_logger.error(f"❌ Error saving draft: {e}")
        auth_logger.error(f"❌ Exception type: {type(e).__name__}")
        import traceback
        auth_logger.error(f"❌ Traceback: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save draft: {str(e)}")

@router.put("/admin/api/blog/posts/{post_id}")
async def update_blog_post(post_id: int, post_data: dict, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def get_blog_post(post_id: int, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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
async def delete_blog_post(post_id: int, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
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

# Blog Tags API endpoints
@router.post("/admin/api/blog/tags")
async def create_blog_tag(tag_data: dict, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Create a new blog tag"""
    from models.blog import BlogTag
    import re

    try:
        # Generate slug from name
        name = tag_data.get("name", "").strip()

        if not name:
            raise HTTPException(status_code=400, detail="Tag name is required")

        # Create slug (URL-friendly version of the name)
        slug = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
        slug = re.sub(r'\s+', '-', slug).strip('-')

        # Check if tag already exists
        existing_tag = db.query(BlogTag).filter(
            (BlogTag.name == name) | (BlogTag.slug == slug)
        ).first()

        if existing_tag:
            raise HTTPException(status_code=400, detail="Tag with this name or slug already exists")

        # Create new tag
        new_tag = BlogTag(
            name=name,
            slug=slug,
            description=tag_data.get("description", ""),
            color=tag_data.get("color", "#6366f1"),  # Default color
            is_featured=tag_data.get("is_featured", False)
        )

        db.add(new_tag)
        db.commit()
        db.refresh(new_tag)

        response_data = {
            "success": True,
            "tag": {
                "id": str(new_tag.id),
                "name": new_tag.name,
                "slug": new_tag.slug,
                "description": new_tag.description,
                "color": new_tag.color,
                "post_count": new_tag.post_count,
                "is_featured": new_tag.is_featured
            }
        }

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create tag")

@router.get("/admin/api/blog/tags")
async def get_blog_tags(current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get all blog tags"""
    from models.blog import BlogTag, BlogPost
    from sqlalchemy import func

    try:
        # Get all tags with post counts
        tags_query = db.query(BlogTag).order_by(BlogTag.name.asc())
        tags = tags_query.all()

        # Format tags for frontend
        tags_data = []
        for tag in tags:
            # Get actual post count for this tag
            actual_count = db.query(func.count(BlogPost.id)).filter(
                cast(BlogPost.tags, String).like(f'%"{tag.slug}"%')  # Cast JSON to String for Postgres compatibility
            ).scalar() or 0

            # Update post_count if it's outdated
            if tag.post_count != actual_count:
                tag.post_count = actual_count
                db.flush()  # Update without committing

            tags_data.append({
                "id": str(tag.id),
                "name": tag.name,
                "slug": tag.slug,
                "description": tag.description or "",
                "color": tag.color,
                "count": actual_count,
                "is_featured": tag.is_featured
            })

        db.commit()  # Commit any post_count updates

        return {"tags": tags_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch tags")

@router.delete("/admin/api/blog/tags/{tag_id}")
async def delete_blog_tag(tag_id: int, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Delete a blog tag"""
    from models.blog import BlogTag

    try:
        # Find the tag
        tag = db.query(BlogTag).filter(BlogTag.id == tag_id).first()
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        # Delete the tag
        db.delete(tag)
        db.commit()

        return {"success": True, "message": f"Tag '{tag.name}' deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete tag")

@router.get("/admin/api/blog/render-template/{template_name}")
@router.get("/api/admin/blog/render-template/{template_name}")
async def render_blog_template(template_name: str, current_user = Depends(get_current_active_user)):
    """Render a blog template for the editor"""
    from pathlib import Path
    import re
    from jinja2 import Environment, FileSystemLoader
    from datetime import datetime

    try:
        # Map template names
        template_map = {
            'template1': 'template1-banner-image.html',
            'template2': 'template2-banner-video.html',
            'template3': 'template3-listing.html'
        }

        if template_name not in template_map:
            raise HTTPException(status_code=404, detail="Template not found")

        template_file = template_map[template_name]
        project_root = Path(__file__).resolve().parents[3]
        template_path = project_root / "blog" / "templates" / template_file

        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template file not found")

        # Read the template file
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Extract the content block (between {% block content %} and {% endblock %})
        content_match = re.search(r'{% block content %}(.*?){% endblock %}', template_content, re.DOTALL | re.IGNORECASE)
        if not content_match:
            raise HTTPException(status_code=500, detail="Could not extract template content")

        template_content_block = content_match.group(1).strip()

        # For the editor, we'll use the raw content block and let the frontend handle variable replacement
        # Replace Jinja2 variables with sample data for preview
        rendered_html = template_content_block
        rendered_html = rendered_html.replace('{% if post_data and post_data.featured_image %}', '')
        rendered_html = rendered_html.replace('{% else %}', '')
        rendered_html = rendered_html.replace('{% endif %}', '')
        rendered_html = rendered_html.replace('{{ post_data.title }}', 'Sample Post Title')
        rendered_html = rendered_html.replace('{{ post_data.excerpt }}', 'This is a sample excerpt for the blog post.')
        rendered_html = rendered_html.replace('{{ post_data.author }}', 'NekwasaR')
        rendered_html = rendered_html.replace('{{ post_data.featured_image }}', 'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=1920&h=1080&fit=crop&crop=center')
        rendered_html = rendered_html.replace('{{ post_data.tags[0] }}', 'Technology')
        rendered_html = rendered_html.replace('{{ post_data.published_at | strftime(\'%B %d, %Y\') }}', 'November 6, 2025')

        # Add special classes for editor-specific behavior
        # Make comment count dynamic and non-editable, start with 0 comments
        rendered_html = rendered_html.replace(
            '<span class="bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-semibold">47 Comments</span>',
            '<span class="bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-semibold comment-count-display">0 Comments</span>'
        )

        # Make entire comment section non-editable
        rendered_html = rendered_html.replace(
            '<section id="comments" class="bg-white rounded-lg border border-gray-200 mt-6 no-edit">',
            '<section id="comments" class="bg-white rounded-lg border border-gray-200 mt-6 no-edit comment-section">'
        )

        # Add special classes for related/trending posts to make them editable via modal
        rendered_html = rendered_html.replace(
            '<a href="/blog/ai-revolutionizing-healthcare" class="flex gap-3 group">',
            '<a href="/blog/ai-revolutionizing-healthcare" class="flex gap-3 group related-post-item" data-post-index="0" data-section="related">'
        )
        rendered_html = rendered_html.replace(
            '<a href="/blog/rise-of-quantum-computing" class="flex gap-3 group">',
            '<a href="/blog/rise-of-quantum-computing" class="flex gap-3 group related-post-item" data-post-index="1" data-section="related">'
        )
        rendered_html = rendered_html.replace(
            '<a href="/blog/machine-learning-ethics" class="flex gap-3 group">',
            '<a href="/blog/machine-learning-ethics" class="flex gap-3 group related-post-item" data-post-index="2" data-section="related">'
        )

        # Trending posts
        rendered_html = rendered_html.replace(
            '<a href="/blog/ai-changing-finance" class="flex gap-3 group">',
            '<a href="/blog/ai-changing-finance" class="flex gap-3 group trending-post-item" data-post-index="0" data-section="trending">'
        )
        rendered_html = rendered_html.replace(
            '<a href="/blog/crypto-market-2025" class="flex gap-3 group">',
            '<a href="/blog/crypto-market-2025" class="flex gap-3 group trending-post-item" data-post-index="1" data-section="trending">'
        )
        rendered_html = rendered_html.replace(
            '<a href="/blog/real-estate-trends" class="flex gap-3 group">',
            '<a href="/blog/real-estate-trends" class="flex gap-3 group trending-post-item" data-post-index="2" data-section="trending">'
        )

        # Extract and remove styles from rendered content
        style_match = re.search(r'<style[^>]*>(.*?)</style>', rendered_html, re.DOTALL | re.IGNORECASE)
        if style_match:
            template_styles = style_match.group(1).strip()
            # Remove the style tag from content
            rendered_html = re.sub(r'<style[^>]*>.*?</style>', '', rendered_html, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            template_styles = ""

        # Load global blog template assets (CSS/JS) so the editor can render everything
        global_styles = ""
        global_scripts = ""
        try:
            project_root = Path(__file__).resolve().parents[3]
            base_css_path = project_root / "blog" / "templates" / "css" / "blog-templates.css"
            if base_css_path.exists():
                global_styles = base_css_path.read_text(encoding="utf-8")
        except Exception as e:
            pass

        try:
            project_root = Path(__file__).resolve().parents[3]
            base_js_path = project_root / "blog" / "templates" / "js" / "blog-templates.js"
            if base_js_path.exists():
                global_scripts = base_js_path.read_text(encoding="utf-8")
        except Exception as e:
            pass

        # Return the rendered content, template-scoped styles, and global assets
        result = {
            "html": rendered_html,
            "styles": template_styles,
            "globalStyles": global_styles,
            "globalScripts": global_scripts,
            "template": template_name
        }
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render template: {str(e)}")


@router.get("/api/blog/posts/section/{section}")
async def get_posts_by_section(section: str, limit: int = 10, db: Session = Depends(get_db)):
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