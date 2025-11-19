from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.app.services.newsletter_service import NewsletterService
from backend.app.database import get_db
from sqlalchemy.orm import Session
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

    print("Newsletter scheduler initialized - Weekly newsletter scheduled for every Monday at 9 AM")

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