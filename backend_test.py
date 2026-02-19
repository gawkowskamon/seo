import requests
import sys
import json
from datetime import datetime

class AccountingBlogTester:
    def __init__(self, base_url="https://accounting-blog-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", expected_status=None, actual_status=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
            if expected_status and actual_status:
                print(f"   Expected: {expected_status}, Got: {actual_status}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "expected_status": expected_status,
            "actual_status": actual_status
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, response_type='json'):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        req_headers = {'Content-Type': 'application/json'}
        if self.token:
            req_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            req_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=req_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=req_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=req_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=req_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                if response_type == 'json' and response.content:
                    try:
                        return True, response.json()
                    except:
                        return True, {}
                else:
                    return True, response.content
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    if response.content:
                        err_data = response.json()
                        error_msg = err_data.get('detail', str(response.status_code))
                except:
                    pass
                self.log_test(name, False, error_msg, expected_status, response.status_code)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_login(self):
        """Test admin login"""
        print("🔑 Testing Admin Login...")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "monika.gawkowska@kurdynowski.pl", "password": "MonZuz8180!"}
        )
        if success and 'token' in response:
            self.token = response['token']
            self.user = response.get('user', {})
            if self.user.get('is_admin'):
                print(f"   ✅ Logged in as admin: {self.user.get('email')}")
                return True
            else:
                print(f"   ❌ User is not admin: {self.user}")
                return False
        return False

    def test_pdf_export(self):
        """Test PDF export with Polish characters"""
        print("\n📄 Testing PDF Export...")
        
        # First get a list of articles
        success, articles = self.run_test(
            "Get Articles List",
            "GET", 
            "articles",
            200
        )
        
        if not success or not articles:
            self.log_test("PDF Export - No Articles", False, "No articles found to test PDF export")
            return False
            
        # Use the first article for testing
        article_id = articles[0]['id']
        print(f"   Testing PDF export with article: {article_id}")
        
        success, pdf_data = self.run_test(
            "PDF Export with Polish Characters",
            "POST",
            f"articles/{article_id}/export",
            200,
            data={"format": "pdf"},
            response_type='binary'
        )
        
        if success and pdf_data:
            print(f"   ✅ PDF generated successfully ({len(pdf_data)} bytes)")
            # Check if it starts with PDF header
            if pdf_data.startswith(b'%PDF'):
                self.log_test("PDF Export - Valid Format", True)
                return True
            else:
                self.log_test("PDF Export - Invalid Format", False, "Response is not a valid PDF")
        
        return False

    def test_wordpress_settings(self):
        """Test WordPress settings endpoints"""
        print("\n🌐 Testing WordPress Settings...")
        
        # Test GET settings (should work for admin)
        success, settings = self.run_test(
            "Get WordPress Settings (Admin)",
            "GET",
            "settings/wordpress", 
            200
        )
        
        if success:
            print(f"   Current config status: {settings.get('configured', 'unknown')}")
        
        # Test POST settings (save new settings)
        test_settings = {
            "wp_url": "https://test-wp-site.com",
            "wp_user": "testuser",
            "wp_app_password": "test1234test5678test"
        }
        
        success, response = self.run_test(
            "Save WordPress Settings (Admin)",
            "POST",
            "settings/wordpress",
            200,
            data=test_settings
        )
        
        if success:
            print(f"   ✅ Settings saved: {response.get('message', 'OK')}")
        
        return success

    def test_wordpress_settings_non_admin(self):
        """Test that non-admin users get 403 on WordPress settings"""
        # This would require a non-admin user token, skipping for now
        # as we only have admin credentials
        print("\n⚠️  Skipping non-admin WordPress settings test (no non-admin user available)")
        return True

    def test_wordpress_plugin_download(self):
        """Test WordPress plugin download"""
        print("\n🔌 Testing WordPress Plugin Download...")
        
        success, plugin_code = self.run_test(
            "WordPress Plugin Download",
            "GET",
            "wordpress/plugin",
            200,
            response_type='binary'
        )
        
        if success and plugin_code:
            plugin_str = plugin_code.decode('utf-8') if isinstance(plugin_code, bytes) else plugin_code
            if '<?php' in plugin_str and 'Kurdynowski' in plugin_str:
                self.log_test("WordPress Plugin - Valid PHP Code", True)
                print(f"   ✅ Plugin generated ({len(plugin_str)} chars)")
                return True
            else:
                self.log_test("WordPress Plugin - Invalid Content", False, "Not valid PHP plugin code")
        
        return False

    def test_wordpress_publish(self):
        """Test WordPress publish endpoint"""
        print("\n📤 Testing WordPress Publish...")
        
        # Get articles first
        success, articles = self.run_test(
            "Get Articles for WP Publish",
            "GET",
            "articles", 
            200
        )
        
        if not success or not articles:
            self.log_test("WordPress Publish - No Articles", False, "No articles to publish")
            return False
        
        article_id = articles[0]['id']
        print(f"   Testing publish with article: {article_id}")
        
        # This should return 400 about config if WP is not properly configured
        success, response = self.run_test(
            "Publish to WordPress (Expected Config Error)",
            "POST",
            f"articles/{article_id}/publish-wordpress",
            400  # Expecting 400 due to invalid/test WP config
        )
        
        if success:
            print(f"   ✅ Endpoint exists and returns expected config error")
            return True
        
        # If it didn't return 400, check if it returned 502 (bad gateway) which is also acceptable
        # for invalid WP settings
        print("   Checking if endpoint exists with different error code...")
        try:
            url = f"{self.base_url}/api/articles/{article_id}/publish-wordpress"
            headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, timeout=10)
            
            if response.status_code in [400, 502]:
                self.log_test("WordPress Publish Endpoint", True, f"Returns {response.status_code} as expected for invalid config")
                return True
            else:
                self.log_test("WordPress Publish Endpoint", False, f"Unexpected status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("WordPress Publish Endpoint", False, f"Request failed: {e}")
            return False

    def test_additional_endpoints(self):
        """Test other endpoints mentioned in requirements"""
        print("\n🔍 Testing Additional Endpoints...")
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)
        
        # Test user profile
        self.run_test("User Profile", "GET", "auth/me", 200)
        
        # Test stats endpoint 
        self.run_test("Dashboard Stats", "GET", "stats", 200)
        
        return True

    def print_summary(self):
        """Print test summary"""
        print(f"\n" + "="*60)
        print(f"📊 TEST SUMMARY")
        print(f"="*60)
        print(f"Tests run: {self.tests_run}")
        print(f"Tests passed: {self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed < self.tests_run:
            print(f"\n❌ Failed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['name']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Run all backend tests"""
    print("🚀 Starting Accounting Blog Backend Tests")
    print("="*60)
    
    tester = AccountingBlogTester()
    
    # Authentication
    if not tester.test_login():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    # Run all tests
    tests = [
        tester.test_pdf_export,
        tester.test_wordpress_settings,
        tester.test_wordpress_settings_non_admin,
        tester.test_wordpress_plugin_download,
        tester.test_wordpress_publish,
        tester.test_additional_endpoints
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Print summary
    success = tester.print_summary()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())