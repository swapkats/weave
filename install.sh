#!/bin/bash
# Weave CLI Installation Script
# Usage: curl -fsSL https://weave.dev/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="weave/weave-cli"
BRANCH="main"
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/archive/refs/heads/${BRANCH}.zip"
INSTALL_DIR="${HOME}/.weave-cli"
PYTHON_MIN_VERSION="3.9"

# Print colored message
print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}┌────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}│                                        │${NC}"
    echo -e "${BLUE}│  ${CYAN}🧵  Weave CLI Installation${BLUE}       │${NC}"
    echo -e "${BLUE}│                                        │${NC}"
    echo -e "${BLUE}└────────────────────────────────────────┘${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."

    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        print_info "Please install Python ${PYTHON_MIN_VERSION} or higher"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Found Python ${PYTHON_VERSION}"

    # Basic version check (comparing major.minor)
    MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]); then
        print_warning "Python ${PYTHON_VERSION} found, but ${PYTHON_MIN_VERSION}+ recommended"
    fi
}

# Check curl or wget
check_downloader() {
    print_info "Checking download tools..."

    if command_exists curl; then
        DOWNLOADER="curl"
        print_success "curl is available"
    elif command_exists wget; then
        DOWNLOADER="wget"
        print_success "wget is available"
    else
        print_error "Neither curl nor wget is installed"
        print_info "Please install curl or wget first"
        exit 1
    fi
}

# Check pip
check_pip() {
    print_info "Checking pip installation..."

    if ! command_exists pip3 && ! python3 -m pip --version >/dev/null 2>&1; then
        print_error "pip is not installed"
        print_info "Please install pip first"
        exit 1
    fi

    print_success "pip is available"
}

# Download file
download_file() {
    local url=$1
    local output=$2

    if [ "$DOWNLOADER" = "curl" ]; then
        curl -fsSL "$url" -o "$output"
    else
        wget -q "$url" -O "$output"
    fi
}

# Install Weave
install_weave() {
    print_info "Installing Weave CLI..."

    # Check if already installed
    if command_exists weave; then
        print_warning "Weave CLI is already installed"
        read -p "Reinstall? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Keeping existing installation"
            return
        fi
        pip3 uninstall -y weave-cli 2>/dev/null || true
    fi

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Download source code archive
    print_info "Downloading from GitHub..."
    download_file "$DOWNLOAD_URL" "weave.zip"
    print_success "Downloaded source code"

    # Extract archive
    print_info "Extracting files..."
    if command_exists unzip; then
        unzip -q weave.zip
    else
        print_error "unzip is not installed"
        print_info "Please install unzip: sudo apt install unzip"
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    # Find extracted directory
    EXTRACT_DIR=$(find . -maxdepth 1 -type d -name "weave-cli-*" | head -1)

    if [ -z "$EXTRACT_DIR" ]; then
        print_error "Failed to extract source code"
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    # Install package
    print_info "Installing package..."
    cd "$EXTRACT_DIR"
    pip3 install --quiet .
    print_success "Weave CLI installed"

    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Install optional features
install_optional() {
    echo ""
    print_info "Optional Features"
    echo ""

    read -p "Install LLM support (OpenAI, Anthropic)? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installing LLM support..."
        pip3 install --quiet openai anthropic
        print_success "LLM support installed"
    fi

    read -p "Install deployment support (AWS, GCP, Docker)? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installing deployment support..."
        pip3 install --quiet boto3 docker
        print_success "Deployment support installed"
    fi

    read -p "Install development tools (auto-reload)? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "Installing development tools..."
        pip3 install --quiet watchdog
        print_success "Development tools installed"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."

    if command_exists weave; then
        VERSION=$(weave --version 2>&1 || echo "unknown")
        print_success "Weave CLI is installed: $VERSION"
    else
        print_warning "weave command not found in PATH"
        print_info "You may need to restart your shell or add to PATH"
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    echo -e "${GREEN}┌────────────────────────────────────────┐${NC}"
    echo -e "${GREEN}│  Installation Complete! 🎉            │${NC}"
    echo -e "${GREEN}└────────────────────────────────────────┘${NC}"
    echo ""
    print_info "Next Steps:"
    echo ""
    echo "  1. Verify installation:"
    echo -e "     ${CYAN}weave --version${NC}"
    echo ""
    echo "  2. Run setup wizard:"
    echo -e "     ${CYAN}weave setup${NC}"
    echo ""
    echo "  3. Install shell completion:"
    echo -e "     ${CYAN}weave completion bash --install${NC}"
    echo ""
    echo "  4. Create example project:"
    echo -e "     ${CYAN}weave init${NC}"
    echo ""
    echo "  5. Test with mock execution:"
    echo -e "     ${CYAN}weave apply${NC}"
    echo ""
    echo -e "${BLUE}📚 Documentation:${NC} https://docs.weave.dev"
    echo -e "${BLUE}💬 Community:${NC}     https://github.com/weave/weave-cli"
    echo ""
}

# Main installation flow
main() {
    print_header

    # Pre-flight checks
    check_python
    check_downloader
    check_pip

    echo ""

    # Install
    install_weave

    # Optional features
    install_optional

    echo ""

    # Verify
    verify_installation

    # Next steps
    show_next_steps
}

# Run main function
main
