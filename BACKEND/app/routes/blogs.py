from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db
from models.blog import BlogPost as BlogPostModel, BlogComment, BlogLike
from schemas import BlogPost, BlogPostCreate, Comment, CommentCreate, Like, LikeCreate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Templates directory
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/", response_model=list[BlogPost])
async def get_blog_posts(limit: int = 10, db: Session = Depends(get_db)):
    """Get latest blog posts for homepage"""
    posts = db.query(BlogPostModel).order_by(BlogPostModel.published_at.desc()).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=BlogPost)
async def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Get single blog post with comments"""
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        raise HTTPException(404, "Blog post not found")

    # Increment view count
    post.view_count += 1
    db.commit()

    return post

@router.post("/", response_model=BlogPost)
async def create_blog_post(post: BlogPostCreate, db: Session = Depends(get_db)):
    """Create new blog post (admin only)"""
    db_post = BlogPostModel(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.post("/{post_id}/comments", response_model=Comment)
async def create_comment(post_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    """Create new comment (pending approval)"""
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        raise HTTPException(404, "Blog post not found")

    db_comment = BlogComment(blog_post_id=post_id, **comment.dict())
    db.add(db_comment)

    # Update comment count
    post.comment_count += 1
    db.commit()
    db.refresh(db_comment)

    return db_comment

@router.post("/{post_id}/likes", response_model=Like)
async def like_post(post_id: int, like: LikeCreate, db: Session = Depends(get_db)):
    """Like a blog post"""
    # Check if already liked
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == like.user_identifier
    ).first()

    if existing:
        raise HTTPException(400, "Already liked this post")

    # Create like
    db_like = BlogLike(blog_post_id=post_id, **like.dict())
    db.add(db_like)

    # Update like count
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    post.like_count += 1
    db.commit()
    db.refresh(db_like)

    return db_like

@router.delete("/{post_id}/likes")
async def unlike_post(post_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Unlike a blog post"""
    # Find existing like
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == user_identifier
    ).first()

    if not existing:
        raise HTTPException(404, "Like not found")

    # Delete like
    db.delete(existing)

    # Update like count
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if post.like_count > 0:
        post.like_count -= 1
    db.commit()

    return {"message": "Post unliked successfully"}

@router.get("/{post_id}/likes/status")
async def get_like_status(post_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Check if user has liked a post"""
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == user_identifier
    ).first()

    return {"liked": existing is not None}

@router.get("/{post_id}/comments", response_model=list[Comment])
async def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Get approved comments for a blog post"""
    comments = db.query(BlogComment).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).order_by(BlogComment.created_at).all()

    return comments

@router.get("/{post_id}/comments-tree")
async def get_comments_tree(post_id: int, db: Session = Depends(get_db)):
    """Get approved comments for a blog post with nested replies"""
    # Get all approved comments for this post
    all_comments = db.query(BlogComment).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).order_by(BlogComment.created_at).all()

    # Build comment tree
    comment_dict = {}
    root_comments = []

    # First pass: create comment objects
    for comment in all_comments:
        comment_data = {
            "id": comment.id,
            "author": comment.author_name,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "replies": []
        }
        comment_dict[comment.id] = comment_data

    # Second pass: build hierarchy
    for comment in all_comments:
        if comment.parent_id and comment.parent_id in comment_dict:
            # This is a reply
            comment_dict[comment.parent_id]["replies"].append(comment_dict[comment.id])
        else:
            # This is a root comment
            root_comments.append(comment_dict[comment.id])

    return {"comments": root_comments}

@router.put("/comments/{comment_id}/approve")
async def approve_comment(comment_id: int, db: Session = Depends(get_db)):
    """Approve a comment (admin only)"""
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")

    comment.is_approved = True
    db.commit()
    return {"message": "Comment approved"}

@router.delete("/{post_id}")
async def delete_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Delete blog post (admin only)"""
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        raise HTTPException(404, "Blog post not found")

    db.delete(post)
    db.commit()
    return {"message": "Blog post deleted"}

# Section-based endpoints for homepage
@router.get("/posts/section/{section}", response_model=list[BlogPost])
async def get_posts_by_section(section: str, limit: int = 10, db: Session = Depends(get_db)):
    """Get blog posts by section (latest, popular, featured, others)"""
    if section == "latest":
        posts = db.query(BlogPostModel).order_by(BlogPostModel.published_at.desc()).limit(limit).all()
    elif section == "popular":
        posts = db.query(BlogPostModel).order_by(BlogPostModel.view_count.desc()).limit(limit).all()
    elif section == "featured":
        posts = db.query(BlogPostModel).filter(BlogPostModel.priority > 0).order_by(BlogPostModel.priority.desc(), BlogPostModel.published_at.desc()).limit(limit).all()
    elif section == "others":
        posts = db.query(BlogPostModel).order_by(BlogPostModel.published_at.desc()).limit(limit).all()
    else:
        raise HTTPException(400, f"Invalid section: {section}")

    return posts

@router.get("/blog/media", response_class=HTMLResponse)
@router.get("/blog/media/", response_class=HTMLResponse)
async def blog_media(request: Request):
    """Serve blog media library page"""
    logger.info(f"📚 BLOG MEDIA: Media page accessed - Method: {request.method}, URL: {request.url}")
    logger.info(f"📚 BLOG MEDIA: Request headers: {dict(request.headers)}")
    logger.info(f"📚 BLOG MEDIA: Template path exists: {(templates_dir / 'admin_blog_media.html').exists()}")
    
    try:
        response = templates.TemplateResponse("admin_blog_media.html", {"request": request})
        logger.info(f"📚 BLOG MEDIA: Template response created successfully")
        return response
    except Exception as e:
        logger.error(f"📚 BLOG MEDIA: Error creating template response: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"📚 BLOG MEDIA: Traceback: {traceback.format_exc()}")
        raise

@router.get("/blog/drafts", response_class=HTMLResponse)
@router.get("/blog/drafts/", response_class=HTMLResponse)
async def blog_drafts(request: Request):
    """Serve blog drafts management page"""
    logger.info(f"📝 BLOG DRAFTS: Drafts page accessed - Method: {request.method}, URL: {request.url}")
    logger.info(f"📝 BLOG DRAFTS: Request headers: {dict(request.headers)}")
    logger.info(f"📝 BLOG DRAFTS: Template path exists: {(templates_dir / 'admin_blog_drafts.html').exists()}")
    
    try:
        response = templates.TemplateResponse("admin_blog_drafts.html", {"request": request})
        logger.info(f"📝 BLOG DRAFTS: Template response created successfully")
        return response
    except Exception as e:
        logger.error(f"📝 BLOG DRAFTS: Error creating template response: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"📝 BLOG DRAFTS: Traceback: {traceback.format_exc()}")
        raise

@router.get("/blog/categories", response_class=HTMLResponse)
@router.get("/blog/categories/", response_class=HTMLResponse)
async def blog_categories(request: Request):
    """Serve blog categories management page"""
    logger.info(f"🏷️ BLOG CATEGORIES: Categories page accessed - Method: {request.method}, URL: {request.url}")
    logger.info(f"🏷️ BLOG CATEGORIES: Request headers: {dict(request.headers)}")
    logger.info(f"🏷️ BLOG CATEGORIES: Template path exists: {(templates_dir / 'admin_blog_categories.html').exists()}")
    
    try:
        response = templates.TemplateResponse("admin_blog_categories.html", {"request": request})
        logger.info(f"🏷️ BLOG CATEGORIES: Template response created successfully")
        return response
    except Exception as e:
        logger.error(f"🏷️ BLOG CATEGORIES: Error creating template response: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"🏷️ BLOG CATEGORIES: Traceback: {traceback.format_exc()}")
        raise

@router.get("/blog/tags", response_class=HTMLResponse)
@router.get("/blog/tags/", response_class=HTMLResponse)
async def blog_tags(request: Request):
    """Serve blog tags management page"""
    logger.info(f"🏷️ BLOG TAGS: Tags page accessed - Method: {request.method}, URL: {request.url}")
    logger.info(f"🏷️ BLOG TAGS: Request headers: {dict(request.headers)}")
    logger.info(f"🏷️ BLOG TAGS: Template path exists: {(templates_dir / 'admin_blog_tags.html').exists()}")
    
    try:
        response = templates.TemplateResponse("admin_blog_tags.html", {"request": request})
        logger.info(f"🏷️ BLOG TAGS: Template response created successfully")
        return response
    except Exception as e:
        logger.error(f"🏷️ BLOG TAGS: Error creating template response: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"🏷️ BLOG TAGS: Traceback: {traceback.format_exc()}")
        raise