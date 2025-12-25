from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.blog import BlogPost as BlogPostModel, BlogComment, BlogLike, CommentLike, TemporalUser as TemporalUserModel
from schemas import BlogPost, BlogPostCreate, BlogPostSchedule, Comment, CommentCreate, Like, LikeCreate, TemporalUser, TemporalUserCreate, CommentLike as CommentLikeSchema, CommentLikeCreate
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
    posts = db.query(BlogPostModel).filter(BlogPostModel.status == 'published').order_by(BlogPostModel.published_at.desc()).limit(limit).all()
    return posts

@router.get("/scheduled", response_model=list[BlogPost])
async def get_scheduled_posts(db: Session = Depends(get_db)):
    """Get scheduled blog posts for admin"""
    posts = db.query(BlogPostModel).filter(BlogPostModel.status == 'scheduled').order_by(BlogPostModel.scheduled_at.asc()).all()
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

@router.post("/schedule", response_model=BlogPost)
async def schedule_blog_post(post: BlogPostSchedule, db: Session = Depends(get_db)):
    """Schedule a blog post for future publication"""
    logger.info(f"📅 SCHEDULE POST: Scheduling post '{post.title}' for {post.scheduled_at} in {post.scheduled_timezone}")

    # Check if slug already exists
    existing = db.query(BlogPostModel).filter(BlogPostModel.slug == post.slug).first()
    if existing:
        logger.error(f"📅 SCHEDULE POST: Slug '{post.slug}' already exists")
        raise HTTPException(400, f"Post with slug '{post.slug}' already exists")

    # Create the scheduled post
    db_post = BlogPostModel(
        **post.dict(exclude={'scheduled_at', 'scheduled_timezone', 'include_on_homepage', 'include_on_route_pages', 'selected_routes'}),
        status='scheduled',
        scheduled_at=post.scheduled_at,
        scheduled_timezone=post.scheduled_timezone
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)

    logger.info(f"📅 SCHEDULE POST: Post scheduled successfully with id={db_post.id}")
    return db_post

@router.post("/{post_id}/comments", response_model=Comment)
async def create_comment(post_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    """Create new comment (pending approval)"""
    logger.info(f"🔥 COMMENT CREATE: Received request for post_id={post_id}")
    logger.info(f"🔥 COMMENT CREATE: Comment data: author_name='{comment.author_name}', content_length={len(comment.content) if comment.content else 0}")

    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    if not post:
        logger.error(f"🔥 COMMENT CREATE: Post not found for id={post_id}")
        raise HTTPException(404, "Blog post not found")

    logger.info(f"🔥 COMMENT CREATE: Found post, current comment_count={post.comment_count}")

    db_comment = BlogComment(blog_post_id=post_id, is_approved=True, **comment.dict())
    db.add(db_comment)

    # Update comment count
    old_count = post.comment_count
    post.comment_count += 1
    logger.info(f"🔥 COMMENT CREATE: Incrementing count from {old_count} to {post.comment_count}")

    try:
        db.commit()
        logger.info(f"🔥 COMMENT CREATE: Database commit successful")
        db.refresh(db_comment)
        logger.info(f"🔥 COMMENT CREATE: Comment created with id={db_comment.id}, final post comment_count={post.comment_count}")
        # Set like_count for the new comment (always 0 for new comments)
        db_comment.like_count = 0
        return db_comment
    except Exception as e:
        logger.error(f"🔥 COMMENT CREATE: Database commit failed: {str(e)}")
        db.rollback()
        raise HTTPException(500, "Failed to save comment")

@router.post("/{post_id}/likes")
async def like_post(post_id: int, like: LikeCreate, db: Session = Depends(get_db)):
    """Like a blog post"""
    # Check if already liked
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == like.user_identifier
    ).first()

    liked = False
    if existing:
        # Already liked, just return success
        liked = True
    else:
        # Create like
        db_like = BlogLike(blog_post_id=post_id, **like.dict())
        db.add(db_like)

        # Update like count
        post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
        post.like_count += 1
        liked = True
        db.commit()
        db.refresh(db_like)

    # Get updated count
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    return {"liked": liked, "like_count": post.like_count}

@router.delete("/{post_id}/likes")
async def unlike_post(post_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Unlike a blog post"""
    # Find existing like
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == user_identifier
    ).first()

    unliked = False
    if existing:
        # Delete like
        db.delete(existing)

        # Update like count
        post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
        if post.like_count > 0:
            post.like_count -= 1
        unliked = True
        db.commit()

    # Get updated count
    post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
    return {"unliked": unliked, "like_count": post.like_count}

@router.get("/{post_id}/likes/status")
async def get_like_status(post_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Check if user has liked a post"""
    existing = db.query(BlogLike).filter(
        BlogLike.blog_post_id == post_id,
        BlogLike.user_identifier == user_identifier
    ).first()

    return {"liked": existing is not None}

@router.post("/comments/{comment_id}/likes")
async def like_comment(comment_id: int, like: CommentLikeCreate, db: Session = Depends(get_db)):
    """Like a comment"""
    # Check if comment exists
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(404, "Comment not found")

    # Check if already liked
    existing = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_identifier == like.user_identifier
    ).first()

    liked = False
    if existing:
        # Already liked, just return success
        liked = True
    else:
        # Create like
        db_like = CommentLike(comment_id=comment_id, **like.dict())
        db.add(db_like)
        liked = True
        db.commit()
        db.refresh(db_like)

    # Get updated like count
    like_count = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == comment_id).scalar()

    return {"liked": liked, "like_count": like_count}

@router.delete("/comments/{comment_id}/likes")
async def unlike_comment(comment_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Unlike a comment"""
    # Find existing like
    existing = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_identifier == user_identifier
    ).first()

    unliked = False
    if existing:
        # Delete like
        db.delete(existing)
        unliked = True
        db.commit()

    # Get updated like count
    like_count = db.query(func.count(CommentLike.id)).filter(CommentLike.comment_id == comment_id).scalar()

    return {"unliked": unliked, "like_count": like_count}

@router.get("/comments/{comment_id}/likes/status")
async def get_comment_like_status(comment_id: int, user_identifier: str, db: Session = Depends(get_db)):
    """Check if user has liked a comment"""
    existing = db.query(CommentLike).filter(
        CommentLike.comment_id == comment_id,
        CommentLike.user_identifier == user_identifier
    ).first()

    return {"liked": existing is not None}

@router.get("/{post_id}/comments", response_model=list[Comment])
async def get_comments(post_id: int, db: Session = Depends(get_db)):
    """Get approved comments for a blog post"""
    from sqlalchemy import func
    comments_with_likes = db.query(
        BlogComment,
        func.count(CommentLike.id).label('like_count')
    ).outerjoin(CommentLike, BlogComment.id == CommentLike.comment_id).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).group_by(BlogComment.id).order_by(BlogComment.created_at).all()

    # Update like_count on each comment
    for comment, like_count in comments_with_likes:
        comment.like_count = like_count

    return [comment for comment, _ in comments_with_likes]

@router.get("/comments/{comment_id}")
async def get_comment(comment_id: int, db: Session = Depends(get_db)):
    """Get a single comment with like count"""
    from sqlalchemy import func
    comment_with_likes = db.query(
        BlogComment,
        func.count(CommentLike.id).label('like_count')
    ).outerjoin(CommentLike, BlogComment.id == CommentLike.comment_id).filter(
        BlogComment.id == comment_id
    ).group_by(BlogComment.id).first()

    if not comment_with_likes:
        raise HTTPException(404, "Comment not found")

    comment, like_count = comment_with_likes
    comment.like_count = like_count
    return comment

@router.get("/{post_id}/comments-tree")
async def get_comments_tree(post_id: int, db: Session = Depends(get_db)):
    """Get approved comments for a blog post with nested replies"""
    # Get all approved comments for this post with like counts
    from sqlalchemy import func
    comments_with_likes = db.query(
        BlogComment,
        func.count(CommentLike.id).label('like_count')
    ).outerjoin(CommentLike, BlogComment.id == CommentLike.comment_id).filter(
        BlogComment.blog_post_id == post_id,
        BlogComment.is_approved == True
    ).group_by(BlogComment.id).order_by(BlogComment.created_at).all()

    # Build comment tree
    comment_dict = {}
    root_comments = []

    # First pass: create comment objects
    for comment, like_count in comments_with_likes:
        comment_data = {
            "id": comment.id,
            "author": comment.author_name,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "like_count": like_count,
            "replies": []
        }
        comment_dict[comment.id] = comment_data

    # Second pass: build hierarchy
    for comment, _ in comments_with_likes:
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

# Temporal User Management
@router.post("/temporal-users", response_model=TemporalUser)
async def create_temporal_user(user: TemporalUserCreate, request: Request, db: Session = Depends(get_db)):
    """Create or update a temporal user based on fingerprint"""
    logger.info(f'💾 CREATE TEMPORAL USER: fingerprint={user.fingerprint}, name={user.name}')
    try:
        # Check if user already exists
        existing_user = db.query(TemporalUserModel).filter(TemporalUserModel.fingerprint == user.fingerprint).first()

        if existing_user:
            logger.info(f'💾 CREATE TEMPORAL USER: Updating existing user id={existing_user.id}')
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
            logger.info(f'💾 CREATE TEMPORAL USER: Updated user id={existing_user.id}')
            return existing_user
        else:
            # Create new user
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=3)

            logger.info(f'💾 CREATE TEMPORAL USER: Creating new user with expires_at={expires_at}')
            
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
            logger.info(f'💾 CREATE TEMPORAL USER: Created new user id={db_user.id}')
            return db_user
    except Exception as e:
        logger.error(f'💾 CREATE TEMPORAL USER: Error: {type(e).__name__}: {str(e)}')
        import traceback
        logger.error(f'💾 CREATE TEMPORAL USER: Traceback: {traceback.format_exc()}')
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