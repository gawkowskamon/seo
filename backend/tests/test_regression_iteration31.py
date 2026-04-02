"""
Regression Test Suite - Iteration 31
Testing all endpoints after major refactoring (server.py split into 10 route modules)

Modules tested:
- auth.py: Auth & Admin routes
- articles.py: Article CRUD, generation, export
- surfer.py: SurferSEO endpoints
- images.py: Image generation & library
- content.py: WordPress, calendar, chat
- seo_tools.py: SEO audit, analytics, plagiarism
- ai_features.py: Bulk ops, versions, meta, schedule
- social.py: Social media scheduling
- notifications.py: Email notifications
- competition_monitor.py: Competition monitoring
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


class TestHealthAndAuth:
    """Test health check and authentication endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_health_check(self):
        """GET /api/health - should return healthy status"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "llm_key_configured" in data
        print(f"✓ Health check passed: {data}")
    
    def test_login_success(self):
        """POST /api/auth/login - should return token and user"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Login success: user={data['user']['email']}, is_admin={data['user']['is_admin']}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login - should return 401 for invalid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected with 401")
    
    def test_get_me_without_auth(self):
        """GET /api/auth/me - should return 401 without token"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ /auth/me correctly requires authentication")


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login and get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["token"]
        self.user = response.json()["user"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_me(self):
        """GET /api/auth/me - should return current user"""
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ GET /auth/me: {data['email']}")
    
    def test_list_articles(self):
        """GET /api/articles - should return list of articles"""
        response = self.session.get(f"{BASE_URL}/api/articles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /articles: {len(data)} articles found")
    
    def test_get_stats(self):
        """GET /api/stats - should return dashboard statistics"""
        response = self.session.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "avg_seo_score" in data
        assert "needs_improvement" in data
        print(f"✓ GET /stats: total={data['total_articles']}, avg_seo={data['avg_seo_score']}")
    
    def test_list_templates(self):
        """GET /api/templates - should return content templates"""
        response = self.session.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"✓ GET /templates: templates loaded")
    
    def test_list_image_styles(self):
        """GET /api/image-styles - should return image styles"""
        response = self.session.get(f"{BASE_URL}/api/image-styles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"✓ GET /image-styles: styles loaded")


class TestSocialMediaScheduling:
    """Test social media scheduling endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.created_post_id = None
    
    def test_list_scheduled_posts(self):
        """GET /api/social/scheduled - should return scheduled posts"""
        response = self.session.get(f"{BASE_URL}/api/social/scheduled")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /social/scheduled: {len(data)} posts")
    
    def test_schedule_post_validation(self):
        """POST /api/social/schedule - should validate required fields"""
        # Missing platform
        response = self.session.post(f"{BASE_URL}/api/social/schedule", json={
            "text": "Test post",
            "scheduled_at": "2026-02-01T10:00:00Z"
        })
        assert response.status_code == 400
        print("✓ POST /social/schedule validates missing platform")
        
        # Missing text
        response = self.session.post(f"{BASE_URL}/api/social/schedule", json={
            "platform": "linkedin",
            "scheduled_at": "2026-02-01T10:00:00Z"
        })
        assert response.status_code == 400
        print("✓ POST /social/schedule validates missing text")
    
    def test_schedule_post_success(self):
        """POST /api/social/schedule - should create scheduled post"""
        response = self.session.post(f"{BASE_URL}/api/social/schedule", json={
            "platform": "linkedin",
            "text": "TEST_Regression test post for iteration 31",
            "scheduled_at": "2026-02-01T10:00:00Z",
            "hashtags": ["#test", "#regression"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["platform"] == "linkedin"
        assert data["status"] == "scheduled"
        self.created_post_id = data["id"]
        print(f"✓ POST /social/schedule: created post {data['id']}")
        
        # Cleanup
        if self.created_post_id:
            self.session.delete(f"{BASE_URL}/api/social/scheduled/{self.created_post_id}")


class TestNotifications:
    """Test notification endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_get_notification_settings(self):
        """GET /api/notifications/settings - should return settings"""
        response = self.session.get(f"{BASE_URL}/api/notifications/settings")
        assert response.status_code == 200
        data = response.json()
        assert "email_enabled" in data
        assert "frequency" in data
        print(f"✓ GET /notifications/settings: email_enabled={data['email_enabled']}, frequency={data['frequency']}")
    
    def test_check_updates(self):
        """POST /api/notifications/check-updates - should check article updates"""
        response = self.session.post(f"{BASE_URL}/api/notifications/check-updates")
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        print(f"✓ POST /notifications/check-updates: {data['total']} notifications")
    
    def test_notification_settings_without_auth(self):
        """GET /api/notifications/settings - should require auth"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/notifications/settings")
        assert response.status_code == 401
        print("✓ /notifications/settings correctly requires auth")


class TestCompetitionMonitoring:
    """Test competition monitoring endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_list_monitors(self):
        """GET /api/competition/monitors - should return monitors"""
        response = self.session.get(f"{BASE_URL}/api/competition/monitors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /competition/monitors: {len(data)} monitors")
    
    def test_add_monitor_validation(self):
        """POST /api/competition/monitor - should validate keyword"""
        response = self.session.post(f"{BASE_URL}/api/competition/monitor", json={
            "keyword": ""
        })
        assert response.status_code == 400
        print("✓ POST /competition/monitor validates empty keyword")
    
    def test_monitors_without_auth(self):
        """GET /api/competition/monitors - should require auth"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/competition/monitors")
        assert response.status_code == 401
        print("✓ /competition/monitors correctly requires auth")


class TestSurferSEO:
    """Test SurferSEO endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_keyword_research_validation(self):
        """POST /api/surfer/keyword-research - should validate seed_keyword"""
        response = self.session.post(f"{BASE_URL}/api/surfer/keyword-research", json={
            "seed_keyword": ""
        })
        assert response.status_code == 400
        print("✓ POST /surfer/keyword-research validates empty seed_keyword")
    
    def test_audit_url_validation(self):
        """POST /api/surfer/audit-url - should validate url"""
        response = self.session.post(f"{BASE_URL}/api/surfer/audit-url", json={
            "url": ""
        })
        assert response.status_code == 400
        print("✓ POST /surfer/audit-url validates empty url")
    
    def test_content_planner_validation(self):
        """POST /api/surfer/content-planner - should validate keywords"""
        response = self.session.post(f"{BASE_URL}/api/surfer/content-planner", json={
            "keywords": []
        })
        assert response.status_code == 400
        print("✓ POST /surfer/content-planner validates empty keywords")


class TestImageGeneration:
    """Test image generation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_start_image_generation(self):
        """POST /api/images/generate - should start generation job"""
        response = self.session.post(f"{BASE_URL}/api/images/generate", json={
            "prompt": "TEST_Professional accounting office illustration",
            "style": "hero"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "processing"
        print(f"✓ POST /images/generate: job_id={data['job_id']}")
    
    def test_image_status_not_found(self):
        """GET /api/images/generate/status/{job_id} - should return 404 for invalid job"""
        response = self.session.get(f"{BASE_URL}/api/images/generate/status/invalid-job-id")
        assert response.status_code == 404
        print("✓ GET /images/generate/status returns 404 for invalid job")
    
    def test_library_images(self):
        """GET /api/library/images - should return image library"""
        response = self.session.get(f"{BASE_URL}/api/library/images")
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert "total" in data
        print(f"✓ GET /library/images: {data['total']} images")


class TestArticleGeneration:
    """Test article generation endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_start_article_generation(self):
        """POST /api/articles/generate - should start generation job"""
        response = self.session.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "TEST_Regression test article",
            "primary_keyword": "test regression",
            "secondary_keywords": ["pytest", "automation"],
            "target_length": 500,
            "tone": "profesjonalny",
            "template": "standard"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ POST /articles/generate: job_id={data['job_id']}")
    
    def test_generation_status_not_found(self):
        """GET /api/articles/generate/status/{job_id} - should return 404 for invalid job"""
        response = self.session.get(f"{BASE_URL}/api/articles/generate/status/invalid-job-id")
        assert response.status_code == 404
        print("✓ GET /articles/generate/status returns 404 for invalid job")


class TestAdminEndpoints:
    """Test admin-only endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_admin_list_users(self):
        """GET /api/admin/users - should return user list for admin"""
        response = self.session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify admin user is in list
        admin_found = any(u["email"] == ADMIN_EMAIL for u in data)
        assert admin_found
        print(f"✓ GET /admin/users: {len(data)} users")
    
    def test_admin_users_without_auth(self):
        """GET /api/admin/users - should require auth"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 401
        print("✓ /admin/users correctly requires auth")


class TestContentEndpoints:
    """Test content-related endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_list_series(self):
        """GET /api/series - should return article series"""
        response = self.session.get(f"{BASE_URL}/api/series")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /series: {len(data)} series")
    
    def test_list_calendars(self):
        """GET /api/content-calendar/list - should return calendars"""
        response = self.session.get(f"{BASE_URL}/api/content-calendar/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /content-calendar/list: {len(data)} calendars")
    
    def test_scheduled_articles(self):
        """GET /api/articles/scheduled - should return scheduled articles"""
        response = self.session.get(f"{BASE_URL}/api/articles/scheduled")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /articles/scheduled: {len(data)} scheduled")


class TestSEOTools:
    """Test SEO tools endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_subscription_plans(self):
        """GET /api/subscription/plans - should return plans"""
        response = self.session.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"✓ GET /subscription/plans: plans loaded")
    
    def test_subscription_status(self):
        """GET /api/subscription/status - should return status"""
        response = self.session.get(f"{BASE_URL}/api/subscription/status")
        assert response.status_code == 200
        data = response.json()
        assert "has_subscription" in data
        print(f"✓ GET /subscription/status: has_subscription={data['has_subscription']}")
    
    def test_seo_audit_history(self):
        """GET /api/seo-audit/history - should return audit history"""
        response = self.session.get(f"{BASE_URL}/api/seo-audit/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /seo-audit/history: {len(data)} audits")
    
    def test_newsletter_list(self):
        """GET /api/newsletter/list - should return newsletters"""
        response = self.session.get(f"{BASE_URL}/api/newsletter/list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /newsletter/list: {len(data)} newsletters")


class TestAIFeatures:
    """Test AI features endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        self.token = response.json()["token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def test_list_categories(self):
        """GET /api/articles/categories-list - should return categories"""
        # Note: /articles/categories is shadowed by /articles/{article_id} route
        # Use /articles/categories-list instead
        response = self.session.get(f"{BASE_URL}/api/articles/categories-list")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /articles/categories-list: {len(data)} categories")
    
    def test_bulk_delete_validation(self):
        """POST /api/articles/bulk-delete - should validate article_ids"""
        response = self.session.post(f"{BASE_URL}/api/articles/bulk-delete", json={
            "article_ids": []
        })
        assert response.status_code == 400
        print("✓ POST /articles/bulk-delete validates empty article_ids")
    
    def test_bulk_category_validation(self):
        """POST /api/articles/bulk-category - should validate input"""
        response = self.session.post(f"{BASE_URL}/api/articles/bulk-category", json={
            "article_ids": [],
            "category": ""
        })
        assert response.status_code == 400
        print("✓ POST /articles/bulk-category validates empty input")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
