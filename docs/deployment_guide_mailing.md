# Mailing System Deployment Guide

This guide details the steps to deploy the new Brevo-integrated mailing system to your server.

## 1. Prerequisites

-   **Brevo Account**: You need an active account at [Brevo (Sendinblue)](https://www.brevo.com/).
-   **API Key**: Generate an API Key from your Brevo Dashboard (Profile -> SMTP & API -> Create a new API Key).
-   **Verified Domain**: Ensure `nekwasar.com` is verified in Brevo (Senders & IP -> Domains) for better deliverability.

## 2. Environment Configuration

On your server, open your `.env` file (usually in `/home/nekwasar/Documents/asabak/BACKEND/app/.env` or similar).

Add the following lines at the end:

```bash
# ... existing config ...

# Brevo (Sendinblue) Email Configuration
BREVO_API_KEY=your_xkeysib_api_key_here
SENDER_EMAIL=hello@nekwasar.com
```

*Replace `your_xkeysib_api_key_here` with your actual API key.*

## 3. Install Dependencies

You need to install the Brevo Python SDK. Run this command in your backend directory (activate your virtual environment first if used):

```bash
# If using a virtual environment (recommended)
source venv/bin/activate
pip install sib-api-v3-sdk

# OR if running system-wide (be careful)
pip3 install sib-api-v3-sdk --break-system-packages
```

## 4. Updates Database Schema

New tables and columns have been added to support newsletter templates and automation. You must update your production database schema.

I have created a safe utility script for this. Run:

```bash
cd /home/nekwasar/Documents/asabak/BACKEND/app
# Make sure your virtual env is active
python3 update_db_schema.py
```

*Expected Output:*
```
🔄 Checking database schema...
   🔨 Ensuring base tables exist...
   Current columns in newsletter_campaigns: ...
   ➕ Adding template_id to newsletter_campaigns
   ➕ Adding customized_html to newsletter_campaigns
   ...
✅ Database schema updated successfully!
```

## 5. Deploy Code Changes

Ensure the following files are updated on your server (git pull or copy):

-   `BACKEND/app/core/config.py`: Added Brevo settings.
-   `BACKEND/app/services/email_service.py`: **[NEW]** Core email logic.
-   `BACKEND/app/models/blog.py`: Updated models.
-   `BACKEND/app/services/newsletter_service.py`: Refactored to use `EmailService`.
-   `BACKEND/app/routes/newsletter.py`: Updated subscription logic.
-   `BACKEND/app/routes/contacts.py`: Added admin notification.
-   `BACKEND/app/update_db_schema.py`: **[NEW]** Migration utility.
-   `BACKEND/app/verify_mailing_system.py`: **[NEW]** Verification utility.

## 6. Restart Application

Restart your FastAPI application to load the new environment variables and code.

```bash
# Example (adjust based on how you run your app)
sudo systemctl restart asabak-backend
# OR
pm2 restart all
```

## 7. Verification

Run the verification script to confirm everything is working live:

```bash
python3 verify_mailing_system.py
```

*Expected Output:*
```
📧 Testing Brevo Email Sending...
✅ Email successfully sent to hello@nekwasar.com!
```

## Troubleshooting

-   **"Database column does not exist"**: Run step 4 (`update_db_schema.py`) again.
-   **"Email not sent"**: Check `BREVO_API_KEY` in `.env`. Ensure your Brevo daily quota (300 emails) is not exceeded.
-   **"ModuleNotFoundError: sib_api_v3_sdk"**: Re-run step 3 (pip install).
