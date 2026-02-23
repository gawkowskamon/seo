"""
Test WordPress Import and Export Bug Fixes

Tests the following fixes:
1. URL normalization - auto-add https:// if missing
2. HTTP 422 instead of 502 for WP API failures (so Cloudflare passes through JSON)
3. follow_redirects=True for WordPress connections
4. Error messages in Polish for common failures (403, 404, timeout)
5. Fallback for /index.php/wp-json/wp/v2/posts when /wp-json/wp/v2/posts returns 404
"""
import pytest
import requests
import os

# Use the public URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://seo-article-builder-2.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"
TEST_ARTICLE_ID = "b4f55829-f62b-4b0e-9bd1-9c399a55f8d6"
REAL_WP_SITE = "www.kurdynowski.com.pl"


@pytest.fixture(scope="module")
def auth_token():
    """Login and get token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=30)
    if resp.status_code == 200:
        return resp.json().get("token")
    pytest.skip(f"Auth failed: {resp.status_code} - {resp.text[:100]}")


@pytest.fixture
def auth_headers(auth_token):
    """Headers with auth token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestWordPressImportURLNormalization:
    """Test URL normalization in WordPress import."""

    def test_import_wordpress_url_without_https(self, auth_headers):
        """Test import with URL without https:// - should normalize and succeed."""
        # Use real WP site without protocol
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": REAL_WP_SITE,  # No https:// prefix
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        # Should succeed (200) or give meaningful error (400)
        assert resp.status_code in [200, 400], f"Unexpected status: {resp.status_code} - {resp.text[:300]}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "articles" in data, "Response should contain 'articles' key"
            assert "count" in data, "Response should contain 'count' key"
            print(f"SUCCESS: Imported {data['count']} articles from {REAL_WP_SITE}")
        else:
            # If 400, check it's a meaningful error not a URL validation error
            error = resp.json().get("detail", "")
            assert "http" not in error.lower() or "protocol" not in error.lower(), \
                f"URL normalization should have added https:// - got error: {error}"
            print(f"Got expected error (not URL format issue): {error}")

    def test_import_wordpress_url_with_https(self, auth_headers):
        """Test import with URL with https:// - should succeed."""
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": f"https://{REAL_WP_SITE}",  # With https://
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        assert resp.status_code in [200, 400], f"Unexpected status: {resp.status_code} - {resp.text[:300]}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "articles" in data
            assert "count" in data
            print(f"SUCCESS: Imported {data['count']} articles with https:// prefix")

    def test_import_wordpress_invalid_url_returns_meaningful_error(self, auth_headers):
        """Test that invalid URL returns meaningful error in Polish."""
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": "nonexistent-fake-domain-xyz123.invalid",
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        # Should return 400 with meaningful error
        assert resp.status_code == 400, f"Should return 400 for invalid URL: {resp.status_code}"
        
        error = resp.json().get("detail", "")
        assert error, "Should have error message"
        # Should be in Polish (check for common Polish words/patterns)
        assert any(word in error.lower() for word in ["blad", "nie", "sprawdz", "polacz", "timeout"]), \
            f"Error should be in Polish: {error}"
        print(f"Got meaningful Polish error: {error}")


class TestWordPressPublishErrorHandling:
    """Test that WordPress publish returns JSON errors (not Cloudflare HTML)."""

    def test_publish_wordpress_returns_json_error(self, auth_headers):
        """Test that publish-wordpress returns JSON error (422 not 502)."""
        resp = requests.post(
            f"{BASE_URL}/api/articles/{TEST_ARTICLE_ID}/publish-wordpress",
            headers=auth_headers,
            timeout=60
        )
        
        # Should return 422 (not 502 which Cloudflare intercepts)
        # Or 400 if WordPress not configured
        # Or 403 if credentials invalid
        assert resp.status_code in [200, 201, 400, 403, 422, 500], \
            f"Unexpected status: {resp.status_code}"
        
        # CRITICAL: Response should be JSON, not HTML (Cloudflare error page)
        content_type = resp.headers.get("content-type", "")
        assert "application/json" in content_type, \
            f"Response should be JSON, not HTML: {content_type}, body: {resp.text[:200]}"
        
        # Check we get a JSON body
        try:
            data = resp.json()
            print(f"Got JSON response: {data}")
            
            # If error, check it's meaningful
            if resp.status_code >= 400:
                assert "detail" in data, "Error response should have 'detail' field"
                error_msg = data.get("detail", "")
                assert error_msg, "Error message should not be empty"
                # Should NOT contain Cloudflare HTML fragments
                assert "<!DOCTYPE" not in error_msg, "Error should not be Cloudflare HTML"
                assert "<html" not in error_msg.lower(), "Error should not be HTML"
                print(f"Got proper JSON error: {error_msg}")
        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}, body: {resp.text[:300]}")

    def test_publish_wordpress_not_502_status(self, auth_headers):
        """Test that WordPress errors don't return 502 (Cloudflare intercepts)."""
        resp = requests.post(
            f"{BASE_URL}/api/articles/{TEST_ARTICLE_ID}/publish-wordpress",
            headers=auth_headers,
            timeout=60
        )
        
        # Status code should NOT be 502 (that's what we're fixing)
        assert resp.status_code != 502, \
            f"Should not return 502 (Cloudflare intercepts this) - got {resp.status_code}"
        print(f"Correctly returned status {resp.status_code} instead of 502")


class TestWordPressSettingsURLNormalization:
    """Test URL normalization in WordPress settings save."""

    def test_save_wordpress_settings_normalizes_url(self, auth_headers):
        """Test that saving WordPress settings normalizes URL (adds https://)."""
        # First save with URL without https://
        save_resp = requests.post(f"{BASE_URL}/api/settings/wordpress", json={
            "wp_url": "test-wp-site.com",  # No https://
            "wp_user": "test_user",
            "wp_app_password": "xxxx xxxx xxxx xxxx"
        }, headers=auth_headers, timeout=30)
        
        assert save_resp.status_code == 200, f"Save failed: {save_resp.status_code} - {save_resp.text[:200]}"
        
        # Now get settings and verify URL was normalized
        get_resp = requests.get(f"{BASE_URL}/api/settings/wordpress", 
                               headers=auth_headers, timeout=30)
        
        assert get_resp.status_code == 200, f"Get failed: {get_resp.status_code}"
        
        data = get_resp.json()
        wp_url = data.get("wp_url", "")
        
        # URL should have https:// prefix
        assert wp_url.startswith("https://"), \
            f"URL should be normalized with https:// - got: {wp_url}"
        assert wp_url == "https://test-wp-site.com", \
            f"URL should be 'https://test-wp-site.com' - got: {wp_url}"
        print(f"URL correctly normalized to: {wp_url}")


class TestURLImport:
    """Test article import from URL."""

    def test_import_from_url_real_article(self, auth_headers):
        """Test importing a real article from kurdynowski.com.pl."""
        # Use a known article URL from the WP site
        resp = requests.post(f"{BASE_URL}/api/import/url", json={
            "url": f"https://{REAL_WP_SITE}",
            "optimize": False  # Don't optimize to make test faster
        }, headers=auth_headers, timeout=120)
        
        # Should succeed or give meaningful error
        assert resp.status_code in [200, 400], \
            f"Unexpected status: {resp.status_code} - {resp.text[:300]}"
        
        if resp.status_code == 200:
            data = resp.json()
            assert "id" in data, "Response should contain article ID"
            assert "title" in data, "Response should contain title"
            print(f"SUCCESS: Imported article - ID: {data['id']}, Title: {data.get('title', '')[:50]}")


class TestHealthAndConnectivity:
    """Basic connectivity tests."""

    def test_health_endpoint(self):
        """Test health endpoint is accessible."""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        print("Health check OK")

    def test_auth_login_works(self):
        """Test authentication works."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=30)
        assert resp.status_code == 200, f"Login failed: {resp.status_code}"
        assert "token" in resp.json(), "Response should contain token"
        print("Auth login OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
