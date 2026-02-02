#!/bin/bash

# GitHub Runner Health Check Script
# Verifies that the self-hosted runner is properly configured and operational

set -e

# Configuration
RUNNER_DIR="$HOME/actions-runner"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_check() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

# Check if runner directory exists
check_runner_directory() {
    log_check "Checking runner directory..."
    
    if [ ! -d "$RUNNER_DIR" ]; then
        log_error "Runner directory not found: $RUNNER_DIR"
        return 1
    fi
    
    if [ ! -f "$RUNNER_DIR/run.sh" ]; then
        log_error "Runner executable not found: $RUNNER_DIR/run.sh"
        return 1
    fi
    
    log_info "Runner directory exists: $RUNNER_DIR"
    return 0
}

# Check runner configuration
check_runner_config() {
    log_check "Checking runner configuration..."
    
    if [ ! -f "$RUNNER_DIR/.runner" ]; then
        log_error "Runner configuration file not found: $RUNNER_DIR/.runner"
        return 1
    fi
    
    # Check if runner is configured with correct labels
    if grep -q "solops-local" "$RUNNER_DIR/.runner" 2>/dev/null; then
        log_info "Runner configured with correct labels"
    else
        log_warn "Runner labels may not be configured correctly"
    fi
    
    return 0
}

# Check dependencies
check_dependencies() {
    log_check "Checking dependencies..."
    
    local errors=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version)
        log_info "Python: $python_version"
    else
        log_error "Python 3 not found"
        errors=$((errors + 1))
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        git_version=$(git --version)
        log_info "Git: $git_version"
    else
        log_error "Git not found"
        errors=$((errors + 1))
    fi
    
    # Check jq
    if command -v jq &> /dev/null; then
        jq_version=$(jq --version)
        log_info "jq: $jq_version"
    else
        log_error "jq not found"
        errors=$((errors + 1))
    fi
    
    # Check Claude CLI
    if command -v claude &> /dev/null; then
        if claude --help > /dev/null 2>&1; then
            log_info "Claude CLI: Available and functional"
        else
            log_warn "Claude CLI: Available but may need authentication"
        fi
    else
        log_error "Claude CLI not found"
        errors=$((errors + 1))
    fi
    
    return $errors
}

# Check environment configuration
check_environment() {
    log_check "Checking environment configuration..."
    
    if [ -f "$RUNNER_DIR/.env" ]; then
        log_info "Environment file exists: $RUNNER_DIR/.env"
        
        # Check for required variables (without revealing values)
        if grep -q "GITHUB_TOKEN=" "$RUNNER_DIR/.env"; then
            log_info "GITHUB_TOKEN configured"
        else
            log_warn "GITHUB_TOKEN not found in .env file"
        fi
        
        if grep -q "PYTHONPATH=" "$RUNNER_DIR/.env"; then
            log_info "PYTHONPATH configured"
        else
            log_warn "PYTHONPATH not found in .env file"
        fi
    else
        log_warn "Environment file not found: $RUNNER_DIR/.env"
    fi
}

# Check runner service status
check_service_status() {
    log_check "Checking runner service status..."
    
    if [ -f "$RUNNER_DIR/.service" ]; then
        log_info "Runner is configured as a service"
        
        # Try to check service status
        if sudo "$RUNNER_DIR/svc.sh" status > /dev/null 2>&1; then
            log_info "Runner service is running"
        else
            log_warn "Runner service may not be running"
        fi
    else
        log_info "Runner is not configured as a service (manual execution)"
    fi
}

# Check runner connectivity
check_connectivity() {
    log_check "Checking GitHub connectivity..."
    
    # Test GitHub API connectivity
    if curl -s --connect-timeout 10 https://api.github.com > /dev/null; then
        log_info "GitHub API is reachable"
    else
        log_error "Cannot reach GitHub API"
        return 1
    fi
    
    # Test Claude API connectivity (if configured)
    if curl -s --connect-timeout 10 https://api.anthropic.com > /dev/null; then
        log_info "Claude API is reachable"
    else
        log_warn "Cannot reach Claude API (may not be required)"
    fi
    
    return 0
}

# Test basic functionality
test_functionality() {
    log_check "Testing basic functionality..."
    
    local errors=0
    
    # Test Python import
    if python3 -c "import json, sys, os" 2>/dev/null; then
        log_info "Python basic imports working"
    else
        log_error "Python basic imports failed"
        errors=$((errors + 1))
    fi
    
    # Test jq processing
    if echo '{"test": "success"}' | jq '.test' > /dev/null 2>&1; then
        log_info "jq JSON processing working"
    else
        log_error "jq JSON processing failed"
        errors=$((errors + 1))
    fi
    
    # Test Claude CLI basic command
    if claude --help > /dev/null 2>&1; then
        log_info "Claude CLI basic command working"
    else
        log_warn "Claude CLI basic command failed (may need authentication)"
    fi
    
    return $errors
}

# Generate health report
generate_report() {
    echo ""
    echo "=================================="
    echo "GitHub Runner Health Check Report"
    echo "=================================="
    echo "Timestamp: $(date)"
    echo "Runner Directory: $RUNNER_DIR"
    echo ""
    
    local total_errors=0
    
    if check_runner_directory; then
        echo "✅ Runner Directory: OK"
    else
        echo "❌ Runner Directory: FAILED"
        total_errors=$((total_errors + 1))
    fi
    
    if check_runner_config; then
        echo "✅ Runner Configuration: OK"
    else
        echo "❌ Runner Configuration: FAILED"
        total_errors=$((total_errors + 1))
    fi
    
    dep_errors=$(check_dependencies)
    if [ $dep_errors -eq 0 ]; then
        echo "✅ Dependencies: OK"
    else
        echo "❌ Dependencies: $dep_errors errors"
        total_errors=$((total_errors + dep_errors))
    fi
    
    check_environment
    echo "ℹ️  Environment: Checked (see details above)"
    
    check_service_status
    echo "ℹ️  Service Status: Checked (see details above)"
    
    if check_connectivity; then
        echo "✅ Connectivity: OK"
    else
        echo "❌ Connectivity: FAILED"
        total_errors=$((total_errors + 1))
    fi
    
    func_errors=$(test_functionality)
    if [ $func_errors -eq 0 ]; then
        echo "✅ Basic Functionality: OK"
    else
        echo "❌ Basic Functionality: $func_errors errors"
        total_errors=$((total_errors + func_errors))
    fi
    
    echo ""
    echo "=================================="
    if [ $total_errors -eq 0 ]; then
        echo "🎉 Overall Status: HEALTHY"
        echo "The runner appears to be properly configured and operational."
    else
        echo "⚠️  Overall Status: ISSUES DETECTED ($total_errors total)"
        echo "Please review the errors above and fix any issues."
    fi
    echo "=================================="
    
    return $total_errors
}

# Main execution
main() {
    echo "GitHub Actions Runner Health Check"
    echo "=================================="
    echo ""
    
    generate_report
    
    local exit_code=$?
    
    echo ""
    echo "Health check completed."
    
    if [ $exit_code -eq 0 ]; then
        echo "Runner is ready for use!"
    else
        echo "Please address the issues before using the runner."
    fi
    
    exit $exit_code
}

# Run main function
main "$@"