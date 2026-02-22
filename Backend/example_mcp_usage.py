#!/usr/bin/env python3
"""
Example: Using MCP Arithmetic Server with MedCompanion

This script demonstrates the complete flow:
1. Start MCP server
2. Get available tools
3. Send chat request with tools to MedCompanion backend
"""

import json
import subprocess
import requests
import sys
from pathlib import Path

BACKEND_URL = "http://localhost:8000"


def main():
    """Demonstrate MCP integration."""
    print("=" * 70)
    print("MCP Arithmetic Server - Usage Example")
    print("=" * 70)
    
    # Step 1: Start MCP server and get tools
    print("\n[Step 1] Getting tools from MCP server...")
    
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.arithmetic_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=Path(__file__).parent
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
        
        tools = response["result"]["tools"]
        print(f"✓ Retrieved {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Step 2: Create session
        print("\n[Step 2] Creating chat session...")
        session_response = requests.post(
            f"{BACKEND_URL}/api/v1/sessions",
            json={"title": "MCP Example"}
        )
        session_id = session_response.json()["session_id"]
        print(f"✓ Session created: {session_id}")
        
        # Step 3: Send chat with tools
        print("\n[Step 3] Sending chat request with tools...")
        print("\nUser: What is 18.7 × 0.015 × 42.3?")
        
        chat_response = requests.post(
            f"{BACKEND_URL}/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "What is 18.7 × 0.015 × 42.3?",
                "domain": "general",
                "mode": "consult",
                "tools": tools
            }
        )
        
        response_text = chat_response.json()["response"]
        print(f"\nMedGemma: {response_text}")
        
        print("\n" + "=" * 70)
        print("NOTE: MedGemma may not naturally output tool calls like")
        print('{"tool": "multiply", "args": {...}} without fine-tuning.')
        print("\nTo make this work fully, you would need to:")
        print("1. Fine-tune MedGemma on tool-calling examples, OR")
        print("2. Add few-shot examples in the system prompt, OR")
        print("3. Use the frontend to parse and execute tool calls")
        print("=" * 70)
        
        # Cleanup
        requests.delete(f"{BACKEND_URL}/api/v1/sessions/{session_id}")
        
    finally:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Backend is not running")
        print("\nPlease start the backend:")
        print("  cd /Users/navin1/MedCompanion")
        print("  source medgemma-env/bin/activate")
        print("  ./start_server.sh")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
