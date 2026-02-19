import requests
import sys
import json
from datetime import datetime

class ImageLibraryTester:
    def __init__(self, base_url="https://accounting-blog-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_data = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, use_auth=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=data, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASS - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ FAIL - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail}")
                    except:
                        print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ FAIL - Timeout after {timeout}s")
            return False, {}
        except Exception as e:
            print(f"❌ FAIL - Error: {str(e)}")
            return False, {}

    def login_admin(self):
        """Login with admin credentials"""
        data = {
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, data=data, use_auth=False)
        if success:
            self.token = response['token']
            self.user_data = response['user']
            print(f"   Logged in as: {self.user_data.get('email')} (Admin: {self.user_data.get('is_admin')})")
            return True
        return False

    def test_library_endpoints(self):
        """Test basic library endpoints"""
        print("\n📚 Testing Library Endpoints...")
        
        # Test GET /api/library/images
        success, response = self.run_test("Library - List Images", "GET", "library/images", 200)
        if success:
            images = response.get('images', [])
            total = response.get('total', 0)
            print(f"   Found {total} images ({len(images)} in current page)")
            if images:
                img = images[0]
                print(f"   Sample: {img.get('prompt', '')[:50]}... (style: {img.get('style')})")
                self.sample_image_id = img.get('id')
        
        # Test search
        success, response = self.run_test("Library - Search", "GET", "library/images", 200, 
                                        data={"q": "test", "limit": 5})
        if success:
            print(f"   Search returned {len(response.get('images', []))} results")
        
        # Test filter by style
        success, response = self.run_test("Library - Filter by Style", "GET", "library/images", 200,
                                        data={"style": "hero", "limit": 5})
        if success:
            images = response.get('images', [])
            print(f"   Style filter returned {len(images)} hero images")
        
        # Test GET /api/library/tags
        success, response = self.run_test("Library - List Tags", "GET", "library/tags", 200)
        if success:
            tags = response if isinstance(response, list) else []
            print(f"   Found {len(tags)} unique tags")
            if tags:
                print(f"   Sample tags: {[t.get('tag', 'N/A') for t in tags[:3]]}")

    def test_image_tag_management(self):
        """Test image tag management"""
        print("\n🏷️  Testing Tag Management...")
        
        if not hasattr(self, 'sample_image_id') or not self.sample_image_id:
            print("   Skipping - no sample image available")
            return
        
        # Test updating image tags
        test_tags = ["test-tag", "księgowość", "automated-test"]
        success, response = self.run_test(
            "Update Image Tags", 
            "PUT", 
            f"images/{self.sample_image_id}/tags", 
            200,
            data={"tags": test_tags}
        )
        if success:
            updated_tags = response.get('tags', [])
            print(f"   Updated tags: {updated_tags}")
            if set(updated_tags) == set(test_tags):
                print(f"   ✅ Tags updated correctly")
            else:
                print(f"   ⚠️  Tag mismatch - expected: {test_tags}, got: {updated_tags}")

    def test_user_scoping(self):
        """Test user scoping for library"""
        print("\n👤 Testing User Scoping...")
        
        success, response = self.run_test("Library - User Scoped Images", "GET", "library/images", 200)
        if success:
            images = response.get('images', [])
            user_id = self.user_data.get('id')
            is_admin = self.user_data.get('is_admin', False)
            
            if is_admin:
                print(f"   Admin user sees {len(images)} images (all users)")
            else:
                # Check if all images belong to current user
                user_images = [img for img in images if img.get('user_id') == user_id]
                print(f"   Non-admin user sees {len(user_images)}/{len(images)} own images")

    def test_admin_user_management_regression(self):
        """Test admin user management still works"""
        print("\n🔧 Testing Admin User Management (Regression)...")
        
        if not self.user_data.get('is_admin'):
            print("   Skipping - user is not admin")
            return
        
        # Test listing users
        success, response = self.run_test("Admin - List Users", "GET", "admin/users", 200)
        if success:
            users = response if isinstance(response, list) else []
            print(f"   Found {len(users)} users in system")
            if users:
                user = users[0]
                required_fields = ['id', 'email', 'full_name', 'is_admin']
                has_fields = all(field in user for field in required_fields)
                print(f"   User structure valid: {has_fields}")

    def test_image_endpoints(self):
        """Test individual image endpoints"""
        print("\n🖼️  Testing Individual Image Endpoints...")
        
        if not hasattr(self, 'sample_image_id') or not self.sample_image_id:
            print("   Skipping - no sample image available")
            return
        
        # Test getting single image
        success, response = self.run_test(
            "Get Single Image", 
            "GET", 
            f"images/{self.sample_image_id}", 
            200
        )
        if success:
            required_fields = ['id', 'prompt', 'style', 'mime_type', 'data']
            has_fields = all(field in response for field in required_fields)
            data_length = len(response.get('data', ''))
            print(f"   Image data length: {data_length} chars")
            print(f"   Has all required fields: {has_fields}")

    def test_image_styles_endpoint(self):
        """Test image styles endpoint"""
        print("\n🎨 Testing Image Styles...")
        
        success, response = self.run_test("Get Image Styles", "GET", "image-styles", 200, use_auth=False)
        if success:
            if isinstance(response, list) and len(response) >= 7:
                print(f"   ✅ Found {len(response)} image styles")
                style_names = [s.get('name', 'Unknown') for s in response]
                print(f"   Available styles: {', '.join(style_names)}")
            else:
                print(f"   ⚠️  Expected at least 7 styles, got {len(response) if isinstance(response, list) else 0}")

    def run_all_tests(self):
        """Run all library tests"""
        print("🚀 Testing Accounting Blog Image Library")
        print(f"Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Login first
        if not self.login_admin():
            print("❌ Failed to login - stopping tests")
            return False
        
        # Run test suites
        self.test_image_styles_endpoint()
        self.test_library_endpoints()
        self.test_image_tag_management()
        self.test_image_endpoints()
        self.test_user_scoping()
        self.test_admin_user_management_regression()
        
        # Print results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ImageLibraryTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All image library tests passed!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed - check output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())