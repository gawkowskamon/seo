import requests
import sys
import json
from datetime import datetime
import time

class SEOArticleAPITester:
    def __init__(self, base_url="https://seo-article-builder-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.article_id = None
        self.token = None
        self.user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Add auth header if token is available and use_auth is True
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

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

    def test_get_templates(self):
        """Test GET /api/templates returns 8 templates"""
        success, response = self.run_test("Get Templates", "GET", "templates", 200)
        if success:
            if not isinstance(response, list):
                print(f"❌ Templates response should be a list, got: {type(response)}")
                return False
            print(f"   Found {len(response)} templates")
            if len(response) != 8:
                print(f"❌ Expected 8 templates, got {len(response)}")
                return False
            
            # Verify template structure
            if len(response) > 0:
                template = response[0]
                required_keys = ['id', 'name', 'description', 'icon', 'category']
                for key in required_keys:
                    if key not in template:
                        print(f"❌ Missing key in template: {key}")
                        return False
                        
            # Show all template names
            template_names = [t.get('name', 'Unknown') for t in response]
            print(f"   Template names: {', '.join(template_names)}")
        return success

    def test_register_user(self):
        """Test POST /api/auth/register creates user and returns JWT token"""
        timestamp = int(datetime.now().timestamp())
        test_email = f"test_user_{timestamp}@kurdynowski.pl"
        test_password = "TestPass123!"
        test_name = f"Test User {timestamp}"
        
        data = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name
        }
        
        success, response = self.run_test("Register New User", "POST", "auth/register", 200, data=data)
        if success:
            required_keys = ['user', 'token']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in register response: {key}")
                    return False
            
            self.token = response['token']
            self.user_data = response['user']
            print(f"   Registered user: {self.user_data.get('email')}")
            print(f"   Token received: {self.token[:20]}...")
            
        return success

    def test_register_duplicate_email(self):
        """Test POST /api/auth/register rejects duplicate email"""
        # Use existing test user email
        data = {
            "email": "test@kurdynowski.pl",
            "password": "test123",
            "full_name": "Duplicate Test"
        }
        
        success, response = self.run_test("Register Duplicate Email", "POST", "auth/register", 400, data=data)
        if success:
            print(f"   ✅ Correctly rejected duplicate email registration")
        return success

    def test_login_user(self):
        """Test POST /api/auth/login authenticates user and returns JWT token"""
        data = {
            "email": "test@kurdynowski.pl",
            "password": "test123"
        }
        
        success, response = self.run_test("Login Existing User", "POST", "auth/login", 200, data=data)
        if success:
            required_keys = ['user', 'token']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in login response: {key}")
                    return False
            
            self.token = response['token']
            self.user_data = response['user']
            print(f"   Logged in user: {self.user_data.get('email')}")
            print(f"   Token received: {self.token[:20]}...")
            
        return success

    def test_get_me_with_token(self):
        """Test GET /api/auth/me returns user data with valid token"""
        if not self.token:
            print("❌ Skipping - no token available")
            return False
            
        success, response = self.run_test("Get User Profile", "GET", "auth/me", 200, use_auth=True)
        if success:
            required_keys = ['id', 'email']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in user profile response: {key}")
                    return False
            
            print(f"   User ID: {response.get('id')}")
            print(f"   Email: {response.get('email')}")
            print(f"   Full name: {response.get('full_name', 'N/A')}")
            
        return success

    def test_get_me_without_token(self):
        """Test GET /api/auth/me returns 401 without token"""
        success, response = self.run_test("Get User Profile Without Token", "GET", "auth/me", 401, use_auth=False)
        if success:
            print(f"   ✅ Correctly rejected request without token")
        return success

    def test_article_generation_with_template(self):
        """Test POST /api/articles/generate accepts template parameter"""
        if not self.token:
            print("❌ Skipping - no token available")
            return False
            
        data = {
            "topic": "Jak rozliczać VAT w jednoosobowej działalności gospodarczej",
            "primary_keyword": "rozliczanie VAT",
            "secondary_keywords": ["VAT księgowość", "płatnik VAT"],
            "target_length": 1500,
            "tone": "profesjonalny",
            "template": "poradnik"  # Test with specific template
        }
        
        print(f"\n🔍 Testing Article Generation with Template...")
        print(f"   ⚠️  This may take 15-30 seconds (calling OpenAI GPT)")
        
        success, response = self.run_test(
            "Article Generation with Template", 
            "POST", 
            "articles/generate", 
            200, 
            data=data,
            timeout=60,
            use_auth=True
        )
        
        if success and 'id' in response:
            self.article_id = response['id']
            print(f"   Generated article ID: {self.article_id}")
            print(f"   Template used: {response.get('template', 'N/A')}")
            
            # Verify the template was saved
            if response.get('template') != 'poradnik':
                print(f"❌ Template not saved correctly. Expected 'poradnik', got '{response.get('template')}'")
                return False
            
            # Check for Polish content
            title = response.get('title', '')
            if title:
                print(f"   Article title: {title}")
                
        return success

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

    def test_get_article_images(self, article_id):
        """Test get images for article endpoint"""
        success, response = self.run_test(
            f"Get Article Images for {article_id}", 
            "GET", 
            f"articles/{article_id}/images", 
            200
        )
        
        if success:
            if not isinstance(response, list):
                print(f"❌ Images response should be a list, got: {type(response)}")
                return False
            print(f"   Found {len(response)} images for article")
            if len(response) > 0:
                # Check first image structure (without data field in list)
                img = response[0]
                required_keys = ['id', 'prompt', 'style', 'mime_type', 'created_at']
                for key in required_keys:
                    if key not in img:
                        print(f"❌ Missing key in image list response: {key}")
                        return False
                print(f"   First image: style={img.get('style')}, prompt={img.get('prompt', '')[:50]}...")
                # Store image ID for full image test
                self.image_id = img.get('id')
                
        return success

    def test_get_single_image(self):
        """Test get single image endpoint"""
        if not hasattr(self, 'image_id') or not self.image_id:
            print("❌ Skipping - no image_id available")
            return False
            
        success, response = self.run_test(
            f"Get Single Image {self.image_id}", 
            "GET", 
            f"images/{self.image_id}", 
            200
        )
        
        if success:
            required_keys = ['id', 'prompt', 'style', 'mime_type', 'data', 'created_at']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in single image response: {key}")
                    return False
            
            data_length = len(response.get('data', ''))
            print(f"   Image data length: {data_length} characters (base64)")
            print(f"   MIME type: {response.get('mime_type')}")
            print(f"   Style: {response.get('style')}")
            
            # Validate base64 data
            if data_length < 100:
                print(f"⚠️  Image data seems too small: {data_length} chars")
                return False
                
        return success

    def test_image_generation_skip(self):
        """Skip image generation test as instructed (takes 15-30s)"""
        print(f"\n🔍 Skipping Image Generation Test...")
        print(f"   ⚠️  Skipped as per instructions (takes 15-30s with AI model)")
        print(f"   ✅ Would test: POST /api/images/generate with prompt and style")
        return True

    def test_seo_assistant_analyze(self, article_id):
        """Test SEO Assistant analyze mode"""
        data = {"mode": "analyze"}
        success, response = self.run_test(
            f"SEO Assistant Analyze for {article_id}", 
            "POST", 
            f"articles/{article_id}/seo-assistant", 
            200,
            data=data,
            timeout=120  # Longer timeout for AI analysis
        )
        
        if success:
            required_keys = ['suggestions', 'assistant_message']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in SEO assistant response: {key}")
                    return False
            
            suggestions = response.get('suggestions', [])
            assistant_message = response.get('assistant_message', '')
            
            print(f"   Generated {len(suggestions)} SEO suggestions")
            print(f"   Assistant message: {assistant_message[:100]}...")
            
            # Validate suggestions structure
            if len(suggestions) > 0:
                first_suggestion = suggestions[0]
                required_suggestion_keys = ['id', 'title', 'category', 'impact', 'rationale', 'apply_target']
                for key in required_suggestion_keys:
                    if key not in first_suggestion:
                        print(f"❌ Missing key in suggestion: {key}")
                        return False
                
                print(f"   First suggestion: {first_suggestion.get('title', 'N/A')}")
                print(f"   Impact: {first_suggestion.get('impact', 'N/A')}")
                print(f"   Category: {first_suggestion.get('category', 'N/A')}")
                
                # Check for Polish content
                polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
                suggestion_text = (first_suggestion.get('title', '') + ' ' + first_suggestion.get('rationale', '')).lower()
                has_polish = any(char in suggestion_text for char in polish_chars)
                if has_polish:
                    print(f"   ✅ Polish characters found in SEO suggestions")
                else:
                    print(f"   ⚠️  No Polish characters detected in suggestions")
            
        return success

    def test_seo_assistant_chat(self, article_id):
        """Test SEO Assistant chat mode"""
        data = {
            "mode": "chat",
            "message": "Jak mogę poprawić SEO tego artykułu?",
            "history": []
        }
        success, response = self.run_test(
            f"SEO Assistant Chat for {article_id}", 
            "POST", 
            f"articles/{article_id}/seo-assistant", 
            200,
            data=data,
            timeout=120  # Longer timeout for AI chat
        )
        
        if success:
            required_keys = ['suggestions', 'assistant_message']
            for key in required_keys:
                if key not in response:
                    print(f"❌ Missing key in SEO assistant chat response: {key}")
                    return False
            
            suggestions = response.get('suggestions', [])
            assistant_message = response.get('assistant_message', '')
            
            print(f"   Chat response: {assistant_message[:150]}...")
            print(f"   Additional suggestions: {len(suggestions)}")
            
            # Check for Polish content in response
            polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
            response_text = assistant_message.lower()
            has_polish = any(char in response_text for char in polish_chars)
            if has_polish:
                print(f"   ✅ Polish characters found in chat response")
            else:
                print(f"   ⚠️  No Polish characters detected in chat response")
            
        return success

    def test_seo_assistant_invalid_article(self):
        """Test SEO Assistant with invalid article ID"""
        invalid_id = "invalid-article-id-12345"
        data = {"mode": "analyze"}
        success, response = self.run_test(
            f"SEO Assistant Invalid Article {invalid_id}", 
            "POST", 
            f"articles/{invalid_id}/seo-assistant", 
            404,  # Expect 404 for invalid article
            data=data
        )
        
        if success:
            print(f"   ✅ Properly returns 404 for invalid article ID")
        
        return success

def main():
    print("🚀 Testing SEO Article Builder API - Authentication & Templates")
    print("=" * 60)
    
    tester = SEOArticleAPITester()
    
    # Test core functionality first
    print("\n🏠 Basic API Tests")
    tester.test_api_root()
    tester.test_get_stats()
    
    # Test new template system
    print("\n📋 Template System Tests")
    tester.test_get_templates()
    
    # Test authentication system
    print("\n🔐 Authentication System Tests")
    tester.test_register_user()
    tester.test_register_duplicate_email()
    tester.test_login_user()
    tester.test_get_me_with_token()
    tester.test_get_me_without_token()
    
    # Test article generation with templates
    print("\n📝 Article Generation with Templates")
    tester.test_article_generation_with_template()
    
    # Test basic article operations
    print("\n📚 Article Management Tests")
    tester.test_list_articles()
    if tester.article_id:
        tester.test_get_article()
        tester.test_seo_scoring()
        tester.test_export_functionality()
    
    # Print final results
    print("\n" + "=" * 60)
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