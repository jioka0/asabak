import os
import shutil
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import re
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_, text
from fastapi import UploadFile, HTTPException

from backend.app.models.blog import (
    BlogPost, MediaFile, ContentRevision, ContentWorkflow,
    SEOMetadata, ContentTemplate, ContentAnalytics, BulkOperation
)
from backend.app.schemas.blog import (
    BlogPostCreate, BlogPost as BlogPostSchema, ContentRevisionCreate,
    ContentWorkflowCreate, SEOMetadataCreate, ContentTemplateCreate,
    ContentAnalyticsCreate, BulkOperationCreate, SEOAnalysisResponse,
    ContentScheduleRequest, ContentScheduleResponse, MediaFileCreate
)

class ContentService:
    def __init__(self, db: Session):
        self.db = db
        self.media_base_path = Path("uploads/media")
        self.media_base_path.mkdir(parents=True, exist_ok=True)

    def create_post_with_workflow(self, post_data: BlogPostCreate, author: str) -> BlogPost:
        """Create a new blog post with workflow management"""
        try:
            # Create the post
            db_post = BlogPost(**post_data.dict())
            db_post.slug = self._generate_slug(db_post.title)
            self.db.add(db_post)
            self.db.flush()  # Get the post ID

            # Create initial workflow
            workflow = ContentWorkflow(
                post_id=db_post.id,
                status="draft",
                priority="medium",
                assigned_to=author
            )
            self.db.add(workflow)

            # Create initial SEO metadata if not provided
            if not self.db.query(SEOMetadata).filter(SEOMetadata.post_id == db_post.id).first():
                seo_data = SEOMetadataCreate(
                    meta_title=db_post.title[:60] if len(db_post.title) > 60 else db_post.title,
                    meta_description=db_post.excerpt[:160] if db_post.excerpt and len(db_post.excerpt) > 160 else (db_post.excerpt or ""),
                    focus_keyword=db_post.tags[0] if db_post.tags else None
                )
                seo_meta = SEOMetadata(post_id=db_post.id, **seo_data.dict())
                self.db.add(seo_meta)

            # Create initial revision
            revision = ContentRevision(
                post_id=db_post.id,
                revision_number=1,
                title=db_post.title,
                content=db_post.content,
                excerpt=db_post.excerpt,
                tags=db_post.tags,
                section=db_post.section,
                featured_image=db_post.featured_image,
                revised_by=author,
                revision_note="Initial post creation"
            )
            self.db.add(revision)

            self.db.commit()
            self.db.refresh(db_post)
            return db_post

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create post: {str(e)}")

    def update_post_with_revision(self, post_id: int, update_data: Dict[str, Any], author: str) -> BlogPost:
        """Update a post and create a revision"""
        try:
            post = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if not post:
                raise HTTPException(404, "Post not found")

            # Get current revision number
            latest_revision = self.db.query(ContentRevision).filter(
                ContentRevision.post_id == post_id
            ).order_by(desc(ContentRevision.revision_number)).first()

            revision_number = (latest_revision.revision_number + 1) if latest_revision else 1

            # Create revision before updating
            revision = ContentRevision(
                post_id=post_id,
                revision_number=revision_number,
                title=post.title,
                content=post.content,
                excerpt=post.excerpt,
                tags=post.tags,
                section=post.section,
                featured_image=post.featured_image,
                revised_by=author,
                revision_note="Auto-saved revision before update"
            )
            self.db.add(revision)

            # Update the post
            for key, value in update_data.items():
                if hasattr(post, key):
                    setattr(post, key, value)

            # Update slug if title changed
            if 'title' in update_data:
                post.slug = self._generate_slug(update_data['title'])

            self.db.commit()
            self.db.refresh(post)
            return post

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update post: {str(e)}")

    def schedule_post(self, schedule_data: ContentScheduleRequest) -> ContentScheduleResponse:
        """Schedule a post for publication"""
        try:
            post = self.db.query(BlogPost).filter(BlogPost.id == schedule_data.post_id).first()
            if not post:
                raise HTTPException(404, "Post not found")

            # Update post with scheduled time
            post.published_at = schedule_data.publish_at

            # Update workflow status
            workflow = self.db.query(ContentWorkflow).filter(
                ContentWorkflow.post_id == schedule_data.post_id
            ).first()

            if workflow:
                workflow.status = "scheduled"
                workflow.due_date = schedule_data.publish_at

            self.db.commit()

            return ContentScheduleResponse(
                success=True,
                post_id=schedule_data.post_id,
                scheduled_at=schedule_data.publish_at,
                message=f"Post scheduled for publication at {schedule_data.publish_at}"
            )

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to schedule post: {str(e)}")

    def upload_media(self, file: UploadFile, alt_text: Optional[str] = None,
                    caption: Optional[str] = None, uploaded_by: str = "admin") -> Dict[str, Any]:
        """Upload and process media files"""
        try:
            # Validate file type
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if file.content_type not in allowed_types:
                raise HTTPException(400, f"File type {file.content_type} not allowed")

            # Generate unique filename
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = self.media_base_path / unique_filename

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Get file size
            file_size = file_path.stat().st_size

            # Create database record
            media_file = MediaFile(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_url=f"/uploads/media/{unique_filename}",
                file_type="image",
                mime_type=file.content_type,
                file_size=file_size,
                alt_text=alt_text,
                caption=caption,
                uploaded_by=uploaded_by
            )

            self.db.add(media_file)
            self.db.commit()
            self.db.refresh(media_file)

            return {
                "success": True,
                "file_id": media_file.id,
                "file_url": media_file.file_url,
                "filename": media_file.filename,
                "file_size": media_file.file_size,
                "message": "File uploaded successfully"
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to upload media: {str(e)}")

    def analyze_seo(self, post_id: int, content: Optional[str] = None) -> SEOAnalysisResponse:
        """Analyze content for SEO optimization"""
        try:
            post = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if not post:
                raise HTTPException(404, "Post not found")

            analysis_content = content or post.content or ""
            title = post.title
            excerpt = post.excerpt or ""

            # Calculate readability score (simplified Flesch Reading Ease)
            readability_score = self._calculate_readability_score(analysis_content)

            # Calculate SEO score
            seo_score = self._calculate_seo_score(title, excerpt, analysis_content)

            # Generate suggestions
            suggestions = self._generate_seo_suggestions(title, excerpt, analysis_content)

            # Keyword analysis
            keyword_analysis = self._analyze_keywords(analysis_content)

            # Recommendations
            recommendations = self._generate_recommendations(title, excerpt, analysis_content)

            return SEOAnalysisResponse(
                post_id=post_id,
                readability_score=readability_score,
                seo_score=seo_score,
                suggestions=suggestions,
                keyword_analysis=keyword_analysis,
                recommendations=recommendations
            )

        except Exception as e:
            raise Exception(f"Failed to analyze SEO: {str(e)}")

    def update_workflow(self, post_id: int, workflow_data: Dict[str, Any], updated_by: str) -> ContentWorkflow:
        """Update content workflow status"""
        try:
            workflow = self.db.query(ContentWorkflow).filter(
                ContentWorkflow.post_id == post_id
            ).first()

            if not workflow:
                # Create new workflow if doesn't exist
                workflow = ContentWorkflow(post_id=post_id, **workflow_data)
                self.db.add(workflow)
            else:
                # Update existing workflow
                for key, value in workflow_data.items():
                    if hasattr(workflow, key):
                        setattr(workflow, key, value)

            workflow.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(workflow)
            return workflow

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update workflow: {str(e)}")

    def bulk_operation(self, operation_data: BulkOperationCreate, initiated_by: str) -> BulkOperation:
        """Execute bulk content operations"""
        try:
            # Create bulk operation record
            bulk_op = BulkOperation(
                operation_type=operation_data.operation_type,
                operation_data=operation_data.operation_data,
                affected_posts=operation_data.affected_posts,
                status="pending",
                initiated_by=initiated_by
            )
            self.db.add(bulk_op)
            self.db.flush()  # Get ID

            # Execute the operation
            try:
                if operation_data.operation_type == "publish":
                    self._bulk_publish(operation_data.affected_posts)
                elif operation_data.operation_type == "unpublish":
                    self._bulk_unpublish(operation_data.affected_posts)
                elif operation_data.operation_type == "delete":
                    self._bulk_delete(operation_data.affected_posts)
                elif operation_data.operation_type == "tag_update":
                    self._bulk_update_tags(operation_data.affected_posts, operation_data.operation_data)
                elif operation_data.operation_type == "section_update":
                    self._bulk_update_section(operation_data.affected_posts, operation_data.operation_data)

                bulk_op.status = "completed"
                bulk_op.completed_at = datetime.now()

            except Exception as op_error:
                bulk_op.status = "failed"
                bulk_op.error_message = str(op_error)

            self.db.commit()
            self.db.refresh(bulk_op)
            return bulk_op

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to execute bulk operation: {str(e)}")

    def get_content_analytics(self, post_id: Optional[int] = None,
                            date_from: Optional[datetime] = None,
                            date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get detailed content analytics"""
        try:
            query = self.db.query(ContentAnalytics)

            if post_id:
                query = query.filter(ContentAnalytics.post_id == post_id)

            if date_from:
                query = query.filter(ContentAnalytics.date >= date_from)

            if date_to:
                query = query.filter(ContentAnalytics.date <= date_to)

            results = query.order_by(desc(ContentAnalytics.date)).all()

            return [
                {
                    "id": r.id,
                    "post_id": r.post_id,
                    "date": r.date.isoformat(),
                    "metric_type": r.metric_type,
                    "metric_value": r.metric_value,
                    "device_type": r.device_type,
                    "referrer_type": r.referrer_type,
                    "country": r.country,
                    "source_url": r.source_url
                }
                for r in results
            ]

        except Exception as e:
            raise Exception(f"Failed to get content analytics: {str(e)}")

    # Private helper methods

    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        # Remove special characters and convert to lowercase
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_-]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while self.db.query(BlogPost).filter(BlogPost.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _calculate_readability_score(self, text: str) -> float:
        """Calculate simplified readability score"""
        if not text:
            return 0.0

        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(self._count_syllables(word) for word in text.split())

        if sentences == 0 or words == 0:
            return 0.0

        # Simplified Flesch Reading Ease formula
        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return round(max(0, min(100, score)), 1)

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        if word[0] in vowels:
            count += 1
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
        if word.endswith("e"):
            count -= 1
        if count == 0:
            count += 1
        return count

    def _calculate_seo_score(self, title: str, excerpt: str, content: str) -> float:
        """Calculate overall SEO score"""
        score = 0

        # Title optimization (30 points)
        if 30 <= len(title) <= 60:
            score += 20
        elif 20 <= len(title) <= 70:
            score += 10

        if len(title.split()) <= 10:
            score += 10

        # Meta description (20 points)
        if 120 <= len(excerpt) <= 160:
            score += 20
        elif 100 <= len(excerpt) <= 170:
            score += 10

        # Content length (25 points)
        word_count = len(content.split())
        if word_count >= 300:
            score += 25
        elif word_count >= 150:
            score += 15

        # Keyword usage (15 points)
        # This would be more sophisticated in production
        score += 15

        # Internal linking (10 points)
        # Check for links in content
        if 'href=' in content:
            score += 10

        return round(min(100, score), 1)

    def _generate_seo_suggestions(self, title: str, excerpt: str, content: str) -> List[Dict[str, Any]]:
        """Generate SEO improvement suggestions"""
        suggestions = []

        # Title suggestions
        if len(title) < 30:
            suggestions.append({
                "type": "title",
                "priority": "high",
                "message": "Title is too short. Aim for 30-60 characters.",
                "current": len(title),
                "recommended": "30-60"
            })
        elif len(title) > 60:
            suggestions.append({
                "type": "title",
                "priority": "medium",
                "message": "Title is too long. Consider shortening for better display.",
                "current": len(title),
                "recommended": "30-60"
            })

        # Meta description suggestions
        if len(excerpt) < 120:
            suggestions.append({
                "type": "meta_description",
                "priority": "high",
                "message": "Meta description is too short. Aim for 120-160 characters.",
                "current": len(excerpt),
                "recommended": "120-160"
            })

        # Content suggestions
        word_count = len(content.split())
        if word_count < 300:
            suggestions.append({
                "type": "content_length",
                "priority": "medium",
                "message": "Content is quite short. Consider expanding for better SEO.",
                "current": word_count,
                "recommended": "300+"
            })

        return suggestions

    def _analyze_keywords(self, content: str) -> Dict[str, Any]:
        """Analyze keyword usage in content"""
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}

        # Count word frequencies
        for word in words:
            if len(word) > 3:  # Skip very short words
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top keywords
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_words": len(words),
            "unique_words": len(word_freq),
            "top_keywords": [{"word": word, "count": count} for word, count in top_keywords],
            "keyword_density": {word: round(count / len(words) * 100, 2) for word, count in top_keywords[:5]}
        }

    def _generate_recommendations(self, title: str, excerpt: str, content: str) -> List[str]:
        """Generate content improvement recommendations"""
        recommendations = []

        # Check for heading structure
        if '<h2>' not in content and '<h3>' not in content:
            recommendations.append("Add subheadings (H2, H3) to improve content structure and SEO")

        # Check for images
        if '<img' not in content:
            recommendations.append("Consider adding relevant images to improve engagement")

        # Check for internal links
        if 'href=' not in content:
            recommendations.append("Add internal links to other relevant posts on your blog")

        # Check for external links
        external_links = len(re.findall(r'href=["\']https?://', content))
        if external_links == 0:
            recommendations.append("Consider adding 1-2 authoritative external links for credibility")

        # Check title for power words
        power_words = ['best', 'ultimate', 'complete', 'guide', 'tips', 'secrets', 'hacks']
        has_power_word = any(word in title.lower() for word in power_words)
        if not has_power_word:
            recommendations.append("Consider using power words in your title to increase click-through rates")

        return recommendations

    def _bulk_publish(self, post_ids: List[int]):
        """Bulk publish posts"""
        self.db.query(BlogPost).filter(
            BlogPost.id.in_(post_ids)
        ).update({"published_at": datetime.now()})

        # Update workflow status
        self.db.query(ContentWorkflow).filter(
            ContentWorkflow.post_id.in_(post_ids)
        ).update({"status": "published"})

    def _bulk_unpublish(self, post_ids: List[int]):
        """Bulk unpublish posts"""
        self.db.query(BlogPost).filter(
            BlogPost.id.in_(post_ids)
        ).update({"published_at": None})

        # Update workflow status
        self.db.query(ContentWorkflow).filter(
            ContentWorkflow.post_id.in_(post_ids)
        ).update({"status": "draft"})

    def _bulk_delete(self, post_ids: List[int]):
        """Bulk delete posts"""
        # This would include proper cleanup of related data
        self.db.query(BlogPost).filter(BlogPost.id.in_(post_ids)).delete()

    def _bulk_update_tags(self, post_ids: List[int], tag_data: Dict[str, Any]):
        """Bulk update tags"""
        action = tag_data.get('action', 'add')
        tags = tag_data.get('tags', [])

        for post_id in post_ids:
            post = self.db.query(BlogPost).filter(BlogPost.id == post_id).first()
            if post:
                current_tags = post.tags or []
                if action == 'add':
                    post.tags = list(set(current_tags + tags))
                elif action == 'remove':
                    post.tags = [tag for tag in current_tags if tag not in tags]
                elif action == 'replace':
                    post.tags = tags

    def _bulk_update_section(self, post_ids: List[int], section_data: Dict[str, Any]):
        """Bulk update section"""
        new_section = section_data.get('section')
        if new_section:
            self.db.query(BlogPost).filter(
                BlogPost.id.in_(post_ids)
            ).update({"section": new_section})