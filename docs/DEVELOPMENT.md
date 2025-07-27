# Development Guide

This document provides instructions for setting up and developing the Poe.com Conversation Manager.

## Quick Start

### Automated Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd poe-com-search-conversations
   ```

2. **Run the setup script:**
   ```bash
   # Linux/Mac - Makes scripts executable and runs setup
   chmod +x setup.sh activate.sh
   ./setup.sh
   
   # Windows
   setup.bat
   
   # Cross-platform Python version
   python setup.py
   ```

3. **Configure your tokens:**
   ```bash
   cp config/poe_tokens.json.example config/poe_tokens.json
   # Edit config/poe_tokens.json with your actual Poe.com tokens
   ```

4. **Launch the application:**
   ```bash
   # Activate environment (if not already active)
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate.bat  # Windows
   
   # Launch GUI
   python run_gui.py
   ```

### Manual Setup

If you prefer to set up manually:

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate.bat  # Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python -c "import PyQt6; print('PyQt6 installed successfully')"
   python -c "import selenium; print('Selenium installed successfully')"
   ```

## Development Workflow

### Project Structure
```
poe-com-search-conversations/
├── src/                      # Source code
│   ├── gui/                  # GUI components
│   ├── database.py           # Database operations
│   ├── enhanced_extractor.py # Conversation extraction
│   └── cli.py               # Command-line interface
├── config/                   # Configuration files
├── tests/                    # Test suite
├── docs/                     # Documentation
├── requirements.txt          # Python dependencies
├── setup.sh/bat/py          # Setup scripts
└── run_gui.py               # GUI launcher
```

### Running Components

1. **GUI Application:**
   ```bash
   python run_gui.py
   ```

2. **CLI Interface:**
   ```bash
   python src/cli.py search "python"
   python src/cli.py stats
   python src/cli.py export --format json
   ```

3. **Enhanced Extractor:**
   ```bash
   python src/enhanced_extractor.py --config config/poe_tokens.json
   ```

4. **Database Demo:**
   ```bash
   python demo_database.py
   ```

### Testing

1. **Run database tests:**
   ```bash
   python -m pytest tests/test_database.py -v
   ```

2. **Run all tests:**
   ```bash
   python -m pytest tests/ -v
   ```

### Common Development Tasks

1. **Adding new GUI features:**
   - Edit `src/gui/main_window.py`
   - Update styles in `src/gui/styles.py`
   - Test with `python run_gui.py`

2. **Database modifications:**
   - Edit `src/database.py`
   - Add tests to `tests/test_database.py`
   - Test with `python demo_database.py`

3. **Extraction improvements:**
   - Edit `src/enhanced_extractor.py`
   - Test with sample Poe.com data

## Troubleshooting

### Common Issues

1. **"PyQt6 not found" error:**
   ```bash
   pip install PyQt6
   ```

2. **"Selenium not found" error:**
   ```bash
   pip install selenium webdriver-manager
   ```

3. **ChromeDriver issues:**
   - The webdriver-manager package should handle this automatically
   - If issues persist, manually download ChromeDriver

4. **Virtual environment not activating:**
   ```bash
   # Re-create the environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Database errors:**
   ```bash
   # Delete and recreate database
   rm conversations.db
   python demo_database.py
   ```

### Getting Help

- Check the logs in `poe_extractor.log`
- Run with `--no-headless` to see browser automation
- Use the demo script to test database functionality
- Check the GitHub issues for known problems

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make changes and test thoroughly**
4. **Update documentation**
5. **Submit a pull request**

### Code Style
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where appropriate
- Write tests for new functionality

### Testing Guidelines
- Test all new features
- Ensure existing tests pass
- Add integration tests for GUI components
- Performance test with large datasets