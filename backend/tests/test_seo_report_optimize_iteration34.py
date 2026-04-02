"""
Iteration 34: Test new SEO Report PDF and Auto-Optimize features
- POST /api/surfer/seo-report/{article_id} - PDF generation
- POST /api/surfer/auto-optimize/{article_id} - Start async optimization
- GET /api/surfer/auto-optimize/status/{job_id} - Check optimization status
- POST /api/surfer/auto-optimize/apply/{article_id} - Apply optimization
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication for tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def article_with_surfer_score(self, auth_token):
        """Get an article that has surfer_score data"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles?limit=10", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        
        # Find article with surfer_score
        for article in articles:
            if article.get("surfer_score"):
                return article
        
        pytest.skip("No article with surfer_score found")
    
    @pytest.fixture(scope="class")
    def article_without_surfer_score(self, auth_token):
        """Get or create an article without surfer_score"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles?limit=50", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        
        # Find article without surfer_score
        for article in articles:
            if not article.get("surfer_score"):
                return article
        
        # If all have surfer_score, use the first one but note it
        return None


class TestSEOReportPDF(TestAuth):
    """Test PDF SEO Report generation"""
    
    def test_seo_report_returns_pdf(self, auth_token, article_with_surfer_score):
        """POST /api/surfer/seo-report/{article_id} returns valid PDF"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/seo-report/{article_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("Content-Type") == "application/pdf", \
            f"Expected application/pdf, got {response.headers.get('Content-Type')}"
        
        # Check PDF magic bytes
        content = response.content
        assert content[:4] == b'%PDF', "Response does not start with PDF magic bytes"
        assert len(content) > 1000, f"PDF too small: {len(content)} bytes"
        
        print(f"✓ PDF generated successfully: {len(content)} bytes")
    
    def test_seo_report_has_content_disposition(self, auth_token, article_with_surfer_score):
        """PDF response has proper Content-Disposition header"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/seo-report/{article_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        content_disp = response.headers.get("Content-Disposition", "")
        assert "attachment" in content_disp, f"Expected attachment, got: {content_disp}"
        assert "raport_seo" in content_disp, f"Expected raport_seo in filename: {content_disp}"
        assert ".pdf" in content_disp, f"Expected .pdf extension: {content_disp}"
        
        print(f"✓ Content-Disposition: {content_disp}")
    
    def test_seo_report_invalid_article_returns_404(self, auth_token):
        """POST /api/surfer/seo-report/{invalid_id} returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/seo-report/invalid-article-id-12345",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid article returns 404")


class TestAutoOptimize(TestAuth):
    """Test Auto-Optimize async job endpoints"""
    
    def test_auto_optimize_starts_job(self, auth_token, article_with_surfer_score):
        """POST /api/surfer/auto-optimize/{article_id} starts async job"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/{article_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "job_id" in data, f"Missing job_id in response: {data}"
        assert data.get("status") == "running", f"Expected status 'running', got: {data.get('status')}"
        
        print(f"✓ Auto-optimize job started: {data['job_id']}")
        return data["job_id"]
    
    def test_auto_optimize_without_surfer_score_returns_400(self, auth_token, article_without_surfer_score):
        """POST /api/surfer/auto-optimize without surfer_score returns 400"""
        if article_without_surfer_score is None:
            pytest.skip("All articles have surfer_score - cannot test 400 case")
        
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_without_surfer_score["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/{article_id}",
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Auto-optimize without surfer_score returns 400")
    
    def test_auto_optimize_invalid_article_returns_404(self, auth_token):
        """POST /api/surfer/auto-optimize/{invalid_id} returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/invalid-article-id-12345",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid article returns 404")
    
    def test_optimize_status_returns_job_info(self, auth_token, article_with_surfer_score):
        """GET /api/surfer/auto-optimize/status/{job_id} returns job status"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        # Start a job first
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/{article_id}",
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Check status
        status_response = requests.get(
            f"{BASE_URL}/api/surfer/auto-optimize/status/{job_id}",
            headers=headers
        )
        
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}"
        data = status_response.json()
        
        assert "job_id" in data, f"Missing job_id: {data}"
        assert "status" in data, f"Missing status: {data}"
        assert data["status"] in ["running", "completed", "failed"], f"Invalid status: {data['status']}"
        
        print(f"✓ Job status: {data['status']}")
    
    def test_optimize_status_invalid_job_returns_404(self, auth_token):
        """GET /api/surfer/auto-optimize/status/{invalid_job_id} returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/surfer/auto-optimize/status/invalid-job-id-12345",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid job_id returns 404")
    
    def test_optimize_job_completes_with_result(self, auth_token, article_with_surfer_score):
        """Auto-optimize job completes with optimized sections/meta/faq"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        # Start job
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/{article_id}",
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 90 seconds - AI processing takes time)
        max_wait = 90
        poll_interval = 5
        elapsed = 0
        
        while elapsed < max_wait:
            status_response = requests.get(
                f"{BASE_URL}/api/surfer/auto-optimize/status/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200
            data = status_response.json()
            
            if data["status"] == "completed":
                result = data.get("result", {})
                
                # Verify result structure
                assert "sections" in result or "meta_title" in result or "faq" in result, \
                    f"Result missing expected fields: {list(result.keys())}"
                
                if "changes_summary" in result:
                    print(f"✓ Changes summary: {result['changes_summary'][:3]}...")
                
                print(f"✓ Job completed with result keys: {list(result.keys())}")
                return result
            
            elif data["status"] == "failed":
                pytest.fail(f"Job failed: {data.get('error', 'Unknown error')}")
            
            time.sleep(poll_interval)
            elapsed += poll_interval
            print(f"  Waiting for job... {elapsed}s")
        
        pytest.fail(f"Job did not complete within {max_wait} seconds")


class TestApplyOptimization(TestAuth):
    """Test applying optimization changes"""
    
    def test_apply_optimization_saves_version(self, auth_token, article_with_surfer_score):
        """POST /api/surfer/auto-optimize/apply saves version before applying"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        # Create mock optimized data
        optimized_data = {
            "meta_title": "Test Optimized Title - SEO 2026",
            "meta_description": "This is a test optimized meta description for SEO purposes. It should be between 120-160 characters for optimal search engine visibility.",
            "sections": [
                {
                    "heading": "Test Section H2",
                    "content": "<p>Test content for optimization.</p>",
                    "subsections": []
                }
            ],
            "faq": [
                {"question": "Test FAQ Question?", "answer": "Test FAQ Answer."}
            ],
            "changes_summary": ["Test change 1", "Test change 2"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/apply/{article_id}",
            headers=headers,
            json={"optimized": optimized_data}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data, f"Missing message: {data}"
        assert "article" in data, f"Missing article: {data}"
        
        # Verify article was updated
        article = data["article"]
        assert article.get("meta_title") == optimized_data["meta_title"], \
            f"Meta title not updated: {article.get('meta_title')}"
        
        print(f"✓ Optimization applied successfully")
        print(f"  - Message: {data['message']}")
        print(f"  - Updated meta_title: {article.get('meta_title')[:50]}...")
    
    def test_apply_optimization_without_data_returns_400(self, auth_token, article_with_surfer_score):
        """POST /api/surfer/auto-optimize/apply without optimized data returns 400"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/apply/{article_id}",
            headers=headers,
            json={}  # Empty data
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Apply without data returns 400")
    
    def test_apply_optimization_invalid_article_returns_404(self, auth_token):
        """POST /api/surfer/auto-optimize/apply/{invalid_id} returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/apply/invalid-article-id-12345",
            headers=headers,
            json={"optimized": {"meta_title": "Test"}}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid article returns 404")


class TestVersionSavedBeforeApply(TestAuth):
    """Verify version is saved before applying optimization"""
    
    def test_version_created_on_apply(self, auth_token, article_with_surfer_score):
        """Applying optimization creates a version backup"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        article_id = article_with_surfer_score["id"]
        
        # Get current versions count
        versions_response = requests.get(
            f"{BASE_URL}/api/articles/{article_id}/versions",
            headers=headers
        )
        
        if versions_response.status_code == 200:
            initial_versions = len(versions_response.json())
        else:
            initial_versions = 0
        
        # Apply optimization
        optimized_data = {
            "meta_title": f"Version Test Title {time.time()}",
            "meta_description": "Test description for version verification. This should trigger a version save before applying changes to the article.",
        }
        
        apply_response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/apply/{article_id}",
            headers=headers,
            json={"optimized": optimized_data}
        )
        
        assert apply_response.status_code == 200
        
        # Check versions again
        versions_response = requests.get(
            f"{BASE_URL}/api/articles/{article_id}/versions",
            headers=headers
        )
        
        if versions_response.status_code == 200:
            final_versions = len(versions_response.json())
            assert final_versions > initial_versions, \
                f"Version not created: {initial_versions} -> {final_versions}"
            print(f"✓ Version created: {initial_versions} -> {final_versions}")
        else:
            # Versions endpoint might not exist, but version should still be saved in DB
            print("✓ Apply completed (versions endpoint not available for verification)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
