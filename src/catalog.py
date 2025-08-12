import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Optional

DEFAULT_DB_PATH = os.environ.get("POE_CATALOG_DB", os.path.join("output", "catalog.sqlite"))

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS conversations (
  graph_id TEXT PRIMARY KEY,
  title TEXT,
  slug TEXT,
  url TEXT,
  created_at TEXT,
  updated_at TEXT,
  parent_graph_id TEXT,
  export_md_path TEXT,
  export_assets_path TEXT,
  content_hash TEXT,
  word_count INTEGER,
  page_order INTEGER,
  last_indexed_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  graph_id TEXT PRIMARY KEY,
  conversation_graph_id TEXT NOT NULL,
  title TEXT,
  slug TEXT,
  author TEXT,
  role TEXT,
  ordinal INTEGER,
  created_at TEXT,
  updated_at TEXT,
  parent_graph_id TEXT,
  export_md_path TEXT,
  export_assets_path TEXT,
  content_hash TEXT,
  word_count INTEGER,
  excerpt TEXT,
  last_indexed_at TEXT,
  FOREIGN KEY (conversation_graph_id) REFERENCES conversations(graph_id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_graph_id);
CREATE INDEX IF NOT EXISTS idx_messages_updated_at ON messages(updated_at);
"""

@contextmanager
def connect(db_path: Optional[str] = None):
    fp = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    conn = sqlite3.connect(fp)
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def ensure_schema(db_path: Optional[str] = None):
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)

def _row_to_dict(cursor, row):
    if row is None:
        return None
    cols = [c[0] for c in cursor.description]
    return {k: v for k, v in zip(cols, row)}

def get_conversation(conn: sqlite3.Connection, graph_id: str) -> Optional[Dict[str, Any]]:
    cur = conn.execute("SELECT * FROM conversations WHERE graph_id = ?", (graph_id,))
    return _row_to_dict(cur, cur.fetchone())

def get_message(conn: sqlite3.Connection, graph_id: str) -> Optional[Dict[str, Any]]:
    cur = conn.execute("SELECT * FROM messages WHERE graph_id = ?", (graph_id,))
    return _row_to_dict(cur, cur.fetchone())

def upsert_conversation(conn: sqlite3.Connection, rec: Dict[str, Any]):
    sql = """
    INSERT INTO conversations (graph_id, title, slug, url, created_at, updated_at,
        parent_graph_id, export_md_path, export_assets_path, content_hash, word_count, page_order, last_indexed_at)
    VALUES (:graph_id, :title, :slug, :url, :created_at, :updated_at,
        :parent_graph_id, :export_md_path, :export_assets_path, :content_hash, :word_count, :page_order, :last_indexed_at)
    ON CONFLICT(graph_id) DO UPDATE SET
        title = excluded.title,
        slug = excluded.slug,
        url = excluded.url,
        created_at = COALESCE(conversations.created_at, excluded.created_at),
        updated_at = excluded.updated_at,
        parent_graph_id = excluded.parent_graph_id,
        export_md_path = excluded.export_md_path,
        export_assets_path = excluded.export_assets_path,
        content_hash = excluded.content_hash,
        word_count = excluded.word_count,
        page_order = excluded.page_order,
        last_indexed_at = excluded.last_indexed_at;
    """
    conn.execute(sql, rec)

def upsert_message(conn: sqlite3.Connection, rec: Dict[str, Any]):
    sql = """
    INSERT INTO messages (graph_id, conversation_graph_id, title, slug, author, role, ordinal,
        created_at, updated_at, parent_graph_id, export_md_path, export_assets_path, content_hash, word_count, excerpt, last_indexed_at)
    VALUES (:graph_id, :conversation_graph_id, :title, :slug, :author, :role, :ordinal,
        :created_at, :updated_at, :parent_graph_id, :export_md_path, :export_assets_path, :content_hash, :word_count, :excerpt, :last_indexed_at)
    ON CONFLICT(graph_id) DO UPDATE SET
        title = excluded.title,
        slug = excluded.slug,
        author = excluded.author,
        role = excluded.role,
        ordinal = excluded.ordinal,
        created_at = COALESCE(messages.created_at, excluded.created_at),
        updated_at = excluded.updated_at,
        parent_graph_id = excluded.parent_graph_id,
        export_md_path = excluded.export_md_path,
        export_assets_path = excluded.export_assets_path,
        content_hash = excluded.content_hash,
        word_count = excluded.word_count,
        excerpt = excluded.excerpt,
        last_indexed_at = excluded.last_indexed_at;
    """
    conn.execute(sql, rec)
