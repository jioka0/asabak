from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, func, Enum, BigInteger, Float
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

# Search Models - Full-Text Search with FTS5
class BlogPostFTS(Base):
    """FTS5 virtual table for full-text search"""
    __tablename__ = "blog_posts_fts"
    __table_args__ = {'prefixes': ['VIRTUAL']}

    rowid = Column(Integer, primary_key=True)
    title = Column(Text)
    content = Column(Text)
    excerpt = Column(Text)
    tags = Column(Text)
    section = Column(Text)

# Analytics Models
class PageViewAnalytics(Base):
    __tablename__ = "page_view_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=True)
    session_id = Column(String(255), index=True)
    user_identifier = Column(String(255))  # Hashed IP or user ID
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Device & Browser Info
    user_agent = Column(Text)
    ip_address = Column(String(45))  # Support IPv6
    device_type = Column(String(50))  # mobile, tablet, desktop
    browser = Column(String(100))
    os = Column(String(100))
    screen_resolution = Column(String(20))

    # Geographic Info
    country = Column(String(100))
    city = Column(String(100))
    timezone = Column(String(50))

    # Referral Info
    referrer = Column(Text)
    referrer_domain = Column(String(255))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))

    # Page Context
    page_url = Column(Text)
    time_on_page = Column(Integer)  # seconds
    scroll_depth = Column(Float)    # percentage 0-100

class ContentEngagementAnalytics(Base):
    __tablename__ = "content_engagement_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=True)
    session_id = Column(String(255), index=True)
    user_identifier = Column(String(255))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Engagement Type
    action_type = Column(String(50))  # view, like, share, comment, click, scroll
    element_type = Column(String(100))  # button, link, image, etc.
    element_id = Column(String(255))   # CSS selector or ID
    element_text = Column(Text)        # Link text, button text, etc.

    # Context Data
    page_url = Column(Text)
    section_visible = Column(String(100))  # Which section was visible
    time_on_page = Column(Integer)      # Total time on page when action occurred

    # Additional Metadata
    action_metadata = Column(JSON)  # Flexible data storage

class UserSessionAnalytics(Base):
    __tablename__ = "user_session_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True)
    user_identifier = Column(String(255), index=True)

    # Session Timing
    start_time = Column(DateTime(timezone=True), index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer)  # seconds

    # Session Metrics
    page_views = Column(Integer, default=0)
    unique_pages = Column(Integer, default=0)
    actions_taken = Column(Integer, default=0)

    # Device & Location
    device_type = Column(String(50))
    browser = Column(String(100))
    os = Column(String(100))
    country = Column(String(100))
    city = Column(String(100))

    # Behavior Flags
    is_bounce = Column(Boolean, default=False)  # Single page session
    has_search = Column(Boolean, default=False)
    has_newsletter_signup = Column(Boolean, default=False)
    has_social_share = Column(Boolean, default=False)

    # Entry/Exit Pages
    entry_page = Column(Text)
    exit_page = Column(Text)

class ReferralAnalytics(Base):
    __tablename__ = "referral_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Referral Data
    referrer_url = Column(Text)
    referrer_domain = Column(String(255), index=True)
    referrer_type = Column(String(50))  # search, social, direct, email, etc.

    # UTM Parameters
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_term = Column(String(100))
    utm_content = Column(String(100))

    # Landing Page
    landing_page = Column(Text)
    landing_page_title = Column(String(255))

    # Conversion Tracking
    converted = Column(Boolean, default=False)
    conversion_type = Column(String(50))  # newsletter_signup, contact_form, etc.
    conversion_value = Column(Float, default=0)

class DeviceAnalytics(Base):
    __tablename__ = "device_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Device Details
    user_agent = Column(Text)
    device_type = Column(String(50))  # mobile, tablet, desktop
    device_brand = Column(String(100))
    device_model = Column(String(100))
    os = Column(String(100))
    os_version = Column(String(50))
    browser = Column(String(100))
    browser_version = Column(String(50))

    # Screen & Display
    screen_width = Column(Integer)
    screen_height = Column(Integer)
    viewport_width = Column(Integer)
    viewport_height = Column(Integer)
    pixel_ratio = Column(Float)

    # Network & Performance
    connection_type = Column(String(50))  # 4g, 3g, wifi, etc.
    page_load_time = Column(Float)  # milliseconds

class GeographicAnalytics(Base):
    __tablename__ = "geographic_analytics"

    id = Column(BigInteger, primary_key=True, index=True)
    session_id = Column(String(255), index=True)
    ip_address = Column(String(45))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Geographic Data
    country_code = Column(String(2))
    country_name = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    postal_code = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    timezone = Column(String(50))

    # ISP/Network Info
    isp = Column(String(255))
    organization = Column(String(255))
    asn = Column(String(20))

class RealTimeMetrics(Base):
    __tablename__ = "real_time_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(100), index=True)  # active_users, page_views, etc.
    metric_key = Column(String(255), index=True)   # post_id, country, etc.
    metric_value = Column(Float)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Metadata
    time_window = Column(String(20))  # 1m, 5m, 1h, 24h
    data_type = Column(String(20))    # count, rate, percentage

class AnalyticsReports(Base):
    __tablename__ = "analytics_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50))  # daily, weekly, monthly, custom
    report_name = Column(String(255))
    date_range_start = Column(DateTime(timezone=True))
    date_range_end = Column(DateTime(timezone=True))

    # Report Data
    report_data = Column(JSON)  # Store processed analytics data
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Report Metadata
    total_views = Column(Integer)
    total_sessions = Column(Integer)
    total_users = Column(Integer)
    top_content = Column(JSON)
    key_insights = Column(JSON)