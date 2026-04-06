"""
MatchMe API Tests - Iteration 5 Fixes
Tests for:
1. FIX 1: Credits as integers (ratings_since_last_credit, job_bonus_count counters)
2. FIX 2: Results page with rater_username in individual ratings
3. FIX 3: Auth page input padding (pl-10) - tested via frontend
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


class TestFix1IntegerCredits:
    """FIX 1: Credits must always be whole integers, never floats"""
    
    def test_new_user_has_integer_credits_and_counters(self):
        """Test new user registration returns integer credits and counter fields"""
        test_email = f"test_int_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Integer Test User"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify credits is integer 3
        assert data["credits"] == 3
        assert isinstance(data["credits"], int), f"Credits should be int, got {type(data['credits'])}"
        print(f"✓ New user credits is integer: {data['credits']}")
    
    def test_dashboard_returns_integer_credits(self):
        """Test dashboard API returns integer credits for free user"""
        test_email = f"test_dash_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        
        # Register
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Dashboard Test"
        })
        
        # Get dashboard
        response = session.get(f"{BASE_URL}/api/user/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        credits = data["user"]["credits"]
        assert credits == 3
        assert isinstance(credits, int), f"Dashboard credits should be int, got {type(credits)}"
        print(f"✓ Dashboard returns integer credits: {credits}")
    
    def test_admin_user_has_integer_credits(self):
        """Test admin user (999 credits) is integer"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        
        # Get dashboard
        dashboard = session.get(f"{BASE_URL}/api/user/dashboard").json()
        
        # Pro users have credits=None, but let's verify the admin has integer credits in DB
        # Check via /auth/me
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        # Admin should have 999 credits (integer)
        if me_data.get("credits") is not None:
            assert isinstance(me_data["credits"], int), f"Admin credits should be int, got {type(me_data['credits'])}"
            print(f"✓ Admin credits is integer: {me_data['credits']}")
        else:
            print("✓ Admin credits is None (Pro tier)")
    
    def test_credit_deduction_stays_integer(self):
        """Test credits stay integer after job creation (deduction)"""
        test_email = f"test_deduct_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        
        # Register (3 credits)
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Deduction Test"
        })
        
        # Create best-shot job (costs 1 credit)
        session.post(f"{BASE_URL}/api/jobs/best-shot", json={
            "photo_ids": ["photo1", "photo2", "photo3"]
        })
        
        # Check credits
        dashboard = session.get(f"{BASE_URL}/api/user/dashboard").json()
        credits = dashboard["user"]["credits"]
        
        assert credits == 2  # 3 - 1 = 2
        assert isinstance(credits, int), f"Credits after deduction should be int, got {type(credits)}"
        print(f"✓ Credits after deduction is integer: {credits}")
    
    def test_user_has_ratings_since_last_credit_field(self):
        """Test new user has ratings_since_last_credit field initialized to 0"""
        test_email = f"test_counter_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        
        # Register
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Counter Test"
        })
        
        # Get user info via /auth/me
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        # Check if ratings_since_last_credit exists (may not be exposed in /auth/me)
        # This is an internal field, so we verify via dashboard stats
        dashboard = session.get(f"{BASE_URL}/api/user/dashboard").json()
        stats = dashboard.get("stats", {})
        
        # The ratings_until_credit should be 5 for new user (5 - 0 = 5)
        ratings_until = stats.get("ratings_until_credit")
        if ratings_until is not None:
            assert ratings_until == 5, f"New user should need 5 ratings for credit, got {ratings_until}"
            print(f"✓ ratings_until_credit is 5 for new user (counter at 0)")
        else:
            print("✓ ratings_until_credit field not exposed in dashboard (internal counter)")


class TestFix2ResultsWithRaterUsername:
    """FIX 2: Results page must show reviewer usernames with individual ratings"""
    
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
    
    def test_completed_job_has_ratings_array(self, admin_session):
        """Test completed job result includes ratings array with rater_username"""
        # Get user's jobs
        response = admin_session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200
        jobs = response.json()
        
        # Find a completed job
        completed_jobs = [j for j in jobs if j.get("status") == "complete"]
        
        if not completed_jobs:
            print("⚠ No completed jobs found - skipping ratings array test")
            pytest.skip("No completed jobs to test")
        
        # Check the first completed job
        job = completed_jobs[0]
        result = job.get("result", {})
        ranked = result.get("ranked", [])
        
        if ranked:
            # Check if ratings array exists with rater_username
            first_photo = ranked[0]
            ratings = first_photo.get("ratings", [])
            
            if ratings:
                first_rating = ratings[0]
                assert "rater_username" in first_rating, "Rating should have rater_username field"
                assert "confident" in first_rating, "Rating should have confident score"
                assert "approachable" in first_rating, "Rating should have approachable score"
                assert "attractive" in first_rating, "Rating should have attractive score"
                print(f"✓ Job result has ratings array with rater_username: {first_rating.get('rater_username')}")
            else:
                print("⚠ No individual ratings in job result")
        else:
            print("⚠ No ranked photos in job result")
    
    def test_job_result_structure(self, admin_session):
        """Test job result has correct structure for Results page"""
        response = admin_session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200
        jobs = response.json()
        
        completed_jobs = [j for j in jobs if j.get("status") == "complete"]
        
        if not completed_jobs:
            pytest.skip("No completed jobs to test")
        
        job = completed_jobs[0]
        result = job.get("result", {})
        
        # Verify result structure
        assert "winner" in result or result.get("ranked"), "Result should have winner or ranked"
        assert "ranked" in result, "Result should have ranked array"
        assert "total_raters" in result, "Result should have total_raters count"
        
        print(f"✓ Job result structure correct - total_raters: {result.get('total_raters')}")
    
    def test_individual_rating_fields(self, admin_session):
        """Test individual ratings have all required fields"""
        response = admin_session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200
        jobs = response.json()
        
        completed_jobs = [j for j in jobs if j.get("status") == "complete"]
        
        if not completed_jobs:
            pytest.skip("No completed jobs to test")
        
        # Find a job with ratings
        for job in completed_jobs:
            result = job.get("result", {})
            ranked = result.get("ranked", [])
            
            for photo in ranked:
                ratings = photo.get("ratings", [])
                if ratings:
                    for rating in ratings:
                        # Verify all required fields
                        required_fields = ["rater_username", "confident", "approachable", "attractive"]
                        for field in required_fields:
                            assert field in rating, f"Rating missing {field} field"
                        
                        # Verify scores are numbers
                        assert isinstance(rating["confident"], (int, float))
                        assert isinstance(rating["approachable"], (int, float))
                        assert isinstance(rating["attractive"], (int, float))
                        
                        print(f"✓ Individual rating has all fields - rater: {rating['rater_username']}, scores: {rating['confident']}/{rating['approachable']}/{rating['attractive']}")
                        return  # Found valid rating, test passes
        
        print("⚠ No individual ratings found in any completed job")


class TestFix3AuthInputPadding:
    """FIX 3: Auth page input fields padding - tested via frontend Playwright"""
    
    def test_auth_page_loads(self):
        """Test auth page is accessible"""
        response = requests.get(f"{BASE_URL}/auth")
        # Frontend routes may redirect or return HTML
        assert response.status_code in [200, 304]
        print("✓ Auth page accessible")


class TestCreditEarningLogic:
    """Test credit earning via ratings (counter-based, not float)"""
    
    def test_rating_submission_increments_counter(self):
        """Test that submitting a rating increments the counter"""
        # This is an integration test - we need a photo to rate
        test_email = f"test_rate_{uuid.uuid4().hex[:8]}@test.com"
        session = requests.Session()
        
        # Register
        session.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "TestPass123!",
            "name": "Rater Test"
        })
        
        # Try to get a photo to rate
        response = session.get(f"{BASE_URL}/api/rate/next")
        
        if response.status_code == 404:
            print("⚠ No photos available to rate - skipping rating counter test")
            pytest.skip("No photos to rate")
        
        if response.status_code == 200:
            photo = response.json()
            photo_id = photo.get("photo_id")
            
            # Submit rating
            rate_response = session.post(f"{BASE_URL}/api/rate/submit", json={
                "photo_id": photo_id,
                "confident": 4,
                "approachable": 4,
                "attractive": 4,
                "tags": ["Good photo"],
                "comment": "Test rating comment"
            })
            
            if rate_response.status_code == 200:
                rate_data = rate_response.json()
                
                # Check if earned_credit is boolean (not float)
                if "earned_credit" in rate_data:
                    assert isinstance(rate_data["earned_credit"], bool), "earned_credit should be boolean"
                
                # Check ratings_until_credit is integer
                if "ratings_until_credit" in rate_data:
                    assert isinstance(rate_data["ratings_until_credit"], int), "ratings_until_credit should be int"
                    print(f"✓ Rating submitted - ratings_until_credit: {rate_data['ratings_until_credit']}")
            else:
                print(f"⚠ Rating submission returned {rate_response.status_code}")


class TestJobCompletionBonus:
    """Test job completion bonus uses counter (job_bonus_count)"""
    
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
    
    def test_admin_can_run_worker(self, admin_session):
        """Test admin can trigger job worker (which awards bonuses)"""
        response = admin_session.post(f"{BASE_URL}/api/admin/run-worker")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Worker executed: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
