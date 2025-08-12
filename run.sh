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

# Configurable thresholds / flags
MIN_CONV_THRESHOLD=${MIN_CONV_THRESHOLD:-20}  # Auto full extraction if below
FULL_EXTRACT_REQUESTED=false
for arg in "$@"; do
    case "$arg" in
        --full-extract|--deep) FULL_EXTRACT_REQUESTED=true ;;
    esac
done
if [ "${FULL_EXTRACT:-}" = "1" ]; then
    FULL_EXTRACT_REQUESTED=true
fi

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
    # First attempt (quick headless run)
    if timeout 40 python3 src/quick_list_conversations.py --limit 3 --max-time 35 --scroll-pause 0.8 > /dev/null 2>&1; then
        log_success "Conversation extraction (quick) passed"
        return 0
    fi
    log_warning "Quick extraction attempt failed; retrying with debug + extended timing"

    # Second attempt (debug headless, slower pacing)
    if timeout 110 python3 src/quick_list_conversations.py --limit 3 --max-time 100 --scroll-pause 1.0 --debug > /dev/null 2>&1; then
        log_success "Conversation extraction (debug fallback) passed"
        return 0
    fi
    log_warning "Conversation extraction failed after fallback attempts"
    return 1
}

# Optional smoke test (more thorough but still lightweight)
test_smoke_extraction() {
    if [ ! -f scripts/testing/test_extraction_smoke.py ]; then
        return 0
    fi
    log_step "Running smoke extraction test (optional)..."
    if python3 scripts/testing/test_extraction_smoke.py > /dev/null 2>&1; then
        log_success "Smoke extraction test passed (or skipped)"
    else
        log_warning "Smoke extraction test failed"
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

# Count conversations in SQLite DB quickly (no Python project imports)
count_conversations() {
    local db="storage/conversations.db"
    if [ ! -f "$db" ]; then
        echo 0
        return
    fi
    python3 - <<'PY' 2>/dev/null || echo 0
import sqlite3, sys
try:
    con = sqlite3.connect('storage/conversations.db')
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM conversations")
    print(cur.fetchone()[0])
except Exception:
    print(0)
finally:
    try: con.close()
    except: pass
PY
}

# Attempt a fuller extraction if conversation count is low
maybe_full_extraction() {
    local count
    count=$(count_conversations)
    log_step "Database currently has $count conversations"
    if $FULL_EXTRACT_REQUESTED || [ "$count" -lt "$MIN_CONV_THRESHOLD" ]; then
        log_info "Triggering full extraction (threshold=$MIN_CONV_THRESHOLD, requested=$FULL_EXTRACT_REQUESTED)"
        # Prefer enhanced_extractor (in-depth, infinite scroll)
        if python3 src/enhanced_extractor.py --config config/poe_tokens.json > logs/full_extract_enhanced.log 2>&1; then
            log_success "Enhanced full extraction completed"
            return 0
        else
            log_warning "Enhanced extractor failed (see logs/full_extract_enhanced.log). Falling back to quick getter"
            # Fallback: quick_conversation_getter with a higher limit
            if python3 src/quick_conversation_getter.py --limit 100 > logs/full_extract_quick.log 2>&1; then
                log_success "Quick getter fallback extraction completed"
                return 0
            else
                log_warning "Fallback quick getter also failed (see logs/full_extract_quick.log)"
                return 1
            fi
        fi
    else
        log_info "Conversation count above threshold ($MIN_CONV_THRESHOLD); skipping full extraction"
    fi
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

    # Optional smoke test does not influence blocking status
    test_smoke_extraction

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

    # Optional full extraction phase
    maybe_full_extraction || log_warning "Full extraction phase encountered issues"

    # Step 6: Launch GUI
    launch_gui
}

# Handle interruptions gracefully
trap 'echo; log_info "Interrupted by user"; exit 130' INT

# Run main function
main "$@"
