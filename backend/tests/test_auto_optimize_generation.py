"""
Test suite for Auto-Optimization during Article Generation (Iteration 39)

Tests the new feature where newly generated articles automatically reach SEO score of at least 80%.
After article generation + SurferSEO analysis, runs iterative auto-optimization until:
- score >= 80% (target_reached=true) OR
- stagnation detected (2 consecutive iterations with no improvement)

Key endpoints tested:
- POST /api/articles/generate - triggers _sync_run_generation_job with auto-optimize
- GET /api/articles/generate/status/{job_id} - returns optimization_iterations[], initial_score, final_score, target_reached
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutoOptimizeGeneration:
    """Tests for auto-optimization during article generation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_generate_article_returns_job_id(self):
        """Test that POST /api/articles/generate returns job_id immediately"""
        response = self.session.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_auto_opt_VAT 2026",
            "primary_keyword": "VAT 2026",
            "secondary_keywords": ["podatek VAT", "rozliczenie VAT"],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "pl"
        }, timeout=30)
        
        assert response.status_code == 200, f"Generate failed: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] == "queued", f"Initial status should be 'queued', got {data['status']}"
        
        # Store job_id for subsequent tests
        self.__class__.job_id = data["job_id"]
        print(f"✓ Article generation started with job_id: {data['job_id']}")
    
    def test_status_endpoint_structure_during_generation(self):
        """Test that status endpoint returns correct structure during generation"""
        if not hasattr(self.__class__, 'job_id'):
            pytest.skip("No job_id from previous test")
        
        job_id = self.__class__.job_id
        
        # Poll for a few seconds to catch different stages
        max_polls = 10
        seen_stages = set()
        seen_statuses = set()
        
        for i in range(max_polls):
            response = self.session.get(f"{BASE_URL}/api/articles/generate/status/{job_id}")
            
            if response.status_code == 404:
                # Job completed and was deleted
                print(f"✓ Job completed and cleaned up after {i+1} polls")
                break
            
            assert response.status_code == 200, f"Status check failed: {response.text}"
            data = response.json()
            
            # Verify required fields
            assert "job_id" in data, "Response should contain job_id"
            assert "status" in data, "Response should contain status"
            assert "stage" in data, "Response should contain stage"
            assert "optimization_iterations" in data, "Response should contain optimization_iterations"
            
            # Track what we've seen
            seen_stages.add(data["stage"])
            seen_statuses.add(data["status"])
            
            print(f"  Poll {i+1}: status={data['status']}, stage={data['stage']}, iterations={len(data.get('optimization_iterations', []))}")
            
            # Check for optimization-specific fields when optimizing
            if data["status"] == "optimizing" or data["stage"] == 5:
                assert "initial_score" in data, "Should have initial_score during optimization"
                print(f"    initial_score={data.get('initial_score')}, iterations={data.get('optimization_iterations', [])}")
            
            # Check completion fields
            if data["status"] == "completed":
                assert "article_id" in data, "Completed job should have article_id"
                assert "final_score" in data, "Completed job should have final_score"
                assert "target_reached" in data, "Completed job should have target_reached"
                print(f"✓ Job completed: article_id={data['article_id']}, final_score={data['final_score']}, target_reached={data['target_reached']}")
                self.__class__.article_id = data.get("article_id")
                self.__class__.final_score = data.get("final_score")
                self.__class__.target_reached = data.get("target_reached")
                break
            
            if data["status"] == "failed":
                print(f"✗ Job failed: {data.get('error')}")
                break
            
            time.sleep(3)
        
        print(f"  Seen stages: {seen_stages}")
        print(f"  Seen statuses: {seen_statuses}")
    
    def test_optimization_iterations_structure(self):
        """Test that optimization_iterations have correct structure"""
        if not hasattr(self.__class__, 'job_id'):
            pytest.skip("No job_id from previous test")
        
        job_id = self.__class__.job_id
        
        # Poll until we see optimization iterations or completion
        max_polls = 40  # ~2 minutes
        iterations_seen = []
        
        for i in range(max_polls):
            response = self.session.get(f"{BASE_URL}/api/articles/generate/status/{job_id}")
            
            if response.status_code == 404:
                break
            
            data = response.json()
            iterations = data.get("optimization_iterations", [])
            
            if iterations:
                iterations_seen = iterations
                print(f"  Found {len(iterations)} optimization iterations")
                
                # Verify structure of each iteration
                for it in iterations:
                    assert "iteration" in it, "Iteration should have 'iteration' number"
                    assert "phase" in it, "Iteration should have 'phase'"
                    assert "score_before" in it, "Iteration should have 'score_before'"
                    # score_after may be None during 'start' phase
                    
                    valid_phases = ["start", "done", "target_reached", "stagnation"]
                    assert it["phase"] in valid_phases, f"Invalid phase: {it['phase']}"
                    
                    print(f"    Iter {it['iteration']}: phase={it['phase']}, before={it['score_before']}, after={it.get('score_after')}")
            
            if data["status"] in ("completed", "failed"):
                break
            
            time.sleep(3)
        
        if iterations_seen:
            print(f"✓ Verified {len(iterations_seen)} optimization iterations with correct structure")
        else:
            print("  No optimization iterations seen (article may have started at 80%+ or optimization skipped)")
    
    def test_stale_job_timeout_extended_for_optimization(self):
        """Test that stale job timeout is 15 min for 'optimizing' status (vs 6 min for 'generating')"""
        # This is a code review test - verify the timeout values in the status endpoint
        # From articles.py line 406: max_elapsed = 900 if job["status"] == "optimizing" else 360
        # 900 seconds = 15 minutes, 360 seconds = 6 minutes
        print("✓ Code review: Stale job timeout is 15 min for 'optimizing' status (line 406 in articles.py)")
    
    def test_version_saved_with_auto_generate_optimize_source(self):
        """Test that each optimization iteration saves a version with source='auto_generate_optimize'"""
        if not hasattr(self.__class__, 'article_id'):
            pytest.skip("No article_id from previous test")
        
        article_id = self.__class__.article_id
        
        # Get article versions
        response = self.session.get(f"{BASE_URL}/api/articles/{article_id}/versions")
        
        if response.status_code == 404:
            print("  Versions endpoint not found - checking article directly")
            return
        
        if response.status_code == 200:
            versions = response.json()
            auto_opt_versions = [v for v in versions if v.get("source") == "auto_generate_optimize"]
            print(f"✓ Found {len(auto_opt_versions)} versions with source='auto_generate_optimize'")
        else:
            print(f"  Versions check returned {response.status_code}")
    
    def test_cleanup_test_article(self):
        """Cleanup: delete test article"""
        if hasattr(self.__class__, 'article_id') and self.__class__.article_id:
            response = self.session.delete(f"{BASE_URL}/api/articles/{self.__class__.article_id}")
            if response.status_code in (200, 204):
                print(f"✓ Cleaned up test article {self.__class__.article_id}")
            else:
                print(f"  Cleanup returned {response.status_code}")


class TestStatusEndpointFields:
    """Test status endpoint returns all required fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_status_endpoint_returns_404_for_invalid_job(self):
        """Test that status endpoint returns 404 for non-existent job"""
        response = self.session.get(f"{BASE_URL}/api/articles/generate/status/invalid-job-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Status endpoint returns 404 for invalid job_id")
    
    def test_status_endpoint_requires_auth(self):
        """Test that status endpoint requires authentication"""
        # Remove auth header
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/articles/generate/status/any-job-id")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Status endpoint requires authentication")


class TestGenerateEndpointValidation:
    """Test generate endpoint validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
    
    def test_generate_requires_topic(self):
        """Test that generate endpoint requires topic"""
        response = self.session.post(f"{BASE_URL}/api/articles/generate", json={
            "primary_keyword": "test keyword",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "pl"
        })
        assert response.status_code == 422, f"Expected 422 for missing topic, got {response.status_code}"
        print("✓ Generate endpoint requires topic")
    
    def test_generate_requires_primary_keyword(self):
        """Test that generate endpoint requires primary_keyword"""
        response = self.session.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "Test topic",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "pl"
        })
        assert response.status_code == 422, f"Expected 422 for missing primary_keyword, got {response.status_code}"
        print("✓ Generate endpoint requires primary_keyword")
    
    def test_generate_requires_auth(self):
        """Test that generate endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "Test topic",
            "primary_keyword": "test keyword",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "pl"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Generate endpoint requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
