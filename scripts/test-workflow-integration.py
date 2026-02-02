#!/usr/bin/env python3
"""
Test script to verify workflow integration with Claude CLI.

This script tests the workflow components without requiring actual Claude CLI execution.
"""

import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing module imports...")
    
    try:
        from claude_client_factory import get_claude_client, ClientType
        print("✅ claude_client_factory imported successfully")
        
        from claude_cli_client import ClaudeCLIClient
        print("✅ claude_cli_client imported successfully")
        
        from workflow_engine import get_workflow_engine
        print("✅ workflow_engine imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_client_factory():
    """Test client factory functionality."""
    print("\n🏭 Testing client factory...")
    
    try:
        from claude_client_factory import get_claude_client, get_available_client_types, ClientType
        
        # Test available types
        available = get_available_client_types()
        print(f"✅ Available client types: {[t.value for t in available]}")
        
        # Test client creation
        client = get_claude_client()
        print(f"✅ Created client: {type(client).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Client factory test failed: {e}")
        return False

def test_workflow_engine():
    """Test workflow engine creation."""
    print("\n⚙️ Testing workflow engine...")
    
    try:
        from workflow_engine import get_workflow_engine
        from claude_client_factory import ClientType
        
        # Test workflow engine creation
        engine = get_workflow_engine()
        print(f"✅ Created workflow engine with client: {type(engine.claude_client).__name__}")
        
        # Test with explicit CLI preference
        if ClientType.CLI in [ClientType.CLI]:  # Always true, but shows the pattern
            engine_cli = get_workflow_engine(preferred_client_type=ClientType.CLI)
            print(f"✅ Created CLI-preferred engine: {type(engine_cli.claude_client).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Workflow engine test failed: {e}")
        return False

def test_environment_detection():
    """Test environment-based client detection."""
    print("\n🌍 Testing environment detection...")
    
    try:
        from claude_client_factory import ClaudeClientFactory
        
        factory = ClaudeClientFactory()
        preferred_type = factory._preferred_client_type
        print(f"✅ Detected preferred client type: {preferred_type.value}")
        
        # Test GitHub Actions detection
        github_actions = os.getenv("GITHUB_ACTIONS")
        github_workspace = os.getenv("GITHUB_WORKSPACE")
        
        print(f"📋 GITHUB_ACTIONS: {github_actions}")
        print(f"📋 GITHUB_WORKSPACE: {github_workspace}")
        
        if github_actions and github_workspace:
            print("✅ GitHub Actions environment detected - would prefer CLI")
        else:
            print("ℹ️ Local environment detected - using available client")
        
        return True
    except Exception as e:
        print(f"❌ Environment detection test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("Claude CLI Workflow Integration Test")
    print("=" * 40)
    
    tests = [
        ("Module Imports", test_imports),
        ("Client Factory", test_client_factory),
        ("Workflow Engine", test_workflow_engine),
        ("Environment Detection", test_environment_detection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed - check the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())