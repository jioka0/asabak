from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func, Enum
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

    # New fields for search and organization
    section = Column(Enum('latest', 'popular', 'others', 'featured', name='section_enum'), default='others')
    slug = Column(String(255), unique=True, index=True)  # SEO-friendly URL
    search_index = Column(Text)  # Full-text search content
    priority = Column(Integer, default=0)  # For featured content ordering
    is_featured = Column(Boolean, default=False)  # Featured post flag

    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)  # New: share tracking

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

class BlogShare(Base):
    __tablename__ = "blog_shares"

    id = Column(Integer, primary_key=True, index=True)
    blog_post_id = Column(Integer, ForeignKey("blog_posts.id", ondelete="CASCADE"))
    user_identifier = Column(String(255))  # IP or session ID
    platform = Column(String(50))  # twitter, facebook, linkedin, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlogSection(Base):
    __tablename__ = "blog_sections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(100))  # Phosphor icon name
    color = Column(String(20))  # Hex color code
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BlogTag(Base):
    __tablename__ = "blog_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    icon = Column(String(100))  # Phosphor icon name
    color = Column(String(20))  # Hex color code
    post_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    preferences = Column(JSON)  # Subscription preferences
    is_confirmed = Column(Boolean, default=False)
    unsubscribe_token = Column(String(255), unique=True)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

class SearchAnalytics(Base):
    __tablename__ = "search_analytics"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False)
    results_count = Column(Integer, default=0)
    filters_used = Column(JSON)  # Applied filters
    user_identifier = Column(String(255))  # IP or session ID
    user_agent = Column(String(500))  # Browser info
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class NewsletterCampaign(Base):
    __tablename__ = "newsletter_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    template_type = Column(String(50), default="weekly")  # weekly, announcement, etc.
    status = Column(String(20), default="draft")  # draft, scheduled, sent, failed
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    recipient_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class NewsletterTemplate(Base):
    __tablename__ = "newsletter_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    subject_template = Column(String(255), nullable=False)
    content_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())