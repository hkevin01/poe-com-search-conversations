# Poe.com Conversation Search Tool

A Python tool for listing and searching conversations from Poe.com using Selenium automation.

## Features

- **Graphical User Interface**: Modern PyQt6-based desktop application
- **Conversation Browsing**: Browse and view all your Poe.com conversations
- **Advanced Search**: Full-text search with bot and date filtering
- **Local Storage**: SQLite database with full-text search capabilities
- **Export Options**: Export conversations to JSON, CSV, or Markdown
- **Privacy-Focused**: All processing happens locally, no external servers
- List all conversations from your Poe.com account
- Extract conversation titles and URLs
- Save results to JSON format with timestamps
- Support for both headless and visible browser modes
- Handles lazy-loaded content automatically

## Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd poe-com-search-conversations
   ```

2. **Run the setup script:**
   ```bash
   # Linux/Mac
   chmod +x setup.sh
   ./setup.sh
   
   # Windows
   setup.bat
   
   # Or use Python (cross-platform)
   python setup.py
   ```

3. **Configure authentication:**
   ```bash
   # Copy the example config file
   cp config/poe_tokens.json.example config/poe_tokens.json
   
   # Edit with your actual tokens
   nano config/poe_tokens.json
   ```

   To get these tokens:
   - Open Poe.com in your browser
   - Open Developer Tools (F12)
   - Go to Application/Storage → Cookies → https://poe.com
   - Copy the values for `p-b` (required), `p-lat` and `formkey` (optional)

4. **Activate the virtual environment (if not using setup script):**
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate.bat
   
   # Or use the activation script
   ./activate.sh
   ```

## Usage

### GUI Application (Recommended)
```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI application
python run_gui.py
```

### Basic usage:
```bash
python src/quick_list_conversations.py
```

### With custom config file:
```bash
python src/quick_list_conversations.py --config /path/to/your/tokens.json
```

### Show browser window (for debugging):
```bash
python src/quick_list_conversations.py --no-headless
```

## Output

The tool will:
1. Display found conversations in the terminal
2. Save results to `conversations_YYYYMMDD_HHMMSS.json`

Example output format:
```json
[
  {
    "id": 1,
    "title": "Conversation about Python",
    "url": "https://poe.com/chat/12345",
    "method": "link"
  }
]
```

## Project Structure

```
poe-com-search-conversations/
├── src/
│   └── quick_list_conversations.py    # Main script
├── config/
│   └── poe_tokens.json               # Authentication tokens (create this)
├── docs/
│   └── README.md                     # This file
├── tests/
├── .github/
│   └── copilot/
├── requirements.txt                  # Python dependencies
├── .gitignore                       # Git ignore rules
└── README.md                        # Project documentation
```

## Troubleshooting

### Common Issues:

1. **ChromeDriver not found:**
   - Install webdriver-manager: `pip install webdriver-manager`
   - Or manually install ChromeDriver and add to PATH

2. **Authentication failed:**
   - Verify your `p-b` token is correct and current
   - Try adding `p-lat` and `formkey` tokens

3. **No conversations found:**
   - Run with `--no-headless` to see what's happening
   - Check if you're logged into the correct Poe.com account

4. **Rate limiting:**
   - The script includes delays to avoid rate limiting
   - If you encounter issues, try increasing the sleep times

## Security Notes

- Never commit your `config/poe_tokens.json` file to version control
- Keep your authentication tokens secure and private
- Tokens may expire and need to be refreshed periodically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational and personal use only. Please respect Poe.com's terms of service.