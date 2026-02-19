import requests
import sys
import json
import base64
from datetime import datetime

class AdminFeaturesAPITester:
    def __init__(self, base_url="https://accounting-blog-ai.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None
        self.user_data = None
        self.created_user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, use_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

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

    def test_admin_login(self):
        """Test admin login with Monika's credentials"""
        data = {
            "email": "monika.gawkowska@kurdynowski.pl",
            "password": "MonZuz8180!"
        }
        
        success, response = self.run_test("Admin Login (Monika)", "POST", "auth/login", 200, data=data)
        if success:
            user = response.get('user', {})
            if not user.get('is_admin'):
                print(f"❌ User should have is_admin=true, got: {user.get('is_admin')}")
                return False
            
            self.token = response['token']
            self.user_data = user
            print(f"   ✅ Admin user logged in: {user.get('email')}")
            print(f"   ✅ is_admin: {user.get('is_admin')}")
            
        return success

    def test_admin_list_users(self):
        """Test GET /api/admin/users"""
        success, response = self.run_test("Admin List Users", "GET", "admin/users", 200, use_auth=True)
        if success:
            if not isinstance(response, list):
                print(f"❌ Should be a list, got: {type(response)}")
                return False
            
            print(f"   ✅ Found {len(response)} users in system")
            if response:
                user = response[0]
                required_keys = ['id', 'email', 'full_name', 'is_admin', 'article_count']
                missing_keys = [k for k in required_keys if k not in user]
                if missing_keys:
                    print(f"❌ Missing keys: {missing_keys}")
                    return False
                print(f"   First user: {user.get('email')} (admin: {user.get('is_admin')}, articles: {user.get('article_count')})")
        
        return success

    def test_admin_create_user(self):
        """Test POST /api/admin/users"""
        timestamp = int(datetime.now().timestamp())
        test_email = f"admin_test_{timestamp}@kurdynowski.pl"
        
        data = {
            "email": test_email,
            "password": "AdminTest123!",
            "full_name": f"Admin Test User {timestamp}",
            "is_admin": False
        }
        
        success, response = self.run_test("Admin Create User", "POST", "admin/users", 200, data=data, use_auth=True)
        if success:
            required_keys = ['id', 'email', 'full_name', 'is_admin']
            missing_keys = [k for k in required_keys if k not in response]
            if missing_keys:
                print(f"❌ Missing keys: {missing_keys}")
                return False
            
            print(f"   ✅ Created user: {response.get('email')}")
            self.created_user_id = response.get('id')
        
        return success

    def test_admin_update_user(self):
        """Test PUT /api/admin/users/{user_id}"""
        if not self.created_user_id:
            print("❌ Skipping - no created user available")
            return False
        
        data = {"is_admin": True}
        success, response = self.run_test(
            "Admin Update User Role", 
            "PUT", 
            f"admin/users/{self.created_user_id}", 
            200, 
            data=data, 
            use_auth=True
        )
        if success:
            if response.get('is_admin') != True:
                print(f"❌ Admin status not updated. Expected True, got: {response.get('is_admin')}")
                return False
            print(f"   ✅ Updated user to admin: {response.get('email')}")
        
        return success

    def test_admin_deactivate_user(self):
        """Test DELETE /api/admin/users/{user_id}"""
        if not self.created_user_id:
            print("❌ Skipping - no created user available")
            return False
        
        success, response = self.run_test(
            "Admin Deactivate User", 
            "DELETE", 
            f"admin/users/{self.created_user_id}", 
            200, 
            use_auth=True
        )
        if success:
            if 'message' not in response:
                print(f"❌ Missing message in response")
                return False
            print(f"   ✅ Deactivated user: {response.get('id')}")
        
        return success

    def test_non_admin_access_denied(self):
        """Test non-admin gets 403 for admin endpoints"""
        # Register a non-admin user
        timestamp = int(datetime.now().timestamp())
        test_email = f"nonadmin_{timestamp}@kurdynowski.pl"
        
        data = {
            "email": test_email,
            "password": "NonAdmin123!",
            "full_name": f"Non Admin User {timestamp}"
        }
        
        success, response = self.run_test("Register Non-Admin User", "POST", "auth/register", 200, data=data)
        if not success:
            return False
        
        non_admin_token = response.get('token')
        if not non_admin_token:
            print("❌ No token received")
            return False
        
        # Switch to non-admin token and try admin endpoint
        original_token = self.token
        self.token = non_admin_token
        
        success, response = self.run_test("Non-Admin Access Admin Endpoint", "GET", "admin/users", 403, use_auth=True)
        
        # Restore admin token
        self.token = original_token
        
        if success:
            print(f"   ✅ Non-admin correctly denied access")
        
        return success

    def test_image_generation_with_reference(self):
        """Test POST /api/images/generate with reference_image"""
        # Create minimal PNG (1x1 transparent pixel)
        png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==')
        png_base64 = base64.b64encode(png_data).decode('utf-8')
        
        data = {
            "prompt": "Test accounting illustration with reference",
            "style": "hero",
            "reference_image": {
                "data": png_base64,
                "mime_type": "image/png",
                "name": "test-ref.png"
            }
        }
        
        print(f"   ⚠️  This may take 15-30 seconds (calling AI image model)")
        success, response = self.run_test(
            "Image Generation with Reference", 
            "POST", 
            "images/generate", 
            200, 
            data=data,
            timeout=60,
            use_auth=True
        )
        
        if success:
            required_keys = ['id', 'prompt', 'style', 'mime_type', 'data']
            missing_keys = [k for k in required_keys if k not in response]
            if missing_keys:
                print(f"❌ Missing keys: {missing_keys}")
                return False
            
            print(f"   ✅ Generated image: {response.get('id')}")
            print(f"   Style: {response.get('style')}")
            print(f"   Data length: {len(response.get('data', ''))} chars")
        
        return success

    def test_image_generation_invalid_mime(self):
        """Test POST /api/images/generate rejects invalid MIME types"""
        data = {
            "prompt": "Test image",
            "style": "hero",
            "reference_image": {
                "data": "invalid_data",
                "mime_type": "application/pdf",  # Invalid
                "name": "test.pdf"
            }
        }
        
        success, response = self.run_test(
            "Image Generation Invalid MIME", 
            "POST", 
            "images/generate", 
            400,  # Should fail
            data=data,
            use_auth=True
        )
        
        if success:
            print(f"   ✅ Correctly rejected invalid MIME type")
        
        return success

def main():
    print("🚀 Testing Admin User Management & Image Generator Features")
    print("=" * 60)
    
    tester = AdminFeaturesAPITester()
    
    # Admin login
    print("\n👑 Admin Authentication")
    admin_login_success = tester.test_admin_login()
    
    if admin_login_success:
        # Admin user management tests
        print("\n🔧 Admin User Management")
        tester.test_admin_list_users()
        tester.test_admin_create_user()
        tester.test_admin_update_user()
        tester.test_admin_deactivate_user()
        
        # Authorization tests
        print("\n🚫 Authorization Tests")
        tester.test_non_admin_access_denied()
        
        # Image generator tests
        print("\n🖼️  Image Generation with Reference")
        tester.test_image_generation_with_reference()
        tester.test_image_generation_invalid_mime()
    
    # Results
    print("\n" + "=" * 60)
    print(f"📊 Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())