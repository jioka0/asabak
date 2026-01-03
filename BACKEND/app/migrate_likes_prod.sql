-- Production Migration Script for Likes System
-- Run this in your production database query tool (like pgAdmin) or via psql CLI

BEGIN;

-- 1. Remove duplicate likes (keeping the most recent one by ID usually, or just one of them)
-- This ensures the unique constraint can be applied later
DELETE FROM blog_likes a USING blog_likes b
WHERE a.id < b.id
AND a.blog_post_id = b.blog_post_id
AND a.fingerprint = b.fingerprint;

-- 2. Drop the expiration column (making likes permanent)
ALTER TABLE blog_likes DROP COLUMN IF EXISTS expires_at;

-- 3. Add unique constraint to prevent future duplicates
-- This will fail if duplicates still exist, which is why step 1 is crucial
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_blog_post_like') THEN
        ALTER TABLE blog_likes 
        ADD CONSTRAINT uq_blog_post_like UNIQUE (blog_post_id, fingerprint);
    END IF;
END $$;

COMMIT;
