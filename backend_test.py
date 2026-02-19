import requests
import sys
import json
from datetime import datetime
import time

class SEOArticleAPITester:
    def __init__(self, base_url="https://seo-article-builder.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.article_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail}")
                    except:
                        print(f"   Response: {response.text[:500]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        return self.run_test("Health Check", "GET", "", 200)

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_get_stats(self):
        """Test dashboard stats endpoint"""
        success, response = self.run_test("Dashboard Stats", "GET", "stats", 200)
        if success:
            required_keys = ['total_articles', 'avg_seo_score', 'needs_improvement']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in stats response: {key}")
                    return False
            print(f"   Stats: {response}")
        return success

    def test_list_articles(self):
        """Test list articles endpoint"""
        success, response = self.run_test("List Articles", "GET", "articles", 200)
        if success:
            if not isinstance(response, list):
                print(f"❌ Articles response should be a list, got: {type(response)}")
                return False
            print(f"   Found {len(response)} articles")
        return success

    def test_topic_suggestions(self):
        """Test topic suggestions endpoint"""
        data = {
            "category": "vat",
            "context": "test context for Polish accounting topics"
        }
        success, response = self.run_test(
            "Topic Suggestions", 
            "POST", 
            "topics/suggest", 
            200, 
            data=data,
            timeout=45  # Longer timeout for AI call
        )
        if success and 'topics' in response:
            topics = response['topics']
            print(f"   Generated {len(topics)} topic suggestions")
            if topics and len(topics) > 0:
                first_topic = topics[0]
                print(f"   First topic: {first_topic.get('title', 'N/A')}")
                # Check for Polish characters
                topic_text = str(first_topic)
                polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
                has_polish = any(char in topic_text.lower() for char in polish_chars)
                if has_polish:
                    print(f"   ✅ Polish characters found in topic suggestions")
                else:
                    print(f"   ⚠️  No Polish characters detected in topics")
        return success

    def test_article_generation(self):
        """Test article generation (may be slow)"""
        data = {
            "topic": "Jak rozliczać VAT w jednoosobowej działalności gospodarczej",
            "primary_keyword": "rozliczanie VAT",
            "secondary_keywords": ["VAT księgowość", "płatnik VAT"],
            "target_length": 1500,
            "tone": "profesjonalny"
        }
        
        print(f"\n🔍 Testing Article Generation...")
        print(f"   ⚠️  This may take 15-30 seconds (calling OpenAI GPT)")
        
        success, response = self.run_test(
            "Article Generation", 
            "POST", 
            "articles/generate", 
            200, 
            data=data,
            timeout=60  # Longer timeout for AI generation
        )
        
        if success and 'id' in response:
            self.article_id = response['id']
            print(f"   Generated article ID: {self.article_id}")
            
            # Check for Polish content
            title = response.get('title', '')
            if title:
                print(f"   Article title: {title}")
                polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
                has_polish = any(char in title.lower() for char in polish_chars)
                if has_polish:
                    print(f"   ✅ Polish characters found in generated content")
                
        return success

    def test_get_article(self):
        """Test get single article endpoint"""
        if not self.article_id:
            print("❌ Skipping - no article_id available")
            return False
            
        success, response = self.run_test(
            "Get Article", 
            "GET", 
            f"articles/{self.article_id}", 
            200
        )
        
        if success:
            required_keys = ['id', 'title', 'primary_keyword', 'seo_score']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in article response: {key}")
                    return False
            print(f"   Article loaded successfully")
            
        return success

    def test_seo_scoring(self):
        """Test SEO scoring endpoint"""
        if not self.article_id:
            print("❌ Skipping - no article_id available")
            return False
            
        data = {
            "primary_keyword": "rozliczanie VAT",
            "secondary_keywords": ["VAT księgowość"]
        }
        
        success, response = self.run_test(
            "SEO Scoring", 
            "POST", 
            f"articles/{self.article_id}/score", 
            200,
            data=data
        )
        
        if success:
            if 'percentage' not in response:
                print(f"❌ Missing percentage in SEO score response")
                return False
            print(f"   SEO Score: {response.get('percentage', 0)}%")
            
        return success

    def test_export_functionality(self):
        """Test export endpoints"""
        if not self.article_id:
            print("❌ Skipping - no article_id available")
            return False
            
        formats_to_test = ['facebook', 'google_business', 'html']
        all_passed = True
        
        for format_type in formats_to_test:
            data = {"format": format_type}
            success, response = self.run_test(
                f"Export {format_type.title()}", 
                "POST", 
                f"articles/{self.article_id}/export", 
                200,
                data=data
            )
            
            if success:
                if 'content' not in response or 'format' not in response:
                    print(f"❌ Missing keys in export response for {format_type}")
                    all_passed = False
                else:
                    content_length = len(str(response.get('content', '')))
                    print(f"   {format_type} export: {content_length} characters")
            else:
                all_passed = False
                
        return all_passed

    def test_existing_article(self, article_id):
        """Test existing article with specific ID"""
        success, response = self.run_test(
            f"Get Existing Article {article_id}", 
            "GET", 
            f"articles/{article_id}", 
            200
        )
        
        if success:
            required_keys = ['id', 'title', 'sections', 'faq', 'seo_score']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in article response: {key}")
                    return False
            print(f"   Article title: {response.get('title', 'N/A')}")
            print(f"   SEO score: {response.get('seo_score', {}).get('percentage', 'N/A')}%")
            print(f"   Sections: {len(response.get('sections', []))}")
            print(f"   FAQ items: {len(response.get('faq', []))}")
            self.article_id = article_id  # Set for export tests
            
        return success

    def test_exports_for_existing_article(self, article_id):
        """Test export endpoints for existing article"""
        formats_to_test = ['facebook', 'google_business', 'html']
        all_passed = True
        
        for format_type in formats_to_test:
            data = {"format": format_type}
            success, response = self.run_test(
                f"Export {format_type.title()} for {article_id}", 
                "POST", 
                f"articles/{article_id}/export", 
                200,
                data=data
            )
            
            if success:
                if 'content' not in response or 'format' not in response:
                    print(f"❌ Missing keys in export response for {format_type}")
                    all_passed = False
                else:
                    content_length = len(str(response.get('content', '')))
                    print(f"   {format_type} export: {content_length} characters")
                    # Show preview for shorter content
                    if content_length < 200:
                        print(f"   Preview: {str(response.get('content', ''))[:100]}...")
            else:
                all_passed = False
                
        return all_passed

    def test_regenerate_meta_for_existing_article(self, article_id):
        """Test regenerate meta endpoint for existing article"""
        data = {"section": "meta"}
        success, response = self.run_test(
            f"Regenerate Meta for {article_id}", 
            "POST", 
            f"articles/{article_id}/regenerate", 
            200,
            data=data,
            timeout=45  # Longer timeout for AI regeneration
        )
        
        if success:
            required_keys = ['meta_title', 'meta_description']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in regenerate response: {key}")
                    return False
            
            meta_title = response.get('meta_title', '')
            meta_description = response.get('meta_description', '')
            print(f"   Generated meta title: {meta_title}")
            print(f"   Generated meta description: {meta_description}")
            
            # Check if content is in Polish
            polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
            meta_text = (meta_title + ' ' + meta_description).lower()
            has_polish = any(char in meta_text for char in polish_chars)
            if has_polish:
                print(f"   ✅ Polish characters found in generated meta data")
            else:
                print(f"   ⚠️  No Polish characters detected in meta data")
                
        return success

def main():
    print("🚀 Testing Polish SEO Article Writer API - Focused Test")
    print("=" * 50)
    
    tester = SEOArticleAPITester()
    existing_article_id = "322bc85b-91e7-4888-a055-32a14db1ed85"
    
    # Test required backend endpoints
    print("\n📊 Required Backend API Tests")
    tester.test_get_stats()
    tester.test_list_articles()
    tester.test_existing_article(existing_article_id)
    tester.test_exports_for_existing_article(existing_article_id)
    tester.test_regenerate_meta_for_existing_article(existing_article_id)
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All API tests passed!")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"❌ {failed_tests} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())