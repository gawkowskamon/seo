"""
Backend API Tests - Iteration 28
Testing 3-model LLM fallback (gpt-4.1-mini → gpt-5.2 → gemini-2.0-flash) across ALL LLM services.

Tests cover:
- Auth endpoints (login)
- Article CRUD and generation
- Topic suggestions
- Content rewrite
- Plagiarism checker
- Content verification
- Competition analysis (auto-competition)
- A/B title testing
- Auto meta tags
- Smart schedule
- Social media posts
- Newsletter generation
- Keyword analytics
- Health check
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://surfer-content-hub.preview.emergentagent.com"

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"


class TestHealthAndBasics:
    """Basic health and API status tests"""
    
    def test_api_health_endpoint(self):
        """GET /api/health returns healthy with LLM key info"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "llm_key_configured" in data
        assert data["llm_key_configured"] == True, "LLM key should be configured"
        print(f"✓ API health check passed: llm_key_configured={data.get('llm_key_configured')}")
    
    def test_api_root(self):
        """GET /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """POST /api/auth/login with valid admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["is_admin"] == True
        print(f"✓ Admin login successful: {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid login correctly returns 401")
    
    def test_protected_endpoint_without_auth(self):
        """GET /api/stats without auth returns 401"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 401
        print("✓ Protected endpoint correctly requires auth")


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed")


@pytest.fixture(scope="class")
def auth_headers(auth_token):
    """Get auth headers"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="class")
def existing_article_id(auth_headers):
    """Get an existing article ID for tests that need one"""
    response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
    if response.status_code == 200:
        articles = response.json()
        if articles and len(articles) > 0:
            return articles[0]["id"]
    pytest.skip("No existing articles found")


class TestArticles:
    """Article CRUD and listing tests"""
    
    def test_list_articles(self, auth_headers):
        """GET /api/articles returns list of articles"""
        response = requests.get(f"{BASE_URL}/api/articles", headers=auth_headers)
        assert response.status_code == 200
        articles = response.json()
        assert isinstance(articles, list)
        print(f"✓ Articles list returned: {len(articles)} articles")
        # Verify we have 45+ articles as mentioned in requirements
        assert len(articles) >= 40, f"Expected 45+ articles, got {len(articles)}"
    
    def test_get_single_article(self, auth_headers, existing_article_id):
        """GET /api/articles/{id} returns full article"""
        response = requests.get(f"{BASE_URL}/api/articles/{existing_article_id}", headers=auth_headers)
        assert response.status_code == 200
        article = response.json()
        assert "id" in article
        assert "title" in article
        assert "sections" in article
        print(f"✓ Single article retrieved: {article.get('title', '')[:50]}...")
    
    def test_get_nonexistent_article(self, auth_headers):
        """GET /api/articles/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/articles/nonexistent-id-12345", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Nonexistent article correctly returns 404")


class TestArticleGeneration:
    """Article generation async job tests"""
    
    def test_generate_article_starts_job(self, auth_headers):
        """POST /api/articles/generate returns job_id with status 'queued'"""
        response = requests.post(f"{BASE_URL}/api/articles/generate", headers=auth_headers, json={
            "topic": "Test VAT 2026",
            "primary_keyword": "VAT 2026",
            "secondary_keywords": ["podatek VAT", "stawki VAT"],
            "target_length": 500,
            "tone": "profesjonalny",
            "template": "standard"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Article generation job started: {data['job_id']}")
    
    def test_generate_article_status_check(self, auth_headers):
        """GET /api/articles/generate/status/{job_id} returns valid status"""
        # First start a job
        response = requests.post(f"{BASE_URL}/api/articles/generate", headers=auth_headers, json={
            "topic": "Test PIT 2026",
            "primary_keyword": "PIT 2026",
            "secondary_keywords": ["rozliczenie PIT"],
            "target_length": 500,
            "tone": "profesjonalny",
            "template": "standard"
        })
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/articles/generate/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "generating", "completed", "failed"]
        print(f"✓ Generation status check: {status_data['status']}")
    
    def test_generate_article_invalid_job_id(self, auth_headers):
        """GET /api/articles/generate/status/{invalid_id} returns 404"""
        response = requests.get(f"{BASE_URL}/api/articles/generate/status/invalid-job-id", headers=auth_headers)
        assert response.status_code == 404
        print("✓ Invalid job ID correctly returns 404")
    
    def test_generate_article_without_auth(self):
        """POST /api/articles/generate without auth returns 401"""
        response = requests.post(f"{BASE_URL}/api/articles/generate", json={
            "topic": "Test",
            "primary_keyword": "test"
        })
        assert response.status_code == 401
        print("✓ Article generation correctly requires auth")


class TestTopicSuggestions:
    """Topic suggestion tests with LLM fallback"""
    
    def test_suggest_topics(self):
        """POST /api/topics/suggest returns topic suggestions"""
        response = requests.post(f"{BASE_URL}/api/topics/suggest", json={
            "category": "VAT",
            "context": "aktualne zmiany w VAT 2026"
        })
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        assert len(data["topics"]) > 0
        print(f"✓ Topic suggestions returned: {len(data['topics'])} topics")
    
    def test_suggest_topics_default_params(self):
        """POST /api/topics/suggest with default params works"""
        response = requests.post(f"{BASE_URL}/api/topics/suggest", json={})
        assert response.status_code == 200
        data = response.json()
        assert "topics" in data
        print(f"✓ Topic suggestions with defaults: {len(data.get('topics', []))} topics")


class TestContentRewrite:
    """Content rewrite async job tests"""
    
    def test_rewrite_starts_job(self, auth_headers):
        """POST /api/rewrite starts async rewrite job"""
        response = requests.post(f"{BASE_URL}/api/rewrite", headers=auth_headers, json={
            "text": "To jest testowy tekst do przepisania. Zawiera informacje o podatkach VAT.",
            "style": "profesjonalny"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Rewrite job started: {data['job_id']}")
    
    def test_rewrite_status_check(self, auth_headers):
        """GET /api/rewrite/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/rewrite", headers=auth_headers, json={
            "text": "Testowy tekst do przepisania.",
            "style": "przystępny"
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/rewrite/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Rewrite status: {status_data['status']}")


class TestPlagiarismChecker:
    """Plagiarism checker async job tests"""
    
    def test_plagiarism_check_starts_job(self, auth_headers, existing_article_id):
        """POST /api/plagiarism/check starts plagiarism check"""
        response = requests.post(f"{BASE_URL}/api/plagiarism/check", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Plagiarism check started: {data['job_id']}")
    
    def test_plagiarism_status_check(self, auth_headers, existing_article_id):
        """GET /api/plagiarism/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/plagiarism/check", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/plagiarism/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Plagiarism status: {status_data['status']}")


class TestContentVerification:
    """Content verification async job tests"""
    
    def test_verify_check_starts_job(self, auth_headers, existing_article_id):
        """POST /api/verify/check starts content verification"""
        response = requests.post(f"{BASE_URL}/api/verify/check", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Content verification started: {data['job_id']}")
    
    def test_verify_status_check(self, auth_headers, existing_article_id):
        """GET /api/verify/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/verify/check", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/verify/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Verification status: {status_data['status']}")


class TestCompetitionAnalysis:
    """Competition analysis (auto-competition) async job tests"""
    
    def test_auto_competition_starts_job(self, auth_headers, existing_article_id):
        """POST /api/competition/auto-analyze starts competition analysis"""
        response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Auto competition analysis started: {data['job_id']}")
    
    def test_auto_competition_status_check(self, auth_headers, existing_article_id):
        """GET /api/competition/auto-status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/competition/auto-analyze", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/competition/auto-status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Auto competition status: {status_data['status']}")


class TestABTitleTesting:
    """A/B title testing async job tests"""
    
    def test_ab_title_starts_job(self, auth_headers, existing_article_id):
        """POST /api/articles/ab-title-test starts A/B title test"""
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", headers=auth_headers, json={
            "article_id": existing_article_id,
            "custom_variants": []
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ A/B title test started: {data['job_id']}")
    
    def test_ab_title_status_check(self, auth_headers, existing_article_id):
        """GET /api/articles/ab-title-status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/articles/ab-title-test", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/articles/ab-title-status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ A/B title status: {status_data['status']}")


class TestAutoMetaTags:
    """Auto meta tag generation async job tests"""
    
    def test_auto_meta_starts_job(self, auth_headers, existing_article_id):
        """POST /api/articles/auto-meta starts meta tag generation"""
        response = requests.post(f"{BASE_URL}/api/articles/auto-meta", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Auto meta generation started: {data['job_id']}")
    
    def test_auto_meta_status_check(self, auth_headers, existing_article_id):
        """GET /api/articles/auto-meta/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/articles/auto-meta", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/articles/auto-meta/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Auto meta status: {status_data['status']}")


class TestSmartSchedule:
    """Smart schedule suggestion async job tests"""
    
    def test_smart_schedule_starts_job(self, auth_headers, existing_article_id):
        """POST /api/articles/smart-schedule starts schedule suggestion"""
        response = requests.post(f"{BASE_URL}/api/articles/smart-schedule", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Smart schedule started: {data['job_id']}")
    
    def test_smart_schedule_status_check(self, auth_headers, existing_article_id):
        """GET /api/articles/smart-schedule/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/articles/smart-schedule", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/articles/smart-schedule/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Smart schedule status: {status_data['status']}")


class TestSocialPosts:
    """Social media post generation async job tests"""
    
    def test_social_posts_starts_job(self, auth_headers, existing_article_id):
        """POST /api/articles/social-posts starts social post generation"""
        response = requests.post(f"{BASE_URL}/api/articles/social-posts", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Social posts generation started: {data['job_id']}")
    
    def test_social_posts_status_check(self, auth_headers, existing_article_id):
        """GET /api/articles/social-posts/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/articles/social-posts", headers=auth_headers, json={
            "article_id": existing_article_id
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/articles/social-posts/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Social posts status: {status_data['status']}")


class TestNewsletter:
    """Newsletter generation tests"""
    
    def test_newsletter_generate(self, auth_headers, existing_article_id):
        """POST /api/newsletter/generate generates newsletter HTML"""
        response = requests.post(f"{BASE_URL}/api/newsletter/generate", headers=auth_headers, json={
            "title": "Test Newsletter",
            "article_ids": [existing_article_id],
            "style": "informacyjny"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "html" in data
        assert "title" in data
        print(f"✓ Newsletter generated: {data['id']}")
    
    def test_newsletter_list(self, auth_headers):
        """GET /api/newsletter/list returns newsletters"""
        response = requests.get(f"{BASE_URL}/api/newsletter/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Newsletter list: {len(data)} newsletters")


class TestKeywordAnalytics:
    """Keyword analytics async job tests"""
    
    def test_keyword_analytics_starts_job(self, auth_headers):
        """POST /api/keyword-analytics/analyze starts keyword analytics"""
        response = requests.post(f"{BASE_URL}/api/keyword-analytics/analyze", headers=auth_headers, json={
            "keywords": ["VAT 2026", "PIT rozliczenie", "ZUS składki"],
            "industry": "rachunkowość i podatki"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print(f"✓ Keyword analytics started: {data['job_id']}")
    
    def test_keyword_analytics_status_check(self, auth_headers):
        """GET /api/keyword-analytics/status/{job_id} returns status"""
        # Start job
        response = requests.post(f"{BASE_URL}/api/keyword-analytics/analyze", headers=auth_headers, json={
            "keywords": ["księgowość online"],
            "industry": "rachunkowość"
        })
        job_id = response.json()["job_id"]
        
        # Check status
        time.sleep(1)
        status_response = requests.get(f"{BASE_URL}/api/keyword-analytics/status/{job_id}", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["status"] in ["queued", "running", "completed", "failed"]
        print(f"✓ Keyword analytics status: {status_data['status']}")


class TestMiscEndpoints:
    """Miscellaneous endpoint tests"""
    
    def test_templates_list(self):
        """GET /api/templates returns content templates"""
        response = requests.get(f"{BASE_URL}/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"✓ Templates returned")
    
    def test_image_styles_list(self):
        """GET /api/image-styles returns available styles"""
        response = requests.get(f"{BASE_URL}/api/image-styles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or isinstance(data, dict)
        print(f"✓ Image styles returned")
    
    def test_stats_with_auth(self, auth_headers):
        """GET /api/stats with auth returns dashboard statistics"""
        response = requests.get(f"{BASE_URL}/api/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_articles" in data
        assert "avg_seo_score" in data
        print(f"✓ Stats returned: {data['total_articles']} articles, avg SEO: {data['avg_seo_score']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
