from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from ..database import get_db
from ..models.blog import BlogComment, CommentLike, BlogPost
from ..schemas.blog import CommentLikeCreate, CommentLikeResponse
from typing import Optional

router = APIRouter()

@router.post("/comments/{comment_id}/likes", response_model=CommentLikeResponse)
async def like_comment(comment_id: int, like_data: CommentLikeCreate, db: Session = Depends(get_db)):
    """Like a comment"""
    # Check if comment exists
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user already liked this comment
    existing_like = db.query(CommentLike).filter(
        and_(
            CommentLike.comment_id == comment_id,
            CommentLike.user_identifier == like_data.user_identifier
        )
    ).first()
    
    if existing_like:
        # User already liked, return current state
        like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
        return CommentLikeResponse(
            comment_id=comment_id,
            liked=True,
            like_count=like_count
        )
    
    # Create new like
    new_like = CommentLike(
        comment_id=comment_id,
        user_identifier=like_data.user_identifier
    )
    db.add(new_like)
    db.commit()
    db.refresh(new_like)
    
    # Get updated like count
    like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
    
    return CommentLikeResponse(
        comment_id=comment_id,
        liked=True,
        like_count=like_count
    )

@router.delete("/comments/{comment_id}/likes")
async def unlike_comment(comment_id: int, user_identifier: str = Query(...), db: Session = Depends(get_db)):
    """Unlike a comment"""
    # Check if comment exists
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Delete the like
    like = db.query(CommentLike).filter(
        and_(
            CommentLike.comment_id == comment_id,
            CommentLike.user_identifier == user_identifier
        )
    ).first()
    
    if like:
        db.delete(like)
        db.commit()
    
    # Get updated like count
    like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
    
    return {"comment_id": comment_id, "liked": False, "like_count": like_count}

@router.get("/comments/{comment_id}/likes/status")
async def get_comment_like_status(comment_id: int, user_identifier: str = Query(...), db: Session = Depends(get_db)):
    """Check if user has liked a comment"""
    # Check if comment exists
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user has liked this comment
    existing_like = db.query(CommentLike).filter(
        and_(
            CommentLike.comment_id == comment_id,
            CommentLike.user_identifier == user_identifier
        )
    ).first()
    
    # Get like count
    like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
    
    return {
        "comment_id": comment_id,
        "liked": existing_like is not None,
        "like_count": like_count
    }

@router.get("/comments/{comment_id}/likes/count")
async def get_comment_like_count(comment_id: int, db: Session = Depends(get_db)):
    """Get like count for a comment"""
    # Check if comment exists
    comment = db.query(BlogComment).filter(BlogComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Get like count
    like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment_id).count()
    
    return {"comment_id": comment_id, "like_count": like_count}

@router.get("/posts/{post_id}/comments/likes/status")
async def get_post_comments_like_status(post_id: int, user_identifier: str = Query(...), db: Session = Depends(get_db)):
    """Get like status for all comments in a post"""
    # Check if post exists
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get all comments for this post
    comments = db.query(BlogComment).filter(BlogComment.blog_post_id == post_id).all()
    
    # Get like status for each comment
    result = []
    for comment in comments:
        existing_like = db.query(CommentLike).filter(
            and_(
                CommentLike.comment_id == comment.id,
                CommentLike.user_identifier == user_identifier
            )
        ).first()
        
        like_count = db.query(CommentLike).filter(CommentLike.comment_id == comment.id).count()
        
        result.append({
            "comment_id": comment.id,
            "liked": existing_like is not None,
            "like_count": like_count
        })
    
    return {"post_id": post_id, "comments_likes": result}