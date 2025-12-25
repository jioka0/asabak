from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from services.newsletter_service import NewsletterService
from database import get_db
from sqlalchemy.orm import Session
from models.blog import BlogPost
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def send_weekly_newsletter_job():
    """Scheduled job to send weekly newsletter every Monday at 9 AM"""
    try:
        # Get database session
        db = next(get_db())

        # Create newsletter service and send
        newsletter_service = NewsletterService(db)
        result = await newsletter_service.send_weekly_newsletter()

        print(f"Weekly newsletter sent: {result}")

    except Exception as e:
        print(f"Weekly newsletter job failed: {e}")
    finally:
        db.close()

async def publish_scheduled_posts_job():
    """Check for scheduled posts that are ready to be published"""
    try:
        # Get database session
        db = next(get_db())

        # Get current time
        now = datetime.utcnow()

        # Find scheduled posts that are due
        scheduled_posts = db.query(BlogPost).filter(
            BlogPost.status == 'scheduled',
            BlogPost.scheduled_at <= now
        ).all()

        published_count = 0
        for post in scheduled_posts:
            logger.info(f"🚀 PUBLISHING SCHEDULED POST: '{post.title}' (ID: {post.id})")

            # Update post status to published and set published_at
            post.status = 'published'
            post.published_at = now
            post.scheduled_at = None  # Clear the scheduled time
            post.scheduled_timezone = None

            published_count += 1

        if published_count > 0:
            db.commit()
            logger.info(f"✅ Published {published_count} scheduled posts")
        else:
            logger.debug("No scheduled posts ready for publication")

    except Exception as e:
        logger.error(f"❌ Publish scheduled posts job failed: {e}")
        db.rollback()
    finally:
        db.close()

def init_scheduler():
    """Initialize the scheduler with jobs"""
    # Schedule weekly newsletter for every Monday at 9:00 AM
    scheduler.add_job(
        send_weekly_newsletter_job,
        trigger=CronTrigger(day_of_week='mon', hour=9),
        id='weekly_newsletter',
        name='Send Weekly Newsletter',
        replace_existing=True
    )

    # Schedule post publishing check every minute
    scheduler.add_job(
        publish_scheduled_posts_job,
        trigger=IntervalTrigger(minutes=1),
        id='publish_scheduled_posts',
        name='Publish Scheduled Posts',
        replace_existing=True
    )

    print("Scheduler initialized - Weekly newsletter scheduled for every Monday at 9 AM")
    print("Scheduler initialized - Scheduled posts will be checked every minute")

def start_scheduler():
    """Start the scheduler"""
    if not scheduler.running:
        scheduler.start()
        print("Newsletter scheduler started")

def stop_scheduler():
    """Stop the scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        print("Newsletter scheduler stopped")

# For testing - send newsletter immediately
async def send_newsletter_now():
    """Manually trigger newsletter sending for testing"""
    await send_weekly_newsletter_job()

if __name__ == "__main__":
    # For testing the scheduler
    import asyncio
    asyncio.run(send_newsletter_now())