from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BlogPostBase(BaseModel):
    title: str
    content: Optional[str] = None
    excerpt: Optional[str] = None
    template_type: Optional[str] = None
    featured_image: Optional[str] = None
    video_url: Optional[str] = None
    tags: Optional[List[str]] = None

class BlogPostCreate(BlogPostBase):
    pass

class BlogPost(BlogPostBase):
    id: int
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    author_name: str
    author_email: Optional[str] = None
    content: str
    parent_id: Optional[int] = None

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    blog_post_id: int
    is_approved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LikeCreate(BaseModel):
    user_identifier: str

class Like(BaseModel):
    id: int
    blog_post_id: int
    user_identifier: str
    created_at: datetime

    class Config:
        from_attributes = True