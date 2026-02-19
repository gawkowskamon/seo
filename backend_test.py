#!/usr/bin/env python3
"""
Backend API Tests for Accounting Blog AI App
Tests visual editor features, export functionality, and subscription system
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://blog-optimizer-kit.preview.emergentagent.com"
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"

class BackendTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.token = None
        self.user = None
        self.test_article_id = None
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            self.passed_tests.append(name)
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            self.failed_tests.append({"test": name, "details": details})
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, auth_required: bool = True) -> tuple:
        """Make HTTP request and return (success, response_data)"""
        url = f"{self.base_url}/api{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                return False, f"Unsupported method: {method}"
            
            if response.status_code == expected_status:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, f"Status {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def test_authentication(self):
        """Test admin user authentication"""
        print("\n🔐 Testing Authentication...")
        
        # Test login
        success, response = self.make_request(
            'POST', '/auth/login', 
            {'email': ADMIN_EMAIL, 'password': ADMIN_PASSWORD},
            auth_required=False
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user = response['user']
            self.log_test("Admin Login", True, f"User: {self.user.get('email')}")
            
            # Test get current user
            success, user_data = self.make_request('GET', '/auth/me')
            if success:
                self.log_test("Get Current User", True, f"Admin: {user_data.get('is_admin')}")
            else:
                self.log_test("Get Current User", False, str(user_data))
            return True
        else:
            self.log_test("Admin Login", False, str(response))
            return False
    
    def test_subscription_plans(self):
        """Test subscription plans endpoint"""
        print("\n💳 Testing Subscription Plans...")
        
        # Test get all plans
        success, plans_data = self.make_request('GET', '/subscription/plans', auth_required=False)
        
        if success and isinstance(plans_data, list):
            self.log_test("Get Subscription Plans", True, f"Found {len(plans_data)} plans")
            
            # Verify required plans exist
            plan_ids = [plan.get('id') for plan in plans_data]
            required_plans = ['monthly', 'semiannual', 'annual']
            
            for plan_id in required_plans:
                if plan_id in plan_ids:
                    plan = next(p for p in plans_data if p['id'] == plan_id)
                    self.log_test(f"Plan {plan_id} exists", True, 
                                f"Price: {plan.get('price_netto')} PLN")
                else:
                    self.log_test(f"Plan {plan_id} exists", False, "Plan missing")
            
            # Test specific plan requirements
            monthly_plan = next((p for p in plans_data if p['id'] == 'monthly'), None)
            if monthly_plan:
                if monthly_plan.get('price_netto') == 59.99:
                    self.log_test("Monthly plan price correct", True, "59.99 PLN")
                else:
                    self.log_test("Monthly plan price correct", False, 
                                f"Expected 59.99, got {monthly_plan.get('price_netto')}")
            
            semiannual_plan = next((p for p in plans_data if p['id'] == 'semiannual'), None)
            if semiannual_plan:
                if semiannual_plan.get('discount_pct') == 7:
                    self.log_test("Semiannual discount correct", True, "7%")
                else:
                    self.log_test("Semiannual discount correct", False, 
                                f"Expected 7%, got {semiannual_plan.get('discount_pct')}%")
            
            annual_plan = next((p for p in plans_data if p['id'] == 'annual'), None)
            if annual_plan:
                if annual_plan.get('discount_pct') == 15:
                    self.log_test("Annual discount correct", True, "15%")
                else:
                    self.log_test("Annual discount correct", False, 
                                f"Expected 15%, got {annual_plan.get('discount_pct')}%")
        else:
            self.log_test("Get Subscription Plans", False, str(plans_data))
    
    def test_subscription_status(self):
        """Test subscription status endpoint"""
        print("\n📊 Testing Subscription Status...")
        
        success, status_data = self.make_request('GET', '/subscription/status')
        
        if success:
            self.log_test("Get Subscription Status", True, 
                        f"Has subscription: {status_data.get('has_subscription')}")
        else:
            self.log_test("Get Subscription Status", False, str(status_data))
    
    def test_checkout_simulation(self):
        """Test subscription checkout (will fail due to no tpay config but should return proper error)"""
        print("\n🛒 Testing Subscription Checkout...")
        
        success, checkout_data = self.make_request(
            'POST', '/subscription/checkout',
            {'plan_id': 'monthly'},
            expected_status=503  # Should fail with service unavailable due to no tpay config
        )
        
        if success or 'tpay nie jest jeszcze skonfigurowany' in str(checkout_data):
            self.log_test("Checkout returns proper error", True, "tpay not configured message")
        else:
            self.log_test("Checkout returns proper error", False, str(checkout_data))
    
    def create_test_article(self):
        """Create a test article for export testing"""
        print("\n📝 Creating Test Article...")
        
        article_data = {
            "topic": "Test article for export",
            "primary_keyword": "test eksport",
            "secondary_keywords": ["html", "pdf"],
            "target_length": 500,
            "tone": "profesjonalny",
            "template": "standard"
        }
        
        success, response = self.make_request('POST', '/articles/generate', article_data)
        
        if success and 'id' in response:
            self.test_article_id = response['id']
            self.log_test("Create Test Article", True, f"ID: {self.test_article_id}")
            return True
        else:
            self.log_test("Create Test Article", False, str(response))
            return False
    
    def test_html_export(self):
        """Test HTML export functionality"""
        print("\n🌐 Testing HTML Export...")
        
        if not self.test_article_id:
            self.log_test("HTML Export", False, "No test article available")
            return
        
        success, response = self.make_request(
            'POST', f'/articles/{self.test_article_id}/export',
            {'format': 'html'}
        )
        
        if success and response.get('format') == 'html':
            html_content = response.get('content', '')
            
            # Check for Instrument Serif font
            if 'Instrument Serif' in html_content:
                self.log_test("HTML Export - Instrument Serif font", True)
            else:
                self.log_test("HTML Export - Instrument Serif font", False, "Font not found")
            
            # Check for Kurdynowski branding colors
            if '#04389E' in html_content:  # Navy blue
                self.log_test("HTML Export - Kurdynowski navy color", True)
            else:
                self.log_test("HTML Export - Kurdynowski navy color", False, "Color not found")
            
            if '#F28C28' in html_content or 'hsl(34, 90%' in html_content:  # Amber
                self.log_test("HTML Export - Kurdynowski amber color", True)
            else:
                self.log_test("HTML Export - Kurdynowski amber color", False, "Amber color not found")
            
            self.log_test("HTML Export", True, f"Content length: {len(html_content)}")
        else:
            self.log_test("HTML Export", False, str(response))
    
    def test_pdf_export(self):
        """Test PDF export functionality"""
        print("\n📄 Testing PDF Export...")
        
        if not self.test_article_id:
            self.log_test("PDF Export", False, "No test article available")
            return
        
        # PDF export returns binary data, so we need to handle it differently
        url = f"{self.base_url}/api/articles/{self.test_article_id}/export"
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        
        try:
            response = self.session.post(url, json={'format': 'pdf'}, headers=headers)
            
            if response.status_code == 200:
                if response.headers.get('content-type') == 'application/pdf':
                    pdf_size = len(response.content)
                    self.log_test("PDF Export", True, f"PDF size: {pdf_size} bytes")
                else:
                    self.log_test("PDF Export", False, f"Wrong content type: {response.headers.get('content-type')}")
            else:
                self.log_test("PDF Export", False, f"Status {response.status_code}: {response.text[:200]}")
        except Exception as e:
            self.log_test("PDF Export", False, str(e))
    
    def test_articles_crud(self):
        """Test basic article CRUD operations"""
        print("\n📚 Testing Articles CRUD...")
        
        # List articles
        success, articles = self.make_request('GET', '/articles')
        if success:
            self.log_test("List Articles", True, f"Found {len(articles)} articles")
        else:
            self.log_test("List Articles", False, str(articles))
        
        # Get specific article
        if self.test_article_id:
            success, article = self.make_request('GET', f'/articles/{self.test_article_id}')
            if success:
                self.log_test("Get Article", True, f"Title: {article.get('title', 'N/A')}")
            else:
                self.log_test("Get Article", False, str(article))
    
    def test_health_endpoints(self):
        """Test basic health and info endpoints"""
        print("\n🏥 Testing Health Endpoints...")
        
        # Test root API endpoint
        success, response = self.make_request('GET', '/', auth_required=False)
        if success:
            self.log_test("API Root", True, f"Status: {response.get('status')}")
        else:
            self.log_test("API Root", False, str(response))
        
        # Test health endpoint
        success, response = self.make_request('GET', '/health', auth_required=False)
        if success:
            self.log_test("Health Check", True, f"Status: {response.get('status')}")
        else:
            self.log_test("Health Check", False, str(response))
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        return len(self.failed_tests) == 0

def main():
    print(f"🚀 Starting Backend API Tests")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = BackendTester(BACKEND_URL)
    
    try:
        # Run authentication first
        if not tester.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return 1
        
        # Run all test suites
        tester.test_health_endpoints()
        tester.test_subscription_plans()
        tester.test_subscription_status()
        tester.test_checkout_simulation()
        
        tester.test_articles_crud()
        
        # Try to test exports with existing articles
        if tester.create_test_article():
            tester.test_html_export()
            tester.test_pdf_export()
        else:
            # Use existing article if available
            success, articles = tester.make_request('GET', '/articles')
            if success and articles and len(articles) > 0:
                tester.test_article_id = articles[0]['id']
                print(f"\n📝 Using existing article for export tests: {tester.test_article_id}")
                tester.test_html_export()
                tester.test_pdf_export()
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    
    # Print final summary
    success = tester.print_summary()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())