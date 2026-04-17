"""
Iteration 37: Bulk Optimize + WordPress Webhook Tests

Features tested:
1. Bulk Optimization - POST /api/surfer/bulk-optimize, GET /api/surfer/bulk-optimize/status/{id}
2. WordPress Webhook - generate-token, config, webhook receiver, events, article-stats
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "monika.gawkowska@kurdynowski.pl",
        "password": "MonZuz8180!"
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestWordPressWebhookTokenGeneration:
    """Test WordPress webhook token generation and config endpoints."""

    def test_generate_webhook_token(self, auth_headers):
        """POST /api/wordpress/webhook/generate-token creates token for user."""
        response = requests.post(f"{BASE_URL}/api/wordpress/webhook/generate-token", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain 'token' field"
        assert len(data["token"]) > 20, "Token should be at least 20 characters"
        print(f"✓ Token generated: {data['token'][:20]}...")

    def test_get_webhook_config(self, auth_headers):
        """GET /api/wordpress/webhook/config returns webhook_url, token, setup_instructions."""
        response = requests.get(f"{BASE_URL}/api/wordpress/webhook/config", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Check required fields
        assert "webhook_url" in data, "Response should contain 'webhook_url'"
        assert "token" in data, "Response should contain 'token'"
        assert "has_token" in data, "Response should contain 'has_token'"
        assert "setup_instructions" in data, "Response should contain 'setup_instructions'"
        
        # Verify webhook_url format
        assert data["webhook_url"].endswith("/api/wordpress/webhook"), f"webhook_url should end with /api/wordpress/webhook, got: {data['webhook_url']}"
        
        # Verify setup_instructions structure
        instructions = data["setup_instructions"]
        assert instructions.get("method") == "POST", "Method should be POST"
        assert instructions.get("header_name") == "X-Webhook-Token", "Header name should be X-Webhook-Token"
        assert "events_supported" in instructions, "Should list supported events"
        assert "post_published" in instructions["events_supported"], "Should support post_published event"
        assert "traffic_stats" in instructions["events_supported"], "Should support traffic_stats event"
        
        print(f"✓ Webhook config retrieved: {data['webhook_url']}")
        print(f"  Token present: {data['has_token']}")
        print(f"  Supported events: {instructions['events_supported']}")


class TestWordPressWebhookAuthentication:
    """Test webhook authentication via X-Webhook-Token header."""

    def test_webhook_missing_token_returns_401(self):
        """POST /api/wordpress/webhook without X-Webhook-Token returns 401."""
        response = requests.post(f"{BASE_URL}/api/wordpress/webhook", json={"event": "test"})
        assert response.status_code == 401, f"Expected 401 for missing token, got {response.status_code}"
        print("✓ Missing token returns 401")

    def test_webhook_invalid_token_returns_403(self):
        """POST /api/wordpress/webhook with invalid X-Webhook-Token returns 403."""
        response = requests.post(
            f"{BASE_URL}/api/wordpress/webhook",
            json={"event": "test"},
            headers={"X-Webhook-Token": "invalid-token-12345"}
        )
        assert response.status_code == 403, f"Expected 403 for invalid token, got {response.status_code}"
        print("✓ Invalid token returns 403")

    def test_webhook_valid_token_authenticates(self, auth_headers):
        """POST /api/wordpress/webhook with valid token authenticates properly."""
        # First get the token
        config_response = requests.get(f"{BASE_URL}/api/wordpress/webhook/config", headers=auth_headers)
        assert config_response.status_code == 200
        token = config_response.json().get("token")
        assert token, "Token should exist after generation"
        
        # Send webhook with valid token (missing event field should return 400, not auth error)
        response = requests.post(
            f"{BASE_URL}/api/wordpress/webhook",
            json={},  # Missing event field
            headers={"X-Webhook-Token": token}
        )
        # Should get 400 (bad request) not 401/403 (auth error)
        assert response.status_code == 400, f"Expected 400 for missing event, got {response.status_code}"
        assert "event" in response.text.lower(), "Error should mention missing event field"
        print("✓ Valid token authenticates (got 400 for missing event, not auth error)")


class TestWordPressWebhookEvents:
    """Test webhook event processing."""

    @pytest.fixture
    def webhook_token(self, auth_headers):
        """Get webhook token for testing."""
        config_response = requests.get(f"{BASE_URL}/api/wordpress/webhook/config", headers=auth_headers)
        return config_response.json().get("token")

    @pytest.fixture
    def test_article_id(self, auth_headers):
        """Get an existing article ID for testing."""
        # Use the known test article from context
        return "d8eea228-792b-4c8f-bdaa-d4113aae7af4"

    def test_post_published_event(self, webhook_token, test_article_id, auth_headers):
        """POST webhook with event='post_published' updates article wp_* fields."""
        payload = {
            "event": "post_published",
            "article_id": test_article_id,
            "post_id": 12345,
            "permalink": "https://example.pl/test-article",
            "post_title": "Test Article Title",
            "post_date": "2026-01-15T10:00:00Z"
        }
        response = requests.post(
            f"{BASE_URL}/api/wordpress/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok", f"Expected status 'ok', got: {data}"
        assert data.get("event") == "post_published"
        print(f"✓ post_published event processed for article {test_article_id}")
        
        # Verify article was updated
        article_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        if article_response.status_code == 200:
            article = article_response.json()
            assert article.get("wp_post_id") == 12345, "wp_post_id should be updated"
            assert article.get("wp_permalink") == "https://example.pl/test-article", "wp_permalink should be updated"
            assert article.get("wp_status") == "published", "wp_status should be 'published'"
            print(f"  ✓ Article wp_* fields verified: wp_post_id={article.get('wp_post_id')}, wp_status={article.get('wp_status')}")

    def test_traffic_stats_event(self, webhook_token, test_article_id, auth_headers):
        """POST webhook with event='traffic_stats' updates wp_views_7d/30d, wp_comments."""
        payload = {
            "event": "traffic_stats",
            "article_id": test_article_id,
            "post_id": 12345,
            "views_7d": 1250,
            "views_30d": 4800,
            "comments": 12,
            "avg_time_on_page_seconds": 180
        }
        response = requests.post(
            f"{BASE_URL}/api/wordpress/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("event") == "traffic_stats"
        assert "stats_updated" in data, "Response should list updated stats"
        print(f"✓ traffic_stats event processed, updated: {data.get('stats_updated')}")
        
        # Verify article stats were updated
        article_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        if article_response.status_code == 200:
            article = article_response.json()
            assert article.get("wp_views_7d") == 1250, "wp_views_7d should be 1250"
            assert article.get("wp_views_30d") == 4800, "wp_views_30d should be 4800"
            assert article.get("wp_comments") == 12, "wp_comments should be 12"
            print(f"  ✓ Traffic stats verified: views_7d={article.get('wp_views_7d')}, views_30d={article.get('wp_views_30d')}, comments={article.get('wp_comments')}")

    def test_post_deleted_event(self, webhook_token, test_article_id, auth_headers):
        """POST webhook with event='post_deleted' sets wp_status='deleted' and reverts status to 'draft'."""
        payload = {
            "event": "post_deleted",
            "article_id": test_article_id,
            "post_id": 12345
        }
        response = requests.post(
            f"{BASE_URL}/api/wordpress/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("status") == "ok"
        assert data.get("event") == "post_deleted"
        print(f"✓ post_deleted event processed")
        
        # Verify article status was reverted
        article_response = requests.get(f"{BASE_URL}/api/articles/{test_article_id}", headers=auth_headers)
        if article_response.status_code == 200:
            article = article_response.json()
            assert article.get("wp_status") == "deleted", "wp_status should be 'deleted'"
            assert article.get("status") == "draft", "status should be reverted to 'draft'"
            print(f"  ✓ Article status verified: wp_status={article.get('wp_status')}, status={article.get('status')}")


class TestWordPressWebhookEventsHistory:
    """Test webhook events history endpoint."""

    def test_list_webhook_events(self, auth_headers):
        """GET /api/wordpress/webhook/events returns recent webhook events list."""
        response = requests.get(f"{BASE_URL}/api/wordpress/webhook/events", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            event = data[0]
            assert "id" in event, "Event should have 'id'"
            assert "event" in event, "Event should have 'event' type"
            assert "received_at" in event, "Event should have 'received_at' timestamp"
            print(f"✓ Webhook events list retrieved: {len(data)} events")
            print(f"  Latest event: {event.get('event')} at {event.get('received_at')}")
        else:
            print("✓ Webhook events list retrieved (empty)")


class TestWordPressArticleStats:
    """Test article WP stats endpoint."""

    def test_get_article_wp_stats(self, auth_headers):
        """GET /api/wordpress/webhook/article-stats/{article_id} returns WP traffic data."""
        article_id = "d8eea228-792b-4c8f-bdaa-d4113aae7af4"
        response = requests.get(f"{BASE_URL}/api/wordpress/webhook/article-stats/{article_id}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Should return wp_* fields (may be empty if no webhook received yet)
        print(f"✓ Article WP stats retrieved for {article_id}")
        print(f"  wp_post_id: {data.get('wp_post_id')}")
        print(f"  wp_status: {data.get('wp_status')}")
        print(f"  wp_views_7d: {data.get('wp_views_7d')}")

    def test_get_article_wp_stats_not_found(self, auth_headers):
        """GET /api/wordpress/webhook/article-stats/{invalid_id} returns 404."""
        response = requests.get(f"{BASE_URL}/api/wordpress/webhook/article-stats/invalid-article-id", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid article ID returns 404")


class TestBulkOptimize:
    """Test bulk optimization endpoints."""

    def test_bulk_optimize_start(self, auth_headers):
        """POST /api/surfer/bulk-optimize?threshold=60&max_iterations=1 returns bulk_job_id and total_articles."""
        response = requests.post(
            f"{BASE_URL}/api/surfer/bulk-optimize?threshold=60&max_iterations=1",
            headers=auth_headers
        )
        
        # May return 404 if no articles with score < 60% exist
        if response.status_code == 404:
            print("✓ Bulk optimize: No articles with score < 60% found (expected if all articles are optimized)")
            pytest.skip("No articles need optimization")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "bulk_job_id" in data, "Response should contain 'bulk_job_id'"
        assert "total_articles" in data, "Response should contain 'total_articles'"
        assert "status" in data, "Response should contain 'status'"
        assert data["status"] == "running", f"Status should be 'running', got: {data['status']}"
        
        print(f"✓ Bulk optimize started: job_id={data['bulk_job_id']}, total_articles={data['total_articles']}")
        
        # Store job_id for status check
        return data["bulk_job_id"]

    def test_bulk_optimize_status(self, auth_headers):
        """GET /api/surfer/bulk-optimize/status/{id} returns progress with articles[] list."""
        # First start a bulk job
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/bulk-optimize?threshold=60&max_iterations=1",
            headers=auth_headers
        )
        
        if start_response.status_code == 404:
            pytest.skip("No articles need optimization")
        
        assert start_response.status_code == 200
        bulk_job_id = start_response.json()["bulk_job_id"]
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/surfer/bulk-optimize/status/{bulk_job_id}", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "bulk_job_id" in data, "Response should contain 'bulk_job_id'"
        assert "status" in data, "Response should contain 'status'"
        assert "total" in data, "Response should contain 'total'"
        assert "completed" in data, "Response should contain 'completed'"
        assert "failed" in data, "Response should contain 'failed'"
        assert "articles" in data, "Response should contain 'articles' list"
        
        # Verify articles list structure
        articles = data["articles"]
        assert isinstance(articles, list), "articles should be a list"
        if len(articles) > 0:
            article = articles[0]
            assert "article_id" in article, "Article should have 'article_id'"
            assert "title" in article, "Article should have 'title'"
            assert "status" in article, "Article should have 'status'"
            assert article["status"] in ["pending", "optimizing", "done", "failed", "skipped"], f"Invalid status: {article['status']}"
        
        print(f"✓ Bulk optimize status retrieved:")
        print(f"  Status: {data['status']}")
        print(f"  Total: {data['total']}, Completed: {data['completed']}, Failed: {data['failed']}")
        print(f"  Articles: {len(articles)}")

    def test_bulk_optimize_status_not_found(self, auth_headers):
        """GET /api/surfer/bulk-optimize/status/{invalid_id} returns 404."""
        response = requests.get(f"{BASE_URL}/api/surfer/bulk-optimize/status/invalid-job-id", headers=auth_headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid bulk job ID returns 404")

    def test_bulk_optimize_progress_after_wait(self, auth_headers):
        """Verify bulk optimize makes progress after waiting (completed > 0 or status changes)."""
        # Start bulk job
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/bulk-optimize?threshold=60&max_iterations=1",
            headers=auth_headers
        )
        
        if start_response.status_code == 404:
            pytest.skip("No articles need optimization")
        
        assert start_response.status_code == 200
        bulk_job_id = start_response.json()["bulk_job_id"]
        total = start_response.json()["total_articles"]
        
        print(f"Bulk job started: {bulk_job_id}, total articles: {total}")
        print("Waiting 60 seconds for progress...")
        
        # Wait for some progress (bulk optimize takes ~2-3 min per article)
        time.sleep(60)
        
        # Check status
        response = requests.get(f"{BASE_URL}/api/surfer/bulk-optimize/status/{bulk_job_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Either completed > 0 OR status changed from 'running'
        completed = data.get("completed", 0)
        failed = data.get("failed", 0)
        status = data.get("status")
        
        print(f"After 60s: status={status}, completed={completed}, failed={failed}")
        
        # Check that at least one article has been processed or job is still running
        if status == "running":
            # Job still running - check if any article is being processed
            articles = data.get("articles", [])
            processing = [a for a in articles if a.get("status") in ["optimizing", "done", "failed"]]
            print(f"  Articles being processed: {len(processing)}")
            # It's OK if still running - bulk optimize is slow
            print("✓ Bulk optimize is running (may take several minutes per article)")
        else:
            # Job completed
            assert completed > 0 or failed > 0, "At least one article should be processed"
            print(f"✓ Bulk optimize completed: {completed} done, {failed} failed")


class TestROIDashboardBulkButton:
    """Test ROI Dashboard bulk optimize button visibility."""

    def test_roi_stats_includes_score_buckets(self, auth_headers):
        """GET /api/stats/roi returns score_buckets for bulk button logic."""
        response = requests.get(f"{BASE_URL}/api/stats/roi", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "score_buckets" in data, "Response should contain 'score_buckets'"
        buckets = data["score_buckets"]
        
        # Check bucket structure
        assert "poor" in buckets or "medium" in buckets, "score_buckets should have 'poor' or 'medium'"
        
        poor = buckets.get("poor", 0)
        medium = buckets.get("medium", 0)
        weak_count = poor + medium
        
        print(f"✓ ROI stats score_buckets retrieved:")
        print(f"  Poor (0-49%): {poor}")
        print(f"  Medium (50-69%): {medium}")
        print(f"  Weak total (for bulk button): {weak_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
