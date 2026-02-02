#!/bin/bash

# Self-Hosted GitHub Runner Setup Script
# This script automates the setup of a self-hosted GitHub Actions runner
# for the Self-Evolving Web Application

set -e

# Configuration
RUNNER_VERSION="2.311.0"
RUNNER_DIR="$HOME/actions-runner"
REPO_URL=""
REGISTRATION_TOKEN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if running on macOS
check_os() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script is designed for macOS. Please adapt for your OS."
        exit 1
    fi
    log_info "Running on macOS"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log_error "Git is required but not installed"
        exit 1
    fi
    
    git_version=$(git --version)
    log_info "Git version: $git_version"
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_warn "jq is not installed. Installing via Homebrew..."
        if command -v brew &> /dev/null; then
            brew install jq
        else
            log_error "Homebrew not found. Please install jq manually: https://stedolan.github.io/jq/"
            exit 1
        fi
    fi
    
    jq_version=$(jq --version)
    log_info "jq version: $jq_version"
    
    # Check Claude CLI
    if ! command -v claude &> /dev/null; then
        log_error "Claude CLI is required but not installed"
        log_error "Please install Claude CLI: https://docs.anthropic.com/claude/docs/cli"
        exit 1
    fi
    
    claude_version=$(claude --version 2>/dev/null || echo "Claude CLI available")
    log_info "Claude CLI: $claude_version"
}

# Get user input for configuration
get_configuration() {
    log_info "Getting configuration..."
    
    if [ -z "$REPO_URL" ]; then
        read -p "Enter your GitHub repository URL (e.g., https://github.com/owner/repo): " REPO_URL
    fi
    
    if [ -z "$REGISTRATION_TOKEN" ]; then
        echo "To get a registration token:"
        echo "1. Go to your GitHub repository"
        echo "2. Navigate to Settings > Actions > Runners"
        echo "3. Click 'New self-hosted runner'"
        echo "4. Copy the token from the configuration command"
        echo ""
        read -p "Enter your GitHub runner registration token: " REGISTRATION_TOKEN
    fi
}

# Download and setup runner
setup_runner() {
    log_info "Setting up GitHub Actions runner..."
    
    # Create runner directory
    mkdir -p "$RUNNER_DIR"
    cd "$RUNNER_DIR"
    
    # Download runner if not already present
    if [ ! -f "actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz" ]; then
        log_info "Downloading GitHub Actions runner v${RUNNER_VERSION}..."
        curl -o "actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz" -L \
            "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz"
    fi
    
    # Extract if not already extracted
    if [ ! -f "run.sh" ]; then
        log_info "Extracting runner..."
        tar xzf "./actions-runner-osx-x64-${RUNNER_VERSION}.tar.gz"
    fi
    
    # Configure runner
    log_info "Configuring runner..."
    ./config.sh \
        --url "$REPO_URL" \
        --token "$REGISTRATION_TOKEN" \
        --labels "self-hosted,solops-local" \
        --name "solops-runner" \
        --work "_work" \
        --replace
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    log_info "Environment variables can be set globally in your shell profile:"
    log_info "Add these to ~/.zshrc or ~/.bashrc:"
    echo ""
    echo "export GITHUB_TOKEN=your_github_token_here"
    echo "export PYTHONPATH=$(pwd)/app:$(pwd)"
    echo "export REPO_ROOT=$(pwd)"
    echo ""
    log_info "Then run: source ~/.zshrc"
    echo ""
    log_info "Alternatively, you can create a local .env file (optional):"
    
    # Create environment file template (optional)
    cat > "$RUNNER_DIR/.env.example" << EOF
# Runner Environment Configuration (OPTIONAL)
# These can be set globally in ~/.zshrc instead

# GitHub token for API access (only if not already in shell environment)
# GITHUB_TOKEN=your_github_token_here

# Python path for the repository (update with actual project path)
PYTHONPATH=$(pwd)/app:$(pwd)

# Repository root (update with actual project path)
REPO_ROOT=$(pwd)
EOF
    
    log_info "Optional .env example created at $RUNNER_DIR/.env.example"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    else
        log_warn "requirements.txt not found in current directory"
        log_warn "Make sure to install project dependencies manually"
    fi
}

# Test runner setup
test_setup() {
    log_info "Testing runner setup..."
    
    cd "$RUNNER_DIR"
    
    # Test basic functionality
    log_info "Testing Python..."
    python3 -c "import sys; print(f'Python {sys.version}')"
    
    log_info "Testing jq..."
    echo '{"test": "success"}' | jq '.test'
    
    log_info "Testing Claude CLI..."
    if claude --help > /dev/null 2>&1; then
        log_info "Claude CLI is working"
    else
        log_warn "Claude CLI test failed - please verify authentication"
    fi
    
    log_info "Runner setup test completed"
}

# Create service configuration
create_service_config() {
    log_info "Creating service configuration..."
    
    cat > "$RUNNER_DIR/install-service.sh" << 'EOF'
#!/bin/bash
# Install runner as a system service

cd "$(dirname "$0")"

echo "Installing GitHub Actions runner as service..."
sudo ./svc.sh install

echo "Starting service..."
sudo ./svc.sh start

echo "Service status:"
sudo ./svc.sh status

echo "Service installed successfully!"
echo "To manage the service:"
echo "  Start:   sudo ./svc.sh start"
echo "  Stop:    sudo ./svc.sh stop"
echo "  Status:  sudo ./svc.sh status"
echo "  Uninstall: sudo ./svc.sh uninstall"
EOF
    
    chmod +x "$RUNNER_DIR/install-service.sh"
    
    log_info "Service configuration created at $RUNNER_DIR/install-service.sh"
}

# Main execution
main() {
    log_info "Starting GitHub Actions runner setup..."
    
    check_os
    check_prerequisites
    get_configuration
    setup_runner
    setup_environment
    install_dependencies
    test_setup
    create_service_config
    
    log_info "Runner setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Set environment variables in ~/.zshrc:"
    echo "   export GITHUB_TOKEN=your_token"
    echo "   export PYTHONPATH=/path/to/self-evolving-app/app:/path/to/self-evolving-app"
    echo "   export REPO_ROOT=/path/to/self-evolving-app"
    echo "2. Run: source ~/.zshrc"
    echo "3. Start the runner: cd $RUNNER_DIR && ./run.sh"
    echo "4. Or install as service: cd $RUNNER_DIR && ./install-service.sh"
    echo ""
    echo "Runner directory: $RUNNER_DIR"
    echo "Configuration: Repository-scoped with labels [self-hosted, solops-local]"
}

# Run main function
main "$@"