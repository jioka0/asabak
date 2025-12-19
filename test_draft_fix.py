#!/usr/bin/env python3
"""
Test script to verify the draft counting fix
"""

import requests
import json
from datetime import datetime

def test_draft_counting():
    """Test that drafts are correctly counted in the blog posts API"""
    
    # Configuration
    BASE_URL = "http://127.0.0.1:8000"
    
    # First, let's check if we have any existing posts
    print("🔍 Checking existing blog posts...")
    
    try:
        # Try to get blog posts (this will likely fail without authentication)
        response = requests.get(f"{BASE_URL}/admin/api/blog/posts")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Successfully retrieved blog posts")
            print(f"📊 Stats: {json.dumps(data.get('stats', {}), indent=2)}")
            
            # Check if draft count is working
            stats = data.get('stats', {})
            total_posts = stats.get('totalPosts', 0)
            published_count = stats.get('publishedCount', 0)
            draft_count = stats.get('draftCount', 0)
            
            print(f"📈 Total posts: {total_posts}")
            print(f"📰 Published posts: {published_count}")
            print(f"📝 Draft posts: {draft_count}")
            
            # Verify the counts make sense
            if total_posts == published_count + draft_count:
                print("✅ Counts are consistent!")
            else:
                print("❌ Counts are inconsistent!")
                print(f"   Expected: {total_posts} = {published_count} + {draft_count}")
                print(f"   Actual: {total_posts} ≠ {published_count + draft_count}")
            
            # Show some posts to verify status
            posts = data.get('posts', [])
            if posts:
                print(f"\n📋 Sample posts:")
                for i, post in enumerate(posts[:5]):  # Show first 5 posts
                    status = post.get('status', 'unknown')
                    title = post.get('title', 'Untitled')
                    published_at = post.get('published_at', None)
                    print(f"   {i+1}. {title[:30]}... - Status: {status} - Published: {published_at is not None}")
        else:
            print(f"⚠️ Could not retrieve blog posts: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error testing draft counting: {e}")

if __name__ == "__main__":
    print("🧪 Testing draft counting fix...")
    print("=" * 50)
    test_draft_counting()
    print("=" * 50)
    print("🎯 Test completed!")