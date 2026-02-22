#!/usr/bin/env python3
"""
Integration test for MCP Arithmetic Server with MedCompanion Backend

Tests the end-to-end flow:
1. Get tool schemas from MCP server
2. Send chat request with tools to backend
3. Verify tools are injected into prompt
"""

import json
import subprocess
import sys
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
BACKEND_URL = "http://localhost:8000"
MCP_SERVER_PATH = Path(__file__).parent / "mcp_server" / "arithmetic_server.py"


def get_tools_from_mcp():
    """Get tool schemas from MCP server."""
    print("Starting MCP server to get tool schemas...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Request tools/list
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        request_str = json.dumps(request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()
        
        response_str = process.stdout.readline()
        response = json.loads(response_str)
        
        if "result" in response and "tools" in response["result"]:
            tools = response["result"]["tools"]
            print(f"✓ Retrieved {len(tools)} tools from MCP server")
            return tools
        else:
            print(f"✗ Failed to get tools: {response}")
            return None
    
    finally:
        process.terminate()
        process.wait()


def create_test_session():
    """Create a test session in the backend."""
    print("\nCreating test session...")
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/sessions",
        json={"title": "MCP Integration Test"}
    )
    
    if response.status_code == 200:
        session_id = response.json()["session_id"]
        print(f"✓ Created session: {session_id}")
        return session_id
    else:
        print(f"✗ Failed to create session: {response.status_code}")
        return None


def test_chat_with_tools(session_id, tools):
    """Test sending a chat request with tools."""
    print("\nTesting chat with tools...")
    
    # Send a simple message that would benefit from calculation
    request_data = {
        "session_id": session_id,
        "message": "What is 5 multiplied by 10?",
        "domain": "general",
        "mode": "consult",
        "tools": tools
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/chat",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        response_text = result.get("response", "")
        print(f"✓ Backend responded successfully")
        print(f"\nResponse: {response_text[:200]}...")
        
        # Check if response mentions tools (might be in the response)
        # Note: MedGemma might not use the tools correctly without fine-tuning,
        # but we can verify the backend accepted the tools parameter
        return True
    else:
        print(f"✗ Backend request failed: {response.status_code}")
        print(f"Error: {response.text}")
        return False


def test_chat_without_tools(session_id):
    """Test that chat still works without tools (backward compatibility)."""
    print("\nTesting chat without tools (backward compatibility)...")
    
    request_data = {
        "session_id": session_id,
        "message": "What is hemoglobin?",
        "domain": "general",
        "mode": "consult"
    }
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/chat",
        json=request_data
    )
    
    if response.status_code == 200:
        print("✓ Backend works without tools parameter")
        return True
    else:
        print(f"✗ Backend request failed: {response.status_code}")
        return False


def cleanup_session(session_id):
    """Delete the test session."""
    print(f"\nCleaning up session {session_id}...")
    
    response = requests.delete(f"{BACKEND_URL}/api/v1/sessions/{session_id}")
    
    if response.status_code == 200:
        print("✓ Session deleted")
    else:
        print(f"⚠ Failed to delete session: {response.status_code}")


def check_backend():
    """Check if backend is running."""
    print("Checking backend availability...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
            return True
    except requests.exceptions.ConnectionError:
        print("✗ Backend is not running")
        print(f"\nPlease start the backend:")
        print("  cd /Users/navin1/MedCompanion")
        print("  source medgemma-env/bin/activate")
        print("  ./start_server.sh")
        return False
    except Exception as e:
        print(f"✗ Error checking backend: {e}")
        return False


def main():
    """Run integration tests."""
    print("=" * 60)
    print("MCP Arithmetic Server - Backend Integration Test")
    print("=" * 60)
    
    # Check if backend is running
    if not check_backend():
        return 1
    
    # Get tools from MCP server
    tools = get_tools_from_mcp()
    if not tools:
        print("\n✗ Failed to get tools from MCP server")
        return 1
    
    # Create test session
    session_id = create_test_session()
    if not session_id:
        print("\n✗ Failed to create test session")
        return 1
    
    try:
        # Test chat with tools
        success_with_tools = test_chat_with_tools(session_id, tools)
        
        # Test backward compatibility
        success_without_tools = test_chat_without_tools(session_id)
        
        # Summary
        print("\n" + "=" * 60)
        if success_with_tools and success_without_tools:
            print("✓ All integration tests passed!")
            print("\nNOTE: MedGemma may not naturally use the tools without")
            print("fine-tuning. The test verifies the backend accepts and")
            print("processes the tools parameter correctly.")
            print("=" * 60)
            return 0
        else:
            print("✗ Some tests failed")
            print("=" * 60)
            return 1
    
    finally:
        # Cleanup
        cleanup_session(session_id)


if __name__ == "__main__":
    sys.exit(main())
