#!/usr/bin/env python3
"""
MCP Arithmetic Server

A Model Context Protocol (MCP) compliant server that provides arithmetic operations.
Uses JSON-RPC 2.0 over stdio for communication.

Protocol: https://spec.modelcontextprotocol.io/
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from functools import reduce
import operator
import math

# Configure logging to stderr (stdout is used for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class JSONRPCError(Exception):
    """JSON-RPC error with code and message."""
    
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class MCPArithmeticServer:
    """MCP server providing arithmetic operations."""
    
    # JSON-RPC error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    def __init__(self):
        """Initialize the MCP server."""
        self.server_info = {
            "name": "arithmetic-server",
            "version": "0.1.0"
        }
        self.capabilities = {
            "tools": {}
        }
        logger.info("MCP Arithmetic Server initialized")
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return all available tool schemas."""
        return [
            {
                "name": "multiply",
                "description": "Multiplies an array of numbers together. Returns the product of all numbers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers to multiply",
                            "minItems": 1
                        }
                    },
                    "required": ["numbers"]
                }
            },
            {
                "name": "add",
                "description": "Adds an array of numbers together. Returns the sum of all numbers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers to add",
                            "minItems": 1
                        }
                    },
                    "required": ["numbers"]
                }
            },
            {
                "name": "subtract",
                "description": "Subtracts numbers sequentially. Subtracts all subsequent numbers from the first number.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers to subtract (first - second - third - ...)",
                            "minItems": 2
                        }
                    },
                    "required": ["numbers"]
                }
            },
            {
                "name": "divide",
                "description": "Divides numbers sequentially. Divides the first number by all subsequent numbers.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Array of numbers to divide (first / second / third / ...)",
                            "minItems": 2
                        }
                    },
                    "required": ["numbers"]
                }
            },
            {
                "name": "power",
                "description": "Raises a number to a power. Calculates base^exponent.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "base": {
                            "type": "number",
                            "description": "The base number"
                        },
                        "exponent": {
                            "type": "number",
                            "description": "The exponent"
                        }
                    },
                    "required": ["base", "exponent"]
                }
            },
            {
                "name": "sqrt",
                "description": "Calculates the square root of a number.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "number": {
                            "type": "number",
                            "description": "The number to calculate square root of",
                            "minimum": 0
                        }
                    },
                    "required": ["number"]
                }
            },
            {
                "name": "percentage",
                "description": "Calculates what percentage one number is of another. Returns (part/whole) * 100.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "part": {
                            "type": "number",
                            "description": "The part value"
                        },
                        "whole": {
                            "type": "number",
                            "description": "The whole value"
                        }
                    },
                    "required": ["part", "whole"]
                }
            }
        ]
    
    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name with given arguments."""
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        try:
            if name == "multiply":
                numbers = arguments.get("numbers", [])
                if not numbers:
                    raise JSONRPCError(self.INVALID_PARAMS, "numbers array is required")
                result = reduce(operator.mul, numbers, 1)
                return {"result": result}
            
            elif name == "add":
                numbers = arguments.get("numbers", [])
                if not numbers:
                    raise JSONRPCError(self.INVALID_PARAMS, "numbers array is required")
                result = sum(numbers)
                return {"result": result}
            
            elif name == "subtract":
                numbers = arguments.get("numbers", [])
                if len(numbers) < 2:
                    raise JSONRPCError(self.INVALID_PARAMS, "At least 2 numbers required for subtraction")
                result = numbers[0] - sum(numbers[1:])
                return {"result": result}
            
            elif name == "divide":
                numbers = arguments.get("numbers", [])
                if len(numbers) < 2:
                    raise JSONRPCError(self.INVALID_PARAMS, "At least 2 numbers required for division")
                if any(n == 0 for n in numbers[1:]):
                    raise JSONRPCError(self.INVALID_PARAMS, "Cannot divide by zero")
                result = reduce(operator.truediv, numbers)
                return {"result": result}
            
            elif name == "power":
                base = arguments.get("base")
                exponent = arguments.get("exponent")
                if base is None or exponent is None:
                    raise JSONRPCError(self.INVALID_PARAMS, "base and exponent are required")
                result = math.pow(base, exponent)
                return {"result": result}
            
            elif name == "sqrt":
                number = arguments.get("number")
                if number is None:
                    raise JSONRPCError(self.INVALID_PARAMS, "number is required")
                if number < 0:
                    raise JSONRPCError(self.INVALID_PARAMS, "Cannot calculate square root of negative number")
                result = math.sqrt(number)
                return {"result": result}
            
            elif name == "percentage":
                part = arguments.get("part")
                whole = arguments.get("whole")
                if part is None or whole is None:
                    raise JSONRPCError(self.INVALID_PARAMS, "part and whole are required")
                if whole == 0:
                    raise JSONRPCError(self.INVALID_PARAMS, "whole cannot be zero")
                result = (part / whole) * 100
                return {"result": result}
            
            else:
                raise JSONRPCError(self.METHOD_NOT_FOUND, f"Tool '{name}' not found")
        
        except JSONRPCError:
            raise
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}", exc_info=True)
            raise JSONRPCError(self.INTERNAL_ERROR, f"Error executing tool: {str(e)}")
    
    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        logger.info("Handling initialize request")
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": self.server_info,
            "capabilities": self.capabilities
        }
    
    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        logger.info("Handling tools/list request")
        return {
            "tools": self.get_tool_schemas()
        }
    
    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise JSONRPCError(self.INVALID_PARAMS, "Tool name is required")
        
        result = self.execute_tool(name, arguments)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result)
                }
            ]
        }
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a JSON-RPC request and return a response."""
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        logger.info(f"Processing request: method={method}, id={request_id}")
        
        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            else:
                raise JSONRPCError(self.METHOD_NOT_FOUND, f"Method '{method}' not found")
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            logger.info(f"Request successful: method={method}")
            return response
        
        except JSONRPCError as e:
            logger.error(f"JSON-RPC error: {e.code} - {e.message}")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": e.code,
                    "message": e.message
                }
            }
            if e.data is not None:
                response["error"]["data"] = e.data
            return response
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": self.INTERNAL_ERROR,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def run(self):
        """Run the server, reading from stdin and writing to stdout."""
        logger.info("MCP Arithmetic Server starting...")
        logger.info("Reading JSON-RPC requests from stdin...")
        
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                
                logger.debug(f"Received: {line}")
                
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": self.PARSE_ERROR,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    response_str = json.dumps(error_response)
                    print(response_str, flush=True)
                    continue
                
                # Validate JSON-RPC format
                if not isinstance(request, dict) or request.get("jsonrpc") != "2.0":
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {
                            "code": self.INVALID_REQUEST,
                            "message": "Invalid JSON-RPC 2.0 request"
                        }
                    }
                    response_str = json.dumps(error_response)
                    print(response_str, flush=True)
                    continue
                
                # Handle the request
                response = self.handle_request(request)
                response_str = json.dumps(response)
                logger.debug(f"Sending: {response_str}")
                print(response_str, flush=True)
        
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point."""
    server = MCPArithmeticServer()
    server.run()


if __name__ == "__main__":
    main()
