"""
Phase 2 Features Test Suite - Iteration 14
Tests: SEO Audit, Auto-Update, Competition Analysis, Design Modernization, Multi-file Image Generator
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://content-craft-ai-4.preview.emergentagent.com')

# Test credentials
TEST_EMAIL = "monika.gawkowska@kurdynowski.pl"
TEST_PASSWORD = "MonZuz8180!"


class TestAuthFlow:
    """Test authentication first"""
    
    def test_login_success(self):
        """Login with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in response"
        assert "user" in data, "No user in response"
        assert data["user"]["is_admin"] == True, "User should be admin"
        print(f"✓ Login successful for admin user")
        return data["token"]


class TestSEOAudit:
    """Test SEO Audit functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json()["token"]
    
    def test_seo_audit_without_auth(self):
        """SEO audit should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/seo-audit",
            json={"url": "https://example.com"},
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("✓ SEO audit requires authentication")
    
    def test_seo_audit_basic(self, auth_token):
        """Run SEO audit on example.com (quick test page)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/seo-audit",
            json={"url": "https://example.com"},
            headers=headers,
            timeout=90  # AI processing takes time
        )
        assert response.status_code == 200, f"SEO audit failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "overall_score" in data, "Missing overall_score"
        assert "grade" in data, "Missing grade"
        assert data["grade"] in ["A", "B", "C", "D", "F"], f"Invalid grade: {data['grade']}"
        assert 0 <= data["overall_score"] <= 100, "Score out of range"
        
        # Check category scores
        for category in ["on_page_seo", "content_analysis", "technical_seo"]:
            if category in data:
                assert "score" in data[category], f"Missing score in {category}"
        
        print(f"✓ SEO audit completed: Score={data['overall_score']}, Grade={data['grade']}")
        return data
    
    def test_seo_audit_history(self, auth_token):
        """Get SEO audit history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/seo-audit/history",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"History request failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "History should be a list"
        print(f"✓ SEO audit history retrieved: {len(data)} entries")


class TestAutoUpdate:
    """Test Auto-Update functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json()["token"]
    
    def test_check_updates_without_auth(self):
        """Check updates should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/articles/check-updates",
            json={},
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("✓ Check updates requires authentication")
    
    def test_check_updates(self, auth_token):
        """Run auto-update check on articles"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/articles/check-updates",
            json={},
            headers=headers,
            timeout=120  # AI processing takes time
        )
        assert response.status_code == 200, f"Check updates failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "articles_needing_update" in data or "up_to_date_articles" in data or "summary" in data, \
            "Response missing expected fields"
        
        # Can be empty lists if no articles
        needing = data.get("articles_needing_update", [])
        up_to_date = data.get("up_to_date_articles", [])
        
        print(f"✓ Auto-update check completed: {len(needing)} need updates, {len(up_to_date)} up to date")


class TestCompetitionAnalysis:
    """Test Competition Analysis functionality"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json()["token"]
    
    @pytest.fixture
    def article_id(self, auth_token):
        """Get an existing article ID for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/articles",
            headers=headers,
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Failed to get articles")
        articles = response.json()
        if not articles:
            pytest.skip("No articles available for testing")
        return articles[0]["id"]
    
    def test_competition_analysis_without_auth(self):
        """Competition analysis should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/competition/analyze",
            json={"article_id": "test", "competitor_url": "https://example.com"},
            timeout=30
        )
        assert response.status_code == 401, f"Expected 401 but got {response.status_code}"
        print("✓ Competition analysis requires authentication")


class TestExistingFeatures:
    """Verify existing features still work"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json()["token"]
    
    def test_health_check(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        print("✓ Health check passed")
    
    def test_get_articles(self, auth_token):
        """Get articles list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/articles",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Get articles failed: {response.text}"
        articles = response.json()
        assert isinstance(articles, list), "Articles should be a list"
        print(f"✓ Articles retrieved: {len(articles)} articles")
    
    def test_get_stats(self, auth_token):
        """Get dashboard stats"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/stats",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Get stats failed: {response.text}"
        data = response.json()
        assert "total_articles" in data, "Missing total_articles"
        assert "avg_seo_score" in data, "Missing avg_seo_score"
        print(f"✓ Stats retrieved: {data['total_articles']} articles, {data['avg_seo_score']}% avg score")
    
    def test_get_subscription_plans(self):
        """Get subscription plans (no auth needed)"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans", timeout=30)
        assert response.status_code == 200, f"Get plans failed: {response.text}"
        plans = response.json()
        assert isinstance(plans, list), "Plans should be a list"
        assert len(plans) > 0, "Should have at least one plan"
        print(f"✓ Subscription plans retrieved: {len(plans)} plans")
    
    def test_get_templates(self):
        """Get content templates (no auth needed)"""
        response = requests.get(f"{BASE_URL}/api/templates", timeout=30)
        assert response.status_code == 200, f"Get templates failed: {response.text}"
        templates = response.json()
        assert isinstance(templates, list), "Templates should be a list"
        print(f"✓ Templates retrieved: {len(templates)} templates")
    
    def test_get_image_styles(self):
        """Get image styles (no auth needed)"""
        response = requests.get(f"{BASE_URL}/api/image-styles", timeout=30)
        assert response.status_code == 200, f"Get styles failed: {response.text}"
        styles = response.json()
        assert isinstance(styles, list), "Styles should be a list"
        print(f"✓ Image styles retrieved: {len(styles)} styles")


class TestImageGenerator:
    """Test Image Generator with multi-file support"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        if response.status_code != 200:
            pytest.skip("Authentication failed")
        return response.json()["token"]
    
    def test_image_library(self, auth_token):
        """Get image library"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/library/images",
            headers=headers,
            timeout=30
        )
        assert response.status_code == 200, f"Get library failed: {response.text}"
        data = response.json()
        assert "images" in data, "Missing images"
        assert "total" in data, "Missing total"
        print(f"✓ Image library retrieved: {data['total']} images")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
