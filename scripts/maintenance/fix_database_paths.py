#!/usr/bin/env python3
"""
Fix Database Paths - Ensure all components use correct database location
Updates path references to use storage/conversations.db consistently
"""

import os
import sys
from pathlib import Path


def fix_database_paths():
    """Fix database path references throughout the project."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🔧 Fixing Database Path References")
    print("=" * 40)
    print(f"📁 Project root: {project_root}")
    
    # Move any database files from root to storage
    storage_dir = project_root / "storage"
    storage_dir.mkdir(exist_ok=True)
    
    db_files = ["conversations.db", "conversations.sqlite", "conversations.sqlite3"]
    moved_count = 0
    
    for db_file in db_files:
        root_db = project_root / db_file
        storage_db = storage_dir / db_file
        
        if root_db.exists() and not storage_db.exists():
            try:
                root_db.rename(storage_db)
                print(f"📦 Moved {db_file} to storage/")
                moved_count += 1
            except Exception as e:
                print(f"❌ Failed to move {db_file}: {e}")
        elif root_db.exists() and storage_db.exists():
            # Both exist - remove the root one (storage is canonical)
            try:
                root_db.unlink()
                print(f"🗑️  Removed duplicate {db_file} from root")
            except Exception as e:
                print(f"❌ Failed to remove {db_file}: {e}")
    
    # Check current database location
    canonical_db = storage_dir / "conversations.db"
    print(f"\n📊 Database Status:")
    print(f"   Canonical location: {canonical_db}")
    print(f"   Exists: {'✅ Yes' if canonical_db.exists() else '❌ No'}")
    
    if canonical_db.exists():
        size = canonical_db.stat().st_size
        print(f"   Size: {size:,} bytes")
        
        # Quick check if database has data
        try:
            sys.path.append(str(project_root / "src"))
            from database import ConversationDatabase
            
            db = ConversationDatabase(str(canonical_db))
            stats = db.get_stats()
            print(f"   Conversations: {stats['total_conversations']}")
            print(f"   Messages: {stats['total_messages']}")
        except Exception as e:
            print(f"   Data check failed: {e}")
    
    print(f"\n✅ Database path fixing complete!")
    if moved_count > 0:
        print(f"   Moved {moved_count} database files to storage/")
    
    return canonical_db.exists()


def main():
    """Main function."""
    has_db = fix_database_paths()
    
    if has_db:
        print("\n🎉 Database is properly located in storage/")
        print("💡 Try launching again: python main.py launch")
    else:
        print("\n💡 No existing database found.")
        print("   Run: python main.py launch")
        print("   This will create a new database and populate it.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
