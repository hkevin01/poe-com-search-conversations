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

## Quick Start

### 1. First-Time Setup
```bash
# Clone the repository
git clone <repository-url>
cd poe-com-search-conversations

# Run automated setup
python main.py setup
```

### 2. Configure Authentication
```bash
# Copy the example config file
cp config/poe_tokens.json.example config/poe_tokens.json

# Edit with your actual tokens (see config/README.md for details)
nano config/poe_tokens.json
```

### 3. Launch the Application
```bash
# Recommended: Launch with automatic data population
python main.py launch

# Or launch GUI directly (may be empty initially)
python main.py gui

# Run system health check
python main.py test
```

## Usage

### Main Commands
```bash
# Environment setup
python main.py setup              # First-time setup and dependencies

# Application launch
python main.py launch             # Launch GUI with auto data population
python main.py gui                # Launch GUI directly

# Testing and diagnostics
python main.py test               # System health check
python main.py test-unique        # Database uniqueness tests
```

### Advanced Options
```bash
# Launch with more conversations
python main.py launch --limit 25

# Launch without populating database
python main.py launch --skip-populate

# Force database refresh
python main.py launch --force-populate
```

### Manual Script Execution
```bash
# Setup scripts
python scripts/setup/create_environment.py

# Development scripts
python scripts/development/launch_gui.py
python scripts/development/launch_with_data.py

# Testing scripts
python scripts/testing/test_system.py
python scripts/testing/test_uniqueness.py
```
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

### Full scrolling collection with tuning:
```bash
# Collect all conversations (automatic scrolling)
python src/quick_list_conversations.py --config config/poe_tokens.json \
   --max-scrolls 300 --scroll-pause 0.8

# Limit to first 50 conversations for a quick test
python src/quick_list_conversations.py --limit 50

# Save to a specific output path
python src/quick_list_conversations.py --output exports/conversations_latest.json

# Debug / headed mode with generous timing (recommended if headless finds 0)
python src/quick_list_conversations.py --config config/poe_tokens.json \
   --no-headless --debug --scroll-pause 1.0 --max-time 180

# Headless with extended time & limit for a smoke test
python src/quick_list_conversations.py --config config/poe_tokens.json \
   --debug --scroll-pause 1.0 --max-time 200 --limit 25
```

### Troubleshooting extraction

```text
- If you see [ERROR] Authentication failed (redirected to /login): refresh your p-b cookie (and optional p-lat, formkey).
- If headless returns 0 conversations, try --no-headless or increase --scroll-pause (e.g. 1.0 or 1.5).
- If the UI layout changes, the script now collects both /chat/ and /c/ styles and auto-detects the scroll container.
- Still failing? Re-run with:  --debug --no-headless --scroll-pause 1.2 --max-time 240
- On failure with --debug, inspect debug_artifacts/screenshot.png and debug_artifacts/page.html
```

## Smoke Test (New)

A fast, low‑risk extraction check is available to validate that authentication,
selectors, and scrolling still work after changes or before a longer run.

### Run Manually

```bash
python scripts/testing/test_extraction_smoke.py \
   --config config/poe_tokens.json  # optional, auto-detected if omitted
```

Behavior:

- Headless by default (add `--no-headless` for debugging)
- Limits run time (≈90s default) and conversation count (default 5)
- Produces an output JSON in `exports/` and exits 0 if driver succeeded even
   when 0 conversations were found (to allow layout changes without blocking CI)
- In `--debug` mode saves `debug_artifacts/` (HTML + screenshot) for inspection

### Via run.sh

`./run.sh` now invokes a smoke extraction near the end (non‑blocking). Review
its logs for a quick health signal; failures will be reported but won't stop
other tasks unless earlier critical setup failed.

### Suggested CI Pattern

Add a conditional job that only runs when secret tokens are available:

```yaml
jobs:
   smoke:
      runs-on: ubuntu-latest
      if: secrets.P_B_TOKEN != ''
      steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
            with:
               python-version: '3.11'
         - name: Install deps
            run: pip install -r requirements.txt
         - name: Write tokens
            run: |
               mkdir -p config
               jq -n --arg pb "$P_B_TOKEN" '{"p-b":$pb}' > config/poe_tokens.json
            env:
               P_B_TOKEN: ${{ secrets.P_B_TOKEN }}
         - name: Smoke extraction
            run: python scripts/testing/test_extraction_smoke.py --debug
```

Keep this lightweight to avoid rate limits; the full export / catalog tests
should remain separate.

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

```text
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

### Common Issues

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

## Export & Catalog Pipeline (New)

The project now includes a metadata‑rich export pipeline producing:

- Markdown transcript per conversation
- A merged `merged.jsonl` containing all messages with metadata
- A per‑message `section.jsonl` file under each message slug directory
- A SQLite catalog (`catalog.sqlite`) with `conversations` and `messages` tables

### Quick CLI Usage

```bash
python scripts/export_cli.py --build-db --output-dir output

# Rebuild DB only from existing exported artifacts
python scripts/export_cli.py --index-only --db-path output/catalog.sqlite

# Export only conversations updated since timestamp
python scripts/export_cli.py --build-db --since 2025-01-01T00:00:00Z
```

### Schema Overview

Tables:

`conversations(graph_id PRIMARY KEY, title, slug, url, created_at, updated_at, parent_graph_id, export_md_path, export_assets_path, content_hash, word_count, page_order, last_indexed_at)`

`messages(graph_id PRIMARY KEY, conversation_graph_id, title, slug, author, role, ordinal, created_at, updated_at, parent_graph_id, export_md_path, export_assets_path, content_hash, word_count, excerpt, last_indexed_at)`

### Change Detection

Exports are skipped if both the stored content hash matches and the new `updated_at` is not greater than the stored value. Use `--since` to pre‑filter older conversations before hashing.

### Index-Only Mode

`--index-only` walks existing output folders, reads `merged.jsonl` files, and repopulates the catalog without re‑rendering Markdown or re‑scraping.

### Roadmap

- Replace stub scraper adapter with full Selenium/API conversation fetch
- Add FastAPI endpoints for catalog querying
- Extend tests for per‑message JSONL integrity and search exposure
