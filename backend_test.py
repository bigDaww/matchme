#!/usr/bin/env python3

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class MatchMeAPITester:
    def __init__(self, base_url="https://matchme-preview.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test user credentials
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPass123!"
        self.test_name = "Test User"
        
        # Admin credentials
        self.admin_email = "admin@matchme.com"
        self.admin_password = "AdminMatch2024!"

    def log_test(self, name, success, details="", endpoint=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "endpoint": endpoint
        })

    def test_health_check(self):
        """Test basic health endpoints"""
        try:
            # Test root endpoint
            response = self.session.get(f"{self.api_url}/")
            success = response.status_code == 200
            data = response.json() if success else {}
            
            self.log_test(
                "API Root Health Check", 
                success and data.get("status") == "healthy",
                f"Status: {response.status_code}, Response: {data}",
                "GET /api/"
            )
            
            # Test health endpoint
            response = self.session.get(f"{self.api_url}/health")
            success = response.status_code == 200
            data = response.json() if success else {}
            
            self.log_test(
                "API Health Endpoint", 
                success and data.get("status") == "ok",
                f"Status: {response.status_code}, Response: {data}",
                "GET /api/health"
            )
            
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")

    def test_user_registration(self):
        """Test user registration"""
        try:
            data = {
                "email": self.test_email,
                "password": self.test_password,
                "name": self.test_name
            }
            
            response = self.session.post(f"{self.api_url}/auth/register", json=data)
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                expected_fields = ["user_id", "email", "name", "credits", "tier", "onboarding_completed"]
                has_fields = all(field in user_data for field in expected_fields)
                has_3_credits = user_data.get("credits") == 3
                
                self.log_test(
                    "User Registration",
                    has_fields and has_3_credits,
                    f"Status: {response.status_code}, Credits: {user_data.get('credits')}, Fields: {list(user_data.keys())}",
                    "POST /api/auth/register"
                )
                return user_data
            else:
                self.log_test(
                    "User Registration", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "POST /api/auth/register"
                )
                return None
                
        except Exception as e:
            self.log_test("User Registration", False, f"Exception: {str(e)}")
            return None

    def test_user_login(self):
        """Test user login"""
        try:
            data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.session.post(f"{self.api_url}/auth/login", json=data)
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                # Check if cookies are set
                has_cookies = 'access_token' in response.cookies or 'refresh_token' in response.cookies
                
                self.log_test(
                    "User Login",
                    success and "user_id" in user_data,
                    f"Status: {response.status_code}, Has cookies: {has_cookies}, User ID: {user_data.get('user_id')}",
                    "POST /api/auth/login"
                )
                return user_data
            else:
                self.log_test(
                    "User Login", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "POST /api/auth/login"
                )
                return None
                
        except Exception as e:
            self.log_test("User Login", False, f"Exception: {str(e)}")
            return None

    def test_admin_login(self):
        """Test admin login"""
        try:
            data = {
                "email": self.admin_email,
                "password": self.admin_password
            }
            
            response = self.session.post(f"{self.api_url}/auth/login", json=data)
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                is_admin = user_data.get("tier") == "pro" and user_data.get("credits", 0) >= 999
                
                self.log_test(
                    "Admin Login",
                    success and is_admin,
                    f"Status: {response.status_code}, Tier: {user_data.get('tier')}, Credits: {user_data.get('credits')}",
                    "POST /api/auth/login (admin)"
                )
                return user_data
            else:
                self.log_test(
                    "Admin Login", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "POST /api/auth/login (admin)"
                )
                return None
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return None

    def test_auth_me(self):
        """Test /auth/me endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/auth/me")
            success = response.status_code == 200
            
            if success:
                user_data = response.json()
                self.log_test(
                    "Auth Me Endpoint",
                    "user_id" in user_data and "email" in user_data,
                    f"Status: {response.status_code}, User: {user_data.get('email')}",
                    "GET /api/auth/me"
                )
                return user_data
            else:
                self.log_test(
                    "Auth Me Endpoint", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "GET /api/auth/me"
                )
                return None
                
        except Exception as e:
            self.log_test("Auth Me Endpoint", False, f"Exception: {str(e)}")
            return None

    def test_onboarding(self):
        """Test onboarding completion"""
        try:
            data = {
                "gender": "woman",
                "orientation": "men",
                "dating_app": "hinge"
            }
            
            response = self.session.post(f"{self.api_url}/user/onboarding", json=data)
            success = response.status_code == 200
            
            self.log_test(
                "Onboarding Completion",
                success,
                f"Status: {response.status_code}, Response: {response.json() if success else response.text}",
                "POST /api/user/onboarding"
            )
            
        except Exception as e:
            self.log_test("Onboarding Completion", False, f"Exception: {str(e)}")

    def test_dashboard(self):
        """Test dashboard endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/user/dashboard")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_user = "user" in data
                has_stats = "stats" in data
                has_jobs = "recent_jobs" in data
                
                self.log_test(
                    "Dashboard Endpoint",
                    has_user and has_stats and has_jobs,
                    f"Status: {response.status_code}, Keys: {list(data.keys())}",
                    "GET /api/user/dashboard"
                )
                return data
            else:
                self.log_test(
                    "Dashboard Endpoint", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "GET /api/user/dashboard"
                )
                return None
                
        except Exception as e:
            self.log_test("Dashboard Endpoint", False, f"Exception: {str(e)}")
            return None

    def test_file_upload(self):
        """Test file upload functionality"""
        try:
            # Create a small test image (1x1 pixel PNG)
            test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
            
            # Use requests directly without session to avoid header conflicts
            cookies = self.session.cookies
            files = {'file': ('test.png', test_image_data, 'image/png')}
            
            response = requests.post(
                f"{self.api_url}/upload", 
                files=files,
                cookies=cookies
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_photo_id = "photo_id" in data
                has_storage_path = "storage_path" in data
                
                self.log_test(
                    "File Upload",
                    has_photo_id and has_storage_path,
                    f"Status: {response.status_code}, Photo ID: {data.get('photo_id')}",
                    "POST /api/upload"
                )
                return data.get("photo_id")
            else:
                self.log_test(
                    "File Upload", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "POST /api/upload"
                )
                return None
                
        except Exception as e:
            self.log_test("File Upload", False, f"Exception: {str(e)}")
            return None

    def test_best_shot_job(self, photo_ids):
        """Test best shot job creation"""
        if not photo_ids or len(photo_ids) < 3:
            self.log_test("Best Shot Job", False, "Need at least 3 photos")
            return None
            
        try:
            data = {
                "photo_ids": photo_ids[:3]  # Use first 3 photos
            }
            
            response = self.session.post(f"{self.api_url}/jobs/best-shot", json=data)
            success = response.status_code == 200
            
            if success:
                job_data = response.json()
                has_job_id = "job_id" in job_data
                has_status = job_data.get("status") == "queued"
                
                self.log_test(
                    "Best Shot Job Creation",
                    has_job_id and has_status,
                    f"Status: {response.status_code}, Job ID: {job_data.get('job_id')}",
                    "POST /api/jobs/best-shot"
                )
                return job_data.get("job_id")
            else:
                self.log_test(
                    "Best Shot Job Creation", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "POST /api/jobs/best-shot"
                )
                return None
                
        except Exception as e:
            self.log_test("Best Shot Job Creation", False, f"Exception: {str(e)}")
            return None

    def test_get_jobs(self):
        """Test getting user jobs"""
        try:
            response = self.session.get(f"{self.api_url}/jobs")
            success = response.status_code == 200
            
            if success:
                jobs = response.json()
                is_list = isinstance(jobs, list)
                
                self.log_test(
                    "Get User Jobs",
                    is_list,
                    f"Status: {response.status_code}, Jobs count: {len(jobs) if is_list else 'Not a list'}",
                    "GET /api/jobs"
                )
                return jobs
            else:
                self.log_test(
                    "Get User Jobs", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "GET /api/jobs"
                )
                return None
                
        except Exception as e:
            self.log_test("Get User Jobs", False, f"Exception: {str(e)}")
            return None

    def test_rate_next_photo(self):
        """Test getting next photo to rate"""
        try:
            response = self.session.get(f"{self.api_url}/rate/next")
            
            # This might return 404 if no photos to rate, which is acceptable
            if response.status_code == 200:
                data = response.json()
                has_photo_id = "photo_id" in data
                
                self.log_test(
                    "Get Next Photo to Rate",
                    has_photo_id,
                    f"Status: {response.status_code}, Photo ID: {data.get('photo_id')}",
                    "GET /api/rate/next"
                )
                return data
            elif response.status_code == 404:
                self.log_test(
                    "Get Next Photo to Rate",
                    True,  # 404 is acceptable - no photos to rate
                    f"Status: {response.status_code}, No photos available to rate",
                    "GET /api/rate/next"
                )
                return None
            else:
                self.log_test(
                    "Get Next Photo to Rate", 
                    False, 
                    f"Status: {response.status_code}, Response: {response.text}",
                    "GET /api/rate/next"
                )
                return None
                
        except Exception as e:
            self.log_test("Get Next Photo to Rate", False, f"Exception: {str(e)}")
            return None

    def test_logout(self):
        """Test user logout"""
        try:
            response = self.session.post(f"{self.api_url}/auth/logout", json={})
            success = response.status_code == 200
            
            self.log_test(
                "User Logout",
                success,
                f"Status: {response.status_code}, Response: {response.json() if success else response.text}",
                "POST /api/auth/logout"
            )
            
        except Exception as e:
            self.log_test("User Logout", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🚀 Starting MatchMe API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 50)
        
        # 1. Health checks
        self.test_health_check()
        
        # 2. User registration and auth flow
        user_data = self.test_user_registration()
        if user_data:
            # Login with the registered user
            login_data = self.test_user_login()
            if login_data:
                # Test authenticated endpoints
                self.test_auth_me()
                self.test_onboarding()
                self.test_dashboard()
                
                # Test file upload (upload multiple photos for job testing)
                photo_ids = []
                for i in range(3):
                    photo_id = self.test_file_upload()
                    if photo_id:
                        photo_ids.append(photo_id)
                
                # Test job creation
                if photo_ids:
                    job_id = self.test_best_shot_job(photo_ids)
                    
                # Test jobs listing
                self.test_get_jobs()
                
                # Test rating system
                self.test_rate_next_photo()
                
                # Test logout
                self.test_logout()
        
        # 3. Test admin login separately
        self.test_admin_login()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed < self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MatchMeAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())