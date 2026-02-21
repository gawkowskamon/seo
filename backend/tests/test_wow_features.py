"""
Test WOW features: Dark Mode (frontend-only), AI Chat Assistant, SEO Audit async, Competition analysis async
"""
import pytest
import requests
import time
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://content-craft-ai-4.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✓ API health check passed")

    def test_admin_login(self):
        """Test admin login returns valid token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful - user: {data['user']['email']}")
        return data["token"]


class TestAIChatAssistant:
    """AI Chat assistant endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_chat_requires_auth(self):
        """Chat endpoint should require authentication"""
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "message": "Hello",
            "article_id": ""
        })
        assert response.status_code == 401
        print("✓ Chat endpoint correctly requires authentication")
    
    def test_chat_message_with_auth(self, auth_token):
        """Chat endpoint should respond with AI message when authenticated"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/chat/message", json={
            "message": "Czesc, powiedz krotko co potrafisz",
            "article_id": ""
        }, headers=headers, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        print(f"✓ Chat AI response received ({len(data['response'])} chars)")
    
    def test_chat_clear_session(self, auth_token):
        """Test clearing chat session"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/chat/clear", json={}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cleared"
        print("✓ Chat session cleared successfully")


class TestSEOAuditAsync:
    """SEO Audit async endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_seo_audit_requires_auth(self):
        """SEO audit should require authentication"""
        response = requests.post(f"{BASE_URL}/api/seo-audit", json={"url": "https://example.com"})
        assert response.status_code == 401
        print("✓ SEO audit endpoint correctly requires authentication")
    
    def test_seo_audit_starts_job(self, auth_token):
        """POST /api/seo-audit should return job_id immediately"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/seo-audit", json={
            "url": "https://example.com"
        }, headers=headers, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ SEO audit job started: {data['job_id']}")
        return data["job_id"]
    
    def test_seo_audit_status_polling(self, auth_token):
        """Test SEO audit status polling returns proper statuses"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Start job
        start_response = requests.post(f"{BASE_URL}/api/seo-audit", json={
            "url": "https://example.com"
        }, headers=headers, timeout=10)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll status - wait up to 60 seconds
        max_polls = 30
        poll_interval = 2
        final_status = None
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            status_response = requests.get(f"{BASE_URL}/api/seo-audit/status/{job_id}", headers=headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            print(f"  Poll {i+1}: status = {status_data['status']}")
            
            if status_data["status"] == "completed":
                final_status = "completed"
                assert "result" in status_data
                assert "overall_score" in status_data["result"]
                print(f"✓ SEO audit completed with score: {status_data['result'].get('overall_score')}")
                break
            elif status_data["status"] == "failed":
                final_status = "failed"
                print(f"✗ SEO audit failed: {status_data.get('error')}")
                break
        
        assert final_status in ["completed", "failed"], f"Job did not complete within timeout (last status: {final_status})"
    
    def test_seo_audit_history(self, auth_token):
        """Test SEO audit history endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/seo-audit/history", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ SEO audit history retrieved ({len(data)} audits)")


class TestCompetitionAnalysisAsync:
    """Competition analysis async endpoint tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture
    def article_id(self, auth_token):
        """Get an article ID for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        if len(articles) == 0:
            pytest.skip("No articles available for testing")
        return articles[0]["id"]
    
    def test_competition_requires_auth(self):
        """Competition analysis should require authentication"""
        response = requests.post(f"{BASE_URL}/api/competition/analyze", json={
            "article_id": "test-id",
            "competitor_url": "https://example.com"
        })
        assert response.status_code == 401
        print("✓ Competition analysis correctly requires authentication")
    
    def test_competition_starts_job(self, auth_token, article_id):
        """POST /api/competition/analyze should return job_id immediately"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/competition/analyze", json={
            "article_id": article_id,
            "competitor_url": "https://example.com"
        }, headers=headers, timeout=10)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Competition analysis job started: {data['job_id']}")
    
    def test_competition_status_polling(self, auth_token, article_id):
        """Test competition analysis status polling"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Start job
        start_response = requests.post(f"{BASE_URL}/api/competition/analyze", json={
            "article_id": article_id,
            "competitor_url": "https://example.com"
        }, headers=headers, timeout=10)
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll status - wait up to 60 seconds
        max_polls = 30
        poll_interval = 2
        final_status = None
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            status_response = requests.get(f"{BASE_URL}/api/competition/status/{job_id}", headers=headers)
            assert status_response.status_code == 200
            status_data = status_response.json()
            
            print(f"  Poll {i+1}: status = {status_data['status']}")
            
            if status_data["status"] == "completed":
                final_status = "completed"
                assert "result" in status_data
                print(f"✓ Competition analysis completed")
                break
            elif status_data["status"] == "failed":
                final_status = "failed"
                print(f"✗ Competition analysis failed: {status_data.get('error')}")
                break
        
        assert final_status in ["completed", "failed"], f"Job did not complete within timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
