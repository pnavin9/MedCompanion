#!/usr/bin/env python3
"""
Test script for MedCompanion API server.

This script tests the basic functionality of the server:
1. Health check
2. Create session
3. Send text message
4. Get session history
5. Delete session
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_create_session():
    """Test session creation."""
    print("\nTesting session creation...")
    response = requests.post(
        f"{BASE_URL}/api/v1/sessions",
        json={"title": "Test Session"}
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return data.get("session_id") if response.status_code == 200 else None


def test_chat(session_id, message, domain=None, mode=None):
    """Test chat endpoint."""
    print(f"\nTesting chat with message: '{message}'...")
    if domain and mode:
        print(f"Domain: {domain}, Mode: {mode}")
    
    payload = {
        "session_id": session_id,
        "message": message
    }
    if domain:
        payload["domain"] = domain
    if mode:
        payload["mode"] = mode
    
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json=payload
    )
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200


def test_get_session(session_id):
    """Test getting session history."""
    print(f"\nTesting get session history...")
    response = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200


def test_delete_session(session_id):
    """Test session deletion."""
    print(f"\nTesting session deletion...")
    response = requests.delete(f"{BASE_URL}/api/v1/sessions/{session_id}")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    return response.status_code == 200


def test_chat_with_domain_mode():
    """Test chat with different domain/mode combinations."""
    print("\n" + "="*60)
    print("Testing Domain/Mode Combinations")
    print("="*60)
    
    # Create a test session
    session_id = test_create_session()
    if not session_id:
        print("\n❌ Failed to create session for domain/mode tests!")
        return False
    
    # Test 1: Diagnose Radiology
    print("\n--- Test 1: Diagnose Radiology ---")
    if not test_chat(session_id, "What is pneumonia?", domain="radiology", mode="diagnose"):
        print("❌ Diagnose Radiology test failed!")
        return False
    print("✅ Diagnose Radiology test passed")
    
    # Test 2: Consult General (default behavior)
    print("\n--- Test 2: Consult General ---")
    if not test_chat(session_id, "What is aspirin?", domain="general", mode="consult"):
        print("❌ Consult General test failed!")
        return False
    print("✅ Consult General test passed")
    
    # Test 3: Plan Pathology
    print("\n--- Test 3: Plan Pathology ---")
    if not test_chat(session_id, "What tests should I consider?", domain="pathology", mode="plan"):
        print("❌ Plan Pathology test failed!")
        return False
    print("✅ Plan Pathology test passed")
    
    # Test 4: Mid-conversation domain switch
    print("\n--- Test 4: Mid-conversation Domain Switch ---")
    if not test_chat(session_id, "Now from a dermatology perspective?", domain="dermatology", mode="consult"):
        print("❌ Domain switch test failed!")
        return False
    print("✅ Domain switch test passed")
    
    # Cleanup
    test_delete_session(session_id)
    
    return True


def test_invalid_mode():
    """Test that Agent mode is rejected."""
    print("\n" + "="*60)
    print("Testing Invalid Mode (Agent)")
    print("="*60)
    
    # Create a test session
    session_id = test_create_session()
    if not session_id:
        print("\n❌ Failed to create session for invalid mode test!")
        return False
    
    # Try to use Agent mode (should fail)
    print("\nTesting Agent mode rejection...")
    response = requests.post(
        f"{BASE_URL}/api/v1/chat",
        json={
            "session_id": session_id,
            "message": "Hello",
            "mode": "agent"
        }
    )
    print(f"Status: {response.status_code}")
    
    # Should return 422 (Validation Error)
    if response.status_code == 422:
        print("✅ Agent mode correctly rejected")
        result = True
    else:
        print(f"❌ Expected 422, got {response.status_code}")
        result = False
    
    # Cleanup
    test_delete_session(session_id)
    
    return result


def main():
    """Run all tests."""
    print("="*60)
    print("MedCompanion API Test Script")
    print("="*60)
    
    # Test health check
    if not test_health():
        print("\n❌ Health check failed!")
        sys.exit(1)
    print("✅ Health check passed")
    
    # Create session
    session_id = test_create_session()
    if not session_id:
        print("\n❌ Session creation failed!")
        sys.exit(1)
    print(f"✅ Session created: {session_id}")
    
    # Send a chat message (basic test)
    if not test_chat(session_id, "What is hemoglobin?"):
        print("\n❌ Chat failed!")
        sys.exit(1)
    print("✅ Chat successful")
    
    # Get session history
    if not test_get_session(session_id):
        print("\n❌ Get session failed!")
        sys.exit(1)
    print("✅ Session history retrieved")
    
    # Delete session
    if not test_delete_session(session_id):
        print("\n❌ Session deletion failed!")
        sys.exit(1)
    print("✅ Session deleted")
    
    # Test domain/mode combinations
    if not test_chat_with_domain_mode():
        print("\n❌ Domain/mode tests failed!")
        sys.exit(1)
    print("✅ All domain/mode tests passed")
    
    # Test invalid mode rejection
    if not test_invalid_mode():
        print("\n❌ Invalid mode test failed!")
        sys.exit(1)
    print("✅ Invalid mode test passed")
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to server.")
        print("Make sure the server is running on http://localhost:8000")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
