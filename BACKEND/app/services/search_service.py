from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, or_, and_, cast, String
from typing import List, Dict, Any, Optional, Tuple
import time
import re
import logging
from datetime import datetime
from models.blog import BlogPost, SearchAnalytics
from schemas.blog import SearchRequest, SearchResponse, BlogPostSearchResult, SearchSuggestions

# Initialize logger
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_posts(self, search_request: SearchRequest) -> SearchResponse:
        """Advanced search function with PostgreSQL full-text search and intelligent ranking"""
        start_time = time.time()

        # Use PostgreSQL full-text search if query provided
        if search_request.query.strip():
            return self._postgresql_fulltext_search(search_request, start_time)

        # Regular search without text query - use the regular search method
        return self._regular_search(search_request, start_time)

    def _regular_search(self, search_request: SearchRequest, start_time: float) -> SearchResponse:
        """Regular search without full-text search - only published posts"""
        query = self.db.query(BlogPost).filter(BlogPost.published_at.isnot(None))

        # Apply section filter
        if search_request.section and search_request.section != "all":
            query = query.filter(BlogPost.section == search_request.section)

        # Apply tag filters
        if search_request.tags:
            tag_conditions = []
            for tag in search_request.tags:
                # Cross-database compatible JSON array search (works for SQLite and PostgreSQL)
                tag_conditions.append(cast(BlogPost.tags, String).like(f'%"{tag}"%'))
            
            if tag_conditions:
                query = query.filter(or_(*tag_conditions))

        # Apply sorting
        if search_request.sort == "recent":
            query = query.order_by(desc(BlogPost.published_at))
        elif search_request.sort == "popular":
            query = query.order_by(desc(BlogPost.view_count + BlogPost.like_count * 2))
        else:  # featured first, then by date
            query = query.order_by(desc(BlogPost.is_featured), desc(BlogPost.priority), desc(BlogPost.published_at))

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        results = query.offset(search_request.offset).limit(search_request.limit).all()

        # Convert to search results
        search_results = []
        for post in results:
            result = BlogPostSearchResult.from_orm(post)
            result.search_score = self._calculate_popularity_score(post)
            result.matched_terms = []
            search_results.append(result)

        search_time = time.time() - start_time

        return SearchResponse(
            results=search_results,
            total=total,
            query=search_request.query,
            filters_applied={
                "section": search_request.section,
                "tags": search_request.tags,
                "sort": search_request.sort
            },
            search_time=round(search_time, 3)
        )

    def _postgresql_fulltext_search(self, search_request: SearchRequest, start_time: float) -> SearchResponse:
        """Full-text search using PostgreSQL full-text search with ranking"""
        try:
            # Build search query
            search_terms = self._parse_search_query(search_request.query)
            
            if not search_terms:
                # Fallback to regular search if no valid terms
                search_request.sort = "relevance"
                return self.search_posts(search_request)

            # Start with base query for published posts
            query = self.db.query(BlogPost).filter(BlogPost.published_at.isnot(None))

            # Build text search conditions for title, excerpt, and content
            text_conditions = []
            for term in search_terms:
                term_condition = or_(
                    BlogPost.title.ilike(f"%{term}%"),
                    BlogPost.excerpt.ilike(f"%{term}%"),
                    BlogPost.content.ilike(f"%{term}%"),
                    cast(BlogPost.tags, String).ilike(f"%{term}%")
                )
                text_conditions.append(term_condition)

            # Apply text search with AND logic (all terms must match somewhere)
            query = query.filter(and_(*text_conditions))

            # Apply section filter
            if search_request.section and search_request.section != "all":
                query = query.filter(BlogPost.section == search_request.section)

            # Apply tag filters
            if search_request.tags:
                tag_conditions = []
                for tag in search_request.tags:
                    tag_conditions.append(cast(BlogPost.tags, String).like(f'%"{tag}"%'))
                
                if tag_conditions:
                    query = query.filter(or_(*tag_conditions))

            # Calculate relevance scores for each post
            results = query.all()
            
            # Calculate relevance scores
            scored_results = []
            for post in results:
                score = self._calculate_relevance_score(post, search_request.query, search_request.tags or [])
                if score > 0:  # Only include posts with some relevance
                    result = BlogPostSearchResult.from_orm(post)
                    result.search_score = score
                    result.matched_terms = self._find_matched_terms(post, search_request.query)
                    scored_results.append(result)

            # Sort by relevance score if sorting by relevance, otherwise use specified sort
            if search_request.sort == "relevance":
                scored_results.sort(key=lambda x: x.search_score, reverse=True)
            elif search_request.sort == "recent":
                scored_results.sort(key=lambda x: x.published_at, reverse=True)
            elif search_request.sort == "popular":
                scored_results.sort(key=lambda x: x.view_count + x.like_count * 2, reverse=True)

            # Apply pagination
            total = len(scored_results)
            paginated_results = scored_results[search_request.offset:search_request.offset + search_request.limit]

            search_time = time.time() - start_time

            return SearchResponse(
                results=paginated_results,
                total=total,
                query=search_request.query,
                filters_applied={
                    "section": search_request.section,
                    "tags": search_request.tags,
                    "sort": search_request.sort
                },
                search_time=round(search_time, 3)
            )

        except Exception as e:
            # Fallback to regular search if full-text search fails
            import traceback
            logger.warning(f"PostgreSQL full-text search failed: {e}. Falling back to regular search.")
            logger.debug(traceback.format_exc())
            # Use the regular search method directly to avoid recursion
            return self._regular_search(search_request, start_time)



    def get_search_suggestions(self, query: str, limit: int = 5) -> SearchSuggestions:
        """Generate search suggestions based on existing content"""
        if not query.strip():
            return SearchSuggestions(
                suggestions=[],
                popular=self._get_popular_searches(limit),
                trending=self._get_trending_topics(limit)
            )

        # Get suggestions from post titles and tags
        suggestions = set()

        # Search in titles
        title_results = self.db.query(BlogPost.title).filter(
            BlogPost.title.ilike(f"%{query}%")
        ).limit(20).all()

        for (title,) in title_results:
            words = title.lower().split()
            for word in words:
                if word.startswith(query.lower()) and len(word) > 2:
                    suggestions.add(word)

        # Search in tags (JSON array)
        tag_results = self.db.query(BlogPost.tags).filter(
            cast(BlogPost.tags, String).like(f"%{query}%")
        ).limit(20).all()

        for (tags,) in tag_results:
            if tags:
                for tag in tags:
                    if tag.lower().startswith(query.lower()):
                        suggestions.add(tag.lower())

        return SearchSuggestions(
            suggestions=list(suggestions)[:limit],
            popular=self._get_popular_searches(limit),
            trending=self._get_trending_topics(limit)
        )

    def get_filters(self) -> Dict[str, Any]:
        """Get available filter options"""
        # Get active sections
        sections = ['latest', 'popular', 'others', 'featured']  # Static for now

        # Get popular tags from actual database content
        tag_usage = {}
        all_posts = self.db.query(BlogPost.tags).filter(BlogPost.published_at.isnot(None)).all()

        for (tags,) in all_posts:
            if tags and isinstance(tags, list):
                for tag in tags:
                    tag_lower = tag.lower().strip()
                    if tag_lower:
                        tag_usage[tag_lower] = tag_usage.get(tag_lower, 0) + 1

        # Sort tags by usage and take top 10
        sorted_tags = sorted(tag_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        tags = [tag for tag, count in sorted_tags]

        return {
            "sections": sections,
            "tags": tags,
            "counts": {
                "sections": {section: self._count_posts_by_section(section) for section in sections},
                "tags": tag_usage  # Return actual counts for all tags
            }
        }

    def log_search_analytics(self, analytics_data: Dict[str, Any]) -> None:
        """Log search analytics"""
        analytics = SearchAnalytics(**analytics_data)
        self.db.add(analytics)
        self.db.commit()

    def _parse_search_query(self, query: str) -> List[str]:
        """Parse search query into individual terms"""
        # Remove special characters and split
        clean_query = re.sub(r'[^\w\s]', ' ', query.lower())
        terms = clean_query.split()
        # Remove common stop words and short terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        return [term for term in terms if len(term) > 2 and term not in stop_words]

    def _apply_text_search(self, query, search_terms: List[str]):
        """Apply full-text search across multiple fields"""
        search_conditions = []

        for term in search_terms:
            term_conditions = []

            # Search in title (highest weight)
            term_conditions.append(BlogPost.title.ilike(f"%{term}%"))

            # Search in excerpt
            term_conditions.append(BlogPost.excerpt.ilike(f"%{term}%"))

            # Search in content
            term_conditions.append(BlogPost.content.ilike(f"%{term}%"))

            # Search in tags (JSON)
            term_conditions.append(cast(BlogPost.tags, String).like(f'%"{term}"%'))

            search_conditions.append(or_(*term_conditions))

        return query.filter(and_(*search_conditions))

    def _calculate_relevance_score(self, post: BlogPost, query: str, tags: List[str]) -> float:
        """Calculate relevance score for search results (fallback method)"""
        score = 0.0

        if not query.strip():
            return score

        query_lower = query.lower()
        search_terms = self._parse_search_query(query)

        # Title matches (highest weight - 10 points)
        title_lower = post.title.lower()
        if query_lower in title_lower:
            score += 15  # Exact phrase match in title
        else:
            title_matches = sum(1 for term in search_terms if term in title_lower)
            score += title_matches * 8  # 8 points per term match in title

        # Excerpt matches (medium weight - 5 points)
        if post.excerpt:
            excerpt_lower = post.excerpt.lower()
            if query_lower in excerpt_lower:
                score += 8
            else:
                excerpt_matches = sum(1 for term in search_terms if term in excerpt_lower)
                score += excerpt_matches * 4

        # Content matches (lower weight - 2 points)
        if post.content:
            content_lower = post.content.lower()
            if query_lower in content_lower:
                score += 5
            else:
                content_matches = sum(1 for term in search_terms if term in content_lower)
                score += content_matches * 2

        # Tag matches (high weight - 12 points)
        if post.tags and isinstance(post.tags, list):
            for search_tag in tags:
                if search_tag.lower() in [tag.lower() for tag in post.tags]:
                    score += 12

        # Section relevance boost
        if post.section == "featured":
            score += 3
        elif post.section == "popular":
            score += 2

        # Popularity boost (recency and engagement)
        if post.published_at:
            try:
                days_since_publish = (datetime.now() - post.published_at).days
                recency_boost = max(0, 10 - days_since_publish)  # Newer posts get boost
                score += recency_boost * 0.5
            except Exception as e:
                logger.error(f"Error calculating recency boost: {e}")
        else:
            score -= 5  # Penalty for missing date

        # Engagement boost
        engagement_score = post.view_count * 0.01 + post.like_count * 0.1 + post.comment_count * 0.2
        score += min(engagement_score, 8)  # Cap at 8 points

        # Featured content boost
        if post.is_featured:
            score += 5

        return round(score, 2)

    def _calculate_popularity_score(self, post: BlogPost) -> float:
        """Calculate popularity score for non-search results"""
        score = 0.0

        # Base popularity from engagement
        score += post.view_count * 0.01
        score += post.like_count * 0.1
        score += post.comment_count * 0.2
        score += post.share_count * 0.3

        # Recency boost
        if post.published_at:
            try:
                days_since_publish = (datetime.now() - post.published_at).days
                recency_boost = max(0, 30 - days_since_publish)  # 30-day recency window
                score += recency_boost
            except Exception as e:
                logger.error(f"Error calculating popularity recency: {e}")
        else:
            score -= 10

        # Featured boost
        if post.is_featured:
            score += 20

        # Priority boost
        score += post.priority * 2

        return round(score, 2)

    def _find_matched_terms(self, post: BlogPost, query: str) -> List[str]:
        """Find which terms from the query matched this post"""
        if not query.strip():
            return []

        terms = self._parse_search_query(query)
        matched = []

        for term in terms:
            if (term in post.title.lower() or
                (post.excerpt and term in post.excerpt.lower()) or
                (post.content and term in post.content.lower())):
                matched.append(term)

        return matched

    def _get_popular_searches(self, limit: int = 5) -> List[str]:
        """Get most popular search queries based on highest viewed posts of all time"""
        try:
            # Get posts with highest view counts of all time
            popular_posts = self.db.query(BlogPost).filter(
                BlogPost.published_at.isnot(None)
            ).order_by(
                desc(BlogPost.view_count)
            ).limit(limit).all()
            
            # Return full titles for search suggestions
            suggestions = []
            for post in popular_posts:
                if post.title:
                    suggestions.append(post.title)
                
            return suggestions[:limit]
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            return ["AI and Machine Learning Fundamentals", "Startup Funding Guide", "Modern Web Development", "Business Strategy 101", "Innovation in Technology"]

    def _get_trending_topics(self, limit: int = 5) -> List[str]:
        """Get trending topics based on posts with highest views in the past 7 days"""
        try:
            from datetime import datetime, timedelta
            
            # Get date 7 days ago
            seven_days_ago = datetime.now() - timedelta(days=7)
            
            # Get posts from the last 7 days ordered by views
            trending_posts = self.db.query(BlogPost).filter(
                BlogPost.published_at >= seven_days_ago,
                BlogPost.published_at.isnot(None)
            ).order_by(
                desc(BlogPost.view_count)
            ).limit(limit).all()
            
            # Return full titles for search suggestions
            suggestions = []
            for post in trending_posts:
                if post.title:
                    suggestions.append(post.title)
                
            return suggestions[:limit]
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return ["Latest Technology Trends 2025", "Artificial Intelligence Breakthroughs", "Blockchain Applications", "Web Development Revolution", "Digital Transformation Guide"]

    def _count_posts_by_section(self, section: str) -> int:
        """Count posts in a specific section"""
        return self.db.query(BlogPost).filter(BlogPost.section == section).count()

    def _count_posts_by_tag(self, tag: str) -> int:
        """Count posts with a specific tag (SQLite compatible)"""
        return self.db.query(BlogPost).filter(
            cast(BlogPost.tags, String).like(f'%"{tag}"%')
        ).count()