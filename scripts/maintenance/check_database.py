#!/usr/bin/env python3
"""
Database Check - Verify database location and content
Checks both possible database locations and shows detailed information
"""

import os
import sys
from pathlib import Path

# Add src to path from project root
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root / 'src'))

def check_database_location(db_path, label):
    """Check a specific database location."""
    print(f"\n🔍 Checking {label}:")
    print(f"   Path: {db_path}")
    print(f"   Exists: {'✅ Yes' if os.path.exists(db_path) else '❌ No'}")
    
    if not os.path.exists(db_path):
        return False, {}
    
    # Check file size
    size = os.path.getsize(db_path)
    print(f"   Size: {size:,} bytes")
    
    if size == 0:
        print(f"   Status: ⚠️  Empty file")
        return True, {"empty": True}
    
    # Try to read database content
    try:
        from database import ConversationDatabase
        db = ConversationDatabase(db_path)
        stats = db.get_stats()
        
        print(f"   Conversations: {stats['total_conversations']}")
        print(f"   Messages: {stats['total_messages']}")
        print(f"   Unique bots: {stats['unique_bots']}")
        
        if stats['total_conversations'] > 0:
            print(f"   Status: ✅ Has data")
            
            # Show recent conversations
            recent = db.get_recent_conversations(3)
            print(f"   Recent conversations:")
            for i, conv in enumerate(recent, 1):
                title = conv.title[:40] + "..." if len(conv.title) > 40 else conv.title
                print(f"     {i}. {title} ({conv.message_count} messages)")
        else:
            print(f"   Status: ⚠️  No conversations")
        
        return True, stats
        
    except Exception as e:
        print(f"   Status: ❌ Database error: {e}")
        return True, {"error": str(e)}

def main():
    """Check database locations and content."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🗄️  Database Location and Content Check")
    print("=" * 50)
    print(f"📁 Project root: {project_root}")
    
    # Possible database locations
    locations = [
        (project_root / "storage" / "conversations.db", "Canonical location (storage/)"),
        (project_root / "conversations.db", "Root directory"),
        (project_root / "src" / "storage" / "conversations.db", "Wrong location (src/storage/)"),
        (project_root / "src" / "conversations.db", "Wrong location (src/)"),
    ]
    
    found_databases = []
    
    for db_path, label in locations:
        exists, info = check_database_location(db_path, label)
        if exists:
            found_databases.append((db_path, label, info))
    
    print(f"\n📊 Summary:")
    print(f"   Total databases found: {len(found_databases)}")
    
    if not found_databases:
        print("   ❌ No databases found!")
        print("\n💡 To create a database with data:")
        print("     python main.py launch --force-populate")
        return 1
    
    # Find the best database
    canonical_db = project_root / "storage" / "conversations.db"
    best_db = None
    best_stats = None
    
    for db_path, label, info in found_databases:
        if db_path == canonical_db and not info.get("empty", False) and not info.get("error"):
            best_db = (db_path, label)
            best_stats = info
            break
    
    if not best_db:
        # Find any database with data
        for db_path, label, info in found_databases:
            if not info.get("empty", False) and not info.get("error") and info.get("total_conversations", 0) > 0:
                best_db = (db_path, label)
                best_stats = info
                break
    
    if best_db:
        print(f"\n✅ Best database found:")
        print(f"   Location: {best_db[0]}")
        print(f"   Type: {best_db[1]}")
        print(f"   Conversations: {best_stats.get('total_conversations', 0)}")
        
        # If best database is not in canonical location, suggest moving it
        if best_db[0] != canonical_db:
            print(f"\n💡 Recommendation:")
            print(f"   Database should be moved to: {canonical_db}")
            print(f"   Run: python scripts/maintenance/fix_database_paths.py")
    else:
        print(f"\n⚠️  No usable database found")
        print(f"   Found databases but they're empty or corrupted")
    
    # Check GUI path specifically
    print(f"\n🖥️  GUI Database Path Check:")
    gui_path = project_root / "src" / "storage" / "conversations.db"
    print(f"   GUI will look for: {gui_path}")
    if gui_path.exists():
        print(f"   ❌ This is wrong location - GUI found database in wrong place")
    else:
        print(f"   ✅ GUI path doesn't exist (good - should use canonical location)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
