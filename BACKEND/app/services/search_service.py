from sqlalchemy.orm import Session
from sqlalchemy import func, text, desc, or_, and_
from typing import List, Dict, Any, Optional, Tuple
import time
import re
from models.blog import BlogPost, SearchAnalytics
from schemas.blog import SearchRequest, SearchResponse, BlogPostSearchResult, SearchSuggestions

class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search_posts(self, search_request: SearchRequest) -> SearchResponse:
        """Main search function with full-text search and filtering"""
        start_time = time.time()

        query = self.db.query(BlogPost)

        # Apply text search if query provided
        if search_request.query.strip():
            search_terms = self._parse_search_query(search_request.query)
            query = self._apply_text_search(query, search_terms)

        # Apply section filter
        if search_request.section and search_request.section != "all":
            query = query.filter(BlogPost.section == search_request.section)

        # Apply tag filters
        if search_request.tags:
            tag_filters = []
            for tag in search_request.tags:
                # Check if tag is in the JSON array
                tag_filters.append(
                    text("JSON_CONTAINS(tags, JSON_QUOTE(:tag))").bindparams(tag=tag)
                )
            if tag_filters:
                query = query.filter(or_(*tag_filters))

        # Apply sorting
        if search_request.sort == "recent":
            query = query.order_by(desc(BlogPost.published_at))
        elif search_request.sort == "popular":
            query = query.order_by(desc(BlogPost.view_count + BlogPost.like_count * 2))
        else:  # relevance (default)
            if search_request.query.strip():
                # For relevance sorting, we need to calculate match scores
                # This is a simplified version - in production you'd use FTS ranking
                query = query.order_by(desc(BlogPost.view_count))
            else:
                query = query.order_by(desc(BlogPost.published_at))

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        results = query.offset(search_request.offset).limit(search_request.limit).all()

        # Convert to search results with scoring
        search_results = []
        for post in results:
            score = self._calculate_relevance_score(post, search_request.query, search_request.tags or [])
            matched_terms = self._find_matched_terms(post, search_request.query)

            result = BlogPostSearchResult.from_orm(post)
            result.search_score = score
            result.matched_terms = matched_terms
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
            text("JSON_SEARCH(tags, 'one', :query) IS NOT NULL")
        ).params(query=f"%{query}%").limit(20).all()

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

        # Get popular tags (top 10 by usage)
        tag_counts = self.db.query(
            func.json_extract(BlogPost.tags, '$[*]')  # This is simplified
        ).all()

        # For now, return static major tags
        tags = ['ai', 'startup', 'innovation', 'opinions', 'business', 'software']

        return {
            "sections": sections,
            "tags": tags,
            "counts": {
                "sections": {section: self._count_posts_by_section(section) for section in sections},
                "tags": {tag: self._count_posts_by_tag(tag) for tag in tags}
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
            term_conditions.append(
                text("JSON_SEARCH(tags, 'one', :term) IS NOT NULL").bindparams(term=term)
            )

            search_conditions.append(or_(*term_conditions))

        return query.filter(and_(*search_conditions))

    def _calculate_relevance_score(self, post: BlogPost, query: str, tags: List[str]) -> float:
        """Calculate relevance score for search results"""
        score = 0.0

        if not query.strip():
            return score

        query_lower = query.lower()

        # Title matches (highest weight)
        if query_lower in post.title.lower():
            score += 10
        elif any(term in post.title.lower() for term in query_lower.split()):
            score += 5

        # Excerpt matches
        if post.excerpt and query_lower in post.excerpt.lower():
            score += 3

        # Content matches
        if post.content and query_lower in post.content.lower():
            score += 1

        # Tag matches
        if post.tags:
            for tag in tags:
                if tag in post.tags:
                    score += 8

        # Popularity boost
        score += min(post.view_count / 100, 5)  # Max 5 points for views
        score += min(post.like_count / 10, 3)   # Max 3 points for likes

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
        """Get most popular search queries"""
        # This would be implemented with actual analytics data
        # For now, return some default popular searches
        return ["ai", "startup", "innovation", "business", "technology"]

    def _get_trending_topics(self, limit: int = 5) -> List[str]:
        """Get trending topics based on recent activity"""
        # This would analyze recent posts and searches
        # For now, return some trending topics
        return ["artificial intelligence", "blockchain", "web development", "startup funding", "digital transformation"]

    def _count_posts_by_section(self, section: str) -> int:
        """Count posts in a specific section"""
        return self.db.query(BlogPost).filter(BlogPost.section == section).count()

    def _count_posts_by_tag(self, tag: str) -> int:
        """Count posts with a specific tag"""
        return self.db.query(BlogPost).filter(
            text("JSON_CONTAINS(tags, JSON_QUOTE(:tag))").bindparams(tag=tag)
        ).count()