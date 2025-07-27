# Scripts Directory

This directory contains various utility and operational scripts for the Poe.com Conversation Manager.

## Structure

```
scripts/
├── setup/              # Setup and installation scripts
├── development/        # Development utilities
├── deployment/         # Deployment and build scripts
├── testing/           # Testing utilities
└── maintenance/       # Database and system maintenance
```

## Scripts Overview

### Setup Scripts
- Environment setup and dependency installation
- Virtual environment creation and management
- Initial configuration helpers

### Development Scripts  
- Development environment launchers
- Database population and testing
- Code quality and testing utilities

### Testing Scripts
- Unit test runners
- Integration test suites
- Database consistency checks

### Maintenance Scripts
- Database backup and restore
- Log cleanup and archival
- Performance monitoring

## Usage

Most scripts are designed to be run from the project root directory:

```bash
# Setup
python scripts/setup/create_environment.py

# Development
python scripts/development/launch_with_data.py

# Testing
python scripts/testing/test_database_integrity.py

# Maintenance
python scripts/maintenance/backup_database.py
```

## Dependencies

Scripts may require:
- Python 3.8+
- Virtual environment activation
- Proper configuration files in `config/`
- Database access for some utilities