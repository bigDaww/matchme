"""
MatchMe API Tests - Comprehensive backend testing
Tests: Auth, Dashboard, Jobs, Ratings, Stripe, Admin Worker
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@matchme.com"
ADMIN_PASSWORD = "AdminMatch2024!"

class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_api_root(self):
        """Test /api/ returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "MatchMe API"
        print("✓ API root endpoint working")
    
    def test_api_health(self):
        """Test /api/health returns ok"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        print("✓ Health endpoint working")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    def test_register_new_user(self):
        """Test user registration with correct response fields"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response fields
        assert "user_id" in data
        assert data["email"] == test_email.lower()
        assert data["name"] == "Test User"
        assert data["credits"] == 3  # Free tier signup credits
        assert data["tier"] == "free"
        assert data["onboarding_completed"] == False
        print(f"✓ User registration working - {test_email}")
    
    def test_register_duplicate_email(self):
        """Test duplicate email registration fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": "TestPass123!",
            "name": "Duplicate User"
        })
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✓ Duplicate email registration blocked")
    
    def test_login_admin_success(self):
        """Test admin login with correct credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response fields
        assert data["email"] == ADMIN_EMAIL
        assert data["tier"] == "pro"
        assert data.get("role") == "admin"
        assert "password_hash" not in data  # Should not expose password
        print("✓ Admin login successful")
        return session
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401
        assert "invalid" in response.json().get("detail", "").lower()
        print("✓ Invalid credentials rejected")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without authentication"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthenticated /auth/me blocked")


class TestDashboardAPI:
    """Dashboard endpoint tests"""
    
    @pytest.fixture
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_dashboard_returns_correct_fields(self, admin_session):
        """Test dashboard API returns correct tier info, credits, stats"""
        response = admin_session.get(f"{BASE_URL}/api/user/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify user info
        assert "user" in data
        user = data["user"]
        assert user["tier"] == "pro"
        assert user["credits"] is None  # Pro users have no credit system
        
        # Verify stats
        assert "stats" in data
        stats = data["stats"]
        assert stats["is_pro"] == True
        assert stats["credits_earned_today"] is None  # Pro users don't earn credits
        
        # Verify tier_info
        assert "tier_info" in data
        tier_info = data["tier_info"]
        assert tier_info["min_ratings"] == 10  # Pro tier
        assert tier_info["time_cap_hours"] == 4  # Pro tier
        assert tier_info["unlimited"] == True
        
        print("✓ Dashboard API returns correct Pro tier info")
    
    def test_dashboard_free_user(self):
        """Test dashboard for free tier user"""
        # Create a new free user
        test_email = f"test_free_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        
        # Register
        reg_response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Free User"
        })
        assert reg_response.status_code == 200
        
        # Get dashboard
        response = session.get(f"{BASE_URL}/api/user/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify free tier info
        user = data["user"]
        assert user["tier"] == "free"
        assert user["credits"] == 3  # Signup credits
        
        stats = data["stats"]
        assert stats["is_pro"] == False
        assert stats["ratings_for_credit"] == 5  # 5 ratings = 1 credit
        
        tier_info = data["tier_info"]
        assert tier_info["min_ratings"] == 3  # Free tier
        assert tier_info["time_cap_hours"] == 24  # Free tier
        
        print("✓ Dashboard API returns correct Free tier info")


class TestJobCreation:
    """Job creation endpoint tests"""
    
    @pytest.fixture
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    @pytest.fixture
    def free_user_session(self):
        """Create and login as free user"""
        test_email = f"test_job_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Job Test User"
        })
        return session
    
    def test_best_shot_requires_3_to_10_photos(self, admin_session):
        """Test best-shot requires 3-10 photos"""
        # Test with 2 photos (too few)
        response = admin_session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": ["photo1", "photo2"]
        })
        assert response.status_code == 400
        assert "3-10" in response.json().get("detail", "")
        
        # Test with 11 photos (too many)
        response = admin_session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": [f"photo{i}" for i in range(11)]
        })
        assert response.status_code == 400
        assert "3-10" in response.json().get("detail", "")
        
        print("✓ Best-shot photo count validation working")
    
    def test_best_shot_pro_user_no_credit_check(self, admin_session):
        """Test Pro users can create best-shot without credit check"""
        response = admin_session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": ["photo1", "photo2", "photo3"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert data["tier"] == "pro"
        print("✓ Pro user best-shot job created without credit check")
    
    def test_profile_analysis_requires_4_to_6_photos(self, admin_session):
        """Test profile-analysis requires 4-6 photos"""
        # Test with 3 photos (too few)
        response = admin_session.post(f"{BASE_URL}/api/jobs/profile-analysis", json={
            "photo_ids": ["photo1", "photo2", "photo3"]
        })
        assert response.status_code == 400
        assert "4-6" in response.json().get("detail", "")
        
        # Test with 7 photos (too many)
        response = admin_session.post(f"{BASE_URL}/api/jobs/profile-analysis", json={
            "photo_ids": [f"photo{i}" for i in range(7)]
        })
        assert response.status_code == 400
        assert "4-6" in response.json().get("detail", "")
        
        print("✓ Profile-analysis photo count validation working")
    
    def test_profile_analysis_pro_user(self, admin_session):
        """Test Pro users can create profile-analysis"""
        response = admin_session.post(f"{BASE_URL}/api/jobs/profile-analysis", json={
            "photo_ids": ["photo1", "photo2", "photo3", "photo4"],
            "bio": "Test bio",
            "prompt_answer": "Test prompt"
        })
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        print("✓ Pro user profile-analysis job created")
    
    def test_free_user_credit_deduction(self, free_user_session):
        """Test free user credits are deducted for job creation"""
        # Get initial credits
        dashboard = free_user_session.get(f"{BASE_URL}/api/user/dashboard").json()
        initial_credits = dashboard["user"]["credits"]
        assert initial_credits == 3  # Signup credits
        
        # Create best-shot job (costs 1 credit)
        response = free_user_session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": ["photo1", "photo2", "photo3"]
        })
        assert response.status_code == 200
        
        # Verify credit deduction
        dashboard = free_user_session.get(f"{BASE_URL}/api/user/dashboard").json()
        assert dashboard["user"]["credits"] == initial_credits - 1
        print("✓ Free user credit deduction working (1 credit for best-shot)")
    
    def test_insufficient_credits_blocked(self):
        """Test job creation blocked when insufficient credits"""
        # Create user with 0 credits
        test_email = f"test_nocredit_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "No Credit User"
        })
        
        # Use all 3 credits (3 best-shot jobs)
        for i in range(3):
            session.post(f"{BASE_URL}/api/jobs/best-shot", json={
                "photo_ids": ["photo1", "photo2", "photo3"]
            })
        
        # Try to create another job
        response = session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": ["photo1", "photo2", "photo3"]
        })
        assert response.status_code == 400
        assert "credit" in response.json().get("detail", "").lower()
        print("✓ Insufficient credits blocked")


class TestRatingSystem:
    """Rating submission endpoint tests"""
    
    @pytest.fixture
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_rate_next_endpoint(self, admin_session):
        """Test /rate/next endpoint"""
        response = admin_session.get(f"{BASE_URL}/api/rate/next")
        # May return 404 if no photos to rate, which is valid
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "photo_id" in data
            assert "url" in data
            assert "is_pro" in data
            print("✓ Rate next endpoint returns photo data")
        else:
            print("✓ Rate next endpoint returns 404 when no photos available")
    
    def test_rating_submit_requires_comment(self, admin_session):
        """Test rating submission requires comment"""
        response = admin_session.post(f"{BASE_URL}/api/rate/submit", json={
            "photo_id": "nonexistent_photo",
            "confident": 4,
            "approachable": 4,
            "attractive": 4,
            "tags": ["Good smile"],
            "comment": ""  # Empty comment
        })
        # Should fail validation or photo not found
        assert response.status_code in [400, 422]
        print("✓ Rating submission validation working")


class TestStripeEndpoints:
    """Stripe subscription endpoint tests"""
    
    @pytest.fixture
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_subscribe_endpoint_creates_checkout(self, admin_session):
        """Test /payments/subscribe creates Stripe checkout session"""
        response = admin_session.post(f"{BASE_URL}/api/payments/subscribe", json={
            "package_id": "priority",
            "origin_url": "https://matchme-preview.preview.emergentagent.com"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert "session_id" in data
        assert "checkout.stripe.com" in data["url"]
        print("✓ Stripe checkout session created for Priority plan")
    
    def test_subscribe_invalid_package(self, admin_session):
        """Test subscribe with invalid package fails"""
        response = admin_session.post(f"{BASE_URL}/api/payments/subscribe", json={
            "package_id": "invalid_package",
            "origin_url": "https://matchme-preview.preview.emergentagent.com"
        })
        assert response.status_code == 400
        assert "invalid" in response.json().get("detail", "").lower()
        print("✓ Invalid package rejected")
    
    def test_webhook_endpoint_exists(self):
        """Test Stripe webhook endpoint exists"""
        # Send empty payload to verify endpoint exists
        response = requests.post(f"{BASE_URL}/api/webhook/stripe", 
                                 data="{}",
                                 headers={"Content-Type": "application/json"})
        # Should return 400 for invalid payload, not 404
        assert response.status_code in [400, 422]
        print("✓ Stripe webhook endpoint exists")


class TestAdminWorker:
    """Admin worker endpoint tests"""
    
    @pytest.fixture
    def admin_session(self):
        """Get authenticated admin session"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return session
    
    def test_run_worker_admin_only(self):
        """Test run-worker requires admin role"""
        # Create non-admin user
        test_email = f"test_nonadmin_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Non Admin"
        })
        
        response = session.post(f"{BASE_URL}/api/admin/run-worker")
        assert response.status_code == 403
        assert "admin" in response.json().get("detail", "").lower()
        print("✓ Run-worker blocked for non-admin users")
    
    def test_run_worker_success(self, admin_session):
        """Test admin can trigger job worker"""
        response = admin_session.post(f"{BASE_URL}/api/admin/run-worker")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "executed" in data["message"].lower()
        print("✓ Admin can trigger job worker")


class TestTierConfiguration:
    """Test tier configuration is correct"""
    
    def test_tier_config_values(self):
        """Verify tier configuration matches requirements"""
        # These values should match TIER_CONFIG in server.py
        expected_config = {
            "free": {
                "min_ratings": 3,
                "time_cap_hours": 24,
                "signup_credits": 3,
                "ratings_for_credit": 5
            },
            "priority": {
                "min_ratings": 7,
                "time_cap_hours": 4,
                "credits_per_month": 12,
                "price_monthly": 9.00
            },
            "pro": {
                "min_ratings": 10,
                "time_cap_hours": 4,
                "price_monthly": 25.00,
                "unlimited": True
            }
        }
        
        # Test by creating users and checking dashboard
        session = requests.Session()
        test_email = f"test_tier_{uuid.uuid4().hex[:8]}@test.com"
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Tier Test"
        })
        
        dashboard = session.get(f"{BASE_URL}/api/user/dashboard").json()
        tier_info = dashboard["tier_info"]
        
        # Verify free tier config
        assert tier_info["min_ratings"] == expected_config["free"]["min_ratings"]
        assert tier_info["time_cap_hours"] == expected_config["free"]["time_cap_hours"]
        
        print("✓ Tier configuration matches requirements")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
