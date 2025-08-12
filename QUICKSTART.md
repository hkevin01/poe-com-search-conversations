# 🚀 Quick Start - Clean Project Structure

## Running the Application

### Simple Start (Recommended)
```bash
# One command to test everything and launch GUI
./run.sh
```

### Manual Commands
```bash
# Setup and launch with data
python main.py launch

# Just launch GUI
python main.py gui

# Run tests
python main.py test
```

## Project Structure (Cleaned)

```
📁 poe-com-search-conversations/
├── 📄 run.sh                    # 🚀 ONE-CLICK START SCRIPT
├── 📄 main.py                   # Clean launcher (delegates to scripts/)
├── 📄 README.md                 # Full documentation
├── 📄 cleanup_root.sh           # Root folder cleanup utility
├── 📁 src/                      # Core application modules
├── 📁 scripts/                  # Organized tools
│   ├── 📁 development/          # GUI launchers
│   ├── 📁 setup/               # Environment setup
│   ├── 📁 testing/             # Test utilities
│   ├── 📁 maintenance/         # Database utilities
│   ├── 📁 deprecated/          # Moved old files
│   └── 📄 export_cli.py        # Export pipeline
├── 📁 tests/                   # Test suites
├── 📁 config/                  # Configuration
├── 📁 docs/                    # Documentation
├── 📁 templates/               # FastAPI templates
├── 📁 static/                  # Web assets
└── 📁 storage/                 # Database files
```

## What run.sh Does

1. ✅ **Environment Setup** - Checks Python, creates venv, installs deps
2. ✅ **Configuration Check** - Verifies poe_tokens.json exists
3. ✅ **System Tests** - Tests core imports and functionality
4. ✅ **Connection Test** - Verifies Poe.com authentication
5. ✅ **Extraction Test** - Tests conversation scraping
6. ✅ **Export Pipeline** - Tests new export/catalog system
7. 🚀 **Launch GUI** - Starts the web interface

## Key Features

- **Zero-config start** with `./run.sh`
- **Comprehensive testing** before GUI launch
- **Clean project structure** with organized scripts
- **New export pipeline** with SQLite catalog
- **FastAPI web interface** instead of PyQt6

## If Tests Fail

The script will warn you but offer to continue anyway. Common issues:

- **No config**: Edit `config/poe_tokens.json` with your Poe.com cookies
- **Connection fail**: Check your p-b token is current
- **Import errors**: Run `pip install -r requirements.txt`

## Development

```bash
# Individual test scripts
python scripts/testing/test_system.py
python scripts/testing/test_login.py
python scripts/testing/test_export_cli.py

# Export pipeline
python scripts/export_cli.py --help

# Maintenance
python scripts/maintenance/check_database.py
```
