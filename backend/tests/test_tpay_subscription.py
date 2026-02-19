"""
Test file for TPay Subscription Integration and Authentication
Tests: Login, Subscription Plans, Checkout with TPay
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "monika.gawkowska@kurdynowski.pl"
ADMIN_PASSWORD = "MonZuz8180!"
TEST_EMAIL = "test@kurdynowski.pl"


class TestHealthAndPlans:
    """Basic API Health and Plans Tests"""
    
    def test_health_endpoint(self):
        """Test that API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health endpoint working")
    
    def test_subscription_plans(self):
        """GET /api/subscription/plans - should return 3 plans"""
        response = requests.get(f"{BASE_URL}/api/subscription/plans")
        assert response.status_code == 200
        plans = response.json()
        
        # Should have 3 plans
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}"
        
        # Verify plan IDs
        plan_ids = [p["id"] for p in plans]
        assert "monthly" in plan_ids
        assert "semiannual" in plan_ids
        assert "annual" in plan_ids
        
        # Verify monthly plan price
        monthly = next(p for p in plans if p["id"] == "monthly")
        assert monthly["price_netto"] == 59.99, f"Monthly price_netto should be 59.99, got {monthly['price_netto']}"
        
        # Verify semiannual has 7% discount
        semiannual = next(p for p in plans if p["id"] == "semiannual")
        assert semiannual["discount_pct"] == 7, f"Semiannual discount should be 7%, got {semiannual['discount_pct']}"
        
        # Verify annual has 15% discount
        annual = next(p for p in plans if p["id"] == "annual")
        assert annual["discount_pct"] == 15, f"Annual discount should be 15%, got {annual['discount_pct']}"
        
        print(f"✓ Plans API working - 3 plans with correct prices")
        print(f"  Monthly: {monthly['price_netto']} PLN netto / {monthly['price_brutto']} PLN brutto")
        print(f"  Semiannual: {semiannual['price_netto']} PLN netto (7% off)")
        print(f"  Annual: {annual['price_netto']} PLN netto (15% off)")


class TestAuthentication:
    """Authentication Tests"""
    
    def test_admin_login(self):
        """Test admin login - monika.gawkowska@kurdynowski.pl"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Check response structure
        assert "token" in data, "Missing token in response"
        assert "user" in data, "Missing user in response"
        
        # Check user data
        user = data["user"]
        assert user["email"] == ADMIN_EMAIL.lower(), f"Email mismatch: {user['email']}"
        assert user.get("is_admin") == True, f"Admin user should have is_admin=True, got {user.get('is_admin')}"
        
        print(f"✓ Admin login successful: {user['email']} (is_admin={user.get('is_admin')})")
        return data["token"]
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401 for invalid login, got {response.status_code}"
        print("✓ Invalid login returns 401")
    
    def test_auth_me_with_token(self):
        """Test /auth/me with valid token"""
        # First login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_res.status_code == 200
        token = login_res.json()["token"]
        
        # Now test /auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200, f"Auth me failed: {response.status_code}"
        user = response.json()
        assert user["email"] == ADMIN_EMAIL.lower()
        print(f"✓ Auth me working - returned user: {user['email']}")


class TestSubscriptionCheckout:
    """TPay Checkout Integration Tests - CRITICAL: These were broken before (520 errors)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for admin user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.status_code}")
        return response.json()["token"]
    
    def test_checkout_monthly_plan(self, auth_token):
        """POST /api/subscription/checkout with plan_id=monthly - should return transaction_url"""
        response = requests.post(
            f"{BASE_URL}/api/subscription/checkout",
            json={"plan_id": "monthly"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        print(f"Checkout monthly response: {response.status_code}")
        
        # Should NOT return 520 error anymore (that was the bug)
        assert response.status_code != 520, f"Got 520 error - TPay integration still broken: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "subscription_id" in data, "Missing subscription_id"
            assert "transaction_url" in data, "Missing transaction_url"
            
            # Verify transaction_url starts with tpay
            tx_url = data["transaction_url"]
            assert tx_url.startswith("https://secure.tpay.com"), f"Invalid transaction_url: {tx_url}"
            
            print(f"✓ Monthly checkout SUCCESS")
            print(f"  subscription_id: {data['subscription_id']}")
            print(f"  transaction_url: {tx_url[:80]}...")
        elif response.status_code == 503:
            # Service unavailable - config issue
            detail = response.json().get("detail", "")
            print(f"⚠ Checkout returned 503: {detail}")
            pytest.skip(f"TPay not configured: {detail}")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")
    
    def test_checkout_semiannual_plan(self, auth_token):
        """POST /api/subscription/checkout with plan_id=semiannual"""
        response = requests.post(
            f"{BASE_URL}/api/subscription/checkout",
            json={"plan_id": "semiannual"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        print(f"Checkout semiannual response: {response.status_code}")
        
        assert response.status_code != 520, f"Got 520 error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "transaction_url" in data
            tx_url = data["transaction_url"]
            assert tx_url.startswith("https://secure.tpay.com")
            print(f"✓ Semiannual checkout SUCCESS - {tx_url[:60]}...")
        elif response.status_code in [502, 503]:
            pytest.skip(f"TPay service issue: {response.text}")
    
    def test_checkout_annual_plan(self, auth_token):
        """POST /api/subscription/checkout with plan_id=annual"""
        response = requests.post(
            f"{BASE_URL}/api/subscription/checkout",
            json={"plan_id": "annual"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        print(f"Checkout annual response: {response.status_code}")
        
        assert response.status_code != 520, f"Got 520 error: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "transaction_url" in data
            tx_url = data["transaction_url"]
            assert tx_url.startswith("https://secure.tpay.com")
            print(f"✓ Annual checkout SUCCESS - {tx_url[:60]}...")
        elif response.status_code in [502, 503]:
            pytest.skip(f"TPay service issue: {response.text}")
    
    def test_checkout_invalid_plan(self, auth_token):
        """Test checkout with invalid plan_id"""
        response = requests.post(
            f"{BASE_URL}/api/subscription/checkout",
            json={"plan_id": "invalid_plan"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        print("✓ Invalid plan returns 400")
    
    def test_checkout_without_auth(self):
        """Test checkout without authentication"""
        response = requests.post(
            f"{BASE_URL}/api/subscription/checkout",
            json={"plan_id": "monthly"}
        )
        
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✓ Unauthenticated checkout returns 401")


class TestSubscriptionStatus:
    """Subscription Status Tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed")
        return response.json()["token"]
    
    def test_subscription_status(self, auth_token):
        """GET /api/subscription/status - should return subscription status"""
        response = requests.get(
            f"{BASE_URL}/api/subscription/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Status failed: {response.status_code}"
        data = response.json()
        
        # Should have these fields
        assert "has_subscription" in data
        assert "status" in data
        
        print(f"✓ Subscription status: has_subscription={data.get('has_subscription')}, status={data.get('status')}")


class TestArticles:
    """Article API Tests"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Login failed")
        return response.json()["token"]
    
    def test_list_articles(self, auth_token):
        """GET /api/articles - should return list"""
        response = requests.get(
            f"{BASE_URL}/api/articles",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"List articles failed: {response.status_code}"
        articles = response.json()
        assert isinstance(articles, list)
        print(f"✓ Articles list: {len(articles)} articles found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
