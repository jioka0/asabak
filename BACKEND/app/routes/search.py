from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services.search_service import SearchService
from schemas.blog import (
    SearchRequest, SearchResponse, SearchSuggestions,
    SearchAnalyticsCreate, SearchFilters
)
import time

router = APIRouter()

@router.post("/posts", response_model=SearchResponse)
async def search_posts(
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Advanced search with FTS5 full-text search and intelligent ranking"""
    try:
        start_time = time.time()
        search_service = SearchService(db)
        results = search_service.search_posts(search_request)

        # Enhanced analytics logging
        analytics_data = {
            "query": search_request.query,
            "results_count": results.total,
            "filters_used": results.filters_applied,
            "user_identifier": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", ""),
            "search_time": time.time() - start_time,
            "has_results": results.total > 0
        }

        # Log analytics asynchronously (fire and forget)
        try:
            search_service.log_search_analytics(analytics_data)
        except Exception as e:
            print(f"Analytics logging failed: {e}")

        return results

    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")

@router.get("/suggestions", response_model=SearchSuggestions)
async def get_search_suggestions(
    q: str = "",
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get search suggestions and autocomplete options"""
    try:
        search_service = SearchService(db)
        return search_service.get_search_suggestions(q, limit)
    except Exception as e:
        raise HTTPException(500, f"Failed to get suggestions: {str(e)}")

@router.get("/filters", response_model=dict)
async def get_search_filters(db: Session = Depends(get_db)):
    """Get available search filters and their counts"""
    try:
        search_service = SearchService(db)
        return search_service.get_filters()
    except Exception as e:
        raise HTTPException(500, f"Failed to get filters: {str(e)}")

@router.post("/analytics")
async def log_search_analytics(
    analytics: SearchAnalyticsCreate,
    db: Session = Depends(get_db)
):
    """Log search analytics data"""
    try:
        search_service = SearchService(db)
        search_service.log_search_analytics(analytics.dict())
        return {"message": "Analytics logged successfully"}
    except Exception as e:
        raise HTTPException(500, f"Failed to log analytics: {str(e)}")

@router.get("/popular-searches")
async def get_popular_searches(limit: int = 10, db: Session = Depends(get_db)):
    """Get most popular search queries"""
    try:
        search_service = SearchService(db)
        popular = search_service._get_popular_searches(limit)
        return {"popular_searches": popular}
    except Exception as e:
        raise HTTPException(500, f"Failed to get popular searches: {str(e)}")

@router.get("/trending-topics")
async def get_trending_topics(limit: int = 10, db: Session = Depends(get_db)):
    """Get trending topics based on recent activity"""
    try:
        search_service = SearchService(db)
        trending = search_service._get_trending_topics(limit)
        return {"trending_topics": trending}
    except Exception as e:
        raise HTTPException(500, f"Failed to get trending topics: {str(e)}")

@router.get("/stats")
async def get_search_stats(db: Session = Depends(get_db)):
    """Get search statistics and insights"""
    try:
        from sqlalchemy import func
        from models.blog import SearchAnalytics

        # Get basic stats
        total_searches = db.query(func.count(SearchAnalytics.id)).scalar()
        unique_queries = db.query(func.count(func.distinct(SearchAnalytics.query))).scalar()
        avg_results = db.query(func.avg(SearchAnalytics.results_count)).scalar()

        return {
            "total_searches": total_searches or 0,
            "unique_queries": unique_queries or 0,
            "average_results_per_search": round(avg_results or 0, 2)
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get search stats: {str(e)}")