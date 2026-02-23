"""
Test WordPress REST API URL Discovery with Subdirectory Paths

Tests the fix for: WP URL with subdirectory path (e.g., kurdynowski.com.pl/cms-biuro)
where WordPress is installed at root but admin panel is at /cms-biuro.

The REST API discovery should:
1. Try the given URL first (e.g., kurdynowski.com.pl/cms-biuro/wp-json/wp/v2/posts)
2. Fall back to root domain (e.g., kurdynowski.com.pl/wp-json/wp/v2/posts)
3. Validate Content-Type is application/json before accepting a URL

Key test cases:
- POST /api/import/wordpress with URL 'kurdynowski.com.pl/cms-biuro' - should discover API at root
- POST /api/import/wordpress with URL 'www.kurdynowski.com.pl' - should work directly
- POST /api/import/wordpress with URL 'kurdynowski.com.pl' (no path) - should work
- POST /api/articles/{id}/publish-wordpress discovers correct REST API despite subdirectory URL
- Error responses are JSON (not Cloudflare HTML)
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

# WordPress site configurations
REAL_WP_ROOT = "kurdynowski.com.pl"
REAL_WP_SUBDIR = "kurdynowski.com.pl/cms-biuro"
REAL_WP_WWW = "www.kurdynowski.com.pl"


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


class TestWordPressSubdirectoryDiscovery:
    """Test REST API URL discovery with subdirectory paths."""

    def test_import_wordpress_with_subdirectory_path(self, auth_headers):
        """
        CRITICAL TEST: Import with URL that has subdirectory path (/cms-biuro)
        Should discover REST API at root domain, NOT at /cms-biuro/wp-json/
        """
        print(f"\nTesting with subdirectory URL: {REAL_WP_SUBDIR}")
        
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": REAL_WP_SUBDIR,  # kurdynowski.com.pl/cms-biuro
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        print(f"Response status: {resp.status_code}")
        print(f"Response body (first 500 chars): {resp.text[:500]}")
        
        # Should succeed (200) - API discovered at root domain
        assert resp.status_code == 200, \
            f"Expected 200 (API should be discovered at root), got {resp.status_code}. Error: {resp.text[:300]}"
        
        data = resp.json()
        assert "articles" in data, "Response should contain 'articles' key"
        assert "count" in data, "Response should contain 'count' key"
        assert data["count"] > 0, f"Should have found articles, got count: {data['count']}"
        
        print(f"SUCCESS: Discovered API at root and imported {data['count']} articles from subdirectory URL {REAL_WP_SUBDIR}")

    def test_import_wordpress_with_www_prefix(self, auth_headers):
        """Test import with www prefix - should work directly."""
        print(f"\nTesting with www URL: {REAL_WP_WWW}")
        
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": REAL_WP_WWW,  # www.kurdynowski.com.pl
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        print(f"Response status: {resp.status_code}")
        
        assert resp.status_code == 200, \
            f"Expected 200 for www URL, got {resp.status_code}. Error: {resp.text[:300]}"
        
        data = resp.json()
        assert "articles" in data
        assert data["count"] > 0, f"Should have found articles, got count: {data['count']}"
        
        print(f"SUCCESS: Imported {data['count']} articles from {REAL_WP_WWW}")

    def test_import_wordpress_root_domain_no_path(self, auth_headers):
        """Test import with root domain (no path) - should work."""
        print(f"\nTesting with root URL: {REAL_WP_ROOT}")
        
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": REAL_WP_ROOT,  # kurdynowski.com.pl (no path)
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        print(f"Response status: {resp.status_code}")
        
        assert resp.status_code == 200, \
            f"Expected 200 for root URL, got {resp.status_code}. Error: {resp.text[:300]}"
        
        data = resp.json()
        assert "articles" in data
        assert data["count"] > 0
        
        print(f"SUCCESS: Imported {data['count']} articles from {REAL_WP_ROOT}")


class TestWordPressPublishWithSubdirectoryURL:
    """Test WordPress publish discovers correct API despite subdirectory URL in settings."""

    def setup_method(self):
        """Reset WordPress settings to subdirectory URL before each test."""
        pass  # Settings are set up once in test_setup_wordpress_settings_with_subdirectory

    def test_setup_wordpress_settings_with_subdirectory(self, auth_headers):
        """Set WordPress settings with subdirectory URL for subsequent tests."""
        print(f"\nSetting WordPress URL to subdirectory path: {REAL_WP_SUBDIR}")
        
        resp = requests.post(f"{BASE_URL}/api/settings/wordpress", json={
            "wp_url": REAL_WP_SUBDIR,  # kurdynowski.com.pl/cms-biuro
            "wp_user": "testuser",
            "wp_app_password": "xxxx-xxxx-xxxx"  # Test credentials (will fail auth but test discovery)
        }, headers=auth_headers, timeout=30)
        
        assert resp.status_code == 200, f"Failed to save WP settings: {resp.status_code} - {resp.text[:200]}"
        
        # Verify settings were saved
        get_resp = requests.get(f"{BASE_URL}/api/settings/wordpress", 
                               headers=auth_headers, timeout=30)
        assert get_resp.status_code == 200
        
        data = get_resp.json()
        wp_url = data.get("wp_url", "")
        # Should have https:// prefix added
        assert "cms-biuro" in wp_url, f"URL should contain cms-biuro path: {wp_url}"
        print(f"WordPress settings saved with URL: {wp_url}")

    def test_publish_wordpress_discovers_api_returns_json_error(self, auth_headers):
        """
        Test publish-wordpress with subdirectory URL discovers correct API.
        Should return JSON error (401/403 for test credentials), NOT Cloudflare HTML.
        """
        print(f"\nTesting publish with article ID: {TEST_ARTICLE_ID}")
        
        resp = requests.post(
            f"{BASE_URL}/api/articles/{TEST_ARTICLE_ID}/publish-wordpress",
            headers=auth_headers,
            timeout=60
        )
        
        print(f"Response status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('content-type', 'N/A')}")
        print(f"Response body (first 500 chars): {resp.text[:500]}")
        
        # Should NOT be 502 (Cloudflare intercept)
        assert resp.status_code != 502, \
            f"Should not return 502 (Cloudflare intercepts this) - got {resp.status_code}"
        
        # Response should be JSON, not HTML
        content_type = resp.headers.get("content-type", "")
        assert "application/json" in content_type, \
            f"Response should be JSON, not HTML. Content-Type: {content_type}, Body: {resp.text[:200]}"
        
        # Parse JSON response
        try:
            data = resp.json()
            print(f"JSON response: {data}")
            
            # Check for meaningful error message
            if resp.status_code >= 400:
                # Should have 'detail' field with error
                assert "detail" in data, f"Error response should have 'detail' field: {data}"
                error_msg = data.get("detail", "")
                
                # Should NOT be Cloudflare HTML
                assert "<!DOCTYPE" not in error_msg, "Error should not be Cloudflare HTML"
                assert "<html" not in error_msg.lower(), "Error should not be HTML"
                
                # Should be in Polish (common error words)
                polish_words = ["blad", "nie", "sprawdz", "wordpress", "logowania", "haslo", "uprawnien"]
                assert any(word in error_msg.lower() for word in polish_words), \
                    f"Error should be meaningful Polish message: {error_msg}"
                
                print(f"Got proper JSON error (expected - test credentials): {error_msg}")
            else:
                # If 200/201, publish succeeded (unlikely with test credentials)
                print(f"Publish succeeded: {data}")
                
        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}, body: {resp.text[:300]}")


class TestWordPressSettingsNormalization:
    """Test WordPress settings URL normalization with subdirectory paths."""

    def test_settings_preserve_subdirectory_path(self, auth_headers):
        """Test that saving WP settings preserves subdirectory path."""
        # Save with subdirectory path
        save_resp = requests.post(f"{BASE_URL}/api/settings/wordpress", json={
            "wp_url": "kurdynowski.com.pl/cms-biuro",
            "wp_user": "test_user",
            "wp_app_password": "test xxxx xxxx"
        }, headers=auth_headers, timeout=30)
        
        assert save_resp.status_code == 200
        
        # Get and verify
        get_resp = requests.get(f"{BASE_URL}/api/settings/wordpress", 
                               headers=auth_headers, timeout=30)
        assert get_resp.status_code == 200
        
        data = get_resp.json()
        wp_url = data.get("wp_url", "")
        
        # Should have https:// prefix AND preserve /cms-biuro path
        assert wp_url.startswith("https://"), f"URL should have https:// prefix: {wp_url}"
        assert "cms-biuro" in wp_url, f"URL should preserve /cms-biuro path: {wp_url}"
        
        print(f"Settings correctly saved with subdirectory: {wp_url}")

    def test_settings_normalize_url_without_https(self, auth_headers):
        """Test URL normalization adds https:// to subdirectory URLs."""
        save_resp = requests.post(f"{BASE_URL}/api/settings/wordpress", json={
            "wp_url": "example.com/wordpress/admin",  # No https://, with subdirectory
            "wp_user": "user",
            "wp_app_password": "pass"
        }, headers=auth_headers, timeout=30)
        
        assert save_resp.status_code == 200
        
        get_resp = requests.get(f"{BASE_URL}/api/settings/wordpress", 
                               headers=auth_headers, timeout=30)
        data = get_resp.json()
        wp_url = data.get("wp_url", "")
        
        assert wp_url == "https://example.com/wordpress/admin", f"URL not normalized correctly: {wp_url}"
        print(f"URL correctly normalized: {wp_url}")


class TestErrorResponseFormat:
    """Test that all WordPress-related errors return JSON, not HTML."""

    def test_invalid_url_returns_json_error(self, auth_headers):
        """Test that invalid URL returns proper JSON error."""
        resp = requests.post(f"{BASE_URL}/api/import/wordpress", json={
            "wp_url": "invalid-fake-domain-12345.xyz/path/to/nowhere",
            "limit": 5
        }, headers=auth_headers, timeout=60)
        
        # Should be 400, not 502
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        
        # Response must be JSON
        content_type = resp.headers.get("content-type", "")
        assert "application/json" in content_type, f"Response should be JSON: {content_type}"
        
        data = resp.json()
        assert "detail" in data, "Error should have 'detail' field"
        
        error_msg = data["detail"]
        assert error_msg, "Error message should not be empty"
        assert "<!DOCTYPE" not in error_msg, "Error should not contain HTML"
        
        print(f"Got proper JSON error for invalid URL: {error_msg}")


class TestHealthAndAuth:
    """Basic connectivity and auth tests."""

    def test_health_endpoint(self):
        """Test health endpoint."""
        resp = requests.get(f"{BASE_URL}/api/health", timeout=30)
        assert resp.status_code == 200
        print("Health check OK")

    def test_auth_login(self):
        """Test authentication."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }, timeout=30)
        assert resp.status_code == 200
        assert "token" in resp.json()
        print("Auth login OK")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
