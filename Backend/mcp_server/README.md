# MCP Arithmetic Server

A Model Context Protocol (MCP) compliant server providing arithmetic operations for AI assistants.

## Overview

This server implements the [Model Context Protocol](https://spec.modelcontextprotocol.io/) specification using JSON-RPC 2.0 over stdio. It provides arithmetic tools that can be used by AI models like MedGemma.

## Features

- **Protocol**: JSON-RPC 2.0 over stdio
- **Transport**: stdin/stdout for easy integration
- **Tools Provided**:
  - `multiply` - Multiply numbers together
  - `add` - Add numbers together
  - `subtract` - Subtract numbers sequentially
  - `divide` - Divide numbers sequentially
  - `power` - Raise to power (a^b)
  - `sqrt` - Square root
  - `percentage` - Calculate percentage

## Installation

The MCP server is already part of the MedCompanion project. No additional installation needed.

## Usage

### Starting the Server

```bash
# From Backend (or repo root with Backend on path), with venv activated:
python -m mcp_server.arithmetic_server
```

The server will read JSON-RPC requests from stdin and write responses to stdout.

### Manual Testing

You can test the server manually by piping JSON-RPC requests:

```bash
# Get list of tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python -m mcp_server.arithmetic_server

# Call multiply tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"multiply","arguments":{"numbers":[5,10]}}}' | python -m mcp_server.arithmetic_server
```

### Running Tests

```bash
# Test MCP server directly
python mcp_server/test_server.py

# Test integration with backend
python test_mcp_integration.py
```

### Integration with MedCompanion Backend

The backend has been modified to accept tool schemas and inject them into system prompts:

```python
import requests

# 1. Get tools from MCP server (via JSON-RPC)
tools = [...]  # Tool schemas from tools/list

# 2. Send chat request with tools
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "session_id": "...",
        "message": "What is 5 times 10?",
        "tools": tools  # Tools injected into prompt
    }
)
```

### Example with curl

```bash
# Create session
SESSION_ID=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title":"MCP Test"}' | jq -r '.session_id')

# Send chat with tools
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "message": "What is 18.7 × 0.015 × 42.3?",
    "tools": [
      {
        "name": "multiply",
        "description": "Multiplies numbers together",
        "inputSchema": {
          "type": "object",
          "properties": {
            "numbers": {
              "type": "array",
              "items": {"type": "number"}
            }
          }
        }
      }
    ]
  }'
```

## JSON-RPC Methods

### initialize

Initialize the server and get capabilities.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "arithmetic-server",
      "version": "0.1.0"
    },
    "capabilities": {
      "tools": {}
    }
  }
}
```

### tools/list

Get list of available tools.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "multiply",
        "description": "Multiplies an array of numbers together",
        "inputSchema": {
          "type": "object",
          "properties": {
            "numbers": {
              "type": "array",
              "items": {"type": "number"}
            }
          },
          "required": ["numbers"]
        }
      }
      // ... more tools
    ]
  }
}
```

### tools/call

Execute a tool.

**Request:**
```json
{
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
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"result\": 11.86395}"
      }
    ]
  }
}
```

## Architecture

```
┌─────────────────┐
│ MedCompanion IDE │
│   (Frontend)     │
└────────┬─────────┘
         │ stdio (future)
         │
┌────────▼─────────┐         ┌──────────────┐
│   MCP Server     │         │   Backend    │
│  (This Server)   │◄────────┤   (FastAPI)  │
└──────────────────┘  HTTP   └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │   MedGemma   │
                              │    Model     │
                              └──────────────┘
```

## Tool Schemas

All tools follow JSON Schema format for input validation. See `arithmetic_server.py` for complete schemas.

## Error Handling

The server returns standard JSON-RPC error codes:

- `-32700` - Parse error
- `-32600` - Invalid request
- `-32601` - Method not found
- `-32602` - Invalid params
- `-32603` - Internal error

## Logging

The server logs to stderr (stdout is reserved for JSON-RPC). To see logs:

```bash
python -m mcp_server.arithmetic_server 2> server.log
```

## Notes

- MedGemma is not fine-tuned for function calling, so it may not naturally output tool call syntax
- The backend correctly injects tools into system prompts
- For production use, consider adding few-shot examples or fine-tuning MedGemma

## License

Part of the MedCompanion project.
