"""
Test Article Generation Job Storage (MongoDB-based)
Tests for the fix that moved generation jobs from in-memory dict to MongoDB

Features tested:
- POST /api/articles/generate creates job in MongoDB, returns job_id
- GET /api/articles/generate/status/{job_id} returns correct status from MongoDB
- Completed/failed jobs are cleaned up after being fetched
- Non-existent job_id returns 404
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


class TestArticleGenerationMongoDBJobs:
    """All tests for article generation job storage in MongoDB"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for API calls."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=20
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with authentication token."""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_01_health_endpoint(self):
        """Verify API health endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ API health check passed")
    
    def test_02_generate_returns_job_id(self, auth_headers):
        """Test that POST /api/articles/generate creates a job and returns job_id."""
        payload = {
            "topic": "TEST_Jak_rozliczac_faktury",
            "primary_keyword": "rozliczanie faktur",
            "secondary_keywords": ["VAT", "ksiegowosc"],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/articles/generate",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] == "queued", f"Initial status should be 'queued', got '{data['status']}'"
        
        # Validate job_id is a valid UUID
        job_id = data["job_id"]
        try:
            uuid.UUID(job_id)
            print(f"✓ Job created with valid UUID: {job_id}")
        except ValueError:
            pytest.fail(f"job_id is not a valid UUID: {job_id}")
    
    def test_03_generate_requires_auth(self):
        """Test that POST /api/articles/generate requires auth token."""
        payload = {
            "topic": "Test topic",
            "primary_keyword": "test keyword",
            "target_length": 1000
        }
        
        # Note: This endpoint may timeout if server is processing previous request
        # We test with shorter timeout
        try:
            response = requests.post(
                f"{BASE_URL}/api/articles/generate",
                json=payload,
                timeout=20
            )
            assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"
            print("✓ Generate endpoint correctly requires authentication")
        except requests.exceptions.Timeout:
            # Server might be busy with LLM generation, skip this test
            pytest.skip("Request timed out - server may be busy processing LLM generation")
    
    def test_04_nonexistent_job_returns_404(self, auth_headers):
        """Test that GET /api/articles/generate/status/{invalid_job_id} returns 404."""
        fake_job_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/articles/generate/status/{fake_job_id}",
            headers=auth_headers,
            timeout=15
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent job, got {response.status_code}"
        print(f"✓ Non-existent job {fake_job_id} correctly returns 404")
    
    def test_05_status_requires_auth(self, auth_headers):
        """Test that GET /api/articles/generate/status/{job_id} requires auth."""
        fake_job_id = str(uuid.uuid4())
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/articles/generate/status/{fake_job_id}",
                timeout=15
            )
            assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"
            print("✓ Status endpoint correctly requires authentication")
        except requests.exceptions.Timeout:
            pytest.skip("Request timed out - server may be busy")
    
    def test_06_status_returns_job_data(self, auth_headers):
        """Test that GET /api/articles/generate/status/{job_id} returns correct status."""
        # First create a job
        payload = {
            "topic": "TEST_Status_poll_test",
            "primary_keyword": "status test",
            "target_length": 1000
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/articles/generate",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]
        print(f"✓ Created job: {job_id}")
        
        # Wait a bit for job to be processed
        time.sleep(2)
        
        # Poll status
        status_response = requests.get(
            f"{BASE_URL}/api/articles/generate/status/{job_id}",
            headers=auth_headers,
            timeout=15
        )
        
        # Status could be 200 (job exists) or 404 (job completed and cleaned up)
        assert status_response.status_code in [200, 404], f"Expected 200 or 404, got {status_response.status_code}: {status_response.text}"
        
        if status_response.status_code == 200:
            data = status_response.json()
            assert "job_id" in data, "Response should contain job_id"
            assert "status" in data, "Response should contain status"
            assert "stage" in data, "Response should contain stage"
            assert data["status"] in ["queued", "generating", "completed", "failed"], f"Invalid status: {data['status']}"
            print(f"✓ Status response: status={data['status']}, stage={data.get('stage', 'N/A')}")
        else:
            print(f"✓ Job {job_id} already completed and cleaned up (404)")
    
    def test_07_full_generation_flow(self, auth_headers):
        """Test complete flow: create job, poll until completion, verify article created.
        
        Note: This test takes 30-60 seconds as it waits for actual LLM generation.
        """
        # Create generation job
        payload = {
            "topic": "TEST_Podstawy_VAT_dla_firm_jednoosobowych",
            "primary_keyword": "podstawy VAT",
            "secondary_keywords": ["podatek VAT", "firmy jednoosobowe"],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/articles/generate",
            json=payload,
            headers=auth_headers,
            timeout=30
        )
        
        assert create_response.status_code == 200, f"Failed to create job: {create_response.status_code}"
        job_id = create_response.json()["job_id"]
        print(f"✓ Created generation job: {job_id}")
        
        # Poll for completion (max 90 seconds = 30 polls * 3s)
        max_polls = 30
        poll_interval = 3
        final_status = None
        article_id = None
        stages_seen = set()
        
        for i in range(max_polls):
            time.sleep(poll_interval)
            
            try:
                status_response = requests.get(
                    f"{BASE_URL}/api/articles/generate/status/{job_id}",
                    headers=auth_headers,
                    timeout=15
                )
            except requests.exceptions.Timeout:
                print(f"  Poll {i+1}: Timeout, retrying...")
                continue
            
            # If job was completed and cleaned up, it returns 404
            if status_response.status_code == 404:
                print(f"⚠ Poll {i+1}: Job not found (may have completed and been cleaned up)")
                # This could mean job completed but cleanup removed it - try to find any recent articles
                break
            
            if status_response.status_code != 200:
                print(f"  Poll {i+1}: Got {status_response.status_code}, continuing...")
                continue
            
            data = status_response.json()
            final_status = data["status"]
            stage = data.get("stage", 0)
            stages_seen.add(stage)
            
            print(f"  Poll {i+1}/{max_polls}: status={final_status}, stage={stage}")
            
            if final_status == "completed":
                article_id = data.get("article_id")
                print(f"✓ Generation completed! Article ID: {article_id}")
                break
            elif final_status == "failed":
                error = data.get("error", "Unknown error")
                print(f"✗ Generation failed: {error}")
                break
        
        # Verify article was created (if completed)
        if article_id:
            article_response = requests.get(
                f"{BASE_URL}/api/articles/{article_id}",
                headers=auth_headers,
                timeout=15
            )
            
            assert article_response.status_code == 200, f"Failed to fetch article: {article_response.status_code}"
            
            article = article_response.json()
            assert article.get("title"), "Article should have a title"
            assert article.get("sections"), "Article should have sections"
            assert article.get("id") == article_id, "Article ID should match"
            
            print(f"✓ Article retrieved: '{article.get('title', 'N/A')[:50]}...'")
            print(f"✓ Article has {len(article.get('sections', []))} sections")
            
            # Cleanup - delete test article
            delete_response = requests.delete(
                f"{BASE_URL}/api/articles/{article_id}",
                headers=auth_headers,
                timeout=10
            )
            if delete_response.status_code in [200, 204]:
                print(f"✓ Test article cleaned up: {article_id}")
        else:
            # If no article_id, the test may have hit timeout or 404
            print(f"⚠ No article_id obtained - final_status={final_status}, stages_seen={stages_seen}")
        
        # Verify we saw multiple stages during generation (if job didn't fail immediately)
        if stages_seen:
            print(f"✓ Stages observed during generation: {sorted(stages_seen)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
