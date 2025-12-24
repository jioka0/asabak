#!/usr/bin/env python3

"""
Test script for comment like functionality
"""

import sys
import os

# Add the backend app to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'BACKEND', 'app'))

from fastapi.testclient import TestClient
from main import app
from database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_comment_likes.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_comment_like_functionality():
    """Test the complete comment like functionality"""
    
    print("🧪 Testing Comment Like Functionality")
    print("=" * 50)
    
    # First, create a test blog post
    post_data = {
        "title": "Test Post",
        "content": "This is a test post for comment likes",
        "excerpt": "Test excerpt",
        "author": "Test Author",
        "template_type": "banner_text",
        "section": "latest",
        "slug": "test-post"
    }
    
    response = client.post("/api/blogs/", json=post_data)
    assert response.status_code == 200
    post = response.json()
    post_id = post["id"]
    print(f"✅ Created test post with ID: {post_id}")
    
    # Create a test comment
    comment_data = {
        "author_name": "Test User",
        "author_email": "test@example.com",
        "content": "This is a test comment",
        "parent_id": None
    }
    
    response = client.post(f"/api/blogs/{post_id}/comments", json=comment_data)
    assert response.status_code == 200
    comment = response.json()
    comment_id = comment["id"]
    print(f"✅ Created test comment with ID: {comment_id}")
    
    # Test 1: Like a comment
    print("\n📝 Test 1: Like a comment")
    user_identifier = "test_user_123"
    
    response = client.post(f"/api/blogs/comments/{comment_id}/likes", json={"user_identifier": user_identifier})
    assert response.status_code == 200
    result = response.json()
    
    assert result["liked"] == True
    assert result["like_count"] == 1
    print(f"✅ Comment liked successfully. Like count: {result['like_count']}")
    
    # Test 2: Try to like the same comment again (should return already liked)
    print("\n📝 Test 2: Like same comment again")
    
    response = client.post(f"/api/blogs/comments/{comment_id}/likes", json={"user_identifier": user_identifier})
    assert response.status_code == 200
    result = response.json()
    
    assert result["liked"] == True
    assert result["like_count"] == 1  # Should still be 1
    print(f"✅ Second like attempt handled correctly. Like count: {result['like_count']}")
    
    # Test 3: Unlike the comment
    print("\n📝 Test 3: Unlike the comment")
    
    response = client.delete(f"/api/blogs/comments/{comment_id}/likes?user_identifier={user_identifier}")
    assert response.status_code == 200
    result = response.json()
    
    assert result["unliked"] == True
    assert result["like_count"] == 0
    print(f"✅ Comment unliked successfully. Like count: {result['like_count']}")
    
    # Test 4: Check like status
    print("\n📝 Test 4: Check like status")
    
    response = client.get(f"/api/blogs/comments/{comment_id}/likes/status?user_identifier={user_identifier}")
    assert response.status_code == 200
    result = response.json()
    
    assert result["liked"] == False
    print(f"✅ Like status check correct. Liked: {result['liked']}")
    
    # Test 5: Like with different user
    print("\n📝 Test 5: Like with different user")
    user_identifier_2 = "test_user_456"
    
    response = client.post(f"/api/blogs/comments/{comment_id}/likes", json={"user_identifier": user_identifier_2})
    assert response.status_code == 200
    result = response.json()
    
    assert result["liked"] == True
    assert result["like_count"] == 1
    print(f"✅ Different user liked comment. Like count: {result['like_count']}")
    
    # Test 6: Get comments tree with like counts
    print("\n📝 Test 6: Get comments tree with like counts")
    
    response = client.get(f"/api/blogs/{post_id}/comments-tree")
    assert response.status_code == 200
    result = response.json()
    
    assert len(result["comments"]) == 1
    comment_data = result["comments"][0]
    assert comment_data["id"] == comment_id
    assert comment_data["like_count"] == 1
    print(f"✅ Comments tree includes like count. Like count: {comment_data['like_count']}")
    
    # Test 7: Invalid comment ID
    print("\n📝 Test 7: Invalid comment ID")
    
    response = client.post("/api/blogs/comments/99999/likes", json={"user_identifier": user_identifier})
    assert response.status_code == 404
    print("✅ Invalid comment ID handled correctly")
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Comment like functionality is working correctly.")
    
    # Cleanup
    import os
    if os.path.exists("test_comment_likes.db"):
        os.remove("test_comment_likes.db")
        print("🧹 Test database cleaned up")

if __name__ == "__main__":
    test_comment_like_functionality()