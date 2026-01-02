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
        """Advanced search function with FTS5 full-text search and intelligent ranking"""
        start_time = time.time()

        # Use FTS5 for full-text search if query provided
        if search_request.query.strip():
            return self._fts_search(search_request, start_time)

        # Regular search without text query - only published posts
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

    def _fts_search(self, search_request: SearchRequest, start_time: float) -> SearchResponse:
        """Full-text search using FTS5 with advanced ranking"""
        try:
            # Build FTS5 query
            fts_query = self._build_fts_query(search_request.query)

            # Execute FTS search with ranking
            fts_results = self.db.execute(text(f"""
                SELECT
                    b.*,
                    bm25(fts.rowid, 10.0, 5.0, 2.0, 1.0, 1.0) as score,
                    highlight(fts, 0, '<mark>', '</mark>') as highlighted_title,
                    highlight(fts, 1, '<mark>', '</mark>') as highlighted_content,
                    snippet(fts, 1, '<mark>', '</mark>', '...', 50) as excerpt_snippet
                FROM blog_posts_fts fts
                JOIN blog_posts b ON b.id = fts.rowid
                WHERE fts MATCH :query
                ORDER BY bm25(fts.rowid, 10.0, 5.0, 2.0, 1.0, 1.0)
                LIMIT :limit OFFSET :offset
            """), {
                'query': fts_query,
                'limit': search_request.limit + 50,  # Get more for filtering
                'offset': search_request.offset
            }).fetchall()

            # Apply additional filters
            filtered_results = []
            for row in fts_results:
                post_data = dict(row)

                # Apply section filter
                if search_request.section and search_request.section != "all":
                    if post_data.get('section') != search_request.section:
                        continue

                # Apply tag filters
                if search_request.tags:
                    post_tags = post_data.get('tags', [])
                    if not any(tag in post_tags for tag in search_request.tags):
                        continue

                filtered_results.append(post_data)

            # Limit results after filtering
            filtered_results = filtered_results[:search_request.limit]

            # Convert to BlogPostSearchResult objects
            search_results = []
            for post_data in filtered_results:
                # Get full post object (only published)
                post = self.db.query(BlogPost).filter(
                    BlogPost.id == post_data['id'],
                    BlogPost.published_at.isnot(None)
                ).first()
                if post:
                    result = BlogPostSearchResult.from_orm(post)
                    result.search_score = round(post_data.get('score', 0), 2)
                    result.matched_terms = self._extract_highlighted_terms(post_data)
                    search_results.append(result)

            # Get total count (approximate for performance)
            total_count = self.db.execute(text("""
                SELECT COUNT(*) FROM blog_posts_fts WHERE blog_posts_fts MATCH :query
            """), {'query': fts_query}).scalar() or 0

            search_time = time.time() - start_time

            return SearchResponse(
                results=search_results,
                total=min(total_count, 1000),  # Cap for performance
                query=search_request.query,
                filters_applied={
                    "section": search_request.section,
                    "tags": search_request.tags,
                    "sort": "relevance"
                },
                search_time=round(search_time, 3)
            )

        except Exception as e:
            # Fallback to regular search if FTS fails (e.g. table doesn't exist)
            import traceback
            logger.warning(f"FTS search failed or table missing: {e}. Falling back to regular search.")
            logger.debug(traceback.format_exc())
            search_request.sort = "relevance"
            # Return regular search
            return self.search_posts(search_request)

    def _build_fts_query(self, query: str) -> str:
        """Build FTS5 query with advanced operators"""
        # Parse and enhance the query
        terms = self._parse_search_query(query)

        if not terms:
            return query

        # Build FTS query with NEAR operator for phrase matching
        fts_parts = []

        # Add individual terms
        fts_parts.extend(terms)

        # Add phrase matching for consecutive terms
        if len(terms) > 1:
            for i in range(len(terms) - 1):
                if len(terms[i]) > 2 and len(terms[i + 1]) > 2:
                    fts_parts.append(f'"{terms[i]} {terms[i + 1]}"')

        # Add prefix matching for autocomplete
        for term in terms:
            if len(term) > 2:
                fts_parts.append(f'{term}*')

        return ' OR '.join(fts_parts)

    def _extract_highlighted_terms(self, post_data: dict) -> List[str]:
        """Extract highlighted terms from FTS results"""
        highlighted_terms = set()

        # Extract from highlighted title
        if 'highlighted_title' in post_data:
            highlights = re.findall(r'<mark>(.*?)</mark>', post_data['highlighted_title'], re.IGNORECASE)
            highlighted_terms.update(highlights)

        # Extract from highlighted content
        if 'highlighted_content' in post_data:
            highlights = re.findall(r'<mark>(.*?)</mark>', post_data['highlighted_content'], re.IGNORECASE)
            highlighted_terms.update(highlights)

        return list(highlighted_terms)

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

        # Get popular tags (top 10 by usage)
        # For PostgreSQL/SQLite compatible tag fetching
        tag_counts = self.db.query(BlogPost.tags).all()

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
        """Count posts with a specific tag (SQLite compatible)"""
        return self.db.query(BlogPost).filter(
            cast(BlogPost.tags, String).like(f'%"{tag}"%')
        ).count()