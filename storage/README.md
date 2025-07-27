# Storage Directory

This directory contains the SQLite database and related storage files for the Poe.com Conversation Manager.

## Structure

```
storage/
├── conversations.db        # Main SQLite database
├── backups/               # Database backups
├── exports/               # Exported conversations
└── logs/                  # Application logs
```

## Database

The main database file `conversations.db` contains:
- Full conversation content with message-by-message storage
- Bot identification and metadata
- Full-text search capabilities
- Conversation analytics and statistics

## Usage

The database is automatically created when you run:
```bash
python src/quick_conversation_getter.py
```

Or when using the GUI application:
```bash
python run_gui.py
```

## Backup

Regular backups are recommended:
```bash
# Manual backup
cp storage/conversations.db storage/backups/conversations_backup_$(date +%Y%m%d_%H%M%S).db

# Or use the built-in backup feature
python demo_database.py  # Includes backup functionality
```

## Size Considerations

- SQLite is lightweight and efficient for this use case
- Database will grow with conversation content
- Full-text search indexing adds ~20% overhead
- Typical conversation: 1-5KB of storage

## No Docker Required

SQLite is file-based and requires no additional services:
- ✅ No Docker containers needed
- ✅ No server setup required
- ✅ Portable across systems
- ✅ Included with Python
- ✅ Fast and reliable