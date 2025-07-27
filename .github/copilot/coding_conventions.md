# Coding Conventions

## Python Style Guidelines

### General Principles
- Follow PEP 8 style guide
- Use clear, descriptive variable and function names
- Include docstrings for all functions and classes
- Handle errors gracefully with informative messages

### Specific Patterns Used in This Project

#### Function Documentation
```python
def function_name(param1, param2):
    """Brief description of what the function does.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
```

#### Error Handling
- Use try/finally blocks for resource cleanup (especially browser instances)
- Raise informative exceptions with context
- Print user-friendly error messages with emoji prefixes

#### Selenium Patterns
- Always use explicit waits when possible
- Use CSS selectors over XPath for better performance
- Include fallback strategies for element detection
- Set implicit waits at browser setup

#### Configuration Management
- Store sensitive data in external JSON files
- Use expanduser() for cross-platform home directory paths
- Validate required configuration at startup

#### Output Formatting
- Use emoji in console output for better UX (🚀, ✅, ❌, 💾)
- Include progress indicators and clear section dividers
- Save timestamped files to avoid overwrites

#### CLI Design
- Use argparse for command-line interface
- Provide sensible defaults
- Include help text for all options

### Code Organization

#### Import Order
1. Standard library imports
2. Third-party imports
3. Local/project imports

#### Function Order in Files
1. Setup/configuration functions
2. Core business logic functions
3. Utility/helper functions
4. Main function and CLI handling

### Variable Naming Conventions
- `driver` - Selenium WebDriver instance
- `tokens` - Dictionary of authentication tokens
- `convs` - List of conversation dictionaries
- `opts` - WebDriver options object
- Use descriptive names even for temporary variables

### Constants and Configuration
- Use UPPER_CASE for constants
- Group related configuration in dictionaries
- Use default values that work out of the box when possible