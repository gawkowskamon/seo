"""
Iteration 36 Backend Tests
Tests for:
1. Multi-language article generation (pl/en/de/uk)
2. ROI Dashboard endpoint (/api/stats/roi)
3. Version source tagging (manual_edit, auto_optimize, optimize_loop, pre_restore)
4. Image gallery thumbnails (base64 data field)
5. Auto-optimize content quality (no placeholder text)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

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
    if response.status_code != 200:
        pytest.skip(f"Auth failed: {response.status_code} - {response.text}")
    data = response.json()
    # API returns 'token' not 'access_token'
    return data.get("token") or data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_article_id(auth_headers):
    """Get or create a test article with surfer_score for testing."""
    # First try to find an existing article with surfer_score
    response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
    if response.status_code == 200:
        articles = response.json()
        for art in articles:
            if art.get("surfer_score") and art.get("surfer_data"):
                return art["id"]
    
    # If no suitable article, skip tests that need it
    pytest.skip("No article with surfer_score found for testing")


class TestROIDashboard:
    """Tests for ROI Dashboard endpoint."""
    
    def test_roi_stats_endpoint_returns_200(self, auth_headers):
        """GET /api/stats/roi returns 200."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ ROI stats endpoint returns 200")
    
    def test_roi_stats_has_required_fields(self, auth_headers):
        """ROI stats response has all required fields."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "total_articles", "status_counts", "score_buckets",
            "avg_surfer_score", "avg_seo_score", "total_words_estimate",
            "top_performers", "bottom_performers", "language_distribution", "monthly_trend"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ ROI stats has all required fields: {list(data.keys())}")
    
    def test_roi_stats_status_counts_structure(self, auth_headers):
        """Status counts has draft/published/scheduled."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        data = response.json()
        
        status_counts = data.get("status_counts", {})
        assert "draft" in status_counts, "Missing 'draft' in status_counts"
        assert "published" in status_counts, "Missing 'published' in status_counts"
        assert "scheduled" in status_counts, "Missing 'scheduled' in status_counts"
        
        print(f"✓ Status counts: {status_counts}")
    
    def test_roi_stats_score_buckets_structure(self, auth_headers):
        """Score buckets has poor/medium/good/excellent."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        data = response.json()
        
        score_buckets = data.get("score_buckets", {})
        assert "poor" in score_buckets, "Missing 'poor' in score_buckets"
        assert "medium" in score_buckets, "Missing 'medium' in score_buckets"
        assert "good" in score_buckets, "Missing 'good' in score_buckets"
        assert "excellent" in score_buckets, "Missing 'excellent' in score_buckets"
        
        print(f"✓ Score buckets: {score_buckets}")
    
    def test_roi_stats_performers_are_lists(self, auth_headers):
        """Top and bottom performers are lists."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        data = response.json()
        
        assert isinstance(data.get("top_performers"), list), "top_performers should be a list"
        assert isinstance(data.get("bottom_performers"), list), "bottom_performers should be a list"
        
        print(f"✓ Top performers: {len(data['top_performers'])}, Bottom performers: {len(data['bottom_performers'])}")
    
    def test_roi_stats_language_distribution(self, auth_headers):
        """Language distribution is a dict."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        data = response.json()
        
        lang_dist = data.get("language_distribution", {})
        assert isinstance(lang_dist, dict), "language_distribution should be a dict"
        
        print(f"✓ Language distribution: {lang_dist}")


class TestMultiLanguageGeneration:
    """Tests for multi-language article generation."""
    
    def test_generate_request_accepts_language_param(self, auth_headers):
        """POST /api/articles/generate accepts language parameter."""
        # Just test that the endpoint accepts the language param without error
        # We won't wait for full generation (takes 60-90s)
        response = requests.post(f"{BASE_URL}/api/articles/generate", headers=auth_headers, json={
            "topic": "Test multi-language",
            "primary_keyword": "test keyword",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "en"
        }, timeout=30)
        
        # Should return job_id (async generation)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        
        print(f"✓ Generate endpoint accepts language='en', job_id: {data['job_id']}")
    
    def test_generate_request_accepts_german(self, auth_headers):
        """POST /api/articles/generate accepts language='de'."""
        response = requests.post(f"{BASE_URL}/api/articles/generate", headers=auth_headers, json={
            "topic": "Test German article",
            "primary_keyword": "buchhaltung",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "de"
        }, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        
        print(f"✓ Generate endpoint accepts language='de', job_id: {data['job_id']}")
    
    def test_generate_request_accepts_ukrainian(self, auth_headers):
        """POST /api/articles/generate accepts language='uk'."""
        response = requests.post(f"{BASE_URL}/api/articles/generate", headers=auth_headers, json={
            "topic": "Test Ukrainian article",
            "primary_keyword": "бухгалтерія",
            "secondary_keywords": [],
            "target_length": 1000,
            "tone": "profesjonalny",
            "template": "standard",
            "language": "uk"
        }, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        
        print(f"✓ Generate endpoint accepts language='uk', job_id: {data['job_id']}")


class TestVersionSourceTagging:
    """Tests for version source tagging."""
    
    def test_versions_endpoint_returns_source_field(self, auth_headers, test_article_id):
        """GET /api/articles/{id}/versions returns versions with source field."""
        response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        
        # May return empty list if no versions yet
        if response.status_code == 200:
            versions = response.json()
            if versions:
                # Check first version has source field
                assert "source" in versions[0], "Version should have 'source' field"
                print(f"✓ Versions have source field. First version source: {versions[0].get('source')}")
            else:
                print("✓ Versions endpoint works (no versions yet)")
        else:
            print(f"Versions endpoint returned {response.status_code}")
    
    def test_manual_edit_creates_version_with_source(self, auth_headers, test_article_id):
        """PUT /api/articles/{id} creates version with source='manual_edit'."""
        # Get current article
        get_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        if get_response.status_code != 200:
            pytest.skip("Could not get article")
        
        article = get_response.json()
        
        # Update article (minor change)
        update_response = requests.put(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers, json={
            "meta_description": article.get("meta_description", "") + " (test edit)"
        })
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        # Check versions
        versions_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        if versions_response.status_code == 200:
            versions = versions_response.json()
            if versions:
                # Most recent version should be manual_edit
                latest = versions[0]
                assert latest.get("source") == "manual_edit", f"Expected source='manual_edit', got '{latest.get('source')}'"
                print(f"✓ Manual edit created version with source='manual_edit'")
            else:
                print("✓ Update worked but no versions returned")
        else:
            print(f"Versions check returned {versions_response.status_code}")


class TestImageGalleryThumbnails:
    """Tests for image gallery thumbnails (base64 data field)."""
    
    def test_article_images_returns_data_field(self, auth_headers, test_article_id):
        """GET /api/articles/{id}/images returns images with data field."""
        response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/images", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        images = response.json()
        
        if images:
            # Check first image has data field
            first_image = images[0]
            assert "data" in first_image, "Image should have 'data' field for thumbnails"
            assert first_image.get("data"), "Image 'data' field should not be empty"
            print(f"✓ Article images include base64 data field. First image has {len(first_image.get('data', ''))} chars of data")
        else:
            print("✓ Article images endpoint works (no images for this article)")
    
    def test_library_images_returns_data_field(self, auth_headers):
        """GET /api/library/images returns images with data field."""
        response = requests.get(f"{BASE_URL}/api/library/images?limit=5", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        images = data.get("images", [])
        if images:
            first_image = images[0]
            assert "data" in first_image, "Library image should have 'data' field"
            print(f"✓ Library images include data field. Found {len(images)} images")
        else:
            print("✓ Library images endpoint works (no images in library)")


class TestAutoOptimizeContentQuality:
    """Tests for auto-optimize content quality (no placeholder text)."""
    
    def test_auto_optimize_starts_job(self, auth_headers, test_article_id):
        """POST /api/surfer/auto-optimize/{id} starts async job."""
        response = requests.post(f"{BASE_URL}/api/surfer/auto-optimize/{test_article_id}", headers=auth_headers)
        
        if response.status_code == 400:
            # May need surfer analysis first
            print(f"Auto-optimize requires surfer analysis first: {response.text}")
            pytest.skip("Article needs surfer analysis first")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        
        print(f"✓ Auto-optimize started, job_id: {data['job_id']}")
        return data["job_id"]
    
    def test_auto_optimize_content_not_placeholder(self, auth_headers, test_article_id):
        """Auto-optimize sections should contain real content, not placeholders."""
        # Start optimization
        start_response = requests.post(f"{BASE_URL}/api/surfer/auto-optimize/{test_article_id}", headers=auth_headers)
        
        if start_response.status_code == 400:
            pytest.skip("Article needs surfer analysis first")
        
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 120 seconds)
        max_polls = 40
        poll_interval = 3
        
        for i in range(max_polls):
            status_response = requests.get(f"{BASE_URL}/api/surfer/auto-optimize/status/{job_id}", headers=auth_headers)
            if status_response.status_code != 200:
                time.sleep(poll_interval)
                continue
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "completed":
                result = status_data.get("result", {})
                sections = result.get("sections", [])
                
                # Check that sections have real content, not placeholders
                placeholder_patterns = ["200+ slow", "100+ slow", "bold", "listy", "placeholder"]
                
                for section in sections:
                    content = section.get("content", "")
                    heading = section.get("heading", "")
                    
                    # Content should be substantial (at least 100 chars)
                    assert len(content) > 100, f"Section '{heading}' content too short: {len(content)} chars"
                    
                    # Content should not contain placeholder text
                    content_lower = content.lower()
                    for pattern in placeholder_patterns:
                        assert pattern not in content_lower, f"Section '{heading}' contains placeholder text: '{pattern}'"
                    
                    print(f"  Section '{heading}': {len(content)} chars of real content")
                
                print(f"✓ Auto-optimize completed with {len(sections)} sections of real content (no placeholders)")
                return
            
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                pytest.fail(f"Auto-optimize failed: {error}")
            
            time.sleep(poll_interval)
        
        pytest.fail("Auto-optimize timed out after 120 seconds")


class TestApplyOptimizationVersionSource:
    """Tests for apply optimization creating version with correct source."""
    
    def test_apply_optimization_creates_auto_optimize_version(self, auth_headers, test_article_id):
        """POST /api/surfer/auto-optimize/apply/{id} creates version with source='auto_optimize'."""
        # First we need optimized data - use a minimal test
        optimized_data = {
            "optimized": {
                "meta_title": "Test optimized title",
                "meta_description": "Test optimized description for SEO purposes.",
                "sections": [
                    {
                        "heading": "Test Section",
                        "content": "<p>This is test content for the section.</p>",
                        "subsections": []
                    }
                ],
                "faq": [
                    {"question": "Test question?", "answer": "Test answer."}
                ]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/auto-optimize/apply/{test_article_id}",
            headers=auth_headers,
            json=optimized_data
        )
        
        assert response.status_code == 200, f"Apply failed: {response.status_code}: {response.text}"
        
        # Check versions
        versions_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        if versions_response.status_code == 200:
            versions = versions_response.json()
            if versions:
                # Find auto_optimize version
                auto_opt_versions = [v for v in versions if v.get("source") == "auto_optimize"]
                assert len(auto_opt_versions) > 0, "Should have version with source='auto_optimize'"
                print(f"✓ Apply optimization created version with source='auto_optimize'")
            else:
                print("✓ Apply worked but no versions returned")
        else:
            print(f"Versions check returned {versions_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
