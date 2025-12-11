from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from database import get_db
from services.analytics_service import AnalyticsService
from schemas.blog import (
    PageViewAnalyticsCreate, ContentEngagementAnalyticsCreate,
    UserSessionAnalyticsCreate, ReferralAnalyticsCreate,
    AnalyticsDashboardResponse, AnalyticsReportRequest
)

router = APIRouter()

@router.post("/track/pageview")
async def track_page_view(
    analytics_data: PageViewAnalyticsCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track page view analytics"""
    try:
        analytics_service = AnalyticsService(db)

        # Add request-specific data
        analytics_data.ip_address = request.client.host if request.client else None

        page_view = analytics_service.track_page_view(analytics_data)

        return {
            "success": True,
            "tracked": True,
            "id": page_view.id
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to track page view: {str(e)}")

@router.post("/track/engagement")
async def track_engagement(
    engagement_data: ContentEngagementAnalyticsCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track user engagement events"""
    try:
        analytics_service = AnalyticsService(db)
        engagement = analytics_service.track_engagement(engagement_data)

        return {
            "success": True,
            "tracked": True,
            "id": engagement.id
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to track engagement: {str(e)}")

@router.post("/track/session")
async def track_session(
    session_data: UserSessionAnalyticsCreate,
    db: Session = Depends(get_db)
):
    """Track or update user session"""
    try:
        analytics_service = AnalyticsService(db)
        session = analytics_service.track_session(session_data)

        return {
            "success": True,
            "session_id": session.session_id,
            "id": session.id
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to track session: {str(e)}")

@router.post("/track/referral")
async def track_referral(
    referral_data: ReferralAnalyticsCreate,
    db: Session = Depends(get_db)
):
    """Track referral and UTM data"""
    try:
        analytics_service = AnalyticsService(db)
        referral = analytics_service.track_referral(referral_data)

        return {
            "success": True,
            "tracked": True,
            "id": referral.id
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to track referral: {str(e)}")

@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    timeframe_days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db)
):
    """Get analytics dashboard data"""
    try:
        analytics_service = AnalyticsService(db)
        dashboard_data = analytics_service.get_dashboard_data(timeframe_days)

        return dashboard_data

    except Exception as e:
        raise HTTPException(500, f"Failed to get dashboard data: {str(e)}")

@router.get("/realtime")
async def get_realtime_metrics(db: Session = Depends(get_db)):
    """Get real-time analytics metrics (last 5 minutes)"""
    try:
        analytics_service = AnalyticsService(db)
        realtime_data = analytics_service._get_realtime_metrics()

        return {
            "success": True,
            "data": realtime_data,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get real-time metrics: {str(e)}")

@router.post("/reports/generate")
async def generate_report(
    report_request: AnalyticsReportRequest,
    db: Session = Depends(get_db)
):
    """Generate analytics report"""
    try:
        analytics_service = AnalyticsService(db)
        report = analytics_service.generate_report(report_request)

        return {
            "success": True,
            "report_id": report.id,
            "report_name": report.report_name,
            "generated_at": report.generated_at.isoformat(),
            "data": report.report_data
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to generate report: {str(e)}")

@router.get("/reports")
async def get_reports(
    report_type: Optional[str] = None,
    limit: int = Query(20, description="Number of reports to return"),
    db: Session = Depends(get_db)
):
    """Get list of generated reports"""
    try:
        from models.blog import AnalyticsReports

        query = db.query(AnalyticsReports)
        if report_type:
            query = query.filter(AnalyticsReports.report_type == report_type)

        reports = query.order_by(
            AnalyticsReports.generated_at.desc()
        ).limit(limit).all()

        return {
            "success": True,
            "reports": [
                {
                    "id": report.id,
                    "report_type": report.report_type,
                    "report_name": report.report_name,
                    "generated_at": report.generated_at.isoformat(),
                    "date_range": {
                        "start": report.date_range_start.isoformat(),
                        "end": report.date_range_end.isoformat()
                    },
                    "total_views": report.total_views,
                    "total_sessions": report.total_sessions,
                    "total_users": report.total_users
                }
                for report in reports
            ]
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get reports: {str(e)}")

@router.get("/reports/{report_id}")
async def get_report(
    report_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed report data"""
    try:
        from models.blog import AnalyticsReports

        report = db.query(AnalyticsReports).filter(
            AnalyticsReports.id == report_id
        ).first()

        if not report:
            raise HTTPException(404, "Report not found")

        return {
            "success": True,
            "report": {
                "id": report.id,
                "report_type": report.report_type,
                "report_name": report.report_name,
                "generated_at": report.generated_at.isoformat(),
                "date_range": {
                    "start": report.date_range_start.isoformat(),
                    "end": report.date_range_end.isoformat()
                },
                "metrics": {
                    "total_views": report.total_views,
                    "total_sessions": report.total_sessions,
                    "total_users": report.total_users
                },
                "data": report.report_data,
                "top_content": report.top_content,
                "key_insights": report.key_insights
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get report: {str(e)}")

@router.get("/content-performance")
async def get_content_performance(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, description="Number of posts to return"),
    db: Session = Depends(get_db)
):
    """Get content performance analytics"""
    try:
        analytics_service = AnalyticsService(db)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        top_content = analytics_service._get_top_content(start, limit)

        return {
            "success": True,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "content_performance": top_content
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get content performance: {str(e)}")

@router.get("/search-analytics")
async def get_search_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, description="Number of queries to return"),
    db: Session = Depends(get_db)
):
    """Get search analytics data"""
    try:
        analytics_service = AnalyticsService(db)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        popular_searches = analytics_service._get_popular_searches(start, limit)

        return {
            "success": True,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "popular_searches": popular_searches
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get search analytics: {str(e)}")

@router.get("/geographic-analytics")
async def get_geographic_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(20, description="Number of countries to return"),
    db: Session = Depends(get_db)
):
    """Get geographic analytics data"""
    try:
        analytics_service = AnalyticsService(db)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        geographic_data = analytics_service._get_geographic_data(start, limit)

        return {
            "success": True,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "geographic_data": geographic_data
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get geographic analytics: {str(e)}")

@router.get("/device-analytics")
async def get_device_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get device and browser analytics"""
    try:
        analytics_service = AnalyticsService(db)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        device_breakdown = analytics_service._get_device_breakdown(start)

        return {
            "success": True,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "device_breakdown": device_breakdown
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get device analytics: {str(e)}")

@router.get("/referral-analytics")
async def get_referral_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(20, description="Number of referrers to return"),
    db: Session = Depends(get_db)
):
    """Get referral source analytics"""
    try:
        analytics_service = AnalyticsService(db)

        # Parse dates
        if start_date:
            start = datetime.fromisoformat(start_date)
        else:
            start = datetime.now() - timedelta(days=30)

        if end_date:
            end = datetime.fromisoformat(end_date)
        else:
            end = datetime.now()

        referral_sources = analytics_service._get_referral_sources(start, limit)

        return {
            "success": True,
            "date_range": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "referral_sources": referral_sources
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get referral analytics: {str(e)}")

@router.get("/summary")
async def get_analytics_summary(
    timeframe_days: int = Query(7, description="Number of days for summary"),
    db: Session = Depends(get_db)
):
    """Get quick analytics summary"""
    try:
        analytics_service = AnalyticsService(db)
        dashboard_data = analytics_service.get_dashboard_data(timeframe_days)

        return {
            "success": True,
            "summary": {
                "total_views": dashboard_data.total_views,
                "total_sessions": dashboard_data.total_sessions,
                "total_users": dashboard_data.total_users,
                "active_users": dashboard_data.active_users,
                "page_views_today": dashboard_data.page_views_today,
                "page_views_yesterday": dashboard_data.page_views_yesterday,
                "top_content_count": len(dashboard_data.top_content),
                "timeframe_days": timeframe_days
            }
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get analytics summary: {str(e)}")