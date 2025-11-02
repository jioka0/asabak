import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template

from models.blog import NewsletterSubscriber, NewsletterCampaign, BlogPost
from schemas.blog import NewsletterSubscriberCreate, NewsletterCampaignCreate

class NewsletterService:
    def __init__(self, db: Session):
        self.db = db
        self.mail_config = ConnectionConfig(
            MAIL_USERNAME=os.getenv("SMTP_USERNAME"),
            MAIL_PASSWORD=os.getenv("SMTP_PASSWORD"),
            MAIL_FROM=os.getenv("FROM_EMAIL"),
            MAIL_PORT=int(os.getenv("SMTP_PORT", 465)),
            MAIL_SERVER=os.getenv("SMTP_SERVER"),
            MAIL_SSL=True,  # Using SSL for port 465
            MAIL_TLS=False,
            USE_CREDENTIALS=True
        )
        self.fm = FastMail(self.mail_config)

    async def subscribe_user(self, subscriber_data: NewsletterSubscriberCreate) -> Dict[str, Any]:
        """Subscribe a user and send welcome email immediately"""
        try:
            # Check if already subscribed
            existing = self.db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.email == subscriber_data.email,
                NewsletterSubscriber.is_active == True
            ).first()

            if existing:
                return {
                    "success": False,
                    "message": "You're already subscribed to our newsletter!",
                    "subscriber_id": existing.id
                }

            # Create new subscriber
            subscriber = NewsletterSubscriber(
                name=subscriber_data.name,
                email=subscriber_data.email,
                preferences=subscriber_data.preferences or {},
                is_active=True
            )

            self.db.add(subscriber)
            self.db.commit()
            self.db.refresh(subscriber)

            # Send welcome email immediately
            await self._send_welcome_email(subscriber)

            return {
                "success": True,
                "message": "Successfully subscribed! Check your email for a welcome message.",
                "subscriber_id": subscriber.id
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Subscription failed: {str(e)}")

    async def unsubscribe_user(self, email: str) -> Dict[str, Any]:
        """Unsubscribe a user"""
        try:
            subscriber = self.db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.email == email,
                NewsletterSubscriber.is_active == True
            ).first()

            if not subscriber:
                return {"success": False, "message": "Email not found in our subscriber list."}

            subscriber.is_active = False
            self.db.commit()

            return {"success": True, "message": "Successfully unsubscribed from our newsletter."}

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Unsubscription failed: {str(e)}")

    async def send_weekly_newsletter(self) -> Dict[str, Any]:
        """Send weekly newsletter to all active subscribers"""
        try:
            # Get active subscribers
            subscribers = self.db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.is_active == True
            ).all()

            if not subscribers:
                return {"success": True, "message": "No active subscribers found.", "sent_count": 0}

            # Get weekly content
            weekly_content = self._get_weekly_content()

            # Create campaign record
            campaign = NewsletterCampaign(
                subject=f"Weekly Update - {datetime.now().strftime('%B %d, %Y')}",
                content=weekly_content,
                template_type="weekly",
                status="sent",
                sent_at=datetime.now(),
                recipient_count=len(subscribers)
            )

            self.db.add(campaign)
            self.db.commit()

            # Send to all subscribers
            sent_count = 0
            failed_count = 0

            for subscriber in subscribers:
                try:
                    await self._send_newsletter_email(subscriber, weekly_content, campaign.subject)
                    sent_count += 1
                except Exception as e:
                    print(f"Failed to send to {subscriber.email}: {e}")
                    failed_count += 1

            return {
                "success": True,
                "message": f"Weekly newsletter sent to {sent_count} subscribers.",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "campaign_id": campaign.id
            }

        except Exception as e:
            self.db.rollback()
            raise Exception(f"Weekly newsletter failed: {str(e)}")

    async def create_campaign(self, campaign_data: NewsletterCampaignCreate) -> NewsletterCampaign:
        """Create a newsletter campaign"""
        try:
            campaign = NewsletterCampaign(**campaign_data.dict())
            self.db.add(campaign)
            self.db.commit()
            self.db.refresh(campaign)
            return campaign
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Campaign creation failed: {str(e)}")

    def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get newsletter subscriber statistics"""
        try:
            total = self.db.query(NewsletterSubscriber).count()
            active = self.db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.is_active == True
            ).count()

            # Get recent subscriptions (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent = self.db.query(NewsletterSubscriber).filter(
                NewsletterSubscriber.subscribed_at >= thirty_days_ago
            ).count()

            return {
                "total_subscribers": total,
                "active_subscribers": active,
                "inactive_subscribers": total - active,
                "recent_subscriptions": recent
            }
        except Exception as e:
            raise Exception(f"Failed to get subscriber stats: {str(e)}")

    async def _send_welcome_email(self, subscriber: NewsletterSubscriber):
        """Send welcome email to new subscriber"""
        subject = "Welcome to NekwasaR Blog! 🎉"

        content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333; text-align: center;">Welcome to NekwasaR Blog! 🎉</h1>

            <p style="font-size: 16px; line-height: 1.6;">Hi {subscriber.name},</p>

            <p style="font-size: 16px; line-height: 1.6;">
                Thank you for subscribing to our newsletter! You'll receive weekly updates featuring:
            </p>

            <ul style="font-size: 16px; line-height: 1.8;">
                <li>Latest insights on AI and technology</li>
                <li>Startup success stories and innovation trends</li>
                <li>Exclusive content and tutorials</li>
                <li>Industry news and analysis</li>
            </ul>

            <p style="font-size: 16px; line-height: 1.6;">
                Our first newsletter will arrive in your inbox soon!
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://nekwasar.com/blog"
                   style="background-color: #007bff; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Visit Our Blog
                </a>
            </div>

            <p style="font-size: 14px; color: #666; text-align: center;">
                You're receiving this because you subscribed to NekwasaR Blog.<br>
                <a href="#" style="color: #666;">Unsubscribe</a> anytime.
            </p>

            <p style="font-size: 14px; color: #666; text-align: center; margin-top: 20px;">
                Best regards,<br>
                <strong>NekwasaR</strong>
            </p>
        </div>
        """

        message = MessageSchema(
            subject=subject,
            recipients=[subscriber.email],
            body=content,
            subtype="html"
        )

        await self.fm.send_message(message)

    async def _send_newsletter_email(self, subscriber: NewsletterSubscriber, content: str, subject: str):
        """Send newsletter email to subscriber"""
        # Add unsubscribe link to content
        unsubscribe_url = f"https://nekwasar.com/api/newsletter/unsubscribe?email={subscriber.email}"

        full_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            {content}

            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">

            <p style="font-size: 12px; color: #666; text-align: center;">
                You're receiving this newsletter because you subscribed to NekwasaR Blog.<br>
                <a href="{unsubscribe_url}" style="color: #666;">Unsubscribe</a> from future emails.
            </p>
        </div>
        """

        message = MessageSchema(
            subject=subject,
            recipients=[subscriber.email],
            body=full_content,
            subtype="html"
        )

        await self.fm.send_message(message)

    def _get_weekly_content(self) -> str:
        """Generate weekly newsletter content from recent posts"""
        try:
            # Get recent posts from the last week
            week_ago = datetime.now() - timedelta(days=7)
            recent_posts = self.db.query(BlogPost).filter(
                BlogPost.published_at >= week_ago,
                BlogPost.is_featured == True
            ).order_by(BlogPost.published_at.desc()).limit(5).all()

            if not recent_posts:
                # Fallback to any recent posts
                recent_posts = self.db.query(BlogPost).filter(
                    BlogPost.published_at >= week_ago
                ).order_by(BlogPost.published_at.desc()).limit(5).all()

            # Build newsletter content
            content_parts = []

            if recent_posts:
                content_parts.append("<h2>This Week's Highlights</h2>")
                for post in recent_posts:
                    content_parts.append(f"""
                    <div style="margin-bottom: 20px; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa;">
                        <h3 style="margin: 0 0 10px 0;">
                            <a href="https://nekwasar.com/blog/{post.slug}"
                               style="color: #007bff; text-decoration: none;">
                                {post.title}
                            </a>
                        </h3>
                        <p style="margin: 0; color: #666; font-size: 14px;">
                            {post.excerpt[:150] + '...' if post.excerpt and len(post.excerpt) > 150 else post.excerpt or 'Read more...'}
                        </p>
                    </div>
                    """)
            else:
                content_parts.append("""
                <h2>This Week's Highlights</h2>
                <p>We're working on some exciting new content! Stay tuned for our next update.</p>
                """)

            # Add footer content
            content_parts.append("""
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://nekwasar.com/blog"
                   style="background-color: #007bff; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 5px; font-weight: bold;">
                    Visit Our Blog
                </a>
            </div>

            <p style="text-align: center; color: #666;">
                Follow us for daily updates:<br>
                <a href="https://twitter.com/nekwasar" style="color: #007bff;">Twitter</a> |
                <a href="https://linkedin.com/in/nekwasar" style="color: #007bff;">LinkedIn</a> |
                <a href="https://github.com/nekwasar" style="color: #007bff;">GitHub</a>
            </p>
            """)

            return "\n".join(content_parts)

        except Exception as e:
            # Fallback content if database query fails
            return """
            <h2>Weekly Update from NekwasaR</h2>
            <p>Thank you for being part of our community! We're working on some exciting new content and insights.</p>
            <p>Check back soon for our latest posts on technology, AI, and innovation.</p>
            """