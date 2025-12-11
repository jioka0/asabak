import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, text
from user_agents import parse as parse_user_agent

from models.blog import (
    PageViewAnalytics, ContentEngagementAnalytics, UserSessionAnalytics,
    ReferralAnalytics, DeviceAnalytics, GeographicAnalytics, RealTimeMetrics,
    AnalyticsReports, BlogPost, SearchAnalytics, NewsletterSubscriber
)
from schemas.blog import (
    PageViewAnalyticsCreate, ContentEngagementAnalyticsCreate,
    UserSessionAnalyticsCreate, ReferralAnalyticsCreate,
    AnalyticsDashboardResponse, AnalyticsReportRequest
)

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def track_page_view(self, analytics_data: PageViewAnalyticsCreate) -> PageViewAnalytics:
        """Track a page view with comprehensive analytics data"""
        try:
            # Parse user agent for device/browser info
            if analytics_data.user_agent:
                ua = parse_user_agent(analytics_data.user_agent)
                analytics_data.device_type = self._get_device_type(ua)
                analytics_data.browser = ua.browser.family if ua.browser.family else None
                analytics_data.os = ua.os.family if ua.os.family else None

            # Hash IP for privacy
            if analytics_data.ip_address:
                analytics_data.user_identifier = hashlib.sha256(
                    analytics_data.ip_address.encode()
                ).hexdigest()[:16]

            # Extract referrer domain
            if analytics_data.referrer:
                from urllib.parse import urlparse
                parsed = urlparse(analytics_data.referrer)
                analytics_data.referrer_domain = parsed.netloc

            # Create analytics record
            page_view = PageViewAnalytics(**analytics_data.dict())
            self.db.add(page_view)
            self.db.commit()
            self.db.refresh(page_view)

            # Update real-time metrics asynchronously
            asyncio.create_task(self._update_realtime_metrics(analytics_data))

            # Update blog post view count if applicable
            if analytics_data.post_id:
                self._increment_post_views(analytics_data.post_id)

            return page_view

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to track page view: {str(e)}")

    def track_engagement(self, engagement_data: ContentEngagementAnalyticsCreate) -> ContentEngagementAnalytics:
        """Track user engagement events"""
        try:
            engagement = ContentEngagementAnalytics(**engagement_data.dict())
            self.db.add(engagement)
            self.db.commit()
            self.db.refresh(engagement)

            # Update real-time engagement metrics
            asyncio.create_task(self._update_engagement_metrics(engagement_data))

            return engagement

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to track engagement: {str(e)}")

    def track_session(self, session_data: UserSessionAnalyticsCreate) -> UserSessionAnalytics:
        """Track or update user session analytics"""
        try:
            # Check if session already exists
            existing_session = self.db.query(UserSessionAnalytics).filter(
                UserSessionAnalytics.session_id == session_data.session_id
            ).first()

            if existing_session:
                # Update existing session
                for key, value in session_data.dict(exclude_unset=True).items():
                    if hasattr(existing_session, key):
                        setattr(existing_session, key, value)
                self.db.commit()
                self.db.refresh(existing_session)
                return existing_session
            else:
                # Create new session
                session = UserSessionAnalytics(**session_data.dict())
                self.db.add(session)
                self.db.commit()
                self.db.refresh(session)
                return session

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to track session: {str(e)}")

    def track_referral(self, referral_data: ReferralAnalyticsCreate) -> ReferralAnalytics:
        """Track referral and UTM data"""
        try:
            referral = ReferralAnalytics(**referral_data.dict())
            self.db.add(referral)
            self.db.commit()
            self.db.refresh(referral)
            return referral

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to track referral: {str(e)}")

    def get_dashboard_data(self, timeframe_days: int = 30) -> AnalyticsDashboardResponse:
        """Get comprehensive dashboard analytics data"""
        try:
            start_date = datetime.now() - timedelta(days=timeframe_days)

            # Basic metrics
            total_views = self.db.query(func.count(PageViewAnalytics.id)).filter(
                PageViewAnalytics.timestamp >= start_date
            ).scalar() or 0

            total_sessions = self.db.query(func.count(func.distinct(UserSessionAnalytics.session_id))).filter(
                UserSessionAnalytics.start_time >= start_date
            ).scalar() or 0

            total_users = self.db.query(func.count(func.distinct(PageViewAnalytics.user_identifier))).filter(
                PageViewAnalytics.timestamp >= start_date
            ).scalar() or 0

            # Real-time metrics (last 5 minutes)
            realtime_cutoff = datetime.now() - timedelta(minutes=5)
            active_users = self.db.query(func.count(func.distinct(PageViewAnalytics.user_identifier))).filter(
                PageViewAnalytics.timestamp >= realtime_cutoff
            ).scalar() or 0

            # Today's and yesterday's views
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)

            page_views_today = self.db.query(func.count(PageViewAnalytics.id)).filter(
                PageViewAnalytics.timestamp >= today_start
            ).scalar() or 0

            page_views_yesterday = self.db.query(func.count(PageViewAnalytics.id)).filter(
                and_(
                    PageViewAnalytics.timestamp >= yesterday_start,
                    PageViewAnalytics.timestamp < today_start
                )
            ).scalar() or 0

            # Top content
            top_content = self._get_top_content(start_date, limit=10)

            # Popular searches
            popular_searches = self._get_popular_searches(start_date, limit=10)

            # Device breakdown
            device_breakdown = self._get_device_breakdown(start_date)

            # Geographic data
            geographic_data = self._get_geographic_data(start_date, limit=10)

            # Referral sources
            referral_sources = self._get_referral_sources(start_date, limit=10)

            # Real-time metrics
            real_time_metrics = self._get_realtime_metrics()

            return AnalyticsDashboardResponse(
                total_views=total_views,
                total_sessions=total_sessions,
                total_users=total_users,
                active_users=active_users,
                page_views_today=page_views_today,
                page_views_yesterday=page_views_yesterday,
                top_content=top_content,
                popular_searches=popular_searches,
                device_breakdown=device_breakdown,
                geographic_data=geographic_data,
                referral_sources=referral_sources,
                real_time_metrics=real_time_metrics
            )

        except Exception as e:
            raise Exception(f"Failed to get dashboard data: {str(e)}")

    def generate_report(self, report_request: AnalyticsReportRequest) -> AnalyticsReports:
        """Generate detailed analytics report"""
        try:
            # Calculate metrics for the date range
            total_views = self.db.query(func.count(PageViewAnalytics.id)).filter(
                and_(
                    PageViewAnalytics.timestamp >= report_request.date_range_start,
                    PageViewAnalytics.timestamp <= report_request.date_range_end
                )
            ).scalar() or 0

            total_sessions = self.db.query(func.count(func.distinct(UserSessionAnalytics.session_id))).filter(
                and_(
                    UserSessionAnalytics.start_time >= report_request.date_range_start,
                    UserSessionAnalytics.end_time <= report_request.date_range_end
                )
            ).scalar() or 0

            total_users = self.db.query(func.count(func.distinct(PageViewAnalytics.user_identifier))).filter(
                and_(
                    PageViewAnalytics.timestamp >= report_request.date_range_start,
                    PageViewAnalytics.timestamp <= report_request.date_range_end
                )
            ).scalar() or 0

            # Get top content and insights
            top_content = self._get_top_content(report_request.date_range_start, limit=20)
            key_insights = self._generate_insights(
                report_request.date_range_start,
                report_request.date_range_end
            )

            # Create report record
            report = AnalyticsReports(
                report_type=report_request.report_type,
                report_name=f"{report_request.report_type.title()} Report - {report_request.date_range_start.date()} to {report_request.date_range_end.date()}",
                date_range_start=report_request.date_range_start,
                date_range_end=report_request.date_range_end,
                report_data={
                    "date_range": {
                        "start": report_request.date_range_start.isoformat(),
                        "end": report_request.date_range_end.isoformat()
                    },
                    "metrics": {
                        "total_views": total_views,
                        "total_sessions": total_sessions,
                        "total_users": total_users,
                        "avg_session_duration": self._calculate_avg_session_duration(
                            report_request.date_range_start, report_request.date_range_end
                        ),
                        "bounce_rate": self._calculate_bounce_rate(
                            report_request.date_range_start, report_request.date_range_end
                        )
                    },
                    "charts": self._generate_chart_data(
                        report_request.date_range_start, report_request.date_range_end
                    ) if report_request.include_charts else None
                },
                total_views=total_views,
                total_sessions=total_sessions,
                total_users=total_users,
                top_content=top_content,
                key_insights=key_insights
            )

            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            return report

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to generate report: {str(e)}")

    # Private helper methods

    def _get_device_type(self, ua) -> str:
        """Determine device type from user agent"""
        if ua.is_mobile:
            return "mobile"
        elif ua.is_tablet:
            return "tablet"
        elif ua.is_pc:
            return "desktop"
        else:
            return "unknown"

    def _increment_post_views(self, post_id: int):
        """Increment view count for a blog post"""
        try:
            post = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if post:
                post.view_count += 1
                self.db.commit()
        except Exception:
            self.db.rollback()

    async def _update_realtime_metrics(self, analytics_data: PageViewAnalyticsCreate):
        """Update real-time metrics for live dashboard"""
        try:
            # Update active users (last 5 minutes)
            metric_key = "active_users_5m"
            await self._update_metric("active_users", metric_key, 1, "5m")

            # Update page views
            if analytics_data.post_id:
                await self._update_metric("page_views", f"post_{analytics_data.post_id}", 1, "24h")

            # Update total page views
            await self._update_metric("page_views", "total", 1, "24h")

        except Exception as e:
            print(f"Failed to update real-time metrics: {e}")

    async def _update_engagement_metrics(self, engagement_data: ContentEngagementAnalyticsCreate):
        """Update engagement metrics"""
        try:
            metric_key = f"{engagement_data.action_type}_{engagement_data.post_id or 'general'}"
            await self._update_metric("engagement", metric_key, 1, "1h")
        except Exception as e:
            print(f"Failed to update engagement metrics: {e}")

    async def _update_metric(self, metric_type: str, metric_key: str, value: float, time_window: str):
        """Update a real-time metric"""
        try:
            # Check if metric exists
            existing = self.db.query(RealTimeMetrics).filter(
                and_(
                    RealTimeMetrics.metric_type == metric_type,
                    RealTimeMetrics.metric_key == metric_key,
                    RealTimeMetrics.time_window == time_window
                )
            ).first()

            if existing:
                existing.metric_value += value
                existing.last_updated = datetime.now()
            else:
                new_metric = RealTimeMetrics(
                    metric_type=metric_type,
                    metric_key=metric_key,
                    metric_value=value,
                    time_window=time_window,
                    data_type="count"
                )
                self.db.add(new_metric)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            print(f"Failed to update metric {metric_type}:{metric_key}: {e}")

    def _get_top_content(self, start_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most viewed content"""
        try:
            results = self.db.query(
                PageViewAnalytics.post_id,
                BlogPost.title,
                func.count(PageViewAnalytics.id).label('views')
            ).join(
                BlogPost, PageViewAnalytics.post_id == BlogPost.id
            ).filter(
                PageViewAnalytics.timestamp >= start_date
            ).group_by(
                PageViewAnalytics.post_id, BlogPost.title
            ).order_by(
                desc('views')
            ).limit(limit).all()

            return [
                {
                    "post_id": row.post_id,
                    "title": row.title,
                    "views": row.views
                }
                for row in results
            ]

        except Exception as e:
            print(f"Failed to get top content: {e}")
            return []

    def _get_popular_searches(self, start_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular search queries"""
        try:
            results = self.db.query(
                SearchAnalytics.query,
                func.count(SearchAnalytics.id).label('count'),
                func.avg(SearchAnalytics.results_count).label('avg_results')
            ).filter(
                SearchAnalytics.timestamp >= start_date
            ).group_by(
                SearchAnalytics.query
            ).order_by(
                desc('count')
            ).limit(limit).all()

            return [
                {
                    "query": row.query,
                    "count": row.count,
                    "avg_results": round(row.avg_results or 0, 1)
                }
                for row in results
            ]

        except Exception as e:
            print(f"Failed to get popular searches: {e}")
            return []

    def _get_device_breakdown(self, start_date: datetime) -> Dict[str, int]:
        """Get device type breakdown"""
        try:
            results = self.db.query(
                PageViewAnalytics.device_type,
                func.count(PageViewAnalytics.id).label('count')
            ).filter(
                and_(
                    PageViewAnalytics.timestamp >= start_date,
                    PageViewAnalytics.device_type.isnot(None)
                )
            ).group_by(
                PageViewAnalytics.device_type
            ).all()

            return {row.device_type: row.count for row in results}

        except Exception as e:
            print(f"Failed to get device breakdown: {e}")
            return {}

    def _get_geographic_data(self, start_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get geographic visitor data"""
        try:
            results = self.db.query(
                PageViewAnalytics.country,
                func.count(PageViewAnalytics.id).label('visitors')
            ).filter(
                and_(
                    PageViewAnalytics.timestamp >= start_date,
                    PageViewAnalytics.country.isnot(None)
                )
            ).group_by(
                PageViewAnalytics.country
            ).order_by(
                desc('visitors')
            ).limit(limit).all()

            return [
                {
                    "country": row.country,
                    "visitors": row.visitors
                }
                for row in results
            ]

        except Exception as e:
            print(f"Failed to get geographic data: {e}")
            return []

    def _get_referral_sources(self, start_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get referral source data"""
        try:
            results = self.db.query(
                PageViewAnalytics.referrer_domain,
                func.count(PageViewAnalytics.id).label('visits')
            ).filter(
                and_(
                    PageViewAnalytics.timestamp >= start_date,
                    PageViewAnalytics.referrer_domain.isnot(None),
                    PageViewAnalytics.referrer_domain != ""
                )
            ).group_by(
                PageViewAnalytics.referrer_domain
            ).order_by(
                desc('visits')
            ).limit(limit).all()

            return [
                {
                    "domain": row.referrer_domain,
                    "visits": row.visits
                }
                for row in results
            ]

        except Exception as e:
            print(f"Failed to get referral sources: {e}")
            return []

    def _get_realtime_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        try:
            # Get metrics from last 5 minutes
            cutoff = datetime.now() - timedelta(minutes=5)

            active_users = self.db.query(
                func.count(func.distinct(PageViewAnalytics.user_identifier))
            ).filter(
                PageViewAnalytics.timestamp >= cutoff
            ).scalar() or 0

            recent_page_views = self.db.query(
                func.count(PageViewAnalytics.id)
            ).filter(
                PageViewAnalytics.timestamp >= cutoff
            ).scalar() or 0

            return {
                "active_users_5m": active_users,
                "page_views_5m": recent_page_views,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Failed to get real-time metrics: {e}")
            return {}

    def _calculate_avg_session_duration(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate average session duration"""
        try:
            result = self.db.query(
                func.avg(UserSessionAnalytics.duration)
            ).filter(
                and_(
                    UserSessionAnalytics.start_time >= start_date,
                    UserSessionAnalytics.end_time <= end_date,
                    UserSessionAnalytics.duration.isnot(None)
                )
            ).scalar()

            return round(result or 0, 2)

        except Exception:
            return 0.0

    def _calculate_bounce_rate(self, start_date: datetime, end_date: datetime) -> float:
        """Calculate bounce rate (single page sessions)"""
        try:
            total_sessions = self.db.query(func.count(UserSessionAnalytics.id)).filter(
                and_(
                    UserSessionAnalytics.start_time >= start_date,
                    UserSessionAnalytics.end_time <= end_date
                )
            ).scalar() or 0

            bounce_sessions = self.db.query(func.count(UserSessionAnalytics.id)).filter(
                and_(
                    UserSessionAnalytics.start_time >= start_date,
                    UserSessionAnalytics.end_time <= end_date,
                    UserSessionAnalytics.is_bounce == True
                )
            ).scalar() or 0

            if total_sessions == 0:
                return 0.0

            return round((bounce_sessions / total_sessions) * 100, 2)

        except Exception:
            return 0.0

    def _generate_chart_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate chart data for reports"""
        try:
            # Daily page views chart
            daily_views = self.db.query(
                func.date(PageViewAnalytics.timestamp).label('date'),
                func.count(PageViewAnalytics.id).label('views')
            ).filter(
                and_(
                    PageViewAnalytics.timestamp >= start_date,
                    PageViewAnalytics.timestamp <= end_date
                )
            ).group_by(
                func.date(PageViewAnalytics.timestamp)
            ).order_by(
                'date'
            ).all()

            # Device breakdown chart
            device_data = self._get_device_breakdown(start_date)

            # Geographic chart
            geo_data = self._get_geographic_data(start_date, limit=20)

            return {
                "daily_page_views": [
                    {"date": str(row.date), "views": row.views}
                    for row in daily_views
                ],
                "device_breakdown": device_data,
                "geographic_distribution": geo_data
            }

        except Exception as e:
            print(f"Failed to generate chart data: {e}")
            return {}

    def _generate_insights(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate key insights from analytics data"""
        try:
            insights = {}

            # Traffic growth
            current_period_views = self.db.query(func.count(PageViewAnalytics.id)).filter(
                and_(
                    PageViewAnalytics.timestamp >= start_date,
                    PageViewAnalytics.timestamp <= end_date
                )
            ).scalar() or 0

            previous_period_start = start_date - (end_date - start_date)
            previous_period_views = self.db.query(func.count(PageViewAnalytics.id)).filter(
                and_(
                    PageViewAnalytics.timestamp >= previous_period_start,
                    PageViewAnalytics.timestamp < start_date
                )
            ).scalar() or 0

            if previous_period_views > 0:
                growth_rate = ((current_period_views - previous_period_views) / previous_period_views) * 100
                insights["traffic_growth"] = round(growth_rate, 1)

            # Top performing content
            top_post = self._get_top_content(start_date, limit=1)
            if top_post:
                insights["top_post"] = top_post[0]

            # Most popular device type
            device_breakdown = self._get_device_breakdown(start_date)
            if device_breakdown:
                top_device = max(device_breakdown.items(), key=lambda x: x[1])
                insights["top_device"] = {
                    "type": top_device[0],
                    "percentage": round((top_device[1] / sum(device_breakdown.values())) * 100, 1)
                }

            return insights

        except Exception as e:
            print(f"Failed to generate insights: {e}")
            return {}