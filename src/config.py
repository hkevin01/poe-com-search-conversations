#!/usr/bin/env python3
"""
Path Configuration Helper
Provides consistent path configuration across all project components
"""

import os

# Project root directory
PROJECT_ROOT = "/home/kevin/Projects/poe-com-search-conversations"

# Configuration paths
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
TOKENS_FILE = os.path.join(CONFIG_DIR, "poe_tokens.json")
TOKENS_EXAMPLE = os.path.join(CONFIG_DIR, "poe_tokens.json.example")

# Database paths
DATABASE_FILE = os.path.join(PROJECT_ROOT, "conversations.db")

# Source paths
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
GUI_DIR = os.path.join(SRC_DIR, "gui")
TESTS_DIR = os.path.join(PROJECT_ROOT, "tests")

# Output paths
EXPORTS_DIR = os.path.join(PROJECT_ROOT, "exports")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Ensure directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    for directory in [CONFIG_DIR, EXPORTS_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)

def get_config_path():
    """Get the path to the tokens configuration file."""
    return TOKENS_FILE

def get_database_path():
    """Get the path to the database file."""
    return DATABASE_FILE

def get_project_root():
    """Get the project root directory."""
    return PROJECT_ROOT

# Auto-create directories on import
ensure_directories()