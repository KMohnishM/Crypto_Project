#!/usr/bin/env python3
"""
Test script to verify the authentication flow and user management
Run this after starting the Docker containers
"""

import requests
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
session = requests.Session()

def print_test(test_name, passed):
    """Print test result"""
    status = "PASS" if passed else "FAIL"
    print(f"{status}: {test_name}")
    return passed

def test_landing_page():
    """Test that landing page loads"""
    try:
        r = session.get(f"{BASE_URL}/")
        return print_test("Landing page loads", r.status_code == 200 and "Hospital Monitoring System" in r.text)
    except Exception as e:
        print(f"ERROR: Landing page test failed: {e}")
        return False

def test_login_page():
    """Test that login page loads"""
    try:
        r = session.get(f"{BASE_URL}/auth/login")
        return print_test("Login page loads", r.status_code == 200 and "Login" in r.text)
    except Exception as e:
        print(f"ERROR: Login page test failed: {e}")
        return False

def test_register_page():
    """Test that register page loads"""
    try:
        r = session.get(f"{BASE_URL}/auth/register")
        return print_test("Register page loads", r.status_code == 200 and "Register" in r.text)
    except Exception as e:
        print(f"ERROR: Register page test failed: {e}")
        return False

def test_protected_routes_redirect():
    """Test that protected routes redirect to login when not authenticated"""
    protected_routes = [
        "/dashboard",
        "/patients/",
        "/analytics"
    ]
    
    all_passed = True
    for route in protected_routes:
        try:
            # Use allow_redirects=False to check if redirect happens
            r = session.get(f"{BASE_URL}{route}", allow_redirects=False)
            # Should get 302 redirect to login
            passed = r.status_code == 302 and "login" in r.headers.get("Location", "").lower()
            all_passed &= print_test(f"Protected route {route} redirects to login", passed)
        except Exception as e:
            print(f"ERROR: Protected route test failed for {route}: {e}")
            all_passed = False
    
    return all_passed

def test_login():
    """Test login with default admin credentials"""
    try:
        # Get login page first to get CSRF token if needed
        r = session.get(f"{BASE_URL}/auth/login")
        
        # Attempt login
        login_data = {
            "username": "admin",
            "password": "admin",
            "remember": "on"
        }
        r = session.post(f"{BASE_URL}/auth/login", data=login_data, allow_redirects=True)
        
        # Check if we're redirected to dashboard
        passed = r.status_code == 200 and "Dashboard" in r.text
        return print_test("Login with admin credentials", passed)
    except Exception as e:
        print(f"ERROR: Login test failed: {e}")
        return False

def test_dashboard_access():
    """Test that dashboard is accessible after login"""
    try:
        r = session.get(f"{BASE_URL}/dashboard")
        passed = r.status_code == 200 and "Welcome back" in r.text
        return print_test("Dashboard accessible after login", passed)
    except Exception as e:
        print(f"ERROR: Dashboard access test failed: {e}")
        return False

def test_patients_access():
    """Test that patients page is accessible after login"""
    try:
        r = session.get(f"{BASE_URL}/patients/")
        passed = r.status_code == 200
        return print_test("Patients page accessible after login", passed)
    except Exception as e:
        print(f"ERROR: Patients access test failed: {e}")
        return False

def test_analytics_access():
    """Test that analytics page is accessible after login"""
    try:
        r = session.get(f"{BASE_URL}/analytics")
        passed = r.status_code == 200
        return print_test("Analytics page accessible after login", passed)
    except Exception as e:
        print(f"ERROR: Analytics access test failed: {e}")
        return False

def test_profile_access():
    """Test that profile page is accessible after login"""
    try:
        r = session.get(f"{BASE_URL}/auth/profile")
        passed = r.status_code == 200 and "Profile" in r.text
        return print_test("Profile page accessible after login", passed)
    except Exception as e:
        print(f"ERROR: Profile access test failed: {e}")
        return False

def test_monitoring_public():
    """Test that monitoring page is publicly accessible"""
    # Create new session to test without authentication
    new_session = requests.Session()
    try:
        r = new_session.get(f"{BASE_URL}/monitoring")
        passed = r.status_code == 200
        return print_test("Monitoring page publicly accessible", passed)
    except Exception as e:
        print(f"ERROR: Monitoring public access test failed: {e}")
        return False

def test_logout():
    """Test logout functionality"""
    try:
        r = session.get(f"{BASE_URL}/auth/logout", allow_redirects=True)
        # Should redirect to landing page
        passed = r.status_code == 200 and "Hospital Monitoring System" in r.text
        return print_test("Logout redirects to landing page", passed)
    except Exception as e:
        print(f"ERROR: Logout test failed: {e}")
        return False

def test_dashboard_after_logout():
    """Test that dashboard is not accessible after logout"""
    try:
        r = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)
        # Should get 302 redirect to login
        passed = r.status_code == 302 and "login" in r.headers.get("Location", "").lower()
        return print_test("Dashboard protected after logout", passed)
    except Exception as e:
        print(f"ERROR: Dashboard after logout test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Authentication Flow Test Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    print("Phase 1: Public Routes")
    print("-" * 60)
    test_results = []
    test_results.append(test_landing_page())
    test_results.append(test_login_page())
    test_results.append(test_register_page())
    test_results.append(test_monitoring_public())
    print()
    
    print("Phase 2: Protected Routes (Before Login)")
    print("-" * 60)
    test_results.append(test_protected_routes_redirect())
    print()
    
    print("Phase 3: Authentication")
    print("-" * 60)
    test_results.append(test_login())
    print()
    
    print("Phase 4: Authenticated Access")
    print("-" * 60)
    test_results.append(test_dashboard_access())
    test_results.append(test_patients_access())
    test_results.append(test_analytics_access())
    test_results.append(test_profile_access())
    print()
    
    print("Phase 5: Logout")
    print("-" * 60)
    test_results.append(test_logout())
    test_results.append(test_dashboard_after_logout())
    print()
    
    print("=" * 60)
    passed = sum(test_results)
    total = len(test_results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Results: {passed}/{total} tests passed ({percentage:.1f}%)")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print(f"WARNING: {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nWARNING: Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: Test suite failed with error: {e}")
        sys.exit(1)
