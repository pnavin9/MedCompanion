#!/usr/bin/env python3
"""
Test script for MCP Arithmetic Server

Tests the JSON-RPC 2.0 protocol over stdio by sending requests
and validating responses.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def send_request(process, request):
    """Send a JSON-RPC request to the server and get response."""
    request_str = json.dumps(request) + "\n"
    process.stdin.write(request_str)
    process.stdin.flush()
    
    response_str = process.stdout.readline()
    return json.loads(response_str)


def test_initialize():
    """Test the initialize method."""
    print("Testing initialize...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = send_request(process, request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert response["result"]["serverInfo"]["name"] == "arithmetic-server"
        print("✓ Initialize test passed")
        
    finally:
        process.terminate()
        process.wait()


def test_tools_list():
    """Test the tools/list method."""
    print("\nTesting tools/list...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = send_request(process, request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "tools" in response["result"]
        
        tools = response["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        
        expected_tools = ["multiply", "add", "subtract", "divide", "power", "sqrt", "percentage"]
        for tool in expected_tools:
            assert tool in tool_names, f"Missing tool: {tool}"
        
        print(f"✓ Tools/list test passed - Found {len(tools)} tools")
        
    finally:
        process.terminate()
        process.wait()


def test_multiply():
    """Test the multiply tool."""
    print("\nTesting multiply tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "multiply",
                "arguments": {
                    "numbers": [18.7, 0.015, 42.3]
                }
            }
        }
        
        response = send_request(process, request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "content" in response["result"]
        
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        expected = 18.7 * 0.015 * 42.3
        assert abs(result - expected) < 0.001, f"Expected {expected}, got {result}"
        
        print(f"✓ Multiply test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_add():
    """Test the add tool."""
    print("\nTesting add tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "add",
                "arguments": {
                    "numbers": [10, 20, 30, 40]
                }
            }
        }
        
        response = send_request(process, request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        assert result == 100, f"Expected 100, got {result}"
        print(f"✓ Add test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_divide():
    """Test the divide tool."""
    print("\nTesting divide tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "divide",
                "arguments": {
                    "numbers": [100, 5, 2]
                }
            }
        }
        
        response = send_request(process, request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        expected = 100 / 5 / 2
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"✓ Divide test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_power():
    """Test the power tool."""
    print("\nTesting power tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "power",
                "arguments": {
                    "base": 2,
                    "exponent": 8
                }
            }
        }
        
        response = send_request(process, request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        assert result == 256, f"Expected 256, got {result}"
        print(f"✓ Power test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_sqrt():
    """Test the sqrt tool."""
    print("\nTesting sqrt tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "sqrt",
                "arguments": {
                    "number": 144
                }
            }
        }
        
        response = send_request(process, request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        assert result == 12, f"Expected 12, got {result}"
        print(f"✓ Sqrt test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_percentage():
    """Test the percentage tool."""
    print("\nTesting percentage tool...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "percentage",
                "arguments": {
                    "part": 25,
                    "whole": 200
                }
            }
        }
        
        response = send_request(process, request)
        
        assert "result" in response
        content = json.loads(response["result"]["content"][0]["text"])
        result = content["result"]
        
        assert result == 12.5, f"Expected 12.5, got {result}"
        print(f"✓ Percentage test passed - Result: {result}")
        
    finally:
        process.terminate()
        process.wait()


def test_error_handling():
    """Test error handling for invalid requests."""
    print("\nTesting error handling...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Test invalid method
        request = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "invalid_method",
            "params": {}
        }
        
        response = send_request(process, request)
        
        assert "error" in response
        assert response["error"]["code"] == -32601  # METHOD_NOT_FOUND
        print("✓ Error handling test passed - Invalid method rejected")
        
    finally:
        process.terminate()
        process.wait()


def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Arithmetic Server Test Suite")
    print("=" * 60)
    
    tests = [
        test_initialize,
        test_tools_list,
        test_multiply,
        test_add,
        test_divide,
        test_power,
        test_sqrt,
        test_percentage,
        test_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
