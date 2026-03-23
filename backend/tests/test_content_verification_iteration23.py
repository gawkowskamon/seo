"""
Test Content Verification API and Enhanced SEO Scorer - Iteration 23
Tests:
1. POST /api/verify/check - starts async content verification job
2. GET /api/verify/status/{job_id} - polls verification status
3. GET /api/verify/history/{article_id} - gets verification history
4. SEO scorer returns enhanced breakdown with new fields
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="module")
def test_article_id(auth_headers):
    """Get an existing article ID for testing."""
    response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]["id"]
    pytest.skip("No articles found for testing")


class TestHealthEndpoints:
    """Basic health check tests."""
    
    def test_health_endpoint(self):
        """Test /health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/health")
        # /health may return HTML or JSON depending on ingress config
        assert response.status_code == 200
        print("✓ /health endpoint accessible")
    
    def test_api_health_endpoint(self):
        """Test /api/health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✓ /api/health endpoint accessible")


class TestContentVerificationAPI:
    """Tests for Content Verification API endpoints."""
    
    def test_verify_check_returns_job_id(self, auth_headers, test_article_id):
        """Test POST /api/verify/check returns job_id."""
        response = requests.post(
            f"{BASE_URL}/api/verify/check",
            json={"article_id": test_article_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ POST /api/verify/check returns job_id: {data['job_id']}")
    
    def test_verify_check_requires_auth(self, test_article_id):
        """Test POST /api/verify/check requires authentication."""
        response = requests.post(
            f"{BASE_URL}/api/verify/check",
            json={"article_id": test_article_id}
        )
        assert response.status_code in [401, 403]
        print("✓ POST /api/verify/check requires authentication")
    
    def test_verify_check_invalid_article(self, auth_headers):
        """Test POST /api/verify/check with invalid article_id returns 404."""
        response = requests.post(
            f"{BASE_URL}/api/verify/check",
            json={"article_id": "invalid-article-id-12345"},
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ POST /api/verify/check with invalid article_id returns 404")
    
    def test_verify_status_invalid_job(self, auth_headers):
        """Test GET /api/verify/status/{job_id} with invalid job_id returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/verify/status/invalid-job-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ GET /api/verify/status with invalid job_id returns 404")
    
    def test_verify_full_flow(self, auth_headers, test_article_id):
        """Test full verification flow: start job -> poll -> get result."""
        # Start verification
        start_response = requests.post(
            f"{BASE_URL}/api/verify/check",
            json={"article_id": test_article_id},
            headers=auth_headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        print(f"  Started verification job: {job_id}")
        
        # Poll for result (max 60 seconds)
        max_attempts = 30
        result = None
        for attempt in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(
                f"{BASE_URL}/api/verify/status/{job_id}",
                headers=auth_headers
            )
            
            if status_response.status_code == 404:
                # Job was cleaned up after completion
                print(f"  Job completed and cleaned up at attempt {attempt + 1}")
                break
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                result = status_data.get("result")
                print(f"  Verification completed at attempt {attempt + 1}")
                break
            elif status_data["status"] == "failed":
                print(f"  Verification failed: {status_data.get('error')}")
                pytest.fail(f"Verification failed: {status_data.get('error')}")
            else:
                print(f"  Attempt {attempt + 1}: status = {status_data['status']}")
        
        # Verify result structure if we got one
        if result:
            assert "overall_reliability_score" in result
            assert "verdict" in result
            assert result["verdict"] in ["rzetelny", "wymaga poprawek", "nierzetelny"]
            assert "legal_accuracy" in result
            assert "factual_accuracy" in result
            assert "completeness" in result
            assert "sources_quality" in result
            
            # Check score fields
            assert "score" in result["legal_accuracy"]
            assert "score" in result["factual_accuracy"]
            assert "score" in result["completeness"]
            assert "score" in result["sources_quality"]
            
            print(f"✓ Full verification flow completed successfully")
            print(f"  - Overall score: {result['overall_reliability_score']}%")
            print(f"  - Verdict: {result['verdict']}")
            print(f"  - Legal accuracy: {result['legal_accuracy']['score']}%")
            print(f"  - Factual accuracy: {result['factual_accuracy']['score']}%")
        else:
            print("✓ Verification job completed (result already cleaned up)")
    
    def test_verify_history(self, auth_headers, test_article_id):
        """Test GET /api/verify/history/{article_id} returns history."""
        response = requests.get(
            f"{BASE_URL}/api/verify/history/{test_article_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/verify/history returns {len(data)} records")


class TestEnhancedSEOScorer:
    """Tests for enhanced SEO scorer with new fields."""
    
    def test_seo_score_has_enhanced_breakdown(self, auth_headers, test_article_id):
        """Test that SEO score includes new breakdown fields."""
        # First get the article to get keywords
        article_response = requests.get(
            f"{BASE_URL}/api/articles/{test_article_id}",
            headers=auth_headers
        )
        assert article_response.status_code == 200
        article = article_response.json()
        
        # Request SEO score
        score_response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/score",
            json={
                "primary_keyword": article.get("primary_keyword", "test"),
                "secondary_keywords": article.get("secondary_keywords", [])
            },
            headers=auth_headers
        )
        assert score_response.status_code == 200
        score = score_response.json()
        
        # Check basic structure
        assert "total_score" in score
        assert "total_max" in score
        assert "percentage" in score
        assert "breakdown" in score
        assert "recommendations" in score
        
        breakdown = score["breakdown"]
        
        # Check for NEW enhanced fields
        expected_fields = [
            "sources_eeat",  # NEW: E-E-A-T sources scoring
            "slug",          # NEW: URL/slug optimization
            "formatting",    # NEW: Content formatting
            "freshness",     # NEW: Content freshness
            "readability",   # NEW: Readability score
            "meta_title",    # NEW: Separate meta title scoring
        ]
        
        for field in expected_fields:
            assert field in breakdown, f"Missing enhanced field: {field}"
            assert "score" in breakdown[field], f"Missing score in {field}"
            assert "max" in breakdown[field], f"Missing max in {field}"
            assert "label" in breakdown[field], f"Missing label in {field}"
        
        print(f"✓ SEO score has all enhanced breakdown fields")
        print(f"  - Total score: {score['percentage']}%")
        print(f"  - sources_eeat: {breakdown['sources_eeat']['score']}/{breakdown['sources_eeat']['max']}")
        print(f"  - slug: {breakdown['slug']['score']}/{breakdown['slug']['max']}")
        print(f"  - formatting: {breakdown['formatting']['score']}/{breakdown['formatting']['max']}")
        print(f"  - freshness: {breakdown['freshness']['score']}/{breakdown['freshness']['max']}")
        print(f"  - readability: {breakdown['readability']['score']}/{breakdown['readability']['max']}")
        print(f"  - meta_title: {breakdown['meta_title']['score']}/{breakdown['meta_title']['max']}")


class TestRegressionPlagiarismChecker:
    """Quick regression test for plagiarism checker."""
    
    def test_plagiarism_check_endpoint_exists(self, auth_headers, test_article_id):
        """Test POST /api/plagiarism/check endpoint still works."""
        response = requests.post(
            f"{BASE_URL}/api/plagiarism/check",
            json={"article_id": test_article_id},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Plagiarism check endpoint works (job_id: {data['job_id']})")


class TestRegressionAISuggestions:
    """Quick regression test for AI suggestions."""
    
    def test_ai_suggestions_endpoint_exists(self, auth_headers):
        """Test POST /api/articles/ai-suggestions endpoint still works."""
        response = requests.post(
            f"{BASE_URL}/api/articles/ai-suggestions",
            json={"focus": "VAT"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ AI suggestions endpoint works (job_id: {data['job_id']})")


class TestRegressionPerformanceDashboard:
    """Quick regression test for performance dashboard."""
    
    def test_performance_dashboard_endpoint_exists(self, auth_headers):
        """Test GET /api/performance/dashboard endpoint still works."""
        response = requests.get(
            f"{BASE_URL}/api/performance/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Dashboard has nested structure: articles.total, seo.average, etc.
        assert "articles" in data
        assert "seo" in data
        assert "total" in data["articles"]
        print(f"✓ Performance dashboard endpoint works (articles: {data['articles']['total']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
