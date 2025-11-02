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