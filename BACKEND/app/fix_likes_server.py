import os
import sys
import logging
from sqlalchemy import text

# Ensure we can import from app directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the configured engine from the application
try:
    from database import engine
    print(f"🔌 Using database engine configured in app...")
except ImportError:
    print("⚠️ Could not import engine from database.py.")
    print("   Please ensure you are running this script from the BACKEND/app directory.")
    sys.exit(1)

def fix_likes_table():
    print("🚀 Starting SERVER MIGRATION for blog_likes table...")
    
    with engine.connect() as connection:
        trans = connection.begin()
        try:
            # 1. Clean up duplicate likes
            print("Cleaning up duplicates...")
            # Keep the one with the highest ID (latest)
            deduplicate_sql = text("""
                DELETE FROM blog_likes a USING blog_likes b
                WHERE a.id < b.id
                AND a.blog_post_id = b.blog_post_id
                AND a.fingerprint = b.fingerprint;
            """)
            connection.execute(deduplicate_sql)
            print("✅ Duplicates removed.")

            # 2. Drop expires_at column
            print("Dropping expires_at column...")
            drop_column_sql = text("""
                ALTER TABLE blog_likes DROP COLUMN IF EXISTS expires_at;
            """)
            connection.execute(drop_column_sql)
            print("✅ expires_at column dropped.")

            # 3. Add unique constraint (safely)
            print("Adding unique constraint...")
            try:
                add_constraint_sql = text("""
                    ALTER TABLE blog_likes 
                    ADD CONSTRAINT uq_blog_post_like UNIQUE (blog_post_id, fingerprint);
                """)
                connection.execute(add_constraint_sql)
                print("✅ Unique constraint added.")
            except Exception as e:
                if "already exists" in str(e):
                    print("ℹ️ Constraint already exists. Skipping.")
                else:
                    print(f"⚠️ Note on constraint: {e}")
                
            trans.commit()
            print("✨ MIGRATION SUCCESSFUL!")
            
        except Exception as e:
            trans.rollback()
            print(f"❌ MIGRATION FAILED: {e}")
            raise e

if __name__ == "__main__":
    # Ensure we have DB connection info
    if not os.getenv("DATABASE_URL"):
        print("⚠️ WARNING: DATABASE_URL not found in environment.")
        print("   Make sure your .env file is present or env vars are set.")
    
    fix_likes_table()
