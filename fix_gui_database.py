#!/usr/bin/env python3
"""
Fix GUI Database Path - Remove wrong database and ensure GUI uses correct location
"""

import os
import sys
from pathlib import Path

def main():
    """Fix the database path issue."""
    project_root = Path.cwd()
    
    print("🔧 Fixing GUI Database Path Issue")
    print("=" * 50)
    print(f"📁 Project root: {project_root}")
    
    # Paths
    good_db = project_root / "storage" / "conversations.db"
    wrong_db = project_root / "src" / "storage" / "conversations.db"
    wrong_storage_dir = project_root / "src" / "storage"
    
    print(f"\n📊 Current Status:")
    print(f"   Good database: {good_db}")
    print(f"   - Exists: {'✅ Yes' if good_db.exists() else '❌ No'}")
    if good_db.exists():
        print(f"   - Size: {good_db.stat().st_size:,} bytes")
    
    print(f"\n   Wrong database: {wrong_db}")
    print(f"   - Exists: {'✅ Yes' if wrong_db.exists() else '❌ No'}")
    if wrong_db.exists():
        print(f"   - Size: {wrong_db.stat().st_size:,} bytes")
    
    # Fix 1: Remove the empty database in wrong location
    if wrong_db.exists():
        try:
            wrong_db.unlink()
            print(f"\n🗑️  Removed empty database from wrong location")
        except Exception as e:
            print(f"\n❌ Failed to remove wrong database: {e}")
            return 1
    
    # Fix 2: Remove the wrong storage directory if it's empty
    if wrong_storage_dir.exists():
        try:
            if not any(wrong_storage_dir.iterdir()):  # Directory is empty
                wrong_storage_dir.rmdir()
                print(f"🗑️  Removed empty src/storage/ directory")
            else:
                print(f"⚠️  src/storage/ directory not empty, keeping it")
        except Exception as e:
            print(f"⚠️  Could not remove src/storage/ directory: {e}")
    
    # Fix 3: Verify the good database
    if not good_db.exists():
        print(f"\n❌ ERROR: Good database not found at {good_db}")
        print("💡 Run: python main.py launch --force-populate")
        return 1
    
    # Test database connection
    print(f"\n🧪 Testing database connection...")
    try:
        sys.path.append(str(project_root / "src"))
        from database import ConversationDatabase
        
        db = ConversationDatabase(str(good_db))
        stats = db.get_stats()
        
        print(f"   ✅ Database connection successful")
        print(f"   📊 Stats: {stats['total_conversations']} conversations, {stats['total_messages']} messages")
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return 1
    
    print(f"\n🎉 Database path fixes complete!")
    print(f"✅ GUI will now use: {good_db}")
    print(f"✅ Database has {stats['total_conversations']} conversations ready to view")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Test the GUI: python main.py gui")
    print(f"   2. Or launch with data check: python main.py launch")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())