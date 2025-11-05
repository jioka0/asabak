from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from database import get_db
from models.blog import BlogPost, BlogComment, BlogLike
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
    posts = db.query(BlogPost).order_by(BlogPost.published_at.desc()).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=BlogPost)
async def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    """Get single blog post with comments"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Blog post not found")

    # Increment view count
    post.view_count += 1
    db.commit()

    return post

@router.post("/", response_model=BlogPost)
async def create_blog_post(post: BlogPostCreate, db: Session = Depends(get_db)):
    """Create new blog post (admin only)"""
    db_post = BlogPost(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.post("/{post_id}/comments", response_model=Comment)
async def create_comment(post_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    """Create new comment (pending approval)"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
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
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    post.like_count += 1
    db.commit()
    db.refresh(db_like)

    return db_like

@router.get("/{post_id}/comments", response_model=list[Comment])
async def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Get approved comments for a blog post"""
    comments = db.query(BlogComment).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).order_by(BlogComment.created_at).all()

    return comments

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
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(404, "Blog post not found")

    db.delete(post)
    db.commit()
    return {"message": "Blog post deleted"}

@router.get("/blog/media", response_class=HTMLResponse)
@router.get("/blog/media/", response_class=HTMLResponse)
async def blog_media(request: Request):
    """Serve blog media library page"""
    logger.info(f"📚 BLOG MEDIA: Media page accessed - Method: {request.method}, URL: {request.url}")
    logger.info(f"📚 BLOG MEDIA: Request headers: {dict(request.headers)}")
    logger.info(f"📚 BLOG MEDIA: Template path exists: {(templates_dir / 'admin_media_library.html').exists()}")
    
    try:
        response = templates.TemplateResponse("admin_media_library.html", {"request": request})
        logger.info(f"📚 BLOG MEDIA: Template response created successfully")
        return response
    except Exception as e:
        logger.error(f"📚 BLOG MEDIA: Error creating template response: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"📚 BLOG MEDIA: Traceback: {traceback.format_exc()}")
        raise