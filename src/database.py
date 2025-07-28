#!/usr/bin/env python3
"""
Poe Search - Core Database Module
Provides SQLite database functionality for storing and searching conversations.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging

@dataclass
class Conversation:
    """Data class representing a conversation."""
    id: Optional[int] = None
    poe_id: str = ""
    title: str = ""
    url: str = ""
    bot_name: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0
    tags: List[str] = None
    content: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

class ConversationDatabase:
    """SQLite database manager for conversations."""
    
    def __init__(self, db_path: str = "conversations.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poe_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    bot_name TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    tags TEXT,  -- JSON array
                    content TEXT,
                    metadata TEXT  -- JSON object
                )
            """)
            
            # Create full-text search table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS conversations_fts 
                USING fts5(title, content, bot_name, tags)
            """)
            
            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_bot_name ON conversations(bot_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON conversations(created_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_updated_at ON conversations(updated_at)"
            )
            
            conn.commit()
    
    def add_conversation(self, conv: Conversation) -> int:
        """Add a conversation to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO conversations 
                (poe_id, title, url, bot_name, created_at, updated_at, 
                 message_count, tags, content, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conv.poe_id, conv.title, conv.url, conv.bot_name,
                conv.created_at, conv.updated_at, conv.message_count,
                json.dumps(conv.tags), conv.content, json.dumps(conv.metadata)
            ))
            
            # Update FTS table
            conn.execute("""
                INSERT OR REPLACE INTO conversations_fts 
                (rowid, title, content, bot_name, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cursor.lastrowid, conv.title, conv.content, 
                conv.bot_name, " ".join(conv.tags)
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def search_conversations(self, query: str, filters: Dict[str, Any] = None) -> List[Conversation]:
        """Search conversations using full-text search and filters."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if query.strip():
                # Full-text search
                sql = """
                    SELECT c.* FROM conversations c
                    JOIN conversations_fts fts ON c.rowid = fts.rowid
                    WHERE conversations_fts MATCH ?
                """
                params = [query]
            else:
                # No search query, get all
                sql = "SELECT * FROM conversations"
                params = []
            
            # Apply filters
            if filters:
                where_clauses = []
                if 'bot_name' in filters:
                    where_clauses.append("bot_name = ?")
                    params.append(filters['bot_name'])
                if 'start_date' in filters:
                    where_clauses.append("created_at >= ?")
                    params.append(filters['start_date'])
                if 'end_date' in filters:
                    where_clauses.append("created_at <= ?")
                    params.append(filters['end_date'])
                
                if where_clauses:
                    if "WHERE" in sql:
                        sql += " AND " + " AND ".join(where_clauses)
                    else:
                        sql += " WHERE " + " AND ".join(where_clauses)
            
            sql += " ORDER BY updated_at DESC"
            
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
            
            conversations = []
            for row in rows:
                conv = Conversation(
                    id=row['id'],
                    poe_id=row['poe_id'],
                    title=row['title'],
                    url=row['url'],
                    bot_name=row['bot_name'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    message_count=row['message_count'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    content=row['content'] or "",
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                conversations.append(conv)
            
            return conversations
    
    def get_conversation_by_id(self, conv_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        conversations = self.search_conversations("", {"id": conv_id})
        return conversations[0] if conversations else None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_conversations,
                    COUNT(DISTINCT bot_name) as unique_bots,
                    SUM(message_count) as total_messages,
                    AVG(message_count) as avg_messages_per_conversation,
                    MIN(created_at) as earliest_conversation,
                    MAX(updated_at) as latest_activity
                FROM conversations
            """)
            row = cursor.fetchone()
            
            # Get bot distribution
            cursor = conn.execute("""
                SELECT bot_name, COUNT(*) as count 
                FROM conversations 
                WHERE bot_name IS NOT NULL 
                GROUP BY bot_name 
                ORDER BY count DESC
            """)
            bot_stats = cursor.fetchall()
            
            return {
                "total_conversations": row[0] or 0,
                "unique_bots": row[1] or 0,
                "total_messages": row[2] or 0,
                "avg_messages_per_conversation": round(row[3] or 0, 2),
                "earliest_conversation": row[4],
                "latest_activity": row[5],
                "bot_distribution": dict(bot_stats)
            }
    
    def export_conversations(self, format: str = "json", filename: str = None) -> str:
        """Export all conversations to specified format."""
        conversations = self.search_conversations("")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversations_export_{timestamp}.{format}"
        
        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([asdict(conv) for conv in conversations], f, 
                         indent=2, ensure_ascii=False, default=str)
        elif format == "csv":
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if conversations:
                    fieldnames = asdict(conversations[0]).keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for conv in conversations:
                        row = asdict(conv)
                        # Convert complex fields to strings
                        row['tags'] = json.dumps(row['tags'])
                        row['metadata'] = json.dumps(row['metadata'])
                        writer.writerow(row)
        elif format == "markdown":
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Poe.com Conversations Export\n\n")
                f.write(f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total conversations: {len(conversations)}\n\n")
                
                for i, conv in enumerate(conversations, 1):
                    f.write(f"## {i}. {conv.title}\n\n")
                    f.write(f"- **Bot**: {conv.bot_name}\n")
                    f.write(f"- **URL**: {conv.url}\n")
                    f.write(f"- **Created**: {conv.created_at}\n")
                    f.write(f"- **Messages**: {conv.message_count}\n")
                    
                    if conv.tags:
                        f.write(f"- **Tags**: {', '.join(conv.tags)}\n")
                    
                    f.write("\n### Content\n\n")
                    
                    if conv.content:
                        try:
                            messages = json.loads(conv.content)
                            for msg in messages:
                                sender = "**User**" if msg['sender'] == 'user' else "**Bot**"
                                f.write(f"{sender}: {msg['content']}\n\n")
                        except json.JSONDecodeError:
                            f.write(f"{conv.content}\n\n")
                    else:
                        f.write("No content available.\n\n")
                    
                    f.write("---\n\n")
        
        return filename
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a backup of the database."""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"conversations_backup_{timestamp}.db"
        
        import shutil
        shutil.copy2(self.db_path, backup_path)
        self.logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup."""
        try:
            import shutil
            shutil.copy2(backup_path, self.db_path)
            self.logger.info(f"Database restored from: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore database: {e}")
            return False
    
    def delete_conversation(self, poe_id: str) -> bool:
        """Delete a conversation by poe_id."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM conversations WHERE poe_id = ?", (poe_id,)
                )
                
                # Also delete from FTS table
                conn.execute(
                    "DELETE FROM conversations_fts WHERE rowid IN "
                    "(SELECT rowid FROM conversations WHERE poe_id = ?)", 
                    (poe_id,)
                )
                
                conn.commit()
                deleted = cursor.rowcount > 0
                
                if deleted:
                    self.logger.info(f"Deleted conversation: {poe_id}")
                else:
                    self.logger.warning(f"Conversation not found: {poe_id}")
                
                return deleted
        except Exception as e:
            self.logger.error(f"Failed to delete conversation {poe_id}: {e}")
            return False
    
    def update_conversation_tags(self, poe_id: str, tags: List[str]) -> bool:
        """Update tags for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE conversations 
                    SET tags = ?, updated_at = ? 
                    WHERE poe_id = ?
                """, (json.dumps(tags), datetime.now(), poe_id))
                
                # Update FTS table
                conn.execute("""
                    UPDATE conversations_fts 
                    SET tags = ? 
                    WHERE rowid = (SELECT rowid FROM conversations WHERE poe_id = ?)
                """, (" ".join(tags), poe_id))
                
                conn.commit()
                updated = cursor.rowcount > 0
                
                if updated:
                    self.logger.info(f"Updated tags for conversation: {poe_id}")
                else:
                    self.logger.warning(f"Conversation not found: {poe_id}")
                
                return updated
        except Exception as e:
            self.logger.error(f"Failed to update tags for {poe_id}: {e}")
            return False
    
    def conversation_exists(self, poe_id: str) -> bool:
        """Check if a conversation with the given poe_id already exists."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT 1 FROM conversations WHERE poe_id = ?", (poe_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error checking conversation existence: {e}")
            return False

    def get_conversation_by_poe_id(self, poe_id: str) -> Optional[Conversation]:
        """Get a conversation by its Poe.com ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT id, poe_id, title, url, bot_name, created_at, updated_at,
                           message_count, content, tags, metadata
                    FROM conversations 
                    WHERE poe_id = ?
                """, (poe_id,))
                
                row = cursor.fetchone()
                if row:
                    return Conversation(
                        id=row['id'],
                        poe_id=row['poe_id'],
                        title=row['title'],
                        url=row['url'],
                        bot_name=row['bot_name'],
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                        message_count=row['message_count'],
                        tags=json.loads(row['tags']) if row['tags'] else [],
                        content=row['content'] or "",
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting conversation by poe_id: {e}")
            return None

    def update_conversation_if_newer(self, conversation: Conversation) -> int:
        """Update conversation if the new version has more content or is newer."""
        try:
            existing = self.get_conversation_by_poe_id(conversation.poe_id)
            
            if not existing:
                # Doesn't exist, add it
                return self.add_conversation(conversation)
            
            # Check if new version has more messages or newer content
            should_update = (
                conversation.message_count > existing.message_count or
                (conversation.updated_at and existing.updated_at and 
                 conversation.updated_at > existing.updated_at) or
                len(conversation.content) > len(existing.content)
            )
            
            if should_update:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        UPDATE conversations 
                        SET title = ?, url = ?, bot_name = ?, updated_at = ?,
                            message_count = ?, content = ?, tags = ?, metadata = ?
                        WHERE poe_id = ?
                    """, (
                        conversation.title,
                        conversation.url, 
                        conversation.bot_name,
                        conversation.updated_at,
                        conversation.message_count,
                        conversation.content,
                        json.dumps(conversation.tags),
                        json.dumps(conversation.metadata),
                        conversation.poe_id
                    ))
                    conn.commit()
                    self.logger.info(f"Updated conversation: {conversation.poe_id}")
                    return existing.id
            else:
                self.logger.info(f"Conversation unchanged: {conversation.poe_id}")
                return existing.id
                
        except Exception as e:
            self.logger.error(f"Error updating conversation: {e}")
            raise

    def export_conversation_by_id(self, poe_id: str, format: str = "json") -> Optional[str]:
        """Export a single conversation by ID."""
        conv = self.get_conversation_by_poe_id(poe_id)
        if not conv:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in conv.title[:50] if c.isalnum() or c in (' ', '-', '_'))
        filename = f"conversation_{safe_title}_{timestamp}.{format}"
        
        if format == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(asdict(conv), f, indent=2, ensure_ascii=False, default=str)
        elif format == "markdown":
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# {conv.title}\n\n")
                f.write(f"- **Bot**: {conv.bot_name}\n")
                f.write(f"- **URL**: {conv.url}\n")
                f.write(f"- **Created**: {conv.created_at}\n")
                f.write(f"- **Messages**: {conv.message_count}\n\n")
                
                if conv.content:
                    try:
                        messages = json.loads(conv.content)
                        for msg in messages:
                            sender = "**User**" if msg['sender'] == 'user' else "**Bot**"
                            f.write(f"{sender}: {msg['content']}\n\n")
                    except json.JSONDecodeError:
                        f.write(f"{conv.content}\n\n")
        
        return filename
    
    def close(self):
        """Close database connection (if needed for cleanup)."""
        # SQLite connections are automatically managed by context managers
        # This method is here for API completeness
        pass
    
    def get_recent_conversations(self, limit: int = 20) -> List[Conversation]:
        """Get most recently updated conversations."""
        return self.search_conversations("", {})[:limit]
    
    def get_conversations_by_bot(self, bot_name: str) -> List[Conversation]:
        """Get all conversations with a specific bot."""
        return self.search_conversations("", {"bot_name": bot_name})
    
    def get_conversations_by_date_range(
        self, start_date: str, end_date: str
    ) -> List[Conversation]:
        """Get conversations within a date range."""
        return self.search_conversations("", {
            "start_date": start_date,
            "end_date": end_date
        })
    
    def get_tagged_conversations(self, tag: str) -> List[Conversation]:
        """Get conversations with a specific tag."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM conversations 
                WHERE json_extract(tags, '$') LIKE ?
                ORDER BY updated_at DESC
            """, (f'%"{tag}"%',))
            
            conversations = []
            for row in cursor.fetchall():
                conv = Conversation(
                    id=row['id'],
                    poe_id=row['poe_id'],
                    title=row['title'],
                    url=row['url'],
                    bot_name=row['bot_name'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    message_count=row['message_count'],
                    tags=json.loads(row['tags']) if row['tags'] else [],
                    content=row['content'] or "",
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
                conversations.append(conv)
            
            return conversations
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags used in conversations."""
        all_tags = set()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT tags FROM conversations WHERE tags IS NOT NULL")
            for row in cursor.fetchall():
                try:
                    tags = json.loads(row[0])
                    all_tags.update(tags)
                except json.JSONDecodeError:
                    continue
        
        return sorted(list(all_tags))
    
    def get_all_bots(self) -> List[str]:
        """Get all unique bot names."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT bot_name 
                FROM conversations 
                WHERE bot_name IS NOT NULL AND bot_name != ''
                ORDER BY bot_name
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def get_conversation_count_by_bot(self) -> Dict[str, int]:
        """Get conversation count for each bot."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT bot_name, COUNT(*) as count 
                FROM conversations 
                WHERE bot_name IS NOT NULL 
                GROUP BY bot_name 
                ORDER BY count DESC
            """)
            return dict(cursor.fetchall())
    
    def get_conversation_count_by_date(self) -> Dict[str, int]:
        """Get conversation count by date (YYYY-MM-DD)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count 
                FROM conversations 
                WHERE created_at IS NOT NULL 
                GROUP BY DATE(created_at) 
                ORDER BY date DESC
            """)
            return dict(cursor.fetchall())
    
    def search_conversation_content(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search within conversation content and return matches with context."""
        matches = []
        
        conversations = self.search_conversations(query)[:limit]
        
        for conv in conversations:
            if not conv.content:
                continue
                
            try:
                messages = json.loads(conv.content)
                for i, msg in enumerate(messages):
                    if query.lower() in msg['content'].lower():
                        # Get some context around the match
                        start_idx = max(0, i - 1)
                        end_idx = min(len(messages), i + 2)
                        context = messages[start_idx:end_idx]
                        
                        matches.append({
                            "conversation_id": conv.id,
                            "conversation_title": conv.title,
                            "message_index": i,
                            "matching_message": msg,
                            "context": context,
                            "url": conv.url
                        })
            except json.JSONDecodeError:
                # Fallback to simple text search
                if query.lower() in conv.content.lower():
                    matches.append({
                        "conversation_id": conv.id,
                        "conversation_title": conv.title,
                        "message_index": 0,
                        "matching_message": {"content": conv.content[:200] + "..."},
                        "context": [],
                        "url": conv.url
                    })
        
        return matches
    
    def update_conversation_metadata(self, poe_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a conversation."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE conversations 
                    SET metadata = ?, updated_at = ? 
                    WHERE poe_id = ?
                """, (json.dumps(metadata), datetime.now(), poe_id))
                
                conn.commit()
                updated = cursor.rowcount > 0
                
                if updated:
                    self.logger.info(f"Updated metadata for conversation: {poe_id}")
                else:
                    self.logger.warning(f"Conversation not found: {poe_id}")
                
                return updated
        except Exception as e:
            self.logger.error(f"Failed to update metadata for {poe_id}: {e}")
            return False
    
    def bulk_update_bot_names(self, mapping: Dict[str, str]) -> int:
        """Bulk update bot names using a mapping dict."""
        updated_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for old_name, new_name in mapping.items():
                    cursor = conn.execute("""
                        UPDATE conversations 
                        SET bot_name = ?, updated_at = ? 
                        WHERE bot_name = ?
                    """, (new_name, datetime.now(), old_name))
                    
                    # Update FTS table
                    conn.execute("""
                        UPDATE conversations_fts 
                        SET bot_name = ? 
                        WHERE bot_name = ?
                    """, (new_name, old_name))
                    
                    updated_count += cursor.rowcount
                
                conn.commit()
                self.logger.info(f"Bulk updated {updated_count} bot names")
                
        except Exception as e:
            self.logger.error(f"Bulk update failed: {e}")
        
        return updated_count
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get detailed database information."""
        with sqlite3.connect(self.db_path) as conn:
            # Get table info
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get database size
            import os
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Get index info
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            return {
                "database_path": self.db_path,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "tables": tables,
                "indexes": indexes,
                "sqlite_version": sqlite3.sqlite_version
            }
    
    def add_url_column_if_missing(self):
        """Add URL column to conversations table if it doesn't exist."""
        try:
            # Check if URL column exists
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(conversations)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'url' not in columns:
                    self.logger.info("📝 Adding URL column to conversations table...")
                    cursor.execute("ALTER TABLE conversations ADD COLUMN url TEXT")
                    conn.commit()
                    self.logger.info("✅ URL column added successfully")
                else:
                    self.logger.debug("✅ URL column already exists")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to add URL column: {e}")
            raise

    def update_conversation(self, conversation: Conversation):
        """Update an existing conversation in the database."""
        try:
            cursor = self.conn.cursor()
            
            # Convert tags to JSON string
            tags_json = json.dumps(conversation.tags) if conversation.tags else "[]"
            
            cursor.execute("""
                UPDATE conversations 
                SET title = ?, url = ?, content = ?, bot_name = ?, 
                    updated_at = ?, message_count = ?, tags = ?, summary = ?
                WHERE id = ?
            """, (
                conversation.title,
                conversation.url,
                conversation.content,
                conversation.bot_name,
                conversation.updated_at,
                conversation.message_count,
                tags_json,
                conversation.summary,
                conversation.id
            ))
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                self.logger.info(f"✅ Updated conversation: {conversation.title[:50]}...")
                return True
            else:
                self.logger.warning(f"⚠️ No conversation found with ID: {conversation.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Failed to update conversation {conversation.id}: {e}")
            self.conn.rollback()
            return False