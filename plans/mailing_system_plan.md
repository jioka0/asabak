# mailing_system_plan.md

## Overview

This plan outlines the implementation of a comprehensive mailing system for "NekwasaR" using the Brevo (Sendinblue) API. The system will handle transactional emails, newsletter management, and inbox management, tailored for the **Brevo Free Plan (300 emails/day limit)**.

## Current State

-   **Backend**: 
    -   Models: `NewsletterSubscriber`, `NewsletterCampaign`.
    -   Services: `NewsletterService` (needs update), `contacts_router`.
-   **Frontend (Admin)**:
    -   `admin_newsletter_subscribers.html`: Functional UI for managing lists.
    -   `admin_newsletter_campaigns.html`: UI for campaign listing & management.
    -   `admin_newsletter_templates.html`: UI for template management (needs backend).
    -   `admin_newsletter_automation.html`: UI for workflows (needs backend).
    -   `admin_newsletter_analytics.html`: UI for stats (needs backend).
-   **Infrastructure**: Brevo API Key provided. Domain `nekwasar.com`.

## Phase 1: Core Configuration & Service Layer

### 1.1 Environment & Limits
-   **Action**: Add Brevo credentials to `.env`.
-   **Action**: Implement `QuotaService` to track daily sends vs the 300 limit.
    -   Check quota before sending.
    -   Queue emails if over quota (for the next day).

### 1.2 Brevo Integration
-   **Action**: Install `sib-api-v3-sdk`.
-   **Action**: Create `services/email_service.py`.
    -   `send_transactional_email(to, subject, html_content)`
    -   `send_batch_email(to_list, subject, html_content)`: Handles batching (e.g., 50 at a time) to respect rate limits.

### 1.3 Database Updates
-   **Model**: `NewsletterTemplate`
    -   `id`, `name`, `html_content` (the raw HTML code), `category`, `thumbnail_url`.
-   **Model**: `NewsletterCampaign`
    -   Add `template_id` (foreign key), `customized_html` (final HTML for this campaign).
-   **Model**: `NewsletterAutomation`
    -   `trigger_type` (e.g., 'welcome', 'abandoned_cart'), `email_template_id`, `delay_hours`, `is_active`.

## Phase 2: Template Management System (User Priority)

### 2.1 Template Backend
-   **Endpoint**: `POST /api/newsletter/templates` - Save raw HTML code from the "Paste Code" UI.
-   **Endpoint**: `GET /api/newsletter/templates` - List all templates.
-   **Endpoint**: `GET /api/newsletter/templates/{id}` - Retrieve code for editing.

### 2.2 Template Admin UI (`admin_newsletter_templates.html`)
-   **Feature**: "Create Template" -> "Paste Code".
    -   User pastes their HTML/CSS.
    -   System saves it as a reusable `NewsletterTemplate`.
-   **Feature**: Preview Mode.
    -   Render the saved HTML in an iframe or modal within the admin.

## Phase 3: Campaign System & Sending

### 3.1 Campaign Creation Flow (`admin_newsletter_campaigns.html`)
1.  **Create**: User names campaign, selects a `NewsletterTemplate`.
2.  **Edit**: The system loads `NewsletterTemplate.html_content` into the editor. Use an HTML editor (like existing textarea or a rich text editor) to modify text/images for *this specific campaign*.
3.  **Save**: Store the result in `NewsletterCampaign.customized_html`.
4.  **Send/Schedule**:
    -   **Immediate**: Trigger background task.
    -   **Scheduled**: Save `scheduled_at`. `apscheduler` picks it up.

### 3.2 Smart Throttling (Free Plan Logic)
-   **Logic**: If a campaign has 500 recipients:
    -   Send 300 immediately.
    -   Queue the remaining 200 for 24 hours later.
    -   Notify admin: "Campaign queued: 300 sent, 200 pending due to quota."

## Phase 4: Automation Workflows (`admin_newsletter_automation.html`)

### 4.1 Fixed Recipes (MVP)
Since a full drag-and-drop builder is complex, we will implement "Fixed Recipes" mapped to the existing UI cards:
1.  **Welcome Series**: Triggered on `subscribe`.
2.  **Contact Form Auto-reply**: Triggered on `contact_form_submit`.

### 4.2 Implementation
-   **Trigger**: When an event occurs (e.g., user subscribes), check `NewsletterAutomation` table for active rules.
-   **Action**: Schedule the email using the `delay_hours` setting.

## Phase 5: Analytics & Reporting (`admin_newsletter_analytics.html`)

### 5.1 Telemetry
-   **Brevo Webhooks**: Configure webhooks to hit `/api/webhooks/brevo`.
    -   Events: `delivered`, `opened`, `clicked`, `bounced`.
-   **Storage**: Update `NewsletterCampaign` stats (`opens`, `clicks`) and `NewsletterSubscriber` history.

### 5.2 Analytics Dashboard
-   **API**: `GET /api/newsletter/analytics`
    -   Returns aggregate data (Open Rate, Click Rate) derived from the webhook data.
-   **UI**: Populate the charts in `admin_newsletter_analytics.html` with this real data.

## Execution Steps

1.  **Dependencies**: Install `sib-api-v3-sdk`.
2.  **DB Migration**: Add `NewsletterTemplate` and `NewsletterAutomation` models.
3.  **Service**: Implement `EmailService` with Brevo and Quota management.
4.  **Templates**: Build Template CRUD API & wire up Admin UI.
5.  **Campaigns**: Build Campaign creation flow (Template -> Edit -> Send) & wire up Admin UI.
6.  **Automation**: Implement the "Welcome" workflow backend.
7.  **Analytics**: Set up Webhook listener and Analytics API.
