#!/usr/bin/env python3
"""
Test script to verify Claude CLI integration locally.
"""

import os
import sys
sys.path.append('app')

from claude_cli_client import ClaudeCLIClient, ClaudeCLIError

def test_claude_cli():
    """Test Claude CLI client locally."""
    print("🧪 Testing Claude CLI Client Locally")
    print("=" * 50)
    
    try:
        # Create client
        client = ClaudeCLIClient(repository_root=".")
        print("✅ Claude CLI client created successfully")
        
        # Test simple prompt
        test_prompt = "Analyze this repository and tell me what kind of application this is in 2-3 sentences."
        
        print(f"\n📝 Testing with prompt: {test_prompt}")
        print("-" * 50)
        
        response = client.generate_response(test_prompt)
        
        print(f"✅ Response received:")
        print(f"   Model: {response.model}")
        print(f"   Repository Context: {response.repository_context}")
        print(f"   Timestamp: {response.timestamp}")
        print(f"   Command: {response.command_used}")
        print(f"\n📄 Content:")
        print(response.content[:500] + "..." if len(response.content) > 500 else response.content)
        
        return True
        
    except ClaudeCLIError as e:
        print(f"❌ Claude CLI Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_claude_cli()
    sys.exit(0 if success else 1)