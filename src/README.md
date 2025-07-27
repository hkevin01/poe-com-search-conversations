# Source Code Directory

This directory contains all the source code for the Poe.com Conversation Manager.

## Structure

```
src/
├── core/                          # Core functionality
│   ├── __init__.py
│   ├── database.py               # Database operations
│   ├── extractor.py              # Conversation extraction
│   └── config.py                 # Configuration management
├── cli/                          # Command-line interface
│   ├── __init__.py
│   ├── cli.py                    # Main CLI interface
│   └── commands.py               # CLI command implementations
├── gui/                          # Graphical user interface
│   ├── __init__.py
│   ├── main_window.py            # Main application window
│   ├── conversation_list.py      # Conversation list widget
│   ├── conversation_viewer.py    # Conversation detail viewer
│   ├── search_widget.py          # Search interface
│   └── styles.py                 # UI styles and themes
├── utils/                        # Utility functions
│   ├── __init__.py
│   ├── logging.py                # Logging configuration
│   └── helpers.py                # Helper functions
├── quick_list_conversations.py   # Phase 1 - Basic listing (legacy)
├── enhanced_extractor.py         # Phase 2 - Enhanced extraction
└── cli.py                        # Phase 2 - CLI interface (legacy)
```

## Usage

### GUI Application
```bash
python -m src.gui.main_window
```

### CLI Application
```bash
python -m src.cli.cli search "python"
python -m src.cli.cli stats
```

### Legacy Scripts
```bash
python src/quick_list_conversations.py
python src/enhanced_extractor.py
```