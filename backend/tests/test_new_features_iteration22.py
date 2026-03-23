"""
Test suite for 3 new features:
1. AI Article Suggestions - /api/articles/ai-suggestions
2. Performance Dashboard - /api/performance/dashboard (admin only)
3. Plagiarism Checker - /api/plagiarism/check

Tests cover:
- API endpoints status codes
- Admin-only access control
- Async job polling pattern
- Response data structure validation
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert "token" in data, f"No token in login response: {data}"
    return data["token"]


def get_admin_headers():
    """Get headers with admin auth"""
    token = get_admin_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


class TestAuthSetup:
    """Authentication setup tests"""
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful, is_admin={data['user']['is_admin']}")


class TestPerformanceDashboard:
    """Performance Dashboard API tests - Admin only"""
    
    def test_performance_dashboard_admin_access(self):
        """Test admin can access performance dashboard"""
        headers = get_admin_headers()
        response = requests.get(f"{BASE_URL}/api/performance/dashboard", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "users" in data, "Missing 'users' in response"
        assert "articles" in data, "Missing 'articles' in response"
        assert "seo" in data, "Missing 'seo' in response"
        assert "top_articles" in data, "Missing 'top_articles' in response"
        assert "recent_articles" in data, "Missing 'recent_articles' in response"
        assert "content" in data, "Missing 'content' in response"
        assert "subscriptions" in data, "Missing 'subscriptions' in response"
        
        # Validate users structure
        assert "total" in data["users"]
        assert "dau" in data["users"]
        assert "mau" in data["users"]
        
        # Validate articles structure
        assert "total" in data["articles"]
        assert "this_week" in data["articles"]
        assert "this_month" in data["articles"]
        assert "per_day" in data["articles"]
        
        # Validate SEO structure
        assert "average" in data["seo"]
        assert "high" in data["seo"]
        assert "medium" in data["seo"]
        assert "low" in data["seo"]
        
        # Validate content structure
        assert "images" in data["content"]
        assert "newsletters" in data["content"]
        assert "wp_published" in data["content"]
        
        print(f"✓ Performance dashboard returns valid data: {data['articles']['total']} articles, {data['users']['total']} users")
    
    def test_performance_dashboard_no_auth(self):
        """Test unauthenticated access is denied"""
        response = requests.get(f"{BASE_URL}/api/performance/dashboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated access denied with status {response.status_code}")
    
    def test_performance_dashboard_articles_per_day(self):
        """Test articles per day data structure"""
        headers = get_admin_headers()
        response = requests.get(f"{BASE_URL}/api/performance/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        per_day = data["articles"]["per_day"]
        assert isinstance(per_day, list), "per_day should be a list"
        assert len(per_day) == 14, f"Expected 14 days, got {len(per_day)}"
        
        for day in per_day:
            assert "date" in day, "Missing 'date' in per_day item"
            assert "count" in day, "Missing 'count' in per_day item"
            assert isinstance(day["count"], int), "count should be integer"
        
        print(f"✓ Articles per day has {len(per_day)} days of data")


class TestAIArticleSuggestions:
    """AI Article Suggestions API tests"""
    
    def test_ai_suggestions_start_job(self):
        """Test starting AI suggestions job returns job_id"""
        headers = get_admin_headers()
        response = requests.post(
            f"{BASE_URL}/api/articles/ai-suggestions",
            json={"count": 3, "focus": ""},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "job_id" in data, "Missing 'job_id' in response"
        assert "status" in data, "Missing 'status' in response"
        assert data["status"] == "queued", f"Expected status 'queued', got {data['status']}"
        
        print(f"✓ AI suggestions job started with job_id: {data['job_id'][:8]}...")
    
    def test_ai_suggestions_poll_status(self):
        """Test polling AI suggestions job status"""
        headers = get_admin_headers()
        
        # Start a job first
        start_response = requests.post(
            f"{BASE_URL}/api/articles/ai-suggestions",
            json={"count": 3, "focus": "podatki"},
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for status (max 30 seconds)
        max_attempts = 15
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"{BASE_URL}/api/articles/ai-suggestions/status/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200, f"Status poll failed: {status_response.text}"
            status_data = status_response.json()
            
            assert "job_id" in status_data
            assert "status" in status_data
            
            if status_data["status"] == "completed":
                assert "result" in status_data, "Missing 'result' in completed response"
                assert "suggestions" in status_data["result"], "Missing 'suggestions' in result"
                suggestions = status_data["result"]["suggestions"]
                assert isinstance(suggestions, list), "suggestions should be a list"
                assert len(suggestions) > 0, "Expected at least 1 suggestion"
                
                # Validate suggestion structure
                first_suggestion = suggestions[0]
                assert "title" in first_suggestion, "Missing 'title' in suggestion"
                assert "primary_keyword" in first_suggestion, "Missing 'primary_keyword' in suggestion"
                
                print(f"✓ AI suggestions completed with {len(suggestions)} suggestions")
                return
            elif status_data["status"] == "failed":
                pytest.fail(f"AI suggestions job failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(2)
        
        pytest.fail(f"AI suggestions job did not complete within {max_attempts * 2} seconds")
    
    def test_ai_suggestions_no_auth(self):
        """Test unauthenticated access is denied"""
        response = requests.post(
            f"{BASE_URL}/api/articles/ai-suggestions",
            json={"count": 3, "focus": ""}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated access denied with status {response.status_code}")
    
    def test_ai_suggestions_invalid_job_id(self):
        """Test polling with invalid job_id returns 404"""
        headers = get_admin_headers()
        response = requests.get(
            f"{BASE_URL}/api/articles/ai-suggestions/status/invalid-job-id-12345",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Invalid job_id returns 404")


class TestPlagiarismChecker:
    """Plagiarism Checker API tests"""
    
    def get_test_article_id(self, headers):
        """Get an existing article ID for testing"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) > 0, "No articles found for testing"
        return articles[0]["id"]
    
    def test_plagiarism_check_start_job(self):
        """Test starting plagiarism check returns job_id"""
        headers = get_admin_headers()
        article_id = self.get_test_article_id(headers)
        
        response = requests.post(
            f"{BASE_URL}/api/plagiarism/check",
            json={"article_id": article_id},
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "job_id" in data, "Missing 'job_id' in response"
        assert "status" in data, "Missing 'status' in response"
        assert data["status"] == "queued", f"Expected status 'queued', got {data['status']}"
        
        print(f"✓ Plagiarism check job started with job_id: {data['job_id'][:8]}...")
    
    def test_plagiarism_check_poll_status(self):
        """Test polling plagiarism check job status"""
        headers = get_admin_headers()
        article_id = self.get_test_article_id(headers)
        
        # Start a job first
        start_response = requests.post(
            f"{BASE_URL}/api/plagiarism/check",
            json={"article_id": article_id},
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for status (max 40 seconds)
        max_attempts = 20
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"{BASE_URL}/api/plagiarism/status/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200, f"Status poll failed: {status_response.text}"
            status_data = status_response.json()
            
            assert "job_id" in status_data
            assert "status" in status_data
            
            if status_data["status"] == "completed":
                assert "result" in status_data, "Missing 'result' in completed response"
                result = status_data["result"]
                
                # Validate result structure
                assert "overall_score" in result, "Missing 'overall_score' in result"
                assert "verdict" in result, "Missing 'verdict' in result"
                assert "summary" in result, "Missing 'summary' in result"
                assert "details" in result, "Missing 'details' in result"
                
                # Validate details structure
                details = result["details"]
                assert "originality" in details, "Missing 'originality' in details"
                assert "style_uniqueness" in details, "Missing 'style_uniqueness' in details"
                
                # Validate score is in valid range
                assert 0 <= result["overall_score"] <= 100, f"Invalid score: {result['overall_score']}"
                
                # Validate verdict is one of expected values
                valid_verdicts = ["oryginalny", "podejrzany", "prawdopodobny plagiat"]
                assert result["verdict"] in valid_verdicts, f"Invalid verdict: {result['verdict']}"
                
                print(f"✓ Plagiarism check completed: score={result['overall_score']}%, verdict={result['verdict']}")
                return
            elif status_data["status"] == "failed":
                pytest.fail(f"Plagiarism check job failed: {status_data.get('error', 'Unknown error')}")
            
            time.sleep(2)
        
        pytest.fail(f"Plagiarism check job did not complete within {max_attempts * 2} seconds")
    
    def test_plagiarism_check_invalid_article(self):
        """Test plagiarism check with invalid article_id returns 404"""
        headers = get_admin_headers()
        response = requests.post(
            f"{BASE_URL}/api/plagiarism/check",
            json={"article_id": "invalid-article-id-12345"},
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Invalid article_id returns 404")
    
    def test_plagiarism_check_no_auth(self):
        """Test unauthenticated access is denied"""
        response = requests.post(
            f"{BASE_URL}/api/plagiarism/check",
            json={"article_id": "some-id"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print(f"✓ Unauthenticated access denied with status {response.status_code}")
    
    def test_plagiarism_status_invalid_job_id(self):
        """Test polling with invalid job_id returns 404"""
        headers = get_admin_headers()
        response = requests.get(
            f"{BASE_URL}/api/plagiarism/status/invalid-job-id-12345",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Invalid job_id returns 404")


class TestHealthEndpoints:
    """Test health endpoints"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        print(f"✓ Health endpoint accessible")
    
    def test_api_health_endpoint(self):
        """Test API health endpoint"""
        headers = get_admin_headers()
        response = requests.get(f"{BASE_URL}/api/health", headers=headers)
        assert response.status_code == 200
        print(f"✓ API health endpoint accessible")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
