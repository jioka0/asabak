from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.blog import BlogPost as BlogPostModel, BlogComment, BlogLike, TemporalUser as TemporalUserModel
from schemas import BlogPost, BlogPostCreate, Comment, CommentCreate, Like, LikeCreate, TemporalUser, TemporalUserCreate
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

@router.get("/tags")
async def get_blog_tags(db: Session = Depends(get_db)):
    """Get all blog tags with post counts (public API)"""
    from models.blog import BlogTag
    from sqlalchemy import func
    
    try:
        # Get all tags
        tags = db.query(BlogTag).order_by(BlogTag.name.asc()).all()
        
        tags_data = []
        for tag in tags:
            # Get actual post count for this tag (only published posts)
            actual_count = db.query(func.count(BlogPostModel.id)).filter(
                BlogPostModel.published_at.isnot(None),
                BlogPostModel.tags.like(f'%"{tag.slug}"%')
            ).scalar() or 0
            
            tags_data.append({
                "id": str(tag.id),
                "name": tag.name,
                "slug": tag.slug,
                "count": actual_count,
                "color": tag.color or "#6366f1"
            })
            
        return {"tags": tags_data}
    except Exception as e:
        logger.error(f"Error fetching tags: {e}")
        raise HTTPException(500, "Failed to fetch tags")

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

    db_comment = BlogComment(blog_post_id=post_id, is_approved=True, **comment.dict())
    db.add(db_comment)

    # Update comment count
    post.comment_count += 1

    try:
        db.commit()
        db.refresh(db_comment)
        return db_comment
    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Failed to save comment")

@router.post("/{post_id}/likes")
async def like_post(post_id: int, like: LikeCreate, db: Session = Depends(get_db)):
    """Like a blog post using device fingerprint"""
    from datetime import datetime, timedelta
    
    logger.info(f"❤️ LIKE REQUEST: post_id={post_id}, like_data={like.dict()}")
    
    # Check if post exists
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        logger.error(f"❌ LIKE REQUEST: Post not found with id={post_id}")
        raise HTTPException(404, "Blog post not found")
    
    # Check if already liked by this fingerprint and not expired
    try:
        existing = db.query(BlogLike).filter(
            BlogLike.blog_post_id == post_id,
            BlogLike.fingerprint == like.fingerprint,
            BlogLike.expires_at > func.now()
        ).first()

        liked = False
        if existing:
            # Already liked, just return success
            liked = True
            logger.info(f"✅ LIKE REQUEST: Already liked by fingerprint={like.fingerprint}")
        else:
            # Create new like with 3-day expiration
            expires_at = datetime.utcnow() + timedelta(days=3)
            db_like = BlogLike(
                blog_post_id=post_id,
                fingerprint=like.fingerprint,
                user_identifier=like.user_identifier,
                expires_at=expires_at
            )
            db.add(db_like)

            # Update like count
            post.like_count += 1
            liked = True
            db.commit()
            db.refresh(db_like)
            logger.info(f"✅ LIKE REQUEST: New like created for fingerprint={like.fingerprint}")

        # Get updated count
        result = {"liked": liked, "like_count": post.like_count}
        logger.info(f"✅ LIKE REQUEST SUCCESS: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ LIKE REQUEST ERROR: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"Failed to process like: {str(e)}")

@router.delete("/{post_id}/likes")
async def unlike_post(post_id: int, fingerprint: str = Query(None, description="Device fingerprint"), user_identifier: str = Query(None, description="Legacy user identifier"), db: Session = Depends(get_db)):
    """Unlike a blog post using device fingerprint or legacy user identifier"""
    # Use fingerprint if available, otherwise fall back to user_identifier
    identifier = fingerprint or user_identifier
    if not identifier:
        raise HTTPException(400, "Either fingerprint or user_identifier is required")
    
    logger.info(f"💔 UNLIKE REQUEST: post_id={post_id}, identifier={identifier}")
    
    # Check if post exists
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        logger.error(f"❌ UNLIKE REQUEST: Post not found with id={post_id}")
        raise HTTPException(404, "Blog post not found")
    
    # Find existing like by fingerprint
    try:
        existing = db.query(BlogLike).filter(
            BlogLike.blog_post_id == post_id,
            (BlogLike.fingerprint == identifier) | (BlogLike.user_identifier == identifier),
            BlogLike.expires_at > func.now()
        ).first()

        unliked = False
        if existing:
            # Delete like
            db.delete(existing)

            # Update like count
            if post.like_count > 0:
                post.like_count -= 1
            unliked = True
            db.commit()
            logger.info(f"✅ UNLIKE REQUEST: Like removed for identifier={identifier}")
        else:
            logger.info(f"⚠️ UNLIKE REQUEST: No like found for identifier={identifier}")

        result = {"unliked": unliked, "like_count": post.like_count}
        logger.info(f"✅ UNLIKE REQUEST SUCCESS: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ UNLIKE REQUEST ERROR: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"Failed to process unlike: {str(e)}")

@router.get("/{post_id}/likes/status")
async def get_like_status(post_id: int, fingerprint: str = Query(None, description="Device fingerprint"), user_identifier: str = Query(None, description="Legacy user identifier"), db: Session = Depends(get_db)):
    """Check if user has liked a post using device fingerprint or legacy user identifier"""
    # Use fingerprint if available, otherwise fall back to user_identifier
    identifier = fingerprint or user_identifier
    if not identifier:
        raise HTTPException(400, "Either fingerprint or user_identifier is required")
    
    logger.info(f"🔍 LIKE STATUS REQUEST: post_id={post_id}, identifier={identifier}")
    
    try:
        existing = db.query(BlogLike).filter(
            BlogLike.blog_post_id == post_id,
            (BlogLike.fingerprint == identifier) | (BlogLike.user_identifier == identifier),
            BlogLike.expires_at > func.now()
        ).first()
        
        result = {"liked": existing is not None}
        logger.info(f"✅ LIKE STATUS RESULT: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ LIKE STATUS ERROR: {str(e)}")
        raise

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
    try:
        response = templates.TemplateResponse("admin_blog_media.html", {"request": request})
        return response
    except Exception as e:
        raise

@router.get("/blog/drafts", response_class=HTMLResponse)
@router.get("/blog/drafts/", response_class=HTMLResponse)
async def blog_drafts(request: Request):
    """Serve blog drafts management page"""
    try:
        response = templates.TemplateResponse("admin_blog_drafts.html", {"request": request})
        return response
    except Exception as e:
        raise

@router.get("/blog/categories", response_class=HTMLResponse)
@router.get("/blog/categories/", response_class=HTMLResponse)
async def blog_categories(request: Request):
    """Serve blog categories management page"""
    try:
        response = templates.TemplateResponse("admin_blog_categories.html", {"request": request})
        return response
    except Exception as e:
        raise

@router.get("/blog/tags", response_class=HTMLResponse)
@router.get("/blog/tags/", response_class=HTMLResponse)
async def blog_tags(request: Request):
    """Serve blog tags management page"""
    try:
        response = templates.TemplateResponse("admin_blog_tags.html", {"request": request})
        return response
    except Exception as e:
        raise

# Temporal User Management
@router.post("/temporal-users", response_model=TemporalUser)
async def create_temporal_user(user: TemporalUserCreate, request: Request, db: Session = Depends(get_db)):
    """Create or update a temporal user based on fingerprint"""
    try:
        # Check if user already exists
        existing_user = db.query(TemporalUserModel).filter(TemporalUserModel.fingerprint == user.fingerprint).first()

        if existing_user:
            # Update existing user
            existing_user.name = user.name
            existing_user.email = user.email
            existing_user.device_info = user.device_info
            existing_user.ip_address = user.ip_address or request.client.host
            existing_user.user_agent = user.user_agent or request.headers.get('user-agent')
            existing_user.last_seen = func.now()

            from datetime import datetime, timedelta
            existing_user.expires_at = datetime.utcnow() + timedelta(days=3)

            db.commit()
            db.refresh(existing_user)
            return existing_user
        else:
            # Create new user
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=3)

            db_user = TemporalUserModel(
                fingerprint=user.fingerprint,
                name=user.name,
                email=user.email,
                device_info=user.device_info,
                ip_address=user.ip_address or request.client.host,
                user_agent=user.user_agent or request.headers.get('user-agent'),
                expires_at=expires_at
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@router.get("/temporal-users/{fingerprint}", response_model=TemporalUser)
async def get_temporal_user(fingerprint: str, db: Session = Depends(get_db)):
    """Get temporal user by fingerprint"""
    logger.info(f'🔍 GET TEMPORAL USER: Looking up fingerprint={fingerprint}')
    try:
        user = db.query(TemporalUserModel).filter(
            TemporalUserModel.fingerprint == fingerprint,
            TemporalUserModel.expires_at > func.now()
        ).first()

        if not user:
            logger.info(f'🔍 GET TEMPORAL USER: User not found or expired for fingerprint={fingerprint}')
            raise HTTPException(404, "User not found or expired")

        # Update last seen
        user.last_seen = func.now()
        db.commit()
        
        logger.info(f'🔍 GET TEMPORAL USER: Found user id={user.id}, name={user.name}')
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'🔍 GET TEMPORAL USER: Error: {type(e).__name__}: {str(e)}')
        import traceback
        logger.error(f'🔍 GET TEMPORAL USER: Traceback: {traceback.format_exc()}')
        raise HTTPException(500, f"Internal server error: {str(e)}")

@router.delete("/temporal-users/expired")
async def cleanup_expired_users(db: Session = Depends(get_db)):
    """Clean up expired temporal users (should be called by scheduler)"""
    expired_count = db.query(TemporalUserModel).filter(
        TemporalUserModel.expires_at <= func.now()
    ).delete()

    db.commit()
    return {"message": f"Cleaned up {expired_count} expired users"}

@router.delete("/likes/expired")
async def cleanup_expired_likes(db: Session = Depends(get_db)):
    """Clean up expired blog post likes (should be called by scheduler)"""
    # Delete expired likes and update like counts
    expired_likes = db.query(BlogLike).filter(
        BlogLike.expires_at <= func.now()
    ).all()
    
    # Group by post_id to update counts efficiently
    post_like_counts = {}
    for like in expired_likes:
        if like.blog_post_id not in post_like_counts:
            post_like_counts[like.blog_post_id] = 0
        post_like_counts[like.blog_post_id] += 1
    
    # Delete expired likes
    db.query(BlogLike).filter(
        BlogLike.expires_at <= func.now()
    ).delete()
    
    # Update like counts for affected posts
    for post_id, like_count in post_like_counts.items():
        post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
        if post and post.like_count >= like_count:
            post.like_count -= like_count
    
    db.commit()
    return {"message": f"Cleaned up {len(expired_likes)} expired likes"}