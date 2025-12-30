from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from services.newsletter_service import NewsletterService
from database import get_db
from sqlalchemy.orm import Session
from models.blog import BlogLike, TemporalUser as TemporalUserModel, BlogPost as BlogPostModel
from sqlalchemy import func
import asyncio

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

async def cleanup_expired_data_job():
    """Scheduled job to cleanup expired likes and temporal users daily at 2 AM"""
    try:
        # Get database session
        db = next(get_db())
        
        # Cleanup expired likes
        try:
            # Get expired likes grouped by post for count updates
            expired_likes = db.query(BlogLike).filter(
                BlogLike.expires_at <= func.now()
            ).all()
            
            # Group by post_id to update counts efficiently
            post_like_counts = {}
            for like in expired_likes:
                if like.blog_post_id not in post_like_counts:
                    post_like_counts[like.blog_post_id] = 0
                post_like_counts[like.blog_post_id] += 1
            
            # Delete expired likes
            db.query(BlogLike).filter(
                BlogLike.expires_at <= func.now()
            ).delete()
            
            # Update like counts for affected posts
            for post_id, like_count in post_like_counts.items():
                post = db.query(BlogPostModel).filter(BlogPostModel.id == post_id).first()
                if post and post.like_count >= like_count:
                    post.like_count -= like_count
            
            print(f"Cleaned up {len(expired_likes)} expired likes")
            
        except Exception as e:
            print(f"Expired likes cleanup failed: {e}")
        
        # Cleanup expired temporal users
        try:
            expired_count = db.query(TemporalUserModel).filter(
                TemporalUserModel.expires_at <= func.now()
            ).delete()
            print(f"Cleaned up {expired_count} expired temporal users")
            
        except Exception as e:
            print(f"Expired temporal users cleanup failed: {e}")
        
        db.commit()
        
    except Exception as e:
        print(f"Cleanup job failed: {e}")
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
    
    # Schedule daily cleanup of expired likes and temporal users at 2:00 AM
    scheduler.add_job(
        cleanup_expired_data_job,
        trigger=CronTrigger(hour=2, minute=0),
        id='cleanup_expired_data',
        name='Cleanup Expired Likes and Users',
        replace_existing=True
    )

    print("Scheduler initialized:")
    print("- Weekly newsletter scheduled for every Monday at 9 AM")
    print("- Daily cleanup scheduled for every day at 2 AM")

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