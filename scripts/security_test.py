#!/usr/bin/env python3
"""
Security validation script for user creation and role management
"""
import os
import sys
import requests
from pathlib import Path
import pytest

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_server_available(base_url="http://localhost:8000"):
    """Check if server is available"""
    try:
        response = requests.get(f"{base_url}/health/", timeout=2)
        return response.status_code == 200
    except (requests.ConnectionError, requests.Timeout):
        return False

@pytest.mark.integration
@pytest.mark.skipif(not check_server_available(), reason="Server not running at localhost:8000")
def test_user_creation_security():
    """Test that user creation security works correctly"""
    base_url = "http://localhost:8000"

    print("🧪 Testing User Creation Security...\n")

    # Test 1: Creación sin autenticación debe fallar
    print("Test 1: User creation without authentication")
    response = requests.post(f"{base_url}/api/v1/users/", json={
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True
    })
    if response.status_code == 401:
        print("✅ PASSED: User creation without auth rejected")
    else:
        print(f"❌ FAILED: Expected 401, got {response.status_code}")
        return False

    # Test 2: Registro público solo debe permitir USER y DONOR
    print("\nTest 2: Public registration role restrictions")
    response = requests.post(f"{base_url}/api/v1/auth/register", json={
        "email": "public@example.com",
        "password": "password123",
        "role": "ADMIN"
    })
    if response.status_code == 400:
        print("✅ PASSED: Public registration blocked ADMIN role")
    else:
        print(f"❌ FAILED: Public registration allowed ADMIN role, status: {response.status_code}")
        return False

    # Test 3: Registro público debe permitir USER
    response = requests.post(f"{base_url}/api/v1/auth/register", json={
        "email": "user@example.com",
        "password": "password123",
        "role": "USER"
    })
    if response.status_code == 201:
        print("✅ PASSED: Public registration allowed USER role")
    else:
        print(f"❌ FAILED: Public registration rejected USER role, status: {response.status_code}")
        return False

    # Test 4: Registro público debe permitir DONOR
    response = requests.post(f"{base_url}/api/v1/auth/register", json={
        "email": "donor@example.com",
        "password": "password123",
        "role": "DONOR"
    })
    if response.status_code == 201:
        print("✅ PASSED: Public registration allowed DONOR role")
    else:
        print(f"❌ FAILED: Public registration rejected DONOR role, status: {response.status_code}")
        return False

    print("\n🎉 All user creation security tests PASSED!")
    return True

@pytest.mark.integration
@pytest.mark.skipif(not check_server_available(), reason="Server not running at localhost:8000")
def test_endpoint_protection():
    """Test that endpoints are properly protected"""
    base_url = "http://localhost:8000"

    print("\n🛡️  Testing Endpoint Protection...\n")

    # Test endpoints that should require authentication
    protected_endpoints = [
        ("GET", "/api/v1/auth/dashboard"),
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/donations"),
        ("GET", "/api/v1/users/"),
    ]

    for method, endpoint in protected_endpoints:
        print(f"Testing {method} {endpoint}")
        if method == "GET":
            response = requests.get(f"{base_url}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{base_url}{endpoint}")

        if response.status_code == 401:
            print(f"✅ PASSED: {endpoint} requires authentication")
        else:
            print(f"❌ FAILED: {endpoint} doesn't require authentication (status: {response.status_code})")
            return False

    print("\n🎉 All endpoint protection tests PASSED!")
    return True

def main():
    """Run all security tests"""
    print("🔐 Running Security Validation Tests\n")
    print("=" * 50)

    success = True

    try:
        success &= test_user_creation_security()
        success &= test_endpoint_protection()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

    print("\n" + "=" * 50)
    if success:
        print("🎉 ALL SECURITY TESTS PASSED!")
        print("✅ Your API is secure and properly protected")
    else:
        print("❌ SOME SECURITY TESTS FAILED!")
        print("🚨 Please fix the security issues before deploying")

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)