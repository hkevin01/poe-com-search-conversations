import asyncio
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Poe.com Conversation Search", version="2.0.0")

# Setup paths
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
DB_PATH = STORAGE_DIR / "conversations.db"
CONFIG_DIR = BASE_DIR / "config"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Create directories if they don't exist
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
STORAGE_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

class ConversationDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                poe_id TEXT UNIQUE,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                bot_name TEXT,
                created_at TEXT,
                updated_at TEXT,
                message_count INTEGER DEFAULT 0,
                content TEXT,
                tags TEXT,
                metadata TEXT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts USING fts5(
                title, content, bot_name, tags,
                content='conversations',
                content_rowid='id'
            )
        ''')

        conn.commit()
        conn.close()

    def search_conversations(self, query: str = "", bot_filter: str = "",
                           date_from: str = "", date_to: str = "", limit: int = 50):
        """Search conversations with filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if query:
            # Use FTS for text search
            sql = '''
                SELECT c.* FROM conversations c
                JOIN conversations_fts fts ON c.id = fts.rowid
                WHERE conversations_fts MATCH ?
            '''
            params = [query]
        else:
            sql = 'SELECT * FROM conversations WHERE 1=1'
            params = []

        if bot_filter:
            sql += ' AND bot_name LIKE ?'
            params.append(f'%{bot_filter}%')

        if date_from:
            sql += ' AND created_at >= ?'
            params.append(date_from)

        if date_to:
            sql += ' AND created_at <= ?'
            params.append(date_to)

        sql += ' ORDER BY extracted_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def get_conversation_by_id(self, conv_id: int):
        """Get a specific conversation by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM conversations WHERE id = ?', (conv_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM conversations')
        total = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT bot_name) as bots FROM conversations WHERE bot_name IS NOT NULL')
        bots = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(created_at) as earliest, MAX(created_at) as latest FROM conversations')
        dates = cursor.fetchone()

        cursor.execute('SELECT AVG(message_count) as avg_messages FROM conversations WHERE message_count > 0')
        avg_messages = cursor.fetchone()[0] or 0

        conn.close()

        return {
            'total_conversations': total,
            'unique_bots': bots,
            'earliest_date': dates[0],
            'latest_date': dates[1],
            'avg_messages': round(avg_messages, 1)
        }

# Initialize database
db = ConversationDB(str(DB_PATH))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main dashboard page"""
    stats = db.get_stats()
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats
    })

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page"""
    return templates.TemplateResponse("search.html", {"request": request})

@app.post("/api/search")
async def api_search(
    query: str = Form(""),
    bot_filter: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form(""),
    limit: int = Form(50)
):
    """API endpoint for searching conversations"""
    try:
        results = db.search_conversations(query, bot_filter, date_from, date_to, limit)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation/{conv_id}")
async def get_conversation(conv_id: int):
    """Get a specific conversation"""
    conversation = db.get_conversation_by_id(conv_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.post("/api/extract")
async def extract_conversations(
    limit: int = Form(10),
    headless: bool = Form(True)
):
    """Trigger conversation extraction"""
    try:
        # Run the extraction script
        cmd = [
            sys.executable,
            str(BASE_DIR / "src" / "quick_list_conversations.py"),
            "--limit", str(limit)
        ]

        if not headless:
            cmd.append("--no-headless")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate()

        if process.returncode == 0:
            return {"success": True, "message": "Extraction completed", "output": stdout}
        else:
            return {"success": False, "error": stderr}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export/{format}")
async def export_conversations(format: str, query: str = "", bot_filter: str = ""):
    """Export conversations in various formats"""
    if format not in ["json", "csv", "markdown"]:
        raise HTTPException(status_code=400, detail="Invalid export format")

    try:
        conversations = db.search_conversations(query, bot_filter, limit=10000)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filename = f"conversations_export_{timestamp}.json"
            filepath = STORAGE_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversations, f, indent=2, ensure_ascii=False)

            return FileResponse(
                filepath,
                media_type='application/json',
                filename=filename
            )

        elif format == "csv":
            import csv
            filename = f"conversations_export_{timestamp}.csv"
            filepath = STORAGE_DIR / filename

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if conversations:
                    writer = csv.DictWriter(f, fieldnames=conversations[0].keys())
                    writer.writeheader()
                    writer.writerows(conversations)

            return FileResponse(
                filepath,
                media_type='text/csv',
                filename=filename
            )

        elif format == "markdown":
            filename = f"conversations_export_{timestamp}.md"
            filepath = STORAGE_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("# Poe.com Conversations Export\n\n")
                f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                for conv in conversations:
                    f.write(f"## {conv['title']}\n\n")
                    f.write(f"- **Bot**: {conv.get('bot_name', 'Unknown')}\n")
                    f.write(f"- **Date**: {conv.get('created_at', 'Unknown')}\n")
                    f.write(f"- **URL**: {conv['url']}\n\n")
                    if conv.get('content'):
                        f.write(f"**Content Preview**:\n{conv['content'][:500]}...\n\n")
                    f.write("---\n\n")

            return FileResponse(
                filepath,
                media_type='text/markdown',
                filename=filename
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    return db.get_stats()

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings configuration page"""
    # Load current config if exists
    config_path = CONFIG_DIR / "poe_tokens.json"
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": config
    })

@app.post("/api/settings")
async def update_settings(
    p_b: str = Form(""),
    p_lat: str = Form(""),
    formkey: str = Form("")
):
    """Update authentication settings"""
    try:
        config = {
            "p-b": p_b,
            "p-lat": p_lat,
            "formkey": formkey
        }

        config_path = CONFIG_DIR / "poe_tokens.json"
        CONFIG_DIR.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        return {"success": True, "message": "Settings saved successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_templates():
    """Create HTML templates"""

    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Poe.com Conversation Search{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body class="bg-gray-50">
    <nav class="bg-blue-600 text-white p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-xl font-bold">Poe.com Search Tool</h1>
            <div class="space-x-4">
                <a href="/" class="hover:text-blue-200">Dashboard</a>
                <a href="/search" class="hover:text-blue-200">Search</a>
                <a href="/settings" class="hover:text-blue-200">Settings</a>
            </div>
        </div>
    </nav>

    <main class="container mx-auto p-6">
        {% block content %}{% endblock %}
    </main>
</body>
</html>'''

    # Dashboard template
    dashboard_template = '''{% extends "base.html" %}

{% block content %}
<div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-700">Total Conversations</h3>
        <p class="text-3xl font-bold text-blue-600">{{ stats.total_conversations }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-700">Unique Bots</h3>
        <p class="text-3xl font-bold text-green-600">{{ stats.unique_bots }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-700">Avg Messages</h3>
        <p class="text-3xl font-bold text-purple-600">{{ stats.avg_messages }}</p>
    </div>
    <div class="bg-white p-6 rounded-lg shadow">
        <h3 class="text-lg font-semibold text-gray-700">Date Range</h3>
        <p class="text-sm text-gray-600">{{ stats.earliest_date }} to {{ stats.latest_date }}</p>
    </div>
</div>

<div class="bg-white p-6 rounded-lg shadow">
    <h2 class="text-xl font-bold mb-4">Quick Actions</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button onclick="extractConversations()"
                class="bg-blue-600 text-white p-4 rounded-lg hover:bg-blue-700">
            Extract New Conversations
        </button>
        <a href="/search"
           class="bg-green-600 text-white p-4 rounded-lg hover:bg-green-700 text-center block">
            Search Conversations
        </a>
        <button onclick="exportAll()"
                class="bg-purple-600 text-white p-4 rounded-lg hover:bg-purple-700">
            Export All Data
        </button>
    </div>
</div>

<script>
async function extractConversations() {
    if (!confirm('This may take several minutes. Continue?')) return;

    const response = await fetch('/api/extract', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'limit=25&headless=true'
    });
    const result = await response.json();
    alert(result.success ? 'Extraction completed!' : 'Error: ' + result.error);
    if (result.success) location.reload();
}

async function exportAll() {
    window.open('/api/export/json');
}
</script>
{% endblock %}'''

    # Search template
    search_template = '''{% extends "base.html" %}

{% block content %}
<div x-data="searchApp()" class="space-y-6">
    <div class="bg-white p-6 rounded-lg shadow">
        <h2 class="text-xl font-bold mb-4">Search Conversations</h2>
        <form @submit.prevent="search()" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input x-model="query" type="text" placeholder="Search text..."
                       class="border p-2 rounded w-full">
                <input x-model="botFilter" type="text" placeholder="Bot name..."
                       class="border p-2 rounded w-full">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input x-model="dateFrom" type="date" class="border p-2 rounded">
                <input x-model="dateTo" type="date" class="border p-2 rounded">
                <select x-model="limit" class="border p-2 rounded">
                    <option value="25">25 results</option>
                    <option value="50">50 results</option>
                    <option value="100">100 results</option>
                </select>
            </div>
            <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
                Search
            </button>
        </form>
    </div>

    <div x-show="results.length > 0" class="bg-white p-6 rounded-lg shadow">
        <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">Results (<span x-text="results.length"></span>)</h3>
            <div class="space-x-2">
                <button @click="exportData('json')" class="bg-green-600 text-white px-3 py-1 rounded text-sm">JSON</button>
                <button @click="exportData('csv')" class="bg-green-600 text-white px-3 py-1 rounded text-sm">CSV</button>
                <button @click="exportData('markdown')" class="bg-green-600 text-white px-3 py-1 rounded text-sm">Markdown</button>
            </div>
        </div>

        <div class="space-y-3">
            <template x-for="conv in results" :key="conv.id">
                <div class="border p-4 rounded hover:bg-gray-50">
                    <h4 class="font-semibold text-blue-600" x-text="conv.title"></h4>
                    <p class="text-sm text-gray-600">
                        <span x-text="conv.bot_name || 'Unknown Bot'"></span> •
                        <span x-text="conv.created_at || 'Unknown Date'"></span> •
                        <span x-text="conv.message_count || 0"></span> messages
                    </p>
                    <div class="mt-2" x-show="conv.tags">
                        <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded" x-text="conv.tags"></span>
                    </div>
                    <div class="mt-2 space-x-2">
                        <a :href="conv.url" target="_blank" class="text-blue-600 text-sm hover:underline">Open in Poe →</a>
                        <button @click="viewDetails(conv.id)" class="text-green-600 text-sm hover:underline">View Details</button>
                    </div>
                </div>
            </template>
        </div>
    </div>
</div>

<script>
function searchApp() {
    return {
        query: '',
        botFilter: '',
        dateFrom: '',
        dateTo: '',
        limit: 50,
        results: [],

        async search() {
            const formData = new FormData();
            formData.append('query', this.query);
            formData.append('bot_filter', this.botFilter);
            formData.append('date_from', this.dateFrom);
            formData.append('date_to', this.dateTo);
            formData.append('limit', this.limit);

            const response = await fetch('/api/search', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            this.results = data.results || [];
        },

        async exportData(format) {
            const params = new URLSearchParams({
                query: this.query,
                bot_filter: this.botFilter
            });
            window.open(`/api/export/${format}?${params}`);
        },

        async viewDetails(convId) {
            const response = await fetch(`/api/conversation/${convId}`);
            const conv = await response.json();
            alert(`Title: ${conv.title}\nBot: ${conv.bot_name}\nMessages: ${conv.message_count}\nContent: ${conv.content ? conv.content.substring(0, 200) + '...' : 'No content available'}`);
        }
    }
}
</script>
{% endblock %}'''

    # Settings template
    settings_template = '''{% extends "base.html" %}

{% block content %}
<div class="bg-white p-6 rounded-lg shadow max-w-2xl mx-auto">
    <h2 class="text-xl font-bold mb-4">Authentication Settings</h2>

    <form id="settingsForm" class="space-y-4">
        <div>
            <label class="block text-sm font-medium mb-1">p-b Token (Required)</label>
            <input name="p_b" type="text" value="{{ config.get('p-b', '') }}"
                   class="border p-2 rounded w-full" placeholder="Your p-b token from Poe.com cookies">
        </div>

        <div>
            <label class="block text-sm font-medium mb-1">p-lat Token (Optional)</label>
            <input name="p_lat" type="text" value="{{ config.get('p-lat', '') }}"
                   class="border p-2 rounded w-full" placeholder="Your p-lat token">
        </div>

        <div>
            <label class="block text-sm font-medium mb-1">formkey (Optional)</label>
            <input name="formkey" type="text" value="{{ config.get('formkey', '') }}"
                   class="border p-2 rounded w-full" placeholder="Your formkey token">
        </div>

        <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700">
            Save Settings
        </button>
    </form>

    <div class="mt-6 p-4 bg-blue-50 rounded">
        <h3 class="font-semibold text-blue-800">How to get tokens:</h3>
        <ol class="list-decimal list-inside text-sm text-blue-700 mt-2 space-y-1">
            <li>Open Poe.com in your browser</li>
            <li>Open Developer Tools (F12)</li>
            <li>Go to Application/Storage → Cookies → https://poe.com</li>
            <li>Copy the values for p-b (required), p-lat and formkey (optional)</li>
        </ol>
    </div>
</div>

<script>
document.getElementById('settingsForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    const response = await fetch('/api/settings', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    alert(result.success ? 'Settings saved!' : 'Error: ' + result.message);
});
</script>
{% endblock %}'''

    # Write templates to files
    templates_to_create = {
        'base.html': base_template,
        'dashboard.html': dashboard_template,
        'search.html': search_template,
        'settings.html': settings_template
    }

    for filename, content in templates_to_create.items():
        filepath = TEMPLATES_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())

if __name__ == "__main__":
    import uvicorn

    # Create templates if they don't exist
    create_templates()

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
