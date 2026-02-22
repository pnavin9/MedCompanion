#!/bin/bash
# Quick Start Guide for MCP Arithmetic Server

echo "========================================"
echo "MCP Arithmetic Server - Quick Start"
echo "========================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠ Virtual environment not activated"
    echo "Run: source medgemma-env/bin/activate"
    exit 1
fi

echo "Choose an option:"
echo "1. Test MCP server (direct)"
echo "2. Test backend integration"
echo "3. Run usage example"
echo "4. Start MCP server (interactive)"
echo "5. Get tools from MCP server"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "Running MCP server tests..."
        python mcp_server/test_server.py
        ;;
    2)
        echo ""
        echo "Testing backend integration..."
        echo "(Make sure backend is running: ./start_server.sh)"
        python test_mcp_integration.py
        ;;
    3)
        echo ""
        echo "Running usage example..."
        echo "(Make sure backend is running: ./start_server.sh)"
        python example_mcp_usage.py
        ;;
    4)
        echo ""
        echo "Starting MCP server..."
        echo "Send JSON-RPC requests via stdin (Ctrl+C to exit)"
        echo ""
        python -m mcp_server.arithmetic_server
        ;;
    5)
        echo ""
        echo "Getting tools from MCP server..."
        echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m mcp_server.arithmetic_server
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
