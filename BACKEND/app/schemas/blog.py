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
    section: Optional[str] = 'others'
    slug: Optional[str] = None
    priority: Optional[int] = 0
    is_featured: Optional[bool] = False

class BlogPostCreate(BlogPostBase):
    pass

class BlogPost(BlogPostBase):
    id: int
    published_at: datetime
    view_count: int
    like_count: int
    comment_count: int
    share_count: int

    class Config:
        from_attributes = True

class BlogPostSearchResult(BlogPost):
    search_score: Optional[float] = None
    matched_terms: Optional[List[str]] = None

class SearchFilters(BaseModel):
    sections: List[str] = ['latest', 'popular', 'others', 'featured']
    tags: List[str] = ['ai', 'startup', 'innovation', 'opinions', 'business', 'software']

class SearchRequest(BaseModel):
    query: str = ""
    section: Optional[str] = None
    tags: Optional[List[str]] = None
    sort: Optional[str] = "relevance"  # relevance, recent, popular
    offset: Optional[int] = 0
    limit: Optional[int] = 20

class SearchResponse(BaseModel):
    results: List[BlogPostSearchResult]
    total: int
    query: str
    filters_applied: dict
    search_time: float

class SearchSuggestions(BaseModel):
    suggestions: List[str]
    popular: List[str]
    trending: List[str]

class SearchAnalyticsCreate(BaseModel):
    query: str
    results_count: int
    filters_used: dict
    user_identifier: str
    user_agent: Optional[str] = None

# Newsletter Schemas
class NewsletterSubscriberBase(BaseModel):
    name: str
    email: str
    preferences: Optional[dict] = None

class NewsletterSubscriberCreate(NewsletterSubscriberBase):
    pass

class NewsletterSubscriber(NewsletterSubscriberBase):
    id: int
    subscribed_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

class NewsletterCampaignBase(BaseModel):
    subject: str
    content: str
    template_type: Optional[str] = "weekly"

class NewsletterCampaignCreate(NewsletterCampaignBase):
    scheduled_at: Optional[datetime] = None

class NewsletterCampaign(NewsletterCampaignBase):
    id: int
    status: str  # draft, scheduled, sent, failed
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    recipient_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class NewsletterTemplateBase(BaseModel):
    name: str
    subject_template: str
    content_template: str

class NewsletterTemplateCreate(NewsletterTemplateBase):
    pass

class NewsletterTemplate(NewsletterTemplateBase):
    id: int
    is_active: bool
    created_at: datetime

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

# Analytics Schemas
class PageViewAnalyticsBase(BaseModel):
    post_id: Optional[int] = None
    session_id: str
    user_identifier: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    screen_resolution: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    timezone: Optional[str] = None
    referrer: Optional[str] = None
    referrer_domain: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    page_url: Optional[str] = None
    time_on_page: Optional[int] = None
    scroll_depth: Optional[float] = None

class PageViewAnalyticsCreate(PageViewAnalyticsBase):
    pass

class PageViewAnalytics(PageViewAnalyticsBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ContentEngagementAnalyticsBase(BaseModel):
    post_id: Optional[int] = None
    session_id: str
    user_identifier: Optional[str] = None
    action_type: str
    element_type: Optional[str] = None
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    page_url: Optional[str] = None
    section_visible: Optional[str] = None
    time_on_page: Optional[int] = None
    action_metadata: Optional[dict] = None

class ContentEngagementAnalyticsCreate(ContentEngagementAnalyticsBase):
    pass

class ContentEngagementAnalytics(ContentEngagementAnalyticsBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class UserSessionAnalyticsBase(BaseModel):
    session_id: str
    user_identifier: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    page_views: int = 0
    unique_pages: int = 0
    actions_taken: int = 0
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    is_bounce: bool = False
    has_search: bool = False
    has_newsletter_signup: bool = False
    has_social_share: bool = False
    entry_page: Optional[str] = None
    exit_page: Optional[str] = None

class UserSessionAnalyticsCreate(UserSessionAnalyticsBase):
    pass

class UserSessionAnalytics(UserSessionAnalyticsBase):
    id: int

    class Config:
        from_attributes = True

class ReferralAnalyticsBase(BaseModel):
    session_id: str
    referrer_url: Optional[str] = None
    referrer_domain: Optional[str] = None
    referrer_type: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    landing_page: Optional[str] = None
    landing_page_title: Optional[str] = None
    converted: bool = False
    conversion_type: Optional[str] = None
    conversion_value: float = 0

class ReferralAnalyticsCreate(ReferralAnalyticsBase):
    pass

class ReferralAnalytics(ReferralAnalyticsBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class AnalyticsDashboardResponse(BaseModel):
    total_views: int
    total_sessions: int
    total_users: int
    active_users: int
    page_views_today: int
    page_views_yesterday: int
    top_content: List[dict]
    popular_searches: List[dict]
    device_breakdown: dict
    geographic_data: List[dict]
    referral_sources: List[dict]
    real_time_metrics: dict

class AnalyticsReportRequest(BaseModel):
    report_type: str  # daily, weekly, monthly, custom
    date_range_start: datetime
    date_range_end: datetime
    include_charts: bool = True
    export_format: Optional[str] = None  # pdf, csv, excel