# FastAPI Web Interface Migration Guide

## Overview

The Poe.com Conversation Search Tool has been successfully migrated from PyQt6 desktop GUI to a modern FastAPI web interface. This provides better accessibility, easier deployment, and cross-platform compatibility.

## What's New

### ✨ Modern Web Interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Tailwind CSS**: Modern, clean styling
- **Real-time Search**: Interactive search with filters
- **Dashboard**: Statistics and quick actions
- **Settings Page**: Easy token configuration

### 🚀 FastAPI Backend
- **REST API**: Programmatic access to all features
- **Async Support**: Better performance for concurrent users
- **Auto Documentation**: Swagger UI at `/docs`
- **Export Functionality**: JSON, CSV, Markdown exports

### 🔧 Enhanced Features
- **Better Database Integration**: Improved FTS search
- **Statistics Dashboard**: Visual overview of conversations
- **Export Options**: Multiple format support
- **Easy Deployment**: Docker support included

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_fastapi.txt
```

### 2. Launch the Web Interface
```bash
python launch_fastapi.py
```

### 3. Access the Application
Open your browser to: **http://localhost:8000**

## File Structure

```
src/
├── fastapi_gui.py          # Main FastAPI application
├── database.py             # Database operations (existing)
├── quick_list_conversations.py  # Extraction (existing)
└── ...

templates/                  # Jinja2 HTML templates
├── base.html              # Base template
├── dashboard.html         # Main dashboard
├── search.html            # Search interface
└── settings.html          # Configuration

static/                    # Static files (auto-created)
scripts/
└── migrate_to_fastapi.py  # Migration helper

launch_fastapi.py          # Launch script
requirements_fastapi.txt   # FastAPI dependencies
Dockerfile                 # Docker deployment
docker-compose.yml         # Docker Compose
```

## API Endpoints

### Web Pages
- `GET /` - Dashboard
- `GET /search` - Search interface
- `GET /settings` - Settings page

### API Endpoints
- `POST /api/search` - Search conversations
- `GET /api/conversation/{id}` - Get specific conversation
- `POST /api/extract` - Trigger extraction
- `GET /api/export/{format}` - Export data
- `GET /api/stats` - Database statistics
- `POST /api/settings` - Update configuration

## Migration Benefits

### Before (PyQt6)
- ❌ Desktop only
- ❌ Platform-specific installation
- ❌ Limited accessibility
- ❌ No remote access
- ❌ Complex deployment

### After (FastAPI)
- ✅ Cross-platform web interface
- ✅ Easy browser access
- ✅ Mobile-friendly
- ✅ Remote access capability
- ✅ Simple deployment
- ✅ REST API for automation
- ✅ Docker support

## Deployment Options

### Local Development
```bash
python launch_fastapi.py
```

### Production with Uvicorn
```bash
uvicorn src.fastapi_gui:app --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
docker-compose up
```

## Configuration

1. **Open Settings Page**: Navigate to `/settings`
2. **Enter Tokens**: Add your Poe.com authentication tokens
3. **Save Configuration**: Settings are stored in `config/poe_tokens.json`

## Usage

### Dashboard
- View conversation statistics
- Quick extract new conversations
- Export all data

### Search
- Full-text search across conversations
- Filter by bot, date range
- Export search results
- View conversation details

### API Usage
```python
import requests

# Search conversations
response = requests.post('http://localhost:8000/api/search',
                        data={'query': 'python'})
results = response.json()

# Get conversation details
conv = requests.get('http://localhost:8000/api/conversation/1')
print(conv.json())
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Use different port
   uvicorn src.fastapi_gui:app --port 8001
   ```

2. **Templates Not Found**
   ```bash
   # Run template creation
   python -c "from src.fastapi_gui import create_templates; create_templates()"
   ```

3. **Database Issues**
   ```bash
   # Check database exists
   ls -la storage/conversations.db
   ```

### Migration from PyQt6

The original PyQt6 GUI files remain in the project but are no longer the primary interface. The FastAPI web interface provides all the same functionality with additional benefits:

- All existing data remains compatible
- Database schema unchanged
- Extraction scripts work identically
- Configuration format unchanged

## Future Enhancements

### Planned Features
- [ ] Real-time extraction monitoring
- [ ] User authentication
- [ ] WebSocket support for live updates
- [ ] Advanced visualization charts
- [ ] Conversation tagging interface
- [ ] Mobile PWA support

### API Extensions
- [ ] Bulk operations
- [ ] Conversation comparison
- [ ] Advanced analytics
- [ ] Webhook support

## Support

For issues or questions:
1. Check the project documentation
2. Review API docs at `/docs`
3. Check the troubleshooting section
4. File an issue in the project repository

---

**The FastAPI migration successfully modernizes the Poe.com Conversation Search Tool while maintaining all existing functionality and adding new capabilities for web-based access and API integration.**
