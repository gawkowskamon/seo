"""
Test Social Media Posts Feature - Iteration 26
Tests:
- POST /api/articles/social-posts - starts async social posts generation
- GET /api/articles/social-posts/status/{job_id} - polls job status
- Regression: Dashboard bulk mode, editor tabs
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "monika.gawkowska@kurdynowski.pl",
        "password": "MonZuz8180!"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(scope="module")
def test_article_id(auth_headers):
    """Get an existing article ID for testing."""
    response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) > 0, "No articles found for testing"
    return articles[0]["id"]


class TestSocialPostsAPI:
    """Test Social Media Posts generation endpoints."""
    
    def test_social_posts_requires_auth(self):
        """POST /api/articles/social-posts requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/social-posts", json={
            "article_id": "test-id"
        })
        assert response.status_code == 401
    
    def test_social_posts_returns_job_id(self, auth_headers, test_article_id):
        """POST /api/articles/social-posts returns job_id with status queued."""
        response = requests.post(f"{BASE_URL}/api/articles/social-posts", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] in ["queued", "processing"]
        print(f"✓ Social posts job started: {data['job_id']}")
    
    def test_social_posts_status_not_found(self, auth_headers):
        """GET /api/articles/social-posts/status/{job_id} returns 404 for non-existent job."""
        response = requests.get(f"{BASE_URL}/api/articles/social-posts/status/non-existent-job", headers=auth_headers)
        assert response.status_code == 404
    
    def test_social_posts_full_flow(self, auth_headers, test_article_id):
        """Full flow: POST to start job, poll until completed, verify result structure."""
        # Start job
        response = requests.post(f"{BASE_URL}/api/articles/social-posts", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        print(f"✓ Job started: {job_id}")
        
        # Poll for completion (max 60 seconds)
        max_attempts = 24
        result = None
        for i in range(max_attempts):
            time.sleep(2.5)
            status_response = requests.get(
                f"{BASE_URL}/api/articles/social-posts/status/{job_id}",
                headers=auth_headers
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            print(f"  Poll {i+1}: status={status_data['status']}")
            
            if status_data["status"] == "completed":
                result = status_data.get("result")
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
        
        assert result is not None, "Job did not complete in time"
        
        # Verify result structure - 4 platforms with 3 posts each
        assert "linkedin" in result, "Missing linkedin posts"
        assert "twitter" in result, "Missing twitter posts"
        assert "facebook" in result, "Missing facebook posts"
        assert "instagram" in result, "Missing instagram posts"
        
        # Each platform should have 3 posts (one per tone)
        for platform in ["linkedin", "twitter", "facebook", "instagram"]:
            posts = result[platform]
            assert isinstance(posts, list), f"{platform} should be a list"
            assert len(posts) == 3, f"{platform} should have 3 posts, got {len(posts)}"
            
            # Verify each post has required fields
            for post in posts:
                assert "tone" in post, f"Post missing tone field"
                assert "text" in post, f"Post missing text field"
                assert post["tone"] in ["profesjonalny", "zachęcający", "z pytaniem"], f"Invalid tone: {post['tone']}"
                assert len(post["text"]) > 10, f"Post text too short"
                
                # LinkedIn, Twitter, Instagram should have hashtags
                if platform in ["linkedin", "twitter", "instagram"]:
                    assert "hashtags" in post, f"{platform} post missing hashtags"
                    assert isinstance(post["hashtags"], list), f"hashtags should be a list"
                
                # All posts should have engagement rating
                assert "estimated_engagement" in post, f"Post missing estimated_engagement"
        
        # Tips should be present
        assert "tips" in result, "Missing tips"
        assert isinstance(result["tips"], list), "tips should be a list"
        
        print(f"✓ Social posts generated successfully:")
        print(f"  - LinkedIn: {len(result['linkedin'])} posts")
        print(f"  - Twitter: {len(result['twitter'])} posts")
        print(f"  - Facebook: {len(result['facebook'])} posts")
        print(f"  - Instagram: {len(result['instagram'])} posts")
        print(f"  - Tips: {len(result['tips'])} tips")


class TestRegressionDashboard:
    """Regression tests for dashboard bulk mode."""
    
    def test_articles_list(self, auth_headers):
        """GET /api/articles returns articles list."""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        articles = response.json()
        assert isinstance(articles, list)
        print(f"✓ Articles list: {len(articles)} articles")
    
    def test_bulk_delete_endpoint_exists(self, auth_headers):
        """POST /api/articles/bulk-delete endpoint exists."""
        response = requests.post(f"{BASE_URL}/api/articles/bulk-delete", json={
            "article_ids": []
        }, headers=auth_headers)
        # Returns 400 when empty list (valid behavior), not 404
        assert response.status_code in [200, 400]
        print("✓ Bulk delete endpoint exists")
    
    def test_bulk_category_endpoint_exists(self, auth_headers):
        """POST /api/articles/bulk-category endpoint exists."""
        response = requests.post(f"{BASE_URL}/api/articles/bulk-category", json={
            "article_ids": [],
            "category": "test"
        }, headers=auth_headers)
        # Returns 400 when empty list (valid behavior), not 404
        assert response.status_code in [200, 400]
        print("✓ Bulk category endpoint exists")
    
    def test_categories_list(self, auth_headers):
        """GET /api/articles/categories-list returns categories."""
        response = requests.get(f"{BASE_URL}/api/articles/categories-list", headers=auth_headers)
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        print(f"✓ Categories list: {len(categories)} categories")


class TestRegressionEditorTabs:
    """Regression tests for editor tabs - all tabs should still work."""
    
    def test_seo_assistant_endpoint(self, auth_headers, test_article_id):
        """POST /api/articles/{id}/seo-assistant endpoint exists."""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/seo-assistant",
            json={"mode": "analyze"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "job_id" in response.json()
        print("✓ SEO assistant endpoint works")
    
    def test_auto_meta_endpoint(self, auth_headers, test_article_id):
        """POST /api/articles/auto-meta endpoint exists."""
        response = requests.post(
            f"{BASE_URL}/api/articles/auto-meta",
            json={"article_id": test_article_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "job_id" in response.json()
        print("✓ Auto meta endpoint works")
    
    def test_smart_schedule_endpoint(self, auth_headers, test_article_id):
        """POST /api/articles/smart-schedule endpoint exists."""
        response = requests.post(
            f"{BASE_URL}/api/articles/smart-schedule",
            json={"article_id": test_article_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "job_id" in response.json()
        print("✓ Smart schedule endpoint works")
    
    def test_versions_endpoint(self, auth_headers, test_article_id):
        """GET /api/articles/{id}/versions endpoint exists."""
        response = requests.get(
            f"{BASE_URL}/api/articles/{test_article_id}/versions",
            headers=auth_headers
        )
        assert response.status_code == 200
        versions = response.json()
        assert isinstance(versions, list)
        print(f"✓ Versions endpoint works: {len(versions)} versions")
    
    def test_competition_endpoint(self, auth_headers, test_article_id):
        """POST /api/competition/analyze endpoint exists."""
        response = requests.post(
            f"{BASE_URL}/api/competition/analyze",
            json={"article_id": test_article_id, "competitor_url": "https://example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "job_id" in response.json()
        print("✓ Competition endpoint works")
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ Health endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
