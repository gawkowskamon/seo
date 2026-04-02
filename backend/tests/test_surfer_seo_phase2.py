"""
Test suite for Phase 2 Surfer SEO endpoints:
- POST /api/surfer/keyword-research
- POST /api/surfer/content-planner
- POST /api/surfer/audit-url
- POST /api/surfer/analyze-serp/async
- GET /api/surfer/analyze-serp/status/{job_id}
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
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("token")


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestSurferKeywordResearch:
    """Tests for POST /api/surfer/keyword-research endpoint."""
    
    def test_keyword_research_success(self, auth_headers):
        """Test keyword research with valid seed keyword."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/keyword-research",
            json={"seed_keyword": "podatki"},
            headers=auth_headers,
            timeout=120  # LLM calls can take time
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "main_keyword" in data, "Response should contain main_keyword"
        assert "keywords" in data, "Response should contain keywords array"
        
        # Verify main_keyword structure
        main_kw = data["main_keyword"]
        assert "keyword" in main_kw, "main_keyword should have keyword field"
        assert "monthly_volume" in main_kw, "main_keyword should have monthly_volume"
        assert "difficulty" in main_kw, "main_keyword should have difficulty"
        
        # Verify keywords array
        assert isinstance(data["keywords"], list), "keywords should be a list"
        assert len(data["keywords"]) > 0, "keywords should not be empty"
        
        # Verify first keyword structure
        first_kw = data["keywords"][0]
        assert "keyword" in first_kw, "keyword item should have keyword field"
        assert "monthly_volume" in first_kw, "keyword item should have monthly_volume"
        print(f"✓ Keyword research returned {len(data['keywords'])} related keywords")
    
    def test_keyword_research_missing_seed(self, auth_headers):
        """Test keyword research without seed_keyword returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/keyword-research",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_keyword_research_no_auth(self):
        """Test keyword research without auth returns 401."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/keyword-research",
            json={"seed_keyword": "test"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestSurferContentPlanner:
    """Tests for POST /api/surfer/content-planner endpoint."""
    
    def test_content_planner_success(self, auth_headers):
        """Test content planner with valid keywords array."""
        keywords = ["podatki", "księgowość", "VAT", "PIT", "CIT", "faktura"]
        response = requests.post(
            f"{BASE_URL}/api/surfer/content-planner",
            json={"keywords": keywords},
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "clusters" in data, "Response should contain clusters array"
        assert isinstance(data["clusters"], list), "clusters should be a list"
        assert len(data["clusters"]) > 0, "clusters should not be empty"
        
        # Verify cluster structure
        first_cluster = data["clusters"][0]
        assert "topic" in first_cluster, "cluster should have topic"
        assert "primary_keyword" in first_cluster, "cluster should have primary_keyword"
        assert "keywords" in first_cluster, "cluster should have keywords array"
        print(f"✓ Content planner returned {len(data['clusters'])} clusters")
    
    def test_content_planner_missing_keywords(self, auth_headers):
        """Test content planner without keywords returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/content-planner",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    
    def test_content_planner_empty_keywords(self, auth_headers):
        """Test content planner with empty keywords array returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/content-planner",
            json={"keywords": []},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestSurferAuditURL:
    """Tests for POST /api/surfer/audit-url endpoint."""
    
    def test_audit_url_success(self, auth_headers):
        """Test URL audit with valid URL."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/audit-url",
            json={"url": "https://www.google.com"},
            headers=auth_headers,
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "overall_score" in data, "Response should contain overall_score"
        assert "issues" in data, "Response should contain issues array"
        assert "opportunities" in data, "Response should contain opportunities array"
        assert "content_analysis" in data, "Response should contain content_analysis"
        
        # Verify overall_score is a number
        assert isinstance(data["overall_score"], (int, float)), "overall_score should be numeric"
        
        # Verify issues array
        assert isinstance(data["issues"], list), "issues should be a list"
        
        # Verify content_analysis structure
        content = data["content_analysis"]
        assert "word_count" in content, "content_analysis should have word_count"
        print(f"✓ URL audit returned score {data['overall_score']} with {len(data['issues'])} issues")
    
    def test_audit_url_missing_url(self, auth_headers):
        """Test URL audit without url returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/audit-url",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestSurferAsyncSERP:
    """Tests for async SERP analysis endpoints."""
    
    def test_analyze_serp_async_start(self, auth_headers):
        """Test starting async SERP analysis job."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={"keyword": "księgowość"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] == "running", f"Expected status 'running', got {data['status']}"
        print(f"✓ Async SERP analysis started with job_id: {data['job_id']}")
        return data["job_id"]
    
    def test_analyze_serp_status(self, auth_headers):
        """Test checking SERP analysis job status."""
        # First start a job
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={"keyword": "podatki"},
            headers=auth_headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Check status
        status_response = requests.get(
            f"{BASE_URL}/api/surfer/analyze-serp/status/{job_id}",
            headers=auth_headers
        )
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}"
        
        data = status_response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] in ["running", "completed", "failed"], f"Unexpected status: {data['status']}"
        print(f"✓ SERP job status: {data['status']}")
    
    def test_analyze_serp_status_invalid_job(self, auth_headers):
        """Test checking status of non-existent job returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/surfer/analyze-serp/status/invalid-job-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_analyze_serp_async_missing_keyword(self, auth_headers):
        """Test async SERP analysis without keyword returns 400."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={},
            headers=auth_headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"


class TestSurferSyncSERP:
    """Tests for sync SERP analysis endpoint."""
    
    def test_analyze_serp_sync(self, auth_headers):
        """Test synchronous SERP analysis."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp",
            json={"keyword": "VAT"},
            headers=auth_headers,
            timeout=180  # LLM calls can take time
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "keyword" in data, "Response should contain keyword"
        assert "benchmarks" in data, "Response should contain benchmarks"
        assert "nlp_terms" in data, "Response should contain nlp_terms"
        
        # Verify benchmarks structure
        benchmarks = data["benchmarks"]
        assert "word_count" in benchmarks, "benchmarks should have word_count"
        assert "headings" in benchmarks, "benchmarks should have headings"
        print(f"✓ Sync SERP analysis returned data for keyword: {data['keyword']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
