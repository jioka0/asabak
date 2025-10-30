from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, JSON, func
from database import Base

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    excerpt = Column(Text)
    template_type = Column(String(50))  # 'banner_text', 'video_text', 'image_text'
    featured_image = Column(String(500))
    video_url = Column(String(500))
    published_at = Column(DateTime(timezone=True), server_default=func.now())
    tags = Column(JSON)  # Changed from ARRAY(String) to JSON for SQLite compatibility
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)

class BlogComment(Base):
    __tablename__ = "blog_comments"

    id = Column(Integer, primary_key=True, index=True)
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"))
    author_name = Column(String(255), nullable=False)
    author_email = Column(String(255))
    content = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    parent_id = Column(Integer, ForeignKey("blog_comments.id"))

class BlogLike(Base):
    __tablename__ = "blog_likes"

    id = Column(Integer, primary_key=True, index=True)
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"))
    user_identifier = Column(String(255))  # IP or session ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2))
    product_type = Column(String(50))  # 'protip', 'app', 'ebook', 'premium'
    file_url = Column(String(500))
    stock_quantity = Column(Integer)
    is_active = Column(Boolean, default=True)

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Admin User Model for Authentication
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))