#!/usr/bin/env python3

import requests
import json
import sys

# Use local backend URL that's working
BASE_URL = "http://127.0.0.1:8001"

def test_admin_login():
    """Test admin login with Monika credentials"""
    print("🔍 Testing admin login...")
    
    data = {
        "email": "monika.gawkowska@kurdynowski.pl",
        "password": "MonZuz8180!"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            user = result.get('user', {})
            is_admin = user.get('is_admin', False)
            
            print(f"✅ Login successful")
            print(f"✅ Email: {user.get('email')}")
            print(f"✅ is_admin: {is_admin}")
            
            if is_admin:
                print("✅ Admin status confirmed")
                return True, result.get('token')
            else:
                print("❌ Admin status not found")
                return False, None
        else:
            print(f"❌ Login failed: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False, None

def test_image_styles():
    """Test GET /api/image-styles returns 8 styles"""
    print("\n🔍 Testing image styles...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/image-styles", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            styles = response.json()
            print(f"✅ Found {len(styles)} image styles")
            
            if len(styles) == 8:
                print("✅ Correct number of styles (8)")
                style_names = [s.get('name', 'Unknown') for s in styles[:3]]
                print(f"✅ Sample styles: {', '.join(style_names)}...")
                return True
            else:
                print(f"❌ Expected 8 styles, got {len(styles)}")
                return False
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_templates():
    """Test GET /api/templates returns 8 templates"""
    print("\n🔍 Testing templates...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/templates", timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            templates = response.json()
            print(f"✅ Found {len(templates)} templates")
            
            if len(templates) == 8:
                print("✅ Correct number of templates (8)")
                template_names = [t.get('name', 'Unknown') for t in templates[:3]]
                print(f"✅ Sample templates: {', '.join(template_names)}...")
                return True
            else:
                print(f"❌ Expected 8 templates, got {len(templates)}")
                return False
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_series_generation(token):
    """Test POST /api/series/generate"""
    print("\n🔍 Testing series generation...")
    
    if not token:
        print("❌ No token available")
        return False
    
    data = {
        "topic": "Test series for CIT accounting",
        "primary_keyword": "rozliczenie CIT",
        "num_parts": 3,
        "source_text": "Basic source context"
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print("⏳ Generating series (may take 15-30 seconds)...")
        response = requests.post(f"{BASE_URL}/api/series/generate", json=data, headers=headers, timeout=60)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            parts = result.get('parts', [])
            print(f"✅ Series generated: {result.get('series_title', 'N/A')}")
            print(f"✅ Parts count: {len(parts)}")
            
            if len(parts) == 3:
                print("✅ Correct number of parts")
                return True
            else:
                print(f"❌ Expected 3 parts, got {len(parts)}")
                return False
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_user_scoped_endpoints(token):
    """Test user-scoped endpoints (articles, series, stats)"""
    print("\n🔍 Testing user-scoped endpoints...")
    
    if not token:
        print("❌ No token available")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    passed = 0
    total = 3
    
    # Test articles
    try:
        response = requests.get(f"{BASE_URL}/api/articles", headers=headers, timeout=10)
        if response.status_code == 200:
            articles = response.json()
            print(f"✅ Articles endpoint: {len(articles)} articles")
            passed += 1
        else:
            print(f"❌ Articles failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Articles error: {e}")
    
    # Test series
    try:
        response = requests.get(f"{BASE_URL}/api/series", headers=headers, timeout=10)
        if response.status_code == 200:
            series = response.json()
            print(f"✅ Series endpoint: {len(series)} series")
            passed += 1
        else:
            print(f"❌ Series failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Series error: {e}")
    
    # Test stats
    try:
        response = requests.get(f"{BASE_URL}/api/stats", headers=headers, timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats endpoint: {stats}")
            passed += 1
        else:
            print(f"❌ Stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats error: {e}")
    
    return passed == total

def main():
    print("🚀 SEO Article Builder - Focused Backend Tests")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 6
    token = None
    
    # Test admin login
    success, token = test_admin_login()
    if success:
        tests_passed += 1
    
    # Test image styles
    if test_image_styles():
        tests_passed += 1
    
    # Test templates
    if test_templates():
        tests_passed += 1
    
    # Test series generation (requires auth)
    if test_series_generation(token):
        tests_passed += 1
    
    # Test user-scoped endpoints (requires auth)
    if test_user_scoped_endpoints(token):
        tests_passed += 2  # This tests 3 endpoints but counts as 2 tests
    
    print(f"\n📊 Results: {tests_passed}/{tests_total} tests passed")
    
    if tests_passed == tests_total:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())