# Project Context for GitHub Copilot

## Project Overview

This is a Python web scraping tool for extracting conversations from Poe.com using Selenium automation.

## Key Components

### Main Script: `src/quick_list_conversations.py`
- **Purpose**: Automate browser to list all conversations from a Poe.com account
- **Technology**: Python + Selenium WebDriver
- **Authentication**: Uses Poe.com cookies (p-b, p-lat, formkey)
- **Output**: JSON file with conversation titles and URLs

### Core Functions
1. `setup_browser()` - Configure Chrome WebDriver with appropriate options
2. `load_tokens()` - Load authentication tokens from JSON config
3. `set_cookies()` - Authenticate with Poe.com using stored cookies
4. `extract_conversations()` - Scrape conversation list from the page
5. `scroll_to_bottom()` - Handle lazy-loaded content
6. `print_and_save()` - Output results to console and JSON file

## Technical Details

### Dependencies
- **selenium**: Web automation framework
- **webdriver-manager**: Automatic ChromeDriver management
- **json/os/time**: Standard library utilities

### Browser Automation Strategy
- Uses Chrome in headless mode by default
- Handles dynamic content loading through scrolling
- Multiple extraction methods for robustness:
  - Direct `/chat/` link detection
  - Chat tile text extraction with fallback URL detection

### Data Structure
Each conversation is stored as:
```python
{
    "id": int,           # Sequential ID
    "title": str,        # Conversation title (truncated to 100 chars)
    "url": str,          # Full Poe.com conversation URL
    "method": str        # Extraction method used ("link" or "tile")
}
```

## Project Goals
1. **Reliability**: Handle Poe.com's dynamic loading and various page layouts
2. **Usability**: Simple CLI interface with clear output
3. **Maintainability**: Clean, documented code with proper error handling
4. **Security**: Safe handling of authentication tokens

## Common Patterns
- Error handling with try/finally for browser cleanup
- Configuration through external JSON files
- Timestamped output files
- Selenium best practices (implicit waits, proper selectors)

## Future Enhancements
- Conversation content extraction
- Search and filtering capabilities
- Export to different formats (CSV, HTML)
- Batch processing and scheduling