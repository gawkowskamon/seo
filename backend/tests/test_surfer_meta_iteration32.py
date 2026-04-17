"""
Iteration 32: Test SurferSEO, Meta Regeneration, Keyword Research, URL Audit
Tests for user-reported issues: 'SurferSEO nie działa' and 'nie działa generowanie zmian w metadanych'
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
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"✓ Login successful, user: {data['user'].get('email')}")


class TestSurferSEOAsync:
    """SurferSEO async SERP analysis tests - User reported: 'SurferSEO nie działa'"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_surfer_analyze_serp_async_returns_job_id(self, auth_token):
        """POST /api/surfer/analyze-serp/async should return job_id"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={"keyword": "księgowość online"},
            headers=headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "job_id" in data, "No job_id in response"
        assert data.get("status") == "running", f"Expected status 'running', got {data.get('status')}"
        print(f"✓ SERP async job started: {data['job_id']}")
        return data["job_id"]
    
    def test_surfer_analyze_serp_async_completes(self, auth_token):
        """POST /api/surfer/analyze-serp/async should complete with result"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Start job
        start_response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={"keyword": "podatek VAT"},
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 60 seconds)
        max_attempts = 20
        for attempt in range(max_attempts):
            time.sleep(3)
            status_response = requests.get(
                f"{BASE_URL}/api/surfer/analyze-serp/status/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                assert "result" in status_data, "No result in completed job"
                result = status_data["result"]
                # Verify result structure
                assert "keyword" in result or "benchmarks" in result, f"Invalid result structure: {result.keys()}"
                print(f"✓ SERP analysis completed after {(attempt+1)*3}s")
                print(f"  Result keys: {list(result.keys())}")
                return
            elif status_data.get("status") == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
        
        pytest.fail(f"Job did not complete within {max_attempts*3} seconds")
    
    def test_surfer_analyze_serp_status_invalid_job(self, auth_token):
        """GET /api/surfer/analyze-serp/status/{job_id} should return 404 for invalid job"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(
            f"{BASE_URL}/api/surfer/analyze-serp/status/invalid-job-id-12345",
            headers=headers
        )
        assert response.status_code == 404
        print("✓ Invalid job returns 404")
    
    def test_surfer_analyze_serp_requires_keyword(self, auth_token):
        """POST /api/surfer/analyze-serp/async should require keyword"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/analyze-serp/async",
            json={"keyword": ""},
            headers=headers
        )
        assert response.status_code == 400
        print("✓ Empty keyword returns 400")


class TestSurferScore:
    """SurferSEO scoring tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def test_article_id(self, auth_token):
        """Get an existing article ID for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        if response.status_code == 200:
            articles = response.json()
            if articles:
                return articles[0]["id"]
        pytest.skip("No articles available for testing")
    
    def test_surfer_score_returns_metrics(self, auth_token, test_article_id):
        """POST /api/surfer/score should return percentage and metrics"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Mock surfer_data for scoring
        surfer_data = {
            "keyword": "test keyword",
            "benchmarks": {
                "word_count": {"min": 1000, "max": 3000, "avg": 2000, "recommended": 2500},
                "headings": {"h2_min": 4, "h2_max": 10, "h2_avg": 6, "h3_min": 2, "h3_max": 8, "h3_avg": 4},
                "paragraphs": {"min": 10, "max": 30, "avg": 20},
                "images": {"min": 2, "max": 6, "avg": 4},
                "lists": {"min": 1, "max": 5, "avg": 3},
                "bold_phrases": {"min": 5, "max": 15, "avg": 10},
                "faq_questions": {"min": 3, "max": 8, "avg": 5}
            },
            "nlp_terms": [
                {"term": "księgowość", "importance": "wysoka", "recommended_count": 3}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/surfer/score",
            json={"article_id": test_article_id, "surfer_data": surfer_data},
            headers=headers
        )
        assert response.status_code == 200, f"Score failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "percentage" in data, "No percentage in score response"
        assert "metrics" in data, "No metrics in score response"
        assert isinstance(data["percentage"], (int, float)), "Percentage should be numeric"
        print(f"✓ Surfer score: {data['percentage']}%")
        print(f"  Metrics: {list(data['metrics'].keys())}")


class TestMetaRegeneration:
    """Meta regeneration tests - User reported: 'nie działa generowanie zmian w metadanych'"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def test_article_id(self, auth_token):
        """Get an existing article ID for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        if response.status_code == 200:
            articles = response.json()
            if articles:
                return articles[0]["id"]
        pytest.skip("No articles available for testing")
    
    def test_regenerate_meta_returns_title_and_description(self, auth_token, test_article_id):
        """POST /api/articles/{article_id}/regenerate with section='meta' should return meta_title and meta_description"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "meta"},
            headers=headers,
            timeout=120
        )
        assert response.status_code == 200, f"Meta regeneration failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "meta_title" in data, f"No meta_title in response. Got: {data.keys()}"
        assert "meta_description" in data, f"No meta_description in response. Got: {data.keys()}"
        assert len(data["meta_title"]) > 0, "meta_title is empty"
        assert len(data["meta_description"]) > 0, "meta_description is empty"
        print(f"✓ Meta regeneration successful")
        print(f"  meta_title: {data['meta_title'][:60]}...")
        print(f"  meta_description: {data['meta_description'][:80]}...")
    
    def test_regenerate_faq_returns_faq_array(self, auth_token, test_article_id):
        """POST /api/articles/{article_id}/regenerate with section='faq' should return faq array"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "faq"},
            headers=headers,
            timeout=120
        )
        assert response.status_code == 200, f"FAQ regeneration failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "faq" in data, f"No faq in response. Got: {data.keys()}"
        assert isinstance(data["faq"], list), "faq should be a list"
        assert len(data["faq"]) > 0, "faq array is empty"
        
        # Verify FAQ item structure
        first_faq = data["faq"][0]
        assert "question" in first_faq, "FAQ item missing 'question'"
        assert "answer" in first_faq, "FAQ item missing 'answer'"
        print(f"✓ FAQ regeneration successful, {len(data['faq'])} items")
        print(f"  First Q: {first_faq['question'][:50]}...")
    
    def test_regenerate_invalid_section_returns_error(self, auth_token, test_article_id):
        """POST /api/articles/{article_id}/regenerate with invalid section should return 400"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/articles/{test_article_id}/regenerate",
            json={"section": "invalid_section"},
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid section returns 400")


class TestAutoMeta:
    """Auto meta generation tests (async pattern)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def test_article_id(self, auth_token):
        """Get an existing article ID for testing"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers)
        if response.status_code == 200:
            articles = response.json()
            if articles:
                return articles[0]["id"]
        pytest.skip("No articles available for testing")
    
    def test_auto_meta_returns_job_id(self, auth_token, test_article_id):
        """POST /api/articles/auto-meta should return job_id"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/articles/auto-meta",
            json={"article_id": test_article_id},
            headers=headers
        )
        assert response.status_code == 200, f"Auto meta failed: {response.text}"
        data = response.json()
        assert "job_id" in data, "No job_id in response"
        print(f"✓ Auto meta job started: {data['job_id']}")
    
    def test_auto_meta_completes_with_results(self, auth_token, test_article_id):
        """POST /api/articles/auto-meta should complete with meta results"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Start job
        start_response = requests.post(
            f"{BASE_URL}/api/articles/auto-meta",
            json={"article_id": test_article_id},
            headers=headers
        )
        assert start_response.status_code == 200
        job_id = start_response.json()["job_id"]
        
        # Poll for completion (max 60 seconds)
        max_attempts = 20
        for attempt in range(max_attempts):
            time.sleep(3)
            status_response = requests.get(
                f"{BASE_URL}/api/articles/auto-meta/status/{job_id}",
                headers=headers
            )
            assert status_response.status_code == 200, f"Status check failed: {status_response.text}"
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                assert "result" in status_data, "No result in completed job"
                result = status_data["result"]
                # Verify result structure
                assert "recommended" in result or "meta_titles" in result, f"Invalid result: {result.keys()}"
                print(f"✓ Auto meta completed after {(attempt+1)*3}s")
                if "recommended" in result:
                    print(f"  Recommended title: {result['recommended'].get('meta_title', '')[:50]}...")
                return
            elif status_data.get("status") == "failed":
                pytest.fail(f"Job failed: {status_data.get('error')}")
        
        pytest.fail(f"Job did not complete within {max_attempts*3} seconds")


class TestKeywordResearch:
    """Keyword Research page API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_keyword_research_returns_main_keyword_and_keywords(self, auth_token):
        """POST /api/surfer/keyword-research should return main_keyword and keywords"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/keyword-research",
            json={"seed_keyword": "faktura VAT"},
            headers=headers,
            timeout=120
        )
        assert response.status_code == 200, f"Keyword research failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "main_keyword" in data, f"No main_keyword in response. Got: {data.keys()}"
        assert "keywords" in data, f"No keywords in response. Got: {data.keys()}"
        assert isinstance(data["keywords"], list), "keywords should be a list"
        assert len(data["keywords"]) > 0, "keywords array is empty"
        
        # Verify main_keyword structure
        main_kw = data["main_keyword"]
        assert "keyword" in main_kw or "monthly_volume" in main_kw, f"Invalid main_keyword: {main_kw.keys()}"
        
        print(f"✓ Keyword research successful")
        print(f"  Main keyword: {main_kw.get('keyword', 'N/A')}")
        print(f"  Related keywords: {len(data['keywords'])}")
    
    def test_keyword_research_requires_seed_keyword(self, auth_token):
        """POST /api/surfer/keyword-research should require seed_keyword"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/keyword-research",
            json={"seed_keyword": ""},
            headers=headers
        )
        assert response.status_code == 400
        print("✓ Empty seed_keyword returns 400")


class TestURLAudit:
    """URL Audit page API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_audit_url_returns_score_and_issues(self, auth_token):
        """POST /api/surfer/audit-url should return url, overall_score, and issues"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/audit-url",
            json={"url": "https://www.gov.pl/web/finanse"},
            headers=headers,
            timeout=120
        )
        assert response.status_code == 200, f"URL audit failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "url" in data, f"No url in response. Got: {data.keys()}"
        assert "overall_score" in data, f"No overall_score in response. Got: {data.keys()}"
        assert "issues" in data, f"No issues in response. Got: {data.keys()}"
        assert isinstance(data["issues"], list), "issues should be a list"
        
        print(f"✓ URL audit successful")
        print(f"  URL: {data['url']}")
        print(f"  Overall score: {data['overall_score']}")
        print(f"  Issues found: {len(data['issues'])}")
    
    def test_audit_url_requires_url(self, auth_token):
        """POST /api/surfer/audit-url should require url"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/audit-url",
            json={"url": ""},
            headers=headers
        )
        assert response.status_code == 400
        print("✓ Empty url returns 400")


class TestContentPlanner:
    """Content Planner API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_content_planner_returns_clusters(self, auth_token):
        """POST /api/surfer/content-planner should return clusters"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/content-planner",
            json={"keywords": ["księgowość online", "faktura VAT", "podatek dochodowy", "ZUS składki"]},
            headers=headers,
            timeout=120
        )
        assert response.status_code == 200, f"Content planner failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "clusters" in data, f"No clusters in response. Got: {data.keys()}"
        assert isinstance(data["clusters"], list), "clusters should be a list"
        
        print(f"✓ Content planner successful")
        print(f"  Clusters: {len(data['clusters'])}")
    
    def test_content_planner_requires_keywords(self, auth_token):
        """POST /api/surfer/content-planner should require keywords"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(
            f"{BASE_URL}/api/surfer/content-planner",
            json={"keywords": []},
            headers=headers
        )
        assert response.status_code == 400
        print("✓ Empty keywords returns 400")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
