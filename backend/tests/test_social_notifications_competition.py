"""
Test suite for Social Media Scheduling, Notifications, and Competition Monitoring features.
Tests backend API endpoints for Phase 3 features.
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

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
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    return response.json().get("token")


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ============ Social Media Scheduling Tests ============

class TestSocialScheduling:
    """Tests for social media scheduling endpoints."""
    
    def test_schedule_post_success(self, auth_headers):
        """POST /api/social/schedule - schedule a new post."""
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        payload = {
            "platform": "linkedin",
            "text": "TEST_Post testowy dla LinkedIn #test #seo",
            "scheduled_at": scheduled_time,
            "hashtags": ["#test", "#seo"]
        }
        response = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["platform"] == "linkedin"
        assert data["status"] == "scheduled"
        # Store for cleanup
        TestSocialScheduling.created_post_id = data["id"]
    
    def test_schedule_post_missing_platform(self, auth_headers):
        """POST /api/social/schedule - returns 400 when platform missing."""
        payload = {
            "text": "Test post",
            "scheduled_at": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert response.status_code == 400
    
    def test_schedule_post_missing_text(self, auth_headers):
        """POST /api/social/schedule - returns 400 when text missing."""
        payload = {
            "platform": "twitter",
            "scheduled_at": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert response.status_code == 400
    
    def test_schedule_post_missing_scheduled_at(self, auth_headers):
        """POST /api/social/schedule - returns 400 when scheduled_at missing."""
        payload = {
            "platform": "facebook",
            "text": "Test post"
        }
        response = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert response.status_code == 400
    
    def test_schedule_post_unauthorized(self):
        """POST /api/social/schedule - returns 401 without auth."""
        payload = {
            "platform": "linkedin",
            "text": "Test",
            "scheduled_at": datetime.utcnow().isoformat() + "Z"
        }
        response = requests.post(f"{BASE_URL}/api/social/schedule", json=payload)
        assert response.status_code == 401
    
    def test_list_scheduled_posts(self, auth_headers):
        """GET /api/social/scheduled - list scheduled posts."""
        response = requests.get(f"{BASE_URL}/api/social/scheduled", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_scheduled_posts_unauthorized(self):
        """GET /api/social/scheduled - returns 401 without auth."""
        response = requests.get(f"{BASE_URL}/api/social/scheduled")
        assert response.status_code == 401
    
    def test_mark_post_published(self, auth_headers):
        """PUT /api/social/scheduled/{id}/publish - mark post as published."""
        # First create a post
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        payload = {
            "platform": "twitter",
            "text": "TEST_Post do publikacji #test",
            "scheduled_at": scheduled_time
        }
        create_resp = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        post_id = create_resp.json()["id"]
        
        # Mark as published
        response = requests.put(f"{BASE_URL}/api/social/scheduled/{post_id}/publish", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/social/scheduled/{post_id}", headers=auth_headers)
    
    def test_delete_scheduled_post(self, auth_headers):
        """DELETE /api/social/scheduled/{id} - delete a scheduled post."""
        # First create a post
        scheduled_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
        payload = {
            "platform": "instagram",
            "text": "TEST_Post do usunięcia #test",
            "scheduled_at": scheduled_time
        }
        create_resp = requests.post(f"{BASE_URL}/api/social/schedule", json=payload, headers=auth_headers)
        assert create_resp.status_code == 200
        post_id = create_resp.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/social/scheduled/{post_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify deleted - should not appear in list
        list_resp = requests.get(f"{BASE_URL}/api/social/scheduled", headers=auth_headers)
        posts = list_resp.json()
        assert not any(p["id"] == post_id for p in posts)
    
    def test_delete_nonexistent_post(self, auth_headers):
        """DELETE /api/social/scheduled/{id} - returns 404 for nonexistent post."""
        response = requests.delete(f"{BASE_URL}/api/social/scheduled/nonexistent-id-12345", headers=auth_headers)
        assert response.status_code == 404


# ============ Notification Settings Tests ============

class TestNotifications:
    """Tests for notification settings and alerts."""
    
    def test_get_notification_settings(self, auth_headers):
        """GET /api/notifications/settings - get notification preferences."""
        response = requests.get(f"{BASE_URL}/api/notifications/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Check expected fields
        assert "email_enabled" in data
        assert "notify_article_age" in data
        assert "notify_seo_drop" in data
        assert "notify_competition" in data
        assert "frequency" in data
    
    def test_get_notification_settings_unauthorized(self):
        """GET /api/notifications/settings - returns 401 without auth."""
        response = requests.get(f"{BASE_URL}/api/notifications/settings")
        assert response.status_code == 401
    
    def test_update_notification_settings(self, auth_headers):
        """PUT /api/notifications/settings - update notification preferences."""
        payload = {
            "email_enabled": True,
            "notify_article_age": True,
            "frequency": "weekly"
        }
        response = requests.put(f"{BASE_URL}/api/notifications/settings", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email_enabled"] == True
        assert data["frequency"] == "weekly"
    
    def test_update_notification_settings_partial(self, auth_headers):
        """PUT /api/notifications/settings - partial update works."""
        payload = {"notify_seo_drop": False}
        response = requests.put(f"{BASE_URL}/api/notifications/settings", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["notify_seo_drop"] == False
    
    def test_check_updates(self, auth_headers):
        """POST /api/notifications/check-updates - check which articles need updating."""
        response = requests.post(f"{BASE_URL}/api/notifications/check-updates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "total" in data
        assert isinstance(data["notifications"], list)
    
    def test_check_updates_unauthorized(self):
        """POST /api/notifications/check-updates - returns 401 without auth."""
        response = requests.post(f"{BASE_URL}/api/notifications/check-updates")
        assert response.status_code == 401
    
    def test_send_test_notification(self, auth_headers):
        """POST /api/notifications/send-test - send mock test email."""
        response = requests.post(f"{BASE_URL}/api/notifications/send-test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent_mock"
        assert "message" in data
        assert "notification" in data
    
    def test_send_test_notification_unauthorized(self):
        """POST /api/notifications/send-test - returns 401 without auth."""
        response = requests.post(f"{BASE_URL}/api/notifications/send-test")
        assert response.status_code == 401
    
    def test_get_notification_history(self, auth_headers):
        """GET /api/notifications/history - get notification send history."""
        response = requests.get(f"{BASE_URL}/api/notifications/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # After sending test, should have at least one entry
        if len(data) > 0:
            assert "subject" in data[0]
            assert "email" in data[0]
            assert "sent_at" in data[0]
    
    def test_get_notification_history_unauthorized(self):
        """GET /api/notifications/history - returns 401 without auth."""
        response = requests.get(f"{BASE_URL}/api/notifications/history")
        assert response.status_code == 401


# ============ Competition Monitoring Tests ============

class TestCompetitionMonitoring:
    """Tests for competition monitoring endpoints."""
    
    created_monitor_id = None
    
    def test_add_competition_monitor(self, auth_headers):
        """POST /api/competition/monitor - add keyword to monitoring (uses AI)."""
        payload = {"keyword": "TEST_księgowość online"}
        response = requests.post(f"{BASE_URL}/api/competition/monitor", json=payload, headers=auth_headers, timeout=120)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["keyword"] == "TEST_księgowość online"
        assert "analysis" in data
        # Check analysis structure
        analysis = data["analysis"]
        assert "top_results" in analysis or "difficulty" in analysis
        TestCompetitionMonitoring.created_monitor_id = data["id"]
    
    def test_add_competition_monitor_missing_keyword(self, auth_headers):
        """POST /api/competition/monitor - returns 400 when keyword missing."""
        response = requests.post(f"{BASE_URL}/api/competition/monitor", json={}, headers=auth_headers)
        assert response.status_code == 400
    
    def test_add_competition_monitor_empty_keyword(self, auth_headers):
        """POST /api/competition/monitor - returns 400 when keyword empty."""
        response = requests.post(f"{BASE_URL}/api/competition/monitor", json={"keyword": ""}, headers=auth_headers)
        assert response.status_code == 400
    
    def test_add_competition_monitor_unauthorized(self):
        """POST /api/competition/monitor - returns 401 without auth."""
        response = requests.post(f"{BASE_URL}/api/competition/monitor", json={"keyword": "test"})
        assert response.status_code == 401
    
    def test_list_competition_monitors(self, auth_headers):
        """GET /api/competition/monitors - list monitored keywords."""
        response = requests.get(f"{BASE_URL}/api/competition/monitors", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_competition_monitors_unauthorized(self):
        """GET /api/competition/monitors - returns 401 without auth."""
        response = requests.get(f"{BASE_URL}/api/competition/monitors")
        assert response.status_code == 401
    
    def test_delete_competition_monitor(self, auth_headers):
        """DELETE /api/competition/monitors/{id} - remove monitoring."""
        # First create a monitor to delete
        payload = {"keyword": "TEST_usuwanie monitora"}
        create_resp = requests.post(f"{BASE_URL}/api/competition/monitor", json=payload, headers=auth_headers, timeout=120)
        if create_resp.status_code != 200:
            pytest.skip("Could not create monitor for deletion test")
        monitor_id = create_resp.json()["id"]
        
        # Delete
        response = requests.delete(f"{BASE_URL}/api/competition/monitors/{monitor_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        
        # Verify deleted
        list_resp = requests.get(f"{BASE_URL}/api/competition/monitors", headers=auth_headers)
        monitors = list_resp.json()
        assert not any(m["id"] == monitor_id for m in monitors)
    
    def test_delete_nonexistent_monitor(self, auth_headers):
        """DELETE /api/competition/monitors/{id} - returns 404 for nonexistent."""
        response = requests.delete(f"{BASE_URL}/api/competition/monitors/nonexistent-id-12345", headers=auth_headers)
        assert response.status_code == 404
    
    def test_delete_monitor_unauthorized(self):
        """DELETE /api/competition/monitors/{id} - returns 401 without auth."""
        response = requests.delete(f"{BASE_URL}/api/competition/monitors/some-id")
        assert response.status_code == 401


# ============ Cleanup ============

@pytest.fixture(scope="module", autouse=True)
def cleanup(auth_token):
    """Cleanup test data after all tests."""
    yield
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    # Cleanup scheduled posts with TEST_ prefix
    try:
        posts = requests.get(f"{BASE_URL}/api/social/scheduled", headers=headers).json()
        for post in posts:
            if "TEST_" in post.get("text", ""):
                requests.delete(f"{BASE_URL}/api/social/scheduled/{post['id']}", headers=headers)
    except:
        pass
    
    # Cleanup competition monitors with TEST_ prefix
    try:
        monitors = requests.get(f"{BASE_URL}/api/competition/monitors", headers=headers).json()
        for mon in monitors:
            if "TEST_" in mon.get("keyword", ""):
                requests.delete(f"{BASE_URL}/api/competition/monitors/{mon['id']}", headers=headers)
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
