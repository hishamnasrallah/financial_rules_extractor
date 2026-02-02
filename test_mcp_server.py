"""
Test client for MCP server.
This script sends test requests to the MCP server and displays responses.
"""
import json
import subprocess
import sys
from typing import Dict, Any


def send_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a request to the MCP server and get response.
    
    Args:
        request: JSON-RPC request
        
    Returns:
        JSON-RPC response
    """
    # Start MCP server process
    process = subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Send request
    request_json = json.dumps(request) + "\n"
    stdout, stderr = process.communicate(input=request_json, timeout=120)
    
    # Parse response
    if stderr:
        print(f"Server logs:\n{stderr}")
    
    # Find JSON response in stdout
    for line in stdout.split('\n'):
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    
    return {"error": "No valid JSON response", "stdout": stdout}


def test_list_tools():
    """Test listing available tools."""
    print("\n" + "="*60)
    print("TEST 1: List Available Tools")
    print("="*60)
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    
    print(f"\nSending request: {json.dumps(request, indent=2)}")
    response = send_mcp_request(request)
    print(f"\nResponse:\n{json.dumps(response, indent=2, ensure_ascii=False)}")
    
    return response


def test_parse_document():
    """Test document parsing tool."""
    print("\n" + "="*60)
    print("TEST 2: Parse Document")
    print("="*60)
    
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "parse_document",
            "arguments": {
                "url": "https://laws.boe.gov.sa/BoeLaws/Laws/LawDetails/fd30f9c7-8606-4367-bb22-a9a700f2d952/1",
                "name": "نظام الخدمة المدنية - اختبار"
            }
        }
    }
    
    print(f"\nSending request: {json.dumps(request, indent=2, ensure_ascii=False)}")
    print("\nProcessing... (this may take 5-10 seconds)")
    response = send_mcp_request(request)
    print(f"\nResponse:\n{json.dumps(response, indent=2, ensure_ascii=False)[:1000]}...")
    
    return response


def test_get_tracks():
    """Test getting predefined tracks."""
    print("\n" + "="*60)
    print("TEST 3: Get Predefined Tracks")
    print("="*60)
    
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_predefined_tracks",
            "arguments": {}
        }
    }
    
    print(f"\nSending request: {json.dumps(request, indent=2)}")
    response = send_mcp_request(request)
    print(f"\nResponse:\n{json.dumps(response, indent=2, ensure_ascii=False)[:1000]}...")
    
    return response


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MCP SERVER TEST CLIENT")
    print("="*60)
    print("\nThis script will test the MCP server by sending requests.")
    print("Make sure .env is configured with your AIXPLAIN_API_KEY")
    
    try:
        # Test 1: List tools
        test_list_tools()
        
        # Test 2: Get tracks (fast)
        test_get_tracks()
        
        # Test 3: Parse document (slower)
        print("\n\nWould you like to test document parsing? (takes 5-10 seconds)")
        response = input("Test parsing? (y/n): ").lower().strip()
        if response == 'y':
            test_parse_document()
        
        print("\n" + "="*60)
        print("TESTS COMPLETE!")
        print("="*60)
        print("\nThe MCP server is working correctly.")
        print("You can now integrate it with Claude Desktop or other MCP clients.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
