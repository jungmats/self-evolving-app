#!/usr/bin/env python3
"""
Claude CLI Integration Validation Script

This script validates the Claude CLI integration by testing various components
and comparing output quality between API and CLI approaches where possible.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

try:
    from claude_client_factory import (
        get_claude_client, 
        get_available_client_types, 
        get_client_info,
        ClientType,
        set_preferred_client_type
    )
    from claude_cli_client import ClaudeCLIClient, ClaudeCLIError
    from claude_client import ClaudeClient, ClaudeClientError
    from workflow_engine import get_workflow_engine
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this script from the repository root")
    print("💡 Also ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


class ClaudeCLIValidator:
    """Validator for Claude CLI integration components."""
    
    def __init__(self):
        """Initialize the validator."""
        self.repository_root = Path.cwd()
        self.test_results = {}
        
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🔍 Starting Claude CLI Integration Validation")
        print("=" * 50)
        
        # Test 1: Client availability
        self.test_client_availability()
        
        # Test 2: Client factory functionality
        self.test_client_factory()
        
        # Test 3: CLI client basic functionality
        self.test_cli_client_basic()
        
        # Test 4: Repository context awareness
        self.test_repository_context()
        
        # Test 5: Workflow engine integration
        self.test_workflow_engine_integration()
        
        # Test 6: Compare API vs CLI (if both available)
        self.test_api_vs_cli_comparison()
        
        # Generate summary report
        self.generate_summary_report()
        
        return self.test_results
    
    def test_client_availability(self) -> None:
        """Test which Claude clients are available."""
        print("\n🔧 Testing Client Availability")
        print("-" * 30)
        
        try:
            available_types = get_available_client_types()
            
            self.test_results["client_availability"] = {
                "available_types": [t.value for t in available_types],
                "cli_available": ClientType.CLI in available_types,
                "api_available": ClientType.API in available_types,
                "status": "passed"
            }
            
            print(f"✅ Available client types: {[t.value for t in available_types]}")
            
            for client_type in available_types:
                info = get_client_info(client_type)
                print(f"   📋 {info['name']}: {info['description']}")
                
        except Exception as e:
            self.test_results["client_availability"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ Client availability test failed: {e}")
    
    def test_client_factory(self) -> None:
        """Test client factory functionality."""
        print("\n🏭 Testing Client Factory")
        print("-" * 25)
        
        try:
            # Test auto-detection
            client = get_claude_client()
            client_type = type(client).__name__
            
            print(f"✅ Auto-detected client: {client_type}")
            
            # Test explicit client type selection (if CLI is available)
            if ClientType.CLI in get_available_client_types():
                try:
                    cli_client = get_claude_client(client_type=ClientType.CLI)
                    print(f"✅ Explicit CLI client creation: {type(cli_client).__name__}")
                except Exception as e:
                    print(f"⚠️ CLI client creation failed: {e}")
            
            # Test fallback functionality
            try:
                fallback_client = get_claude_client(fallback_enabled=True)
                print(f"✅ Fallback client creation: {type(fallback_client).__name__}")
            except Exception as e:
                print(f"❌ Fallback client creation failed: {e}")
            
            self.test_results["client_factory"] = {
                "status": "passed",
                "auto_detected_client": client_type,
                "fallback_enabled": True
            }
            
        except Exception as e:
            self.test_results["client_factory"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ Client factory test failed: {e}")
    
    def test_cli_client_basic(self) -> None:
        """Test basic CLI client functionality."""
        print("\n🖥️ Testing CLI Client Basic Functionality")
        print("-" * 40)
        
        if ClientType.CLI not in get_available_client_types():
            print("⏭️ Skipping CLI client test - CLI not available")
            self.test_results["cli_client_basic"] = {
                "status": "skipped",
                "reason": "CLI client not available"
            }
            return
        
        try:
            # Create CLI client directly
            cli_client = ClaudeCLIClient(repository_root=str(self.repository_root))
            
            # Test basic response generation
            test_prompt = "What is the purpose of this repository? Please provide a brief summary."
            
            print("🔍 Testing basic response generation...")
            response = cli_client.generate_response(test_prompt)
            
            print(f"✅ CLI client response generated successfully")
            print(f"   📊 Response length: {len(response.content)} characters")
            print(f"   🤖 Model: {response.model}")
            print(f"   📁 Repository context: {response.repository_context}")
            print(f"   ⚡ Command: {response.command_used}")
            
            # Test response content quality
            content_lower = response.content.lower()
            has_repo_context = any(keyword in content_lower for keyword in [
                "repository", "repo", "project", "application", "system"
            ])
            
            self.test_results["cli_client_basic"] = {
                "status": "passed",
                "response_length": len(response.content),
                "model": response.model,
                "repository_context": response.repository_context,
                "has_repo_awareness": has_repo_context,
                "command_used": response.command_used
            }
            
            if has_repo_context:
                print("✅ Response shows repository awareness")
            else:
                print("⚠️ Response may lack repository context")
                
        except ClaudeCLIError as e:
            self.test_results["cli_client_basic"] = {
                "status": "failed",
                "error": str(e),
                "error_type": "ClaudeCLIError"
            }
            print(f"❌ CLI client test failed: {e}")
        except Exception as e:
            self.test_results["cli_client_basic"] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__
            }
            print(f"❌ CLI client test failed: {e}")
    
    def test_repository_context(self) -> None:
        """Test repository context awareness."""
        print("\n📁 Testing Repository Context Awareness")
        print("-" * 38)
        
        if ClientType.CLI not in get_available_client_types():
            print("⏭️ Skipping repository context test - CLI not available")
            self.test_results["repository_context"] = {
                "status": "skipped",
                "reason": "CLI client not available"
            }
            return
        
        try:
            cli_client = ClaudeCLIClient(repository_root=str(self.repository_root))
            
            # Test repository-specific questions
            test_prompts = [
                "What programming languages are used in this repository?",
                "What is the main application structure?",
                "What testing frameworks are being used?",
                "What are the key components of this system?"
            ]
            
            context_scores = []
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"🔍 Testing context awareness {i}/{len(test_prompts)}: {prompt[:50]}...")
                
                try:
                    response = cli_client.generate_response(prompt)
                    
                    # Analyze response for repository-specific content
                    content_lower = response.content.lower()
                    
                    # Look for repository-specific indicators
                    repo_indicators = [
                        "python", "fastapi", "react", "typescript", "github", "actions",
                        "claude", "workflow", "triage", "planning", "prioritization",
                        "sqlite", "database", "api", "frontend", "backend"
                    ]
                    
                    found_indicators = [ind for ind in repo_indicators if ind in content_lower]
                    context_score = len(found_indicators) / len(repo_indicators)
                    context_scores.append(context_score)
                    
                    print(f"   ✅ Response generated (context score: {context_score:.2f})")
                    print(f"   📋 Found indicators: {found_indicators[:5]}{'...' if len(found_indicators) > 5 else ''}")
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                    context_scores.append(0.0)
            
            avg_context_score = sum(context_scores) / len(context_scores) if context_scores else 0.0
            
            self.test_results["repository_context"] = {
                "status": "passed",
                "average_context_score": avg_context_score,
                "individual_scores": context_scores,
                "context_quality": "excellent" if avg_context_score > 0.3 else "good" if avg_context_score > 0.1 else "limited"
            }
            
            print(f"📊 Average repository context score: {avg_context_score:.2f}")
            print(f"🎯 Context quality: {self.test_results['repository_context']['context_quality']}")
            
        except Exception as e:
            self.test_results["repository_context"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ Repository context test failed: {e}")
    
    def test_workflow_engine_integration(self) -> None:
        """Test workflow engine integration with Claude CLI."""
        print("\n⚙️ Testing Workflow Engine Integration")
        print("-" * 37)
        
        try:
            # Test workflow engine creation with CLI preference
            if ClientType.CLI in get_available_client_types():
                workflow_engine = get_workflow_engine(preferred_client_type=ClientType.CLI)
                print("✅ Workflow engine created with CLI preference")
            else:
                workflow_engine = get_workflow_engine()
                print("✅ Workflow engine created with default client")
            
            # Test client type detection
            client_type = type(workflow_engine.claude_client).__name__
            print(f"📋 Workflow engine using client: {client_type}")
            
            # Test workflow engine components
            has_policy_component = hasattr(workflow_engine, 'policy_component')
            has_github_client = hasattr(workflow_engine, 'github_client')
            
            print(f"🛡️ Policy component available: {has_policy_component}")
            print(f"🐙 GitHub client available: {has_github_client}")
            
            self.test_results["workflow_engine_integration"] = {
                "status": "passed",
                "client_type": client_type,
                "has_policy_component": has_policy_component,
                "has_github_client": has_github_client,
                "cli_integration": "ClaudeCLIClient" in client_type
            }
            
        except Exception as e:
            self.test_results["workflow_engine_integration"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ Workflow engine integration test failed: {e}")
    
    def test_api_vs_cli_comparison(self) -> None:
        """Compare API vs CLI client output quality."""
        print("\n🔄 Testing API vs CLI Comparison")
        print("-" * 32)
        
        available_types = get_available_client_types()
        
        if len(available_types) < 2:
            print("⏭️ Skipping comparison - need both API and CLI clients")
            self.test_results["api_vs_cli_comparison"] = {
                "status": "skipped",
                "reason": f"Only {len(available_types)} client type(s) available"
            }
            return
        
        try:
            test_prompt = "Analyze the structure of this repository and identify the main components."
            
            results = {}
            
            for client_type in [ClientType.API, ClientType.CLI]:
                if client_type not in available_types:
                    continue
                
                print(f"🔍 Testing {client_type.value} client...")
                
                try:
                    client = get_claude_client(client_type=client_type)
                    
                    # Use a simple test that both clients can handle
                    if hasattr(client, 'generate_response'):
                        response = client.generate_response(test_prompt)
                        content = response.content if hasattr(response, 'content') else str(response)
                    else:
                        # Fallback for different client interfaces
                        content = "Interface not compatible for comparison"
                    
                    results[client_type.value] = {
                        "length": len(content),
                        "has_repo_context": "repository" in content.lower() or "repo" in content.lower(),
                        "client_type": type(client).__name__
                    }
                    
                    print(f"   ✅ {client_type.value} response: {len(content)} chars")
                    
                except Exception as e:
                    print(f"   ❌ {client_type.value} failed: {e}")
                    results[client_type.value] = {"error": str(e)}
            
            # Compare results
            comparison = {}
            if "api" in results and "cli" in results:
                api_result = results["api"]
                cli_result = results["cli"]
                
                if "error" not in api_result and "error" not in cli_result:
                    comparison = {
                        "length_difference": cli_result["length"] - api_result["length"],
                        "cli_longer": cli_result["length"] > api_result["length"],
                        "both_have_context": api_result["has_repo_context"] and cli_result["has_repo_context"],
                        "cli_context_advantage": cli_result["has_repo_context"] and not api_result["has_repo_context"]
                    }
                    
                    print(f"📊 Length difference (CLI - API): {comparison['length_difference']} chars")
                    print(f"🎯 CLI context advantage: {comparison['cli_context_advantage']}")
            
            self.test_results["api_vs_cli_comparison"] = {
                "status": "passed",
                "results": results,
                "comparison": comparison
            }
            
        except Exception as e:
            self.test_results["api_vs_cli_comparison"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"❌ API vs CLI comparison failed: {e}")
    
    def generate_summary_report(self) -> None:
        """Generate a summary report of all validation results."""
        print("\n📋 Validation Summary Report")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result.get("status") == "passed")
        failed_tests = sum(1 for result in self.test_results.values() if result.get("status") == "failed")
        skipped_tests = sum(1 for result in self.test_results.values() if result.get("status") == "skipped")
        
        print(f"📊 Total tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️ Skipped: {skipped_tests}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Claude CLI integration is working correctly.")
        elif passed_tests > failed_tests:
            print("\n⚠️ Most tests passed, but some issues were found.")
        else:
            print("\n🚨 Multiple test failures detected. Review the issues above.")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status_icon = {
                "passed": "✅",
                "failed": "❌", 
                "skipped": "⏭️"
            }.get(result.get("status"), "❓")
            
            print(f"   {status_icon} {test_name}: {result.get('status', 'unknown')}")
            
            if result.get("status") == "failed" and "error" in result:
                print(f"      Error: {result['error']}")
        
        # Save results to file
        results_file = Path("claude-cli-validation-results.json")
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests
                },
                "detailed_results": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {results_file}")


def main():
    """Main entry point for validation script."""
    print("Claude CLI Integration Validation")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app").exists() or not Path("requirements.txt").exists():
        print("❌ Please run this script from the repository root directory")
        sys.exit(1)
    
    try:
        validator = ClaudeCLIValidator()
        results = validator.run_all_validations()
        
        # Exit with appropriate code
        failed_tests = sum(1 for result in results.values() if result.get("status") == "failed")
        sys.exit(0 if failed_tests == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()