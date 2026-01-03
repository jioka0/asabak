from fastapi import APIRouter, Depends, HTTPException, Form, Request, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from services.newsletter_service import NewsletterService
from schemas.blog import NewsletterSubscriberCreate, NewsletterCampaignCreate
from typing import Optional

router = APIRouter()

# Admin endpoints
@router.get("/admin/subscribers")
async def get_all_subscribers(db: Session = Depends(get_db)):
    """Get all newsletter subscribers (admin only)"""
    try:
        from models.blog import NewsletterSubscriber
        
        subscribers = db.query(NewsletterSubscriber).order_by(NewsletterSubscriber.subscribed_at.desc()).all()
        
        return {
            "success": True,
            "subscribers": [
                {
                    "id": sub.id,
                    "name": sub.name,
                    "email": sub.email,
                    "is_active": sub.is_active,
                    "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
                    "unsubscribed_at": sub.unsubscribed_at.isoformat() if sub.unsubscribed_at else None,
                }
                for sub in subscribers
            ]
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get subscribers: {str(e)}")

@router.delete("/admin/subscribers/{subscriber_id}")
async def delete_subscriber(subscriber_id: int, db: Session = Depends(get_db)):
    """Delete a subscriber (admin only)"""
    try:
        from models.blog import NewsletterSubscriber
        
        subscriber = db.query(NewsletterSubscriber).filter(NewsletterSubscriber.id == subscriber_id).first()
        if not subscriber:
            raise HTTPException(404, "Subscriber not found")
        
        db.delete(subscriber)
        db.commit()
        
        return {
            "success": True,
            "message": "Subscriber deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Failed to delete subscriber: {str(e)}")


@router.post("/subscribe")
async def subscribe_newsletter(
    request: Request,
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Subscribe to newsletter - immediate activation, welcome email sent"""
    try:
        newsletter_service = NewsletterService(db)

        subscriber_data = NewsletterSubscriberCreate(
            name=name,
            email=email,
            preferences={}  # Can be extended later
        )

        result = await newsletter_service.subscribe_user(subscriber_data, background_tasks)

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "subscriber_id": result["subscriber_id"]
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "subscriber_id": result.get("subscriber_id")
            }

    except Exception as e:
        raise HTTPException(500, f"Subscription failed: {str(e)}")

@router.post("/unsubscribe")
async def unsubscribe_newsletter(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """Unsubscribe from newsletter"""
    try:
        newsletter_service = NewsletterService(db)
        result = await newsletter_service.unsubscribe_user(email)

        return {
            "success": result["success"],
            "message": result["message"]
        }

    except Exception as e:
        raise HTTPException(500, f"Unsubscription failed: {str(e)}")

@router.get("/unsubscribe")
async def unsubscribe_via_link(
    email: str,
    db: Session = Depends(get_db)
):
    """Unsubscribe via link in newsletter (returns HTML page)"""
    try:
        newsletter_service = NewsletterService(db)
        result = await newsletter_service.unsubscribe_user(email)

        # Return HTML response
        if result["success"]:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Unsubscribed - NekwasaR Blog</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #28a745; }}
                    .message {{ font-size: 18px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1 class="success">✓ Successfully Unsubscribed</h1>
                <p class="message">{result["message"]}</p>
                <p>We're sorry to see you go. You can always subscribe again if you change your mind.</p>
                <a href="https://nekwasar.com/blog">Visit Our Blog</a>
            </body>
            </html>
            """
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Unsubscribe - NekwasaR Blog</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #dc3545; }}
                    .message {{ font-size: 18px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <h1 class="error">Unsubscribe Failed</h1>
                <p class="message">{result["message"]}</p>
                <a href="https://nekwasar.com/blog">Visit Our Blog</a>
            </body>
            </html>
            """

        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - NekwasaR Blog</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <h1 class="error">Error</h1>
            <p>Something went wrong. Please try again later.</p>
            <a href="https://nekwasar.com/blog">Visit Our Blog</a>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=error_html, status_code=500)

@router.post("/admin/send-weekly")
async def send_weekly_newsletter(db: Session = Depends(get_db)):
    """Manually trigger weekly newsletter (admin only)"""
    try:
        newsletter_service = NewsletterService(db)
        result = await newsletter_service.send_weekly_newsletter()

        return {
            "success": result["success"],
            "message": result["message"],
            "sent_count": result["sent_count"],
            "failed_count": result.get("failed_count", 0),
            "campaign_id": result.get("campaign_id")
        }

    except Exception as e:
        raise HTTPException(500, f"Weekly newsletter failed: {str(e)}")

@router.post("/admin/campaigns")
async def create_campaign(
    subject: str = Form(...),
    content: str = Form(...),
    template_type: str = Form("custom"),
    scheduled_at: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Create newsletter campaign (admin only)"""
    try:
        from datetime import datetime

        campaign_data = NewsletterCampaignCreate(
            subject=subject,
            content=content,
            template_type=template_type,
            scheduled_at=datetime.fromisoformat(scheduled_at) if scheduled_at else None
        )

        newsletter_service = NewsletterService(db)
        campaign = await newsletter_service.create_campaign(campaign_data)

        return {
            "success": True,
            "message": "Campaign created successfully",
            "campaign_id": campaign.id
        }

    except Exception as e:
        raise HTTPException(500, f"Campaign creation failed: {str(e)}")

@router.get("/stats")
async def get_newsletter_stats(db: Session = Depends(get_db)):
    """Get newsletter statistics"""
    try:
        newsletter_service = NewsletterService(db)
        stats = newsletter_service.get_subscriber_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get stats: {str(e)}")

@router.get("/test-email")
async def test_email(
    email: str,
    db: Session = Depends(get_db)
):
    """Test email sending (development only)"""
    try:
        newsletter_service = NewsletterService(db)

        # Create test subscriber
        test_subscriber = type('TestSubscriber', (), {
            'name': 'Test User',
            'email': email
        })()

        # Send test welcome email
        await newsletter_service._send_welcome_email(test_subscriber)

        return {
            "success": True,
            "message": f"Test email sent to {email}"
        }

    except Exception as e:
        raise HTTPException(500, f"Test email failed: {str(e)}")