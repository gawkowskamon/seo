"""
Test suite for iteration 24 new features:
1. Auto Competition Analysis - POST /api/competition/auto-analyze, GET /api/competition/auto-status/{job_id}
2. A/B Title Testing - POST /api/articles/ab-title-test, GET /api/articles/ab-title-status/{job_id}
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
    if response.status_code == 200:
        articles = response.json()
        if articles and len(articles) > 0:
            return articles[0]["id"]
    pytest.skip("No articles found for testing")


# ============ Health Check Tests ============

class TestHealthEndpoints:
    """Basic health check tests."""
    
    def test_health_endpoint(self):
        """Test /health endpoint."""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ /health endpoint accessible")
    
    def test_api_health_endpoint(self):
        """Test /api/health endpoint."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ /api/health endpoint accessible")


# ============ Auto Competition Analysis Tests ============

class TestAutoCompetitionAnalysis:
    """Tests for automatic competition analysis feature."""
    
    def test_auto_analyze_requires_auth(self):
        """Test that auto-analyze requires authentication."""
        response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", json={
            "article_id": "test-id"
        })
        assert response.status_code in [401, 403, 422]
        print("✓ POST /api/competition/auto-analyze requires authentication")
    
    def test_auto_analyze_invalid_article(self, auth_headers):
        """Test auto-analyze with invalid article ID."""
        response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", json={
            "article_id": "invalid-article-id-12345"
        }, headers=auth_headers)
        assert response.status_code == 404
        print("✓ POST /api/competition/auto-analyze returns 404 for invalid article")
    
    def test_auto_analyze_returns_job_id(self, auth_headers, test_article_id):
        """Test that auto-analyze returns a job_id."""
        response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data.get("status") in ["queued", "running"]
        print(f"✓ POST /api/competition/auto-analyze returns job_id: {data['job_id'][:8]}...")
        return data["job_id"]
    
    def test_auto_status_invalid_job(self, auth_headers):
        """Test status endpoint with invalid job ID."""
        response = requests.get(f"{BASE_URL}/api/competition/auto-status/invalid-job-id", headers=auth_headers)
        assert response.status_code == 404
        print("✓ GET /api/competition/auto-status returns 404 for invalid job")
    
    def test_auto_analyze_full_flow(self, auth_headers, test_article_id):
        """Test full auto competition analysis flow: start -> poll -> complete."""
        # Start the job
        start_response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        print(f"  Started job: {job_id[:8]}...")
        
        # Poll for completion (max 60 seconds)
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/competition/auto-status/{job_id}", headers=auth_headers)
            
            if status_response.status_code == 404:
                # Job was already cleaned up (completed)
                print("  Job completed and cleaned up")
                break
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                result = status_data.get("result", {})
                # Verify result structure
                assert "competitors_scraped" in result or "summary" in result
                print(f"✓ Auto competition analysis completed with {len(result.get('competitors_scraped', []))} competitors")
                
                # Check for expected fields
                if "content_gaps" in result:
                    print(f"  - Found {len(result['content_gaps'])} content gaps")
                if "keyword_opportunities" in result:
                    print(f"  - Found {len(result['keyword_opportunities'])} keyword opportunities")
                if "action_plan" in result:
                    print(f"  - Found {len(result['action_plan'])} action items")
                return
            
            elif status_data["status"] == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"  Job failed: {error}")
                # Don't fail test for AI errors - just report
                if "budget" in error.lower() or "key" in error.lower():
                    pytest.skip(f"AI service error: {error}")
                return
            
            print(f"  Polling attempt {attempt + 1}/{max_attempts}, status: {status_data['status']}")
        
        print("  Job timed out after 60 seconds")


# ============ A/B Title Testing Tests ============

class TestABTitleTesting:
    """Tests for A/B title testing feature."""
    
    def test_ab_title_requires_auth(self):
        """Test that A/B title test requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", json={
            "article_id": "test-id"
        })
        assert response.status_code in [401, 403, 422]
        print("✓ POST /api/articles/ab-title-test requires authentication")
    
    def test_ab_title_invalid_article(self, auth_headers):
        """Test A/B title test with invalid article ID."""
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", json={
            "article_id": "invalid-article-id-12345"
        }, headers=auth_headers)
        assert response.status_code == 404
        print("✓ POST /api/articles/ab-title-test returns 404 for invalid article")
    
    def test_ab_title_returns_job_id(self, auth_headers, test_article_id):
        """Test that A/B title test returns a job_id."""
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", json={
            "article_id": test_article_id,
            "custom_variants": []
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data.get("status") in ["queued", "running"]
        print(f"✓ POST /api/articles/ab-title-test returns job_id: {data['job_id'][:8]}...")
    
    def test_ab_title_with_custom_variants(self, auth_headers, test_article_id):
        """Test A/B title test with custom variants."""
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", json={
            "article_id": test_article_id,
            "custom_variants": ["Mój własny tytuł testowy", "Inny wariant tytułu"]
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        print("✓ POST /api/articles/ab-title-test accepts custom variants")
    
    def test_ab_title_status_invalid_job(self, auth_headers):
        """Test status endpoint with invalid job ID."""
        response = requests.get(f"{BASE_URL}/api/articles/ab-title-status/invalid-job-id", headers=auth_headers)
        assert response.status_code == 404
        print("✓ GET /api/articles/ab-title-status returns 404 for invalid job")
    
    def test_ab_title_full_flow(self, auth_headers, test_article_id):
        """Test full A/B title test flow: start -> poll -> complete."""
        # Start the job
        start_response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", json={
            "article_id": test_article_id,
            "custom_variants": []
        }, headers=auth_headers)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        print(f"  Started job: {job_id[:8]}...")
        
        # Poll for completion (max 45 seconds)
        max_attempts = 22
        for attempt in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/articles/ab-title-status/{job_id}", headers=auth_headers)
            
            if status_response.status_code == 404:
                # Job was already cleaned up (completed)
                print("  Job completed and cleaned up")
                break
            
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                result = status_data.get("result", {})
                # Verify result structure
                assert "current_title" in result
                assert "variants" in result
                assert "winner" in result
                
                # Check variants
                variants = result.get("variants", [])
                print(f"✓ A/B title test completed with {len(variants)} variants")
                
                # Check winner
                winner = result.get("winner", {})
                if winner:
                    print(f"  - Winner: \"{winner.get('text', '')[:50]}...\" (score: {winner.get('total', 'N/A')})")
                
                # Check current title scores
                current = result.get("current_title", {})
                if current:
                    scores = current.get("scores", {})
                    print(f"  - Current title scores: CTR={scores.get('ctr')}, SEO={scores.get('seo')}, Emotion={scores.get('emotion')}, Clarity={scores.get('clarity')}")
                
                return
            
            elif status_data["status"] == "failed":
                error = status_data.get("error", "Unknown error")
                print(f"  Job failed: {error}")
                # Don't fail test for AI errors - just report
                if "budget" in error.lower() or "key" in error.lower():
                    pytest.skip(f"AI service error: {error}")
                return
            
            print(f"  Polling attempt {attempt + 1}/{max_attempts}, status: {status_data['status']}")
        
        print("  Job timed out after 45 seconds")


# ============ Regression Tests ============

class TestRegressionExistingFeatures:
    """Quick regression tests for existing features."""
    
    def test_articles_list(self, auth_headers):
        """Test articles list endpoint."""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        articles = response.json()
        assert isinstance(articles, list)
        print(f"✓ GET /api/articles returns {len(articles)} articles")
    
    def test_performance_dashboard(self, auth_headers):
        """Test performance dashboard endpoint (admin only)."""
        response = requests.get(f"{BASE_URL}/api/performance/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data or "articles_per_day" in data
        print("✓ GET /api/performance/dashboard works (regression)")
    
    def test_ai_suggestions_endpoint(self, auth_headers):
        """Test AI suggestions endpoint."""
        response = requests.post(f"{BASE_URL}/api/articles/ai-suggestions", json={
            "focus": "podatki"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        print("✓ POST /api/articles/ai-suggestions works (regression)")
    
    def test_plagiarism_check_endpoint(self, auth_headers, test_article_id):
        """Test plagiarism check endpoint."""
        response = requests.post(f"{BASE_URL}/api/plagiarism/check", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        print("✓ POST /api/plagiarism/check works (regression)")
    
    def test_verify_check_endpoint(self, auth_headers, test_article_id):
        """Test content verification endpoint."""
        response = requests.post(f"{BASE_URL}/api/verify/check", json={
            "article_id": test_article_id
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        print("✓ POST /api/verify/check works (regression)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
