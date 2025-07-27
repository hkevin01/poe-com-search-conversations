# Test Suite

This directory contains test files for the Poe.com conversation search tool.

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_conversations.py -v
```

## Test Structure

- `test_conversations.py` - Tests for conversation extraction logic
- `test_config.py` - Tests for configuration loading
- `test_browser.py` - Tests for browser setup and automation

## Requirements

Install test dependencies:
```bash
pip install pytest pytest-mock
```