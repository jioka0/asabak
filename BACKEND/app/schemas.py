from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Blog schemas
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

# Comment schemas
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

# Like schemas
class LikeCreate(BaseModel):
    user_identifier: str

class Like(BaseModel):
    id: int
    blog_post_id: int
    user_identifier: str
    created_at: datetime

    class Config:
        from_attributes = True

# Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    product_type: str
    file_url: Optional[str] = None
    stock_quantity: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

# Contact schemas - FIXED VERSION
class ContactBase(BaseModel):
    name: str
    email: str
    message: str

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    id: int
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Admin Authentication schemas
class AdminUserBase(BaseModel):
    username: str
    email: str

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUser(AdminUserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None