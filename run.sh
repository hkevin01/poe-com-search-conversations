#!/bin/bash
# Poe.com Conversation Manager - Comprehensive Run Script
# Tests connection, conversation extraction, and launches GUI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check if Python is available
check_python() {
    log_step "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi

    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_success "Python ${python_version} found"
}

# Check if virtual environment exists and activate it
setup_venv() {
    log_step "Setting up virtual environment..."

    if [ ! -d "venv" ]; then
        log_warning "Virtual environment not found, creating one..."
        python3 -m venv venv
        log_success "Created virtual environment"
    fi

    # Activate virtual environment
    source venv/bin/activate
    log_success "Activated virtual environment"

    # Upgrade pip and install requirements
    log_step "Installing/updating dependencies..."
    pip install --upgrade pip > /dev/null 2>&1

    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt > /dev/null 2>&1
        log_success "Installed requirements.txt"
    fi

    if [ -f "requirements_fastapi.txt" ]; then
        pip install -r requirements_fastapi.txt > /dev/null 2>&1
        log_success "Installed FastAPI requirements"
    fi
}

# Check configuration
check_config() {
    log_step "Checking configuration..."

    if [ ! -f "config/poe_tokens.json" ]; then
        if [ -f "config/poe_tokens.json.example" ]; then
            log_warning "poe_tokens.json not found, copying from example"
            cp config/poe_tokens.json.example config/poe_tokens.json
            log_warning "Please edit config/poe_tokens.json with your actual tokens"
            log_info "Opening config file for editing..."
            ${EDITOR:-nano} config/poe_tokens.json
        else
            log_error "No configuration files found in config/"
            exit 1
        fi
    else
        log_success "Configuration file found"
    fi
}

# Test system components
test_system() {
    log_step "Running system tests..."

    # Test imports
    if python3 -c "import src.database; import src.fastapi_gui" > /dev/null 2>&1; then
        log_success "Core modules import successfully"
    else
        log_error "Failed to import core modules"
        return 1
    fi

    # Test database connectivity
    if python3 scripts/testing/test_system.py > /dev/null 2>&1; then
        log_success "System tests passed"
    else
        log_warning "Some system tests failed, but continuing..."
    fi
}

# Test connection to Poe.com
test_connection() {
    log_step "Testing connection to Poe.com..."

    if python3 scripts/testing/test_login.py > /dev/null 2>&1; then
        log_success "Connection to Poe.com successful"
        return 0
    else
        log_warning "Connection test failed - check your tokens in config/poe_tokens.json"
        return 1
    fi
}

# Test conversation extraction
test_conversation_extraction() {
    log_step "Testing conversation extraction..."

    # Test with a small limit to avoid long waits
    if timeout 30 python3 src/quick_list_conversations.py --limit 3 > /dev/null 2>&1; then
        log_success "Conversation extraction test passed"
        return 0
    else
        log_warning "Conversation extraction test failed or timed out"
        return 1
    fi
}

# Test export pipeline
test_export_pipeline() {
    log_step "Testing export pipeline..."

    # Test using the dedicated test script
    if python3 scripts/testing/test_export_cli.py; then
        log_success "Export pipeline test passed"
        return 0
    else
        log_warning "Export pipeline test failed"
        return 1
    fi
}

# Launch GUI
launch_gui() {
    log_step "Launching GUI application..."

    # Use the main launcher with launch command for best experience
    log_info "Starting Poe.com Conversation Manager GUI..."
    log_info "The GUI will open in your default web browser"
    log_info "Press Ctrl+C to stop the application"

    python3 main.py launch
}

# Main execution
main() {
    echo "=================================================="
    echo "🚀 Poe.com Conversation Manager - Startup Script"
    echo "=================================================="
    echo

    # Step 1: Check Python
    check_python
    echo

    # Step 2: Setup virtual environment
    setup_venv
    echo

    # Step 3: Check configuration
    check_config
    echo

    # Step 4: Test system
    test_system
    echo

    # Step 5: Test connection (optional)
    log_info "Testing connection and extraction capabilities..."
    connection_ok=true
    extraction_ok=true
    export_ok=true

    if ! test_connection; then
        connection_ok=false
    fi

    if ! test_conversation_extraction; then
        extraction_ok=false
    fi

    if ! test_export_pipeline; then
        export_ok=false
    fi

    echo
    echo "=================================================="
    echo "📊 Pre-launch Test Summary"
    echo "=================================================="
    echo -n "Connection to Poe.com: "
    if [ "$connection_ok" = true ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠️  FAILED${NC}"
    fi

    echo -n "Conversation Extraction: "
    if [ "$extraction_ok" = true ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠️  FAILED${NC}"
    fi

    echo -n "Export Pipeline: "
    if [ "$export_ok" = true ]; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${YELLOW}⚠️  FAILED${NC}"
    fi

    echo "=================================================="
    echo

    # Warn if tests failed but continue
    if [ "$connection_ok" = false ] || [ "$extraction_ok" = false ]; then
        log_warning "Some connectivity tests failed"
        log_info "The GUI will still launch, but you may need to check your configuration"
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Aborted by user. Please check your configuration and try again."
            exit 0
        fi
        echo
    fi

    # Step 6: Launch GUI
    launch_gui
}

# Handle interruptions gracefully
trap 'echo; log_info "Interrupted by user"; exit 130' INT

# Run main function
main "$@"
