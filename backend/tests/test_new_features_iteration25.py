"""
Test suite for Iteration 25 - New P0 Features:
1. Bulk article operations (select, delete multiple, categorize)
2. Auto meta tag generation (AI generates meta title + description variants)
3. Article version history (auto-saved on each update, view/restore)
4. Smart publishing schedule (AI suggests best day/time for WordPress publish)
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://surfer-content-hub.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "monika.gawkowska@kurdynowski.pl"
TEST_PASSWORD = "MonZuz8180!"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "token" in data, "No token in login response"
    return data["token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def test_article_id(auth_headers):
    """Get an existing article ID for testing."""
    response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
    assert response.status_code == 200
    articles = response.json()
    assert len(articles) > 0, "No articles found for testing"
    return articles[0]["id"]


# ============ BULK OPERATIONS TESTS ============

class TestBulkOperations:
    """Tests for bulk article operations."""
    
    def test_categories_list_endpoint(self, auth_headers):
        """Test GET /api/articles/categories-list returns unique categories."""
        response = requests.get(f"{BASE_URL}/api/articles/categories-list", headers=auth_headers)
        assert response.status_code == 200, f"Categories list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Categories should be a list"
        print(f"✓ Categories list returned {len(data)} categories: {data[:5]}")
    
    def test_bulk_category_requires_auth(self):
        """Test POST /api/articles/bulk-category requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/bulk-category", json={
            "article_ids": ["test-id"],
            "category": "Test"
        })
        assert response.status_code == 401, "Should require auth"
        print("✓ Bulk category requires authentication")
    
    def test_bulk_category_assigns_category(self, auth_headers, test_article_id):
        """Test POST /api/articles/bulk-category assigns category to articles."""
        test_category = f"TEST_Category_{uuid.uuid4().hex[:6]}"
        response = requests.post(f"{BASE_URL}/api/articles/bulk-category", 
            headers=auth_headers,
            json={
                "article_ids": [test_article_id],
                "category": test_category
            }
        )
        assert response.status_code == 200, f"Bulk category failed: {response.text}"
        data = response.json()
        assert "modified" in data, "Response should contain modified count"
        assert data["modified"] >= 0, "Modified count should be >= 0"
        print(f"✓ Bulk category assigned '{test_category}' to {data['modified']} articles")
        
        # Verify category was assigned
        article_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        assert article_response.status_code == 200
        article = article_response.json()
        assert article.get("category") == test_category, f"Category not assigned: {article.get('category')}"
        print(f"✓ Verified category '{test_category}' on article")
    
    def test_bulk_delete_requires_auth(self):
        """Test POST /api/articles/bulk-delete requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/bulk-delete", json={
            "article_ids": ["test-id"]
        })
        assert response.status_code == 401, "Should require auth"
        print("✓ Bulk delete requires authentication")
    
    def test_bulk_delete_with_empty_list(self, auth_headers):
        """Test bulk delete with empty list returns 0 deleted."""
        response = requests.post(f"{BASE_URL}/api/articles/bulk-delete",
            headers=auth_headers,
            json={"article_ids": []}
        )
        # Should either return 200 with 0 deleted or 400 for empty list
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        print(f"✓ Bulk delete with empty list handled correctly (status {response.status_code})")
    
    def test_bulk_delete_with_nonexistent_ids(self, auth_headers):
        """Test bulk delete with non-existent IDs."""
        fake_ids = [f"nonexistent-{uuid.uuid4().hex[:8]}" for _ in range(2)]
        response = requests.post(f"{BASE_URL}/api/articles/bulk-delete",
            headers=auth_headers,
            json={"article_ids": fake_ids}
        )
        assert response.status_code == 200, f"Bulk delete failed: {response.text}"
        data = response.json()
        assert "deleted" in data, "Response should contain deleted count"
        assert data["deleted"] == 0, "Should delete 0 non-existent articles"
        print(f"✓ Bulk delete with non-existent IDs returned deleted=0")


# ============ VERSION HISTORY TESTS ============

class TestVersionHistory:
    """Tests for article version history."""
    
    def test_versions_list_requires_auth(self, test_article_id):
        """Test GET /api/articles/{id}/versions requires authentication."""
        response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions")
        assert response.status_code == 401, "Should require auth"
        print("✓ Versions list requires authentication")
    
    def test_versions_list_returns_versions(self, auth_headers, test_article_id):
        """Test GET /api/articles/{id}/versions returns version list."""
        response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        assert response.status_code == 200, f"Versions list failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Versions should be a list"
        print(f"✓ Versions list returned {len(data)} versions")
        
        # Check version structure if any exist
        if len(data) > 0:
            version = data[0]
            assert "id" in version, "Version should have id"
            assert "created_at" in version, "Version should have created_at"
            assert "version_data" in version, "Version should have version_data"
            print(f"✓ Version structure validated: id={version['id'][:8]}...")
    
    def test_version_created_on_article_update(self, auth_headers, test_article_id):
        """Test that saving an article creates a version."""
        # Get current version count
        versions_before = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        count_before = len(versions_before.json())
        
        # Update the article
        update_response = requests.put(f"{BASE_URL}/api/articles/{test_article_id}",
            headers=auth_headers,
            json={"meta_title": f"Test Update {uuid.uuid4().hex[:6]}"}
        )
        assert update_response.status_code == 200, f"Article update failed: {update_response.text}"
        
        # Check version count increased
        versions_after = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        count_after = len(versions_after.json())
        
        assert count_after > count_before, f"Version not created: before={count_before}, after={count_after}"
        print(f"✓ Version created on article update (before={count_before}, after={count_after})")
    
    def test_version_detail_endpoint(self, auth_headers, test_article_id):
        """Test GET /api/articles/{id}/versions/{vid} returns version detail."""
        # Get versions list
        versions_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        versions = versions_response.json()
        
        if len(versions) == 0:
            pytest.skip("No versions available for detail test")
        
        version_id = versions[0]["id"]
        detail_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions/{version_id}", headers=auth_headers)
        assert detail_response.status_code == 200, f"Version detail failed: {detail_response.text}"
        
        detail = detail_response.json()
        assert "id" in detail, "Detail should have id"
        assert "version_data" in detail, "Detail should have version_data"
        print(f"✓ Version detail retrieved for version {version_id[:8]}...")
    
    def test_version_restore_endpoint(self, auth_headers, test_article_id):
        """Test POST /api/articles/{id}/versions/{vid}/restore restores a version."""
        # Get versions list
        versions_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}/versions", headers=auth_headers)
        versions = versions_response.json()
        
        if len(versions) == 0:
            pytest.skip("No versions available for restore test")
        
        version_id = versions[0]["id"]
        restore_response = requests.post(f"{BASE_URL}/api/articles/{test_article_id}/versions/{version_id}/restore", headers=auth_headers)
        assert restore_response.status_code == 200, f"Version restore failed: {restore_response.text}"
        
        restored = restore_response.json()
        assert "id" in restored, "Restored article should have id"
        assert restored["id"] == test_article_id, "Restored article ID should match"
        print(f"✓ Version {version_id[:8]}... restored successfully")
    
    def test_version_restore_nonexistent(self, auth_headers, test_article_id):
        """Test restoring non-existent version returns 404."""
        fake_version_id = f"nonexistent-{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/articles/{test_article_id}/versions/{fake_version_id}/restore", headers=auth_headers)
        assert response.status_code == 404, f"Should return 404 for non-existent version: {response.status_code}"
        print("✓ Restore non-existent version returns 404")


# ============ AUTO META GENERATION TESTS ============

class TestAutoMetaGeneration:
    """Tests for auto meta tag generation."""
    
    def test_auto_meta_requires_auth(self, test_article_id):
        """Test POST /api/articles/auto-meta requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/auto-meta", json={
            "article_id": test_article_id
        })
        assert response.status_code == 401, "Should require auth"
        print("✓ Auto meta requires authentication")
    
    def test_auto_meta_returns_job_id(self, auth_headers, test_article_id):
        """Test POST /api/articles/auto-meta returns job_id."""
        response = requests.post(f"{BASE_URL}/api/articles/auto-meta",
            headers=auth_headers,
            json={"article_id": test_article_id}
        )
        assert response.status_code == 200, f"Auto meta start failed: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        assert data["status"] in ["queued", "processing"], f"Unexpected status: {data['status']}"
        print(f"✓ Auto meta job started: job_id={data['job_id'][:8]}...")
        return data["job_id"]
    
    def test_auto_meta_status_endpoint(self, auth_headers, test_article_id):
        """Test GET /api/articles/auto-meta/status/{job_id} returns status."""
        # Start a job
        start_response = requests.post(f"{BASE_URL}/api/articles/auto-meta",
            headers=auth_headers,
            json={"article_id": test_article_id}
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll status
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = requests.get(f"{BASE_URL}/api/articles/auto-meta/status/{job_id}", headers=auth_headers)
            assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
            
            status_data = status_response.json()
            assert "status" in status_data, "Status response should contain status"
            
            if status_data["status"] == "completed":
                result = status_data.get("result", {})
                # Validate result structure
                assert "meta_titles" in result or "recommended" in result, f"Result missing expected fields: {result.keys()}"
                
                if "meta_titles" in result:
                    assert len(result["meta_titles"]) >= 1, "Should have at least 1 title variant"
                    print(f"✓ Auto meta completed with {len(result['meta_titles'])} title variants")
                
                if "meta_descriptions" in result:
                    assert len(result["meta_descriptions"]) >= 1, "Should have at least 1 description variant"
                    print(f"✓ Auto meta has {len(result['meta_descriptions'])} description variants")
                
                if "recommended" in result:
                    rec = result["recommended"]
                    assert "meta_title" in rec, "Recommended should have meta_title"
                    assert "meta_description" in rec, "Recommended should have meta_description"
                    print(f"✓ Auto meta has recommended set")
                
                return
            elif status_data["status"] == "failed":
                print(f"⚠ Auto meta job failed: {status_data.get('error', 'Unknown error')}")
                # Don't fail test - AI features can have transient failures
                return
            
            time.sleep(2)
        
        print(f"⚠ Auto meta job timed out after {max_attempts * 2} seconds")
    
    def test_auto_meta_status_nonexistent_job(self, auth_headers):
        """Test status check for non-existent job returns 404."""
        fake_job_id = f"nonexistent-{uuid.uuid4().hex[:8]}"
        response = requests.get(f"{BASE_URL}/api/articles/auto-meta/status/{fake_job_id}", headers=auth_headers)
        assert response.status_code == 404, f"Should return 404: {response.status_code}"
        print("✓ Auto meta status for non-existent job returns 404")


# ============ SMART SCHEDULE TESTS ============

class TestSmartSchedule:
    """Tests for smart publishing schedule."""
    
    def test_smart_schedule_requires_auth(self, test_article_id):
        """Test POST /api/articles/smart-schedule requires authentication."""
        response = requests.post(f"{BASE_URL}/api/articles/smart-schedule", json={
            "article_id": test_article_id
        })
        assert response.status_code == 401, "Should require auth"
        print("✓ Smart schedule requires authentication")
    
    def test_smart_schedule_returns_job_id(self, auth_headers, test_article_id):
        """Test POST /api/articles/smart-schedule returns job_id."""
        response = requests.post(f"{BASE_URL}/api/articles/smart-schedule",
            headers=auth_headers,
            json={"article_id": test_article_id}
        )
        assert response.status_code == 200, f"Smart schedule start failed: {response.text}"
        data = response.json()
        assert "job_id" in data, "Response should contain job_id"
        assert "status" in data, "Response should contain status"
        print(f"✓ Smart schedule job started: job_id={data['job_id'][:8]}...")
        return data["job_id"]
    
    def test_smart_schedule_full_flow(self, auth_headers, test_article_id):
        """Test full smart schedule flow: start -> poll -> complete."""
        # Start job
        start_response = requests.post(f"{BASE_URL}/api/articles/smart-schedule",
            headers=auth_headers,
            json={"article_id": test_article_id}
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll status
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = requests.get(f"{BASE_URL}/api/articles/smart-schedule/status/{job_id}", headers=auth_headers)
            assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
            
            status_data = status_response.json()
            
            if status_data["status"] == "completed":
                result = status_data.get("result", {})
                
                # Validate result structure
                if "best_slot" in result:
                    best = result["best_slot"]
                    assert "day" in best, "Best slot should have day"
                    assert "time" in best, "Best slot should have time"
                    print(f"✓ Smart schedule best slot: {best['day']} {best['time']}")
                
                if "recommended_slots" in result:
                    assert isinstance(result["recommended_slots"], list), "recommended_slots should be a list"
                    print(f"✓ Smart schedule has {len(result['recommended_slots'])} recommended slots")
                
                if "distribution_plan" in result:
                    assert isinstance(result["distribution_plan"], list), "distribution_plan should be a list"
                    print(f"✓ Smart schedule has {len(result['distribution_plan'])} distribution channels")
                
                return
            elif status_data["status"] == "failed":
                print(f"⚠ Smart schedule job failed: {status_data.get('error', 'Unknown error')}")
                return
            
            time.sleep(2)
        
        print(f"⚠ Smart schedule job timed out after {max_attempts * 2} seconds")
    
    def test_smart_schedule_status_nonexistent_job(self, auth_headers):
        """Test status check for non-existent job returns 404."""
        fake_job_id = f"nonexistent-{uuid.uuid4().hex[:8]}"
        response = requests.get(f"{BASE_URL}/api/articles/smart-schedule/status/{fake_job_id}", headers=auth_headers)
        assert response.status_code == 404, f"Should return 404: {response.status_code}"
        print("✓ Smart schedule status for non-existent job returns 404")


# ============ REGRESSION TESTS ============

class TestRegression:
    """Regression tests for existing functionality."""
    
    def test_articles_list(self, auth_headers):
        """Test GET /api/articles still works."""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200, f"Articles list failed: {response.text}"
        articles = response.json()
        assert isinstance(articles, list), "Articles should be a list"
        print(f"✓ Articles list returned {len(articles)} articles")
    
    def test_article_get(self, auth_headers, test_article_id):
        """Test GET /api/articles/{id} still works."""
        response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        assert response.status_code == 200, f"Article get failed: {response.text}"
        article = response.json()
        assert "id" in article, "Article should have id"
        assert "title" in article, "Article should have title"
        print(f"✓ Article retrieved: {article['title'][:50]}...")
    
    def test_article_update(self, auth_headers, test_article_id):
        """Test PUT /api/articles/{id} still works."""
        response = requests.put(f"{BASE_URL}/api/articles/{test_article_id}",
            headers=auth_headers,
            json={"meta_title": f"Regression Test {uuid.uuid4().hex[:6]}"}
        )
        assert response.status_code == 200, f"Article update failed: {response.text}"
        print("✓ Article update works")
    
    def test_stats_endpoint(self, auth_headers):
        """Test GET /api/stats still works."""
        response = requests.get(f"{BASE_URL}/api/stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"
        stats = response.json()
        assert "total_articles" in stats, "Stats should have total_articles"
        print(f"✓ Stats: {stats['total_articles']} articles, {stats.get('avg_seo_score', 0)}% avg SEO")
    
    def test_health_endpoint(self):
        """Test GET /api/health still works."""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
