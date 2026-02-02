#!/usr/bin/env python3
"""
Debug script to identify workflow failure issues.
Run this from the runner environment to diagnose problems.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check environment variables."""
    print("🔍 Checking Environment Variables")
    print("-" * 40)
    
    required_vars = ["GITHUB_TOKEN", "PYTHONPATH", "REPO_ROOT"]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't print the full token for security
            if "TOKEN" in var:
                print(f"✅ {var}: {'*' * 20}...{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

def check_claude_cli():
    """Check Claude CLI availability."""
    print("\n🤖 Checking Claude CLI")
    print("-" * 25)
    
    try:
        # Check if claude command exists
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Claude CLI version: {result.stdout.strip()}")
        else:
            print(f"❌ Claude CLI error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Claude CLI not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Claude CLI command timed out")
        return False
    
    try:
        # Check authentication status
        result = subprocess.run(["claude", "auth", "status"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Claude CLI authentication: OK")
        else:
            print(f"⚠️ Claude CLI auth status: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not check Claude CLI auth status: {e}")
    
    return True

def check_python_imports():
    """Check if Python can import required modules."""
    print("\n🐍 Checking Python Imports")
    print("-" * 30)
    
    # Add current directory to path
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    sys.path.insert(0, os.path.join(repo_root, "app"))
    sys.path.insert(0, repo_root)
    
    modules_to_test = [
        "claude_client_factory",
        "claude_cli_client", 
        "workflow_engine",
        "policy_gate",
        "github_client"
    ]
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✅ {module}: Import successful")
        except ImportError as e:
            print(f"❌ {module}: Import failed - {e}")
        except Exception as e:
            print(f"⚠️ {module}: Import error - {e}")

def check_file_paths():
    """Check if required files exist."""
    print("\n📁 Checking File Paths")
    print("-" * 25)
    
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    
    required_files = [
        "app/claude_client_factory.py",
        "app/claude_cli_client.py",
        "app/workflow_engine.py",
        ".github/scripts/functional_workflow_executor.py",
        ".github/scripts/policy_gate_evaluation.py"
    ]
    
    for file_path in required_files:
        full_path = os.path.join(repo_root, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}: Exists")
        else:
            print(f"❌ {file_path}: Missing")

def test_workflow_components():
    """Test workflow components."""
    print("\n⚙️ Testing Workflow Components")
    print("-" * 35)
    
    repo_root = os.getenv("REPO_ROOT", os.getcwd())
    
    # Test policy gate evaluation
    try:
        policy_script = os.path.join(repo_root, ".github/scripts/policy_gate_evaluation.py")
        if os.path.exists(policy_script):
            print("✅ Policy gate script exists")
            # Could test execution here if needed
        else:
            print("❌ Policy gate script missing")
    except Exception as e:
        print(f"❌ Policy gate test failed: {e}")
    
    # Test functional workflow executor
    try:
        executor_script = os.path.join(repo_root, ".github/scripts/functional_workflow_executor.py")
        if os.path.exists(executor_script):
            print("✅ Workflow executor script exists")
        else:
            print("❌ Workflow executor script missing")
    except Exception as e:
        print(f"❌ Workflow executor test failed: {e}")

def test_claude_client_creation():
    """Test Claude client creation."""
    print("\n🔧 Testing Claude Client Creation")
    print("-" * 40)
    
    try:
        from claude_client_factory import get_claude_client, get_available_client_types
        
        # Check available client types
        available_types = get_available_client_types()
        print(f"✅ Available client types: {[t.value for t in available_types]}")
        
        # Try to create a client
        client = get_claude_client()
        print(f"✅ Created client: {type(client).__name__}")
        
    except Exception as e:
        print(f"❌ Claude client creation failed: {e}")

def main():
    """Run all diagnostic checks."""
    print("🔍 Workflow Failure Diagnostic")
    print("=" * 50)
    
    check_environment()
    claude_ok = check_claude_cli()
    check_python_imports()
    check_file_paths()
    test_workflow_components()
    
    if claude_ok:
        test_claude_client_creation()
    
    print("\n" + "=" * 50)
    print("🏁 Diagnostic Complete")
    print("\nNext steps:")
    print("1. Fix any ❌ issues shown above")
    print("2. Check GitHub Actions logs for detailed error messages")
    print("3. Re-run the workflow after fixing issues")

if __name__ == "__main__":
    main()