import sys
import os
import asyncio
from services.email_service import email_service

# Ensure we can import from app
sys.path.append(os.getcwd())

def test_brevo_sending():
    print("📧 Testing Brevo Email Sending...")
    
    recipient = "hello@nekwasar.com"
    subject = "NekwasaR Mailing System Test"
    content = """
    <h1>System Operational</h1>
    <p>This is a confirmation that your new Brevo integration is working correctly.</p>
    <ul>
        <li><strong>API Connection:</strong> Success</li>
        <li><strong>Sender:</strong> NekwasaR Team</li>
        <li><strong>Recipient:</strong> hello@nekwasar.com</li>
    </ul>
    <p>You are ready to send newsletters!</p>
    """
    
    try:
        success = email_service.send_transactional_email(
            to_email=recipient,
            subject=subject,
            html_content=content,
            to_name="Admin"
        )
        
        if success:
            print(f"✅ Email successfully sent to {recipient}!")
            print("   Check your inbox (and spam folder) for 'NekwasaR Mailing System Test'.")
        else:
            print("❌ Email sending failed. detailed logs should be above.")
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

if __name__ == "__main__":
    test_brevo_sending()
