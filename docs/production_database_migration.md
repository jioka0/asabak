# Production Database Migration Guide: Likes System Update

This guide provides step-by-step instructions for updating your production database to support the new "Permanent Likes" system using a database management tool (Option 2).

## ⚠️ Important Warning
Before running any database migration, it is highly recommended to **backup your database** if possible.

## The Migration Script
Copy the following SQL code. This script will:
1.  Remove duplicate likes (cleaning up the data).
2.  Remove the `expires_at` column (making likes permanent).
3.  Add a constraint to ensure a user can only like a post once.

```sql
BEGIN;

-- 1. Remove duplicate likes
-- Keep only one entry per user/device per post
DELETE FROM blog_likes a USING blog_likes b
WHERE a.id < b.id
AND a.blog_post_id = b.blog_post_id
AND a.fingerprint = b.fingerprint;

-- 2. Drop the expiration column
ALTER TABLE blog_likes DROP COLUMN IF EXISTS expires_at;

-- 3. Add unique constraint
-- This prevents future duplicates
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_blog_post_like') THEN
        ALTER TABLE blog_likes 
        ADD CONSTRAINT uq_blog_post_like UNIQUE (blog_post_id, fingerprint);
    END IF;
END $$;

COMMIT;
```

---

## Instructions for Specific Tools

### 🐘 Using pgAdmin

1.  **Log in** to your pgAdmin interface.
2.  In the browser tree on the left, navigate to your server and **find your production database** (e.g., `nekwasar_platform`).
3.  **Right-click** on the database name.
4.  Select **Query Tool** from the context menu.
5.  **Paste** the SQL script from above into the Query Editor window.
6.  Click the **Execute/Play button** (▶️) in the toolbar (or press `F5`).
7.  Check the "Messages" tab at the bottom. It should say "Query returned successfully" or "COMMIT".

### 🦫 Using DBeaver

1.  Open DBeaver and connect to your production database.
2.  **Right-click** on your database connection in the Database Navigator.
3.  Select **SQL Editor** -> **Open SQL Script**.
4.  **Paste** the SQL script into the editor.
5.  Select the entire script (Ctrl+A / Cmd+A).
6.  Click the **Execute SQL Script** button (the orange/play icon usually, or `Alt+X`).
7.  Verify in the Output tab that the transaction was committed.

### 🔌 Using TablePlus

1.  Open TablePlus and connect to your production database.
2.  Click on the **SQL** icon in the top toolbar (or press `Cmd+E` / `Ctrl+E`).
3.  **Paste** the SQL script into the editor.
4.  Click the **Run Current** or **Run All** button.
5.  Ensure the console at the bottom shows "Success".

---

## 🚨 CRITICAL FINAL STEP: Restart Your Server

After the database migration is complete, you **MUST** restart your backend application on the server. The running code currently expects the `expires_at` column to exist; if you don't restart it, users will see "Internal Server Error" when they try to like a post.

**If you use systemd (typical for Linux servers):**
```bash
sudo systemctl restart asabak-backend
# OR
sudo systemctl restart gunicorn
```

**If you use PM2 (Node/Python process manager):**
```bash
pm2 restart asabak-backend
```

**If you use Docker:**
```bash
docker-compose restart backend
```
