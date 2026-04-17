"""
Smart Scheduling Widget API Tests - Iteration 38

Tests for the new Smart Scheduling Widget feature:
- GET /api/smart-scheduling/insights - returns 6 insight categories
- Cache behavior (6h per user)
- refresh=true bypasses cache
- AI trending topics generation
- Content gaps detection
- Best publishing time recommendation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "monika.gawkowska@kurdynowski.pl"
TEST_PASSWORD = "MonZuz8180!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestSmartSchedulingInsights:
    """Tests for GET /api/smart-scheduling/insights endpoint."""
    
    def test_insights_returns_200(self, auth_headers):
        """Insights endpoint returns 200 OK."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ GET /api/smart-scheduling/insights returns 200")
    
    def test_insights_has_all_required_fields(self, auth_headers):
        """Response contains all 6 insight categories + metadata."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        required_fields = [
            "needs_optimization",
            "ready_to_publish", 
            "social_promotion",
            "best_publishing_time",
            "content_gaps",
            "trending_topics",
            "generated_at"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"✓ Field '{field}' present in response")
        
        # cached field should be present (true or false)
        assert "cached" in data, "Missing 'cached' field"
        print(f"✓ cached={data['cached']}")
    
    def test_needs_optimization_structure(self, auth_headers):
        """needs_optimization returns articles with score < 60%."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        needs_opt = data.get("needs_optimization", [])
        assert isinstance(needs_opt, list), "needs_optimization should be a list"
        
        if needs_opt:
            article = needs_opt[0]
            assert "id" in article, "Article missing 'id'"
            assert "title" in article, "Article missing 'title'"
            assert "surfer_score" in article, "Article missing 'surfer_score'"
            
            # Verify score < 60%
            score = article.get("surfer_score", {}).get("percentage", 100)
            assert score < 60, f"Article score {score}% should be < 60%"
            print(f"✓ needs_optimization: {len(needs_opt)} articles with score < 60%")
    
    def test_ready_to_publish_structure(self, auth_headers):
        """ready_to_publish returns drafts with score >= 70% older than 7 days."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        ready = data.get("ready_to_publish", [])
        assert isinstance(ready, list), "ready_to_publish should be a list"
        
        if ready:
            article = ready[0]
            assert "id" in article, "Article missing 'id'"
            assert "title" in article, "Article missing 'title'"
            assert "surfer_score" in article, "Article missing 'surfer_score'"
            assert "created_at" in article, "Article missing 'created_at'"
            
            # Verify score >= 70%
            score = article.get("surfer_score", {}).get("percentage", 0)
            assert score >= 70, f"Article score {score}% should be >= 70%"
            print(f"✓ ready_to_publish: {len(ready)} drafts with score >= 70%")
    
    def test_social_promotion_structure(self, auth_headers):
        """social_promotion returns published articles with high views."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        social = data.get("social_promotion", [])
        assert isinstance(social, list), "social_promotion should be a list"
        
        if social:
            article = social[0]
            assert "id" in article, "Article missing 'id'"
            assert "title" in article, "Article missing 'title'"
            print(f"✓ social_promotion: {len(social)} candidates for social media")
    
    def test_best_publishing_time_structure(self, auth_headers):
        """best_publishing_time returns day, hour_range, reason."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        best_time = data.get("best_publishing_time", {})
        assert isinstance(best_time, dict), "best_publishing_time should be a dict"
        
        assert "day" in best_time, "Missing 'day' field"
        assert "hour_range" in best_time, "Missing 'hour_range' field"
        assert "reason" in best_time, "Missing 'reason' field"
        
        # Default should be Tuesday 9-11 for accounting niche
        print(f"✓ best_publishing_time: {best_time['day']} {best_time['hour_range']}")
    
    def test_content_gaps_structure(self, auth_headers):
        """content_gaps returns keywords used in multiple articles without pillar page."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        gaps = data.get("content_gaps", [])
        assert isinstance(gaps, list), "content_gaps should be a list"
        
        if gaps:
            gap = gaps[0]
            assert "keyword" in gap, "Gap missing 'keyword'"
            assert "article_count" in gap, "Gap missing 'article_count'"
            assert gap["article_count"] >= 2, "Gap should have article_count >= 2"
            print(f"✓ content_gaps: {len(gaps)} keywords without pillar page")
    
    def test_trending_topics_structure(self, auth_headers):
        """trending_topics returns AI-suggested topics with topic, primary_keyword, reason."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        trending = data.get("trending_topics", [])
        assert isinstance(trending, list), "trending_topics should be a list"
        
        if trending:
            topic = trending[0]
            assert "topic" in topic, "Topic missing 'topic'"
            assert "primary_keyword" in topic, "Topic missing 'primary_keyword'"
            assert "reason" in topic, "Topic missing 'reason'"
            print(f"✓ trending_topics: {len(trending)} AI-suggested topics")
            print(f"  - Topic 1: {topic['topic'][:50]}...")


class TestSmartSchedulingCache:
    """Tests for cache behavior."""
    
    def test_first_call_not_cached(self, auth_headers):
        """First call with refresh=true returns cached=false."""
        response = requests.get(
            f"{BASE_URL}/api/smart-scheduling/insights?refresh=true", 
            headers=auth_headers
        )
        data = response.json()
        
        assert data.get("cached") == False, "refresh=true should return cached=false"
        print("✓ refresh=true bypasses cache (cached=false)")
    
    def test_second_call_cached(self, auth_headers):
        """Second call within 6h returns cached=true."""
        # First call to ensure cache exists
        requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        
        # Second call should be cached
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        data = response.json()
        
        assert data.get("cached") == True, "Second call should return cached=true"
        assert "cached_at" in data, "Cached response should have cached_at"
        print(f"✓ Second call returns cached=true (cached_at: {data.get('cached_at')})")
    
    def test_refresh_bypasses_cache(self, auth_headers):
        """refresh=true parameter bypasses cache and regenerates."""
        # First ensure we have cached data
        requests.get(f"{BASE_URL}/api/smart-scheduling/insights", headers=auth_headers)
        
        # Now call with refresh=true
        response = requests.get(
            f"{BASE_URL}/api/smart-scheduling/insights?refresh=true",
            headers=auth_headers
        )
        data = response.json()
        
        assert data.get("cached") == False, "refresh=true should bypass cache"
        assert "generated_at" in data, "Fresh response should have generated_at"
        print(f"✓ refresh=true regenerates insights (generated_at: {data.get('generated_at')})")


class TestSmartSchedulingAuth:
    """Tests for authentication requirements."""
    
    def test_unauthenticated_returns_401(self):
        """Endpoint requires authentication."""
        response = requests.get(f"{BASE_URL}/api/smart-scheduling/insights")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated request returns 401")
    
    def test_invalid_token_returns_401(self):
        """Invalid token returns 401."""
        response = requests.get(
            f"{BASE_URL}/api/smart-scheduling/insights",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid token returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
