#!/usr/bin/env python3
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  content,                      -- full message text
  title,                        -- message title if any
  author,                       -- author username or bot
  role,                         -- user/assistant/system
  conversation_slug,            -- convenience field for joining
  content='messages',           -- contentless table linked to messages
  content_rowid='rowid',
  tokenize='unicode61'
);
"""

TRIGGERS = [
# Insert
"""
CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug)
  VALUES (
    new.rowid,
    coalesce(new.excerpt, ''),            -- or full text if available
    coalesce(new.title, ''),
    coalesce(new.author, ''),
    coalesce(new.role, ''),
    coalesce(new.slug, '')
  );
END;
""",
# Delete
"""
CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content, title, author, role, conversation_slug)
  VALUES('delete', old.rowid, '', '', '', '', '');
END;
""",
# Update
"""
CREATE TRIGGER IF NOT EXISTS messages_au AFTER UPDATE ON messages BEGIN
  INSERT INTO messages_fts(messages_fts, rowid, content, title, author, role, conversation_slug)
  VALUES('delete', old.rowid, '', '', '', '', '');
  INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug)
  VALUES (
    new.rowid,
    coalesce(new.excerpt, ''),
    coalesce(new.title, ''),
    coalesce(new.author, ''),
    coalesce(new.role, ''),
    coalesce(new.slug, '')
  );
END;
"""
]

def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable FTS if available
    conn.execute("PRAGMA case_sensitive_like=OFF;")
    return conn

def ensure_fts(conn: sqlite3.Connection) -> None:
    conn.executescript(FTS_DDL)
    for trg in TRIGGERS:
        conn.executescript(trg)
    # If table is empty but messages has content, rebuild
    cnt = conn.execute("SELECT count(*) FROM messages_fts").fetchone()[0]
    if cnt == 0:
        # Populate from existing messages
        conn.execute("INSERT INTO messages_fts(rowid, content, title, author, role, conversation_slug) "
                     "SELECT rowid, coalesce(excerpt,''), coalesce(title,''), coalesce(author,''), coalesce(role,''), coalesce(slug,'') "
                     "FROM messages;")
    conn.commit()

def build_where(filters: Dict[str, Any]) -> Tuple[str, List[Any]]:
    where: List[str] = []
    params: List[Any] = []
    if filters.get("bot"):
        where.append("c.title LIKE ?")
        params.append(f"%{filters['bot']}%")
    if filters.get("start"):
        where.append("datetime(m.updated_at) >= datetime(?)")
        params.append(filters["start"])
    if filters.get("end"):
        where.append("datetime(m.updated_at) <= datetime(?)")
        params.append(filters["end"])
    return (" AND ".join(where), params)

def search_messages(
    db_path: str,
    query: str,
    bot: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    conn = connect(db_path)
    try:
        # Ensure FTS exists
        try:
            ensure_fts(conn)
            use_fts = True
        except sqlite3.DatabaseError:
            use_fts = False

        filters = {"bot": bot, "start": start, "end": end}
        where_extra, params_extra = build_where(filters)

        if use_fts and query.strip():
            sql = f"""
            SELECT
              m.*, c.title AS conversation_title, c.url AS conversation_url
            FROM messages m
            JOIN conversations c ON c.graph_id = m.conversation_graph_id
            JOIN messages_fts f ON f.rowid = m.rowid
            WHERE f MATCH ?
            {"AND " + where_extra if where_extra else ""}
            ORDER BY m.updated_at DESC
            LIMIT ? OFFSET ?;
            """
            params = [query] + params_extra + [limit, offset]
        else:
            # Fallback: LIKE search across a few columns
            like = f"%{query.strip()}%" if query.strip() else "%"
            sql = f"""
            SELECT
              m.*, c.title AS conversation_title, c.url AS conversation_url
            FROM messages m
            JOIN conversations c ON c.graph_id = m.conversation_graph_id
            WHERE (coalesce(m.excerpt,'') LIKE ? OR coalesce(m.title,'') LIKE ?)
            {"AND " + where_extra if where_extra else ""}
            ORDER BY m.updated_at DESC
            LIMIT ? OFFSET ?;
            """
            params = [like, like] + params_extra + [limit, offset]

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

def search_conversations_fallback(
    db_path: str,
    query: str,
    bot: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Fallback for legacy conversations table search"""
    conn = connect(db_path)
    try:
        where_parts = []
        params = []

        if query.strip():
            where_parts.append("(title LIKE ? OR content LIKE ?)")
            like_query = f"%{query.strip()}%"
            params.extend([like_query, like_query])

        if bot:
            where_parts.append("bot_name LIKE ?")
            params.append(f"%{bot}%")

        if start:
            where_parts.append("datetime(created_at) >= datetime(?)")
            params.append(start)

        if end:
            where_parts.append("datetime(created_at) <= datetime(?)")
            params.append(end)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        sql = f"""
        SELECT * FROM conversations
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
