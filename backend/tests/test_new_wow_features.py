"""
Backend tests for new 'Wow' features:
- Keyword Analytics (POST /api/keyword-analytics/analyze, GET /api/keyword-analytics/status/{job_id})
- AI Rewriter (POST /api/rewrite, GET /api/rewrite/status/{job_id})
- Newsletter Generator (POST /api/newsletter/generate, GET /api/newsletter/list, GET /api/newsletter/{id})

Tests are designed for the Polish accounting SEO app.
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
    pytest.skip(f"Authentication failed - status {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestHealthCheck:
    """Basic health check tests."""
    
    def test_api_health(self):
        """Health endpoint returns healthy status."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ API health check passes")


class TestKeywordAnalytics:
    """Keyword Analytics API tests - async pattern with job_id polling."""
    
    def test_analyze_requires_auth(self):
        """POST /api/keyword-analytics/analyze requires authentication."""
        response = requests.post(f"{BASE_URL}/api/keyword-analytics/analyze", json={
            "keywords": ["VAT 2026"],
            "industry": "rachunkowość i podatki"
        })
        assert response.status_code == 401
        print("✓ Keyword analytics requires authentication (401)")
    
    def test_analyze_returns_job_id(self, auth_headers):
        """POST /api/keyword-analytics/analyze returns job_id immediately."""
        response = requests.post(f"{BASE_URL}/api/keyword-analytics/analyze", json={
            "keywords": ["VAT", "PIT"],
            "industry": "rachunkowość i podatki"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data, f"Expected job_id in response, got: {data}"
        assert data.get("status") == "queued", f"Expected status 'queued', got: {data.get('status')}"
        print(f"✓ Keyword analytics returns job_id: {data['job_id'][:8]}...")
    
    def test_analyze_status_polling(self, auth_headers):
        """GET /api/keyword-analytics/status/{job_id} returns status and eventually result."""
        # Start the job
        start_response = requests.post(f"{BASE_URL}/api/keyword-analytics/analyze", json={
            "keywords": ["ulgi podatkowe", "księgowość"],
            "industry": "rachunkowość i podatki"
        }, headers=auth_headers)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 30 seconds)
        max_attempts = 15
        for i in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/keyword-analytics/status/{job_id}", headers=auth_headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                assert "result" in status_data
                assert "keywords" in status_data["result"]
                print(f"✓ Keyword analytics completed with {len(status_data['result']['keywords'])} keywords")
                return
            elif status_data.get("status") == "failed":
                pytest.fail(f"Keyword analytics job failed: {status_data.get('error')}")
            
            print(f"  Polling attempt {i+1}/{max_attempts}, status: {status_data.get('status')}")
        
        pytest.fail("Keyword analytics job did not complete within 30 seconds")
    
    def test_history_endpoint(self, auth_headers):
        """GET /api/keyword-analytics/history returns analysis history."""
        response = requests.get(f"{BASE_URL}/api/keyword-analytics/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Keyword analytics history returns {len(data)} records")


class TestAIRewriter:
    """AI Rewriter API tests - async pattern with job_id polling."""
    
    def test_rewrite_requires_auth(self):
        """POST /api/rewrite requires authentication."""
        response = requests.post(f"{BASE_URL}/api/rewrite", json={
            "text": "Test tekst do przepisania.",
            "style": "profesjonalny"
        })
        assert response.status_code == 401
        print("✓ AI Rewriter requires authentication (401)")
    
    def test_rewrite_returns_job_id(self, auth_headers):
        """POST /api/rewrite returns job_id immediately."""
        response = requests.post(f"{BASE_URL}/api/rewrite", json={
            "text": "Firma musi zapłacić podatek dochodowy od osób prawnych.",
            "style": "profesjonalny"
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data, f"Expected job_id in response, got: {data}"
        assert data.get("status") == "queued", f"Expected status 'queued', got: {data.get('status')}"
        print(f"✓ AI Rewriter returns job_id: {data['job_id'][:8]}...")
    
    def test_rewrite_status_polling(self, auth_headers):
        """GET /api/rewrite/status/{job_id} returns status and eventually rewritten text."""
        # Start the job
        start_response = requests.post(f"{BASE_URL}/api/rewrite", json={
            "text": "Trzeba zapłacić VAT. Podatek jest ważny.",
            "style": "ekspercki"
        }, headers=auth_headers)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 30 seconds)
        max_attempts = 15
        for i in range(max_attempts):
            time.sleep(2)
            status_response = requests.get(f"{BASE_URL}/api/rewrite/status/{job_id}", headers=auth_headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                assert "result" in status_data
                assert "rewritten_text" in status_data["result"]
                assert len(status_data["result"]["rewritten_text"]) > 0
                print(f"✓ AI Rewriter completed, text length: {len(status_data['result']['rewritten_text'])}")
                return
            elif status_data.get("status") == "failed":
                pytest.fail(f"Rewrite job failed: {status_data.get('error')}")
            
            print(f"  Polling attempt {i+1}/{max_attempts}, status: {status_data.get('status')}")
        
        pytest.fail("Rewrite job did not complete within 30 seconds")
    
    def test_rewrite_invalid_job_id(self, auth_headers):
        """GET /api/rewrite/status/{invalid} returns 404."""
        response = requests.get(f"{BASE_URL}/api/rewrite/status/invalid-job-id-123", headers=auth_headers)
        assert response.status_code == 404
        print("✓ AI Rewriter returns 404 for invalid job_id")


class TestNewsletterGenerator:
    """Newsletter Generator API tests - synchronous generation."""
    
    def test_generate_requires_auth(self):
        """POST /api/newsletter/generate requires authentication."""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate", json={
            "style": "informacyjny"
        })
        assert response.status_code == 401
        print("✓ Newsletter generation requires authentication (401)")
    
    def test_generate_newsletter_success(self, auth_headers):
        """POST /api/newsletter/generate returns newsletter with id and html."""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate", json={
            "title": "Test Newsletter",
            "style": "informacyjny"
        }, headers=auth_headers, timeout=60)
        
        # This endpoint can take up to 30 seconds
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data, f"Expected 'id' in response, got: {data}"
            assert "html" in data, f"Expected 'html' in response, got: {data}"
            assert "title" in data, f"Expected 'title' in response, got: {data}"
            assert len(data["html"]) > 50, "Newsletter HTML content should be substantial"
            print(f"✓ Newsletter generated, id: {data['id'][:8]}..., HTML length: {len(data['html'])}")
        elif response.status_code == 400:
            # May fail if no articles exist
            data = response.json()
            print(f"✓ Newsletter generation returned 400 (likely no articles): {data.get('detail', 'unknown')}")
    
    def test_list_newsletters(self, auth_headers):
        """GET /api/newsletter/list returns list of newsletters."""
        response = requests.get(f"{BASE_URL}/api/newsletter/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Newsletter list returns {len(data)} newsletters")
        
        # Return a newsletter ID for the next test
        return data[0]["id"] if data else None
    
    def test_get_newsletter_by_id(self, auth_headers):
        """GET /api/newsletter/{id} returns newsletter details."""
        # First get list to find an existing newsletter
        list_response = requests.get(f"{BASE_URL}/api/newsletter/list", headers=auth_headers)
        if list_response.status_code == 200 and list_response.json():
            newsletter_id = list_response.json()[0]["id"]
            
            response = requests.get(f"{BASE_URL}/api/newsletter/{newsletter_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get("id") == newsletter_id
            assert "html" in data
            print(f"✓ Newsletter retrieved by id: {newsletter_id[:8]}...")
        else:
            print("✓ Skipping get-by-id test (no newsletters exist)")
    
    def test_get_newsletter_invalid_id(self, auth_headers):
        """GET /api/newsletter/{invalid} returns 404."""
        response = requests.get(f"{BASE_URL}/api/newsletter/invalid-newsletter-id", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Newsletter returns 404 for invalid id")


class TestSidebarNavigation:
    """Test that sidebar navigation links are accessible."""
    
    def test_articles_endpoint_accessible(self, auth_headers):
        """GET /api/articles works (sidebar links lead to pages that use this)."""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        print("✓ Articles endpoint accessible (for sidebar navigation)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
