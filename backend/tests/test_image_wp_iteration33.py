"""
Iteration 33: Test Image Generation datetime fix and WordPress Preview
- BUG FIX: Image generation status endpoint (datetime comparison fix)
- BUG FIX: Batch image generation status endpoint
- NEW FEATURE: WordPress Preview export format
- Meta regeneration section validation
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://surfer-content-hub.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "monika.gawkowska@kurdynowski.pl"
TEST_PASSWORD = "MonZuz8180!"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        return data["token"]
    
    def test_login_success(self):
        """Test login returns token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data


class TestImageGenerationDatetimeFix:
    """Test image generation status endpoint - datetime fix verification"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_single_image_generation_start(self, headers):
        """Test POST /api/images/generate returns job_id"""
        response = requests.post(f"{BASE_URL}/api/images/generate", json={
            "prompt": "TEST_Professional accounting office interior",
            "style": "hero"
        }, headers=headers)
        
        assert response.status_code == 200, f"Failed to start image generation: {response.text}"
        data = response.json()
        assert "job_id" in data, "No job_id in response"
        assert data.get("status") == "processing", f"Expected status 'processing', got {data.get('status')}"
        print(f"✓ Image generation started with job_id: {data['job_id']}")
    
    def test_single_image_generation_status_polling(self, headers):
        """Test GET /api/images/generate/status/{job_id} - the datetime fix"""
        # Start a new job
        start_response = requests.post(f"{BASE_URL}/api/images/generate", json={
            "prompt": "TEST_Modern tax consultant workspace",
            "style": "hero"
        }, headers=headers)
        
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        print(f"Started job: {job_id}")
        
        # Poll for status - THIS IS WHERE THE DATETIME BUG WAS
        # Previously returned 500 with "can't subtract offset-naive and offset-aware datetimes"
        max_polls = 15  # ~45 seconds max
        final_status = None
        
        for i in range(max_polls):
            time.sleep(3)
            status_response = requests.get(f"{BASE_URL}/api/images/generate/status/{job_id}")
            
            # The key assertion - should NOT return 500
            assert status_response.status_code == 200, f"Status endpoint returned {status_response.status_code}: {status_response.text}"
            
            status_data = status_response.json()
            print(f"Poll {i+1}: status={status_data.get('status')}")
            
            if status_data.get("status") == "completed":
                final_status = "completed"
                assert "result" in status_data, "Completed but no result"
                assert "data" in status_data.get("result", {}), "Result missing image data"
                print(f"✓ Image generation completed successfully")
                break
            elif status_data.get("status") == "failed":
                final_status = "failed"
                print(f"Image generation failed: {status_data.get('error')}")
                break
            elif status_data.get("status") == "processing":
                final_status = "processing"
                continue
        
        # We should get a valid status (not 500 error)
        assert final_status in ["completed", "failed", "processing"], f"Unexpected final status: {final_status}"
        print(f"✓ Status polling works correctly (datetime fix verified)")
    
    def test_status_invalid_job_id(self):
        """Test status endpoint with invalid job_id returns 404"""
        response = requests.get(f"{BASE_URL}/api/images/generate/status/invalid-job-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid job_id returns 404")


class TestBatchImageGeneration:
    """Test batch image generation - datetime fix for batch jobs"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_batch_generation_start(self, headers):
        """Test POST /api/images/generate-batch returns job_id"""
        response = requests.post(f"{BASE_URL}/api/images/generate-batch", json={
            "prompt": "TEST_Polish accounting firm logo",
            "style": "hero",
            "num_variants": 2
        }, headers=headers)
        
        assert response.status_code == 200, f"Failed to start batch: {response.text}"
        data = response.json()
        assert "job_id" in data
        assert data.get("status") == "processing"
        assert data.get("total") == 2
        print(f"✓ Batch generation started with job_id: {data['job_id']}")
    
    def test_batch_generation_status_polling(self, headers):
        """Test batch status polling - datetime fix verification"""
        # Start batch job with 2 variants
        start_response = requests.post(f"{BASE_URL}/api/images/generate-batch", json={
            "prompt": "TEST_Tax document illustration",
            "style": "ilustracja",
            "num_variants": 2
        }, headers=headers)
        
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        print(f"Started batch job: {job_id}")
        
        # Poll for status
        max_polls = 25  # ~75 seconds for 2 variants
        final_status = None
        
        for i in range(max_polls):
            time.sleep(3)
            status_response = requests.get(f"{BASE_URL}/api/images/generate/status/{job_id}")
            
            # Should NOT return 500 (datetime fix)
            assert status_response.status_code == 200, f"Batch status returned {status_response.status_code}: {status_response.text}"
            
            status_data = status_response.json()
            print(f"Poll {i+1}: status={status_data.get('status')}")
            
            if status_data.get("status") == "completed":
                final_status = "completed"
                result = status_data.get("result", {})
                variants = result.get("variants", [])
                print(f"✓ Batch completed with {len(variants)} variants")
                assert len(variants) > 0, "No variants in result"
                break
            elif status_data.get("status") == "failed":
                final_status = "failed"
                print(f"Batch failed: {status_data.get('error')}")
                break
            elif status_data.get("status") == "processing":
                final_status = "processing"
                continue
        
        assert final_status in ["completed", "failed", "processing"]
        print(f"✓ Batch status polling works correctly")
    
    def test_batch_invalid_num_variants(self, headers):
        """Test batch with invalid num_variants returns 400"""
        response = requests.post(f"{BASE_URL}/api/images/generate-batch", json={
            "prompt": "TEST_Invalid batch",
            "style": "hero",
            "num_variants": 10  # Max is 4
        }, headers=headers)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid num_variants returns 400")


class TestWordPressPreview:
    """Test WordPress Preview export format"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_article_id(self, headers):
        """Get an existing article ID for testing"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) > 0, "No articles found for testing"
        return articles[0]["id"]
    
    def test_wordpress_export_format(self, headers, test_article_id):
        """Test POST /api/articles/{id}/export with format='wordpress'"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/export",
            json={"format": "wordpress"},
            headers=headers
        )
        
        assert response.status_code == 200, f"WordPress export failed: {response.text}"
        data = response.json()
        
        assert data.get("format") == "wordpress", f"Expected format 'wordpress', got {data.get('format')}"
        assert "content" in data, "No content in response"
        assert len(data["content"]) > 0, "Empty content"
        
        # Verify it's styled HTML content
        content = data["content"]
        assert "<" in content, "Content doesn't look like HTML"
        print(f"✓ WordPress export returns styled content ({len(content)} chars)")
    
    def test_wordpress_export_contains_styling(self, headers, test_article_id):
        """Verify WordPress export contains proper styling"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/export",
            json={"format": "wordpress"},
            headers=headers
        )
        
        assert response.status_code == 200
        content = response.json().get("content", "")
        
        # Check for common WordPress-styled elements
        has_styling = (
            "style=" in content or 
            "class=" in content or
            "<div" in content or
            "<article" in content
        )
        assert has_styling, "WordPress content lacks styling"
        print("✓ WordPress export contains styling")
    
    def test_export_invalid_format(self, headers, test_article_id):
        """Test export with invalid format returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/export",
            json={"format": "invalid_format"},
            headers=headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid export format returns 400")


class TestMetaRegeneration:
    """Test meta regeneration section validation fix"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_article_id(self, headers):
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        assert response.status_code == 200
        articles = response.json()
        assert len(articles) > 0
        return articles[0]["id"]
    
    def test_regenerate_meta_section(self, headers, test_article_id):
        """Test POST /api/articles/{id}/regenerate with section='meta'"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "meta"},
            headers=headers,
            timeout=60
        )
        
        assert response.status_code == 200, f"Meta regeneration failed: {response.text}"
        data = response.json()
        
        assert "meta_title" in data, "No meta_title in response"
        assert len(data["meta_title"]) > 0, "Empty meta_title"
        print(f"✓ Meta regeneration returns meta_title: {data['meta_title'][:50]}...")
    
    def test_regenerate_faq_section(self, headers, test_article_id):
        """Test POST /api/articles/{id}/regenerate with section='faq'"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "faq"},
            headers=headers,
            timeout=60
        )
        
        assert response.status_code == 200, f"FAQ regeneration failed: {response.text}"
        data = response.json()
        
        assert "faq" in data, "No faq in response"
        assert isinstance(data["faq"], list), "faq is not a list"
        assert len(data["faq"]) > 0, "Empty faq array"
        print(f"✓ FAQ regeneration returns {len(data['faq'])} FAQ items")
    
    def test_regenerate_invalid_section(self, headers, test_article_id):
        """Test POST /api/articles/{id}/regenerate with invalid section returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "invalid_section"},
            headers=headers
        )
        
        # Should return 400 (not 500) after the fix
        assert response.status_code == 400, f"Expected 400 for invalid section, got {response.status_code}: {response.text}"
        print("✓ Invalid section returns 400 (validation fix verified)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
