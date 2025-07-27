#!/usr/bin/env python3
"""
Database Migration Script - Add URL Support
Adds URL column to existing conversations table and updates the schema
"""

import sqlite3
import os
import logging
from datetime import datetime

class DatabaseMigration:
    """Handle database schema migrations."""
    
    def __init__(self, db_path: str = "storage/conversations.db"):
        self.db_path = db_path
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_migration(self):
        """Run the URL column migration."""
        self.logger.info("🔄 Starting database migration for URL support...")
        
        try:
            # Ensure database exists
            if not os.path.exists(self.db_path):
                self.logger.info("📁 Database doesn't exist yet - no migration needed")
                return True
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("PRAGMA table_info(conversations)")
            columns = [column[1] for column in cursor.fetchall()]
            self.logger.info(f"📋 Current columns: {', '.join(columns)}")
            
            # Add URL column if missing
            if 'url' not in columns:
                self.logger.info("➕ Adding URL column...")
                cursor.execute("ALTER TABLE conversations ADD COLUMN url TEXT")
                conn.commit()
                self.logger.info("✅ URL column added successfully")
            else:
                self.logger.info("✅ URL column already exists")
            
            # Verify the change
            cursor.execute("PRAGMA table_info(conversations)")
            updated_columns = [column[1] for column in cursor.fetchall()]
            self.logger.info(f"📋 Updated columns: {', '.join(updated_columns)}")
            
            # Show sample data
            cursor.execute("SELECT COUNT(*) FROM conversations")
            count = cursor.fetchone()[0]
            self.logger.info(f"📊 Total conversations in database: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, title, url FROM conversations LIMIT 3")
                samples = cursor.fetchall()
                self.logger.info("📝 Sample conversations:")
                for i, (conv_id, title, url) in enumerate(samples, 1):
                    url_status = "✅ Has URL" if url else "❌ No URL"
                    self.logger.info(f"  {i}. {title[:50]}... - {url_status}")
            
            conn.close()
            
            self.logger.info("🎉 Migration completed successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Migration failed: {e}")
            return False

def main():
    """Run the migration."""
    migration = DatabaseMigration()
    success = migration.run_migration()
    
    if success:
        print("\n✅ Database migration completed successfully!")
        print("📝 The conversations table now supports URL storage.")
        print("🚀 You can now run the enhanced extractor to collect all conversations with URLs.")
    else:
        print("\n❌ Migration failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())