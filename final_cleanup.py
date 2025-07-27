#!/usr/bin/env python3
"""
Comprehensive Root Cleanup - Remove all unnecessary files from root directory
This script will clean up the root and ensure only essential files remain.
"""

import os
import sys
from pathlib import Path

def main():
    """Comprehensive cleanup of root directory."""
    project_root = Path.cwd()
    
    print("🧹 Comprehensive Root Directory Cleanup")
    print("=" * 50)
    print(f"📁 Working directory: {project_root}")
    
    # Check if we're in the right directory
    if not (project_root / "main.py").exists():
        print("❌ Error: main.py not found!")
        print("Please run this script from the project root directory.")
        return 1
    
    # Files that should be removed
    files_to_remove = [
        # Old Python scripts (moved to scripts/)
        "setup.py",
        "create_env.py", 
        "run_gui.py",
        "launch_with_data.py",
        "test_setup.py",
        "test_uniqueness.py",
        "update_paths.py",
        "demo_database.py",
        
        # Shell scripts (kept in root but users should use main.py)
        "setup.sh",
        "setup.bat", 
        "activate.sh",
        
        # Database files (should be in storage/)
        "conversations.db",
        "conversations.sqlite",
        "conversations.sqlite3",
        
        # Cleanup utilities (temporary)
        "show_root_files.py",
        "cleanup_root_files.py",
        
        # Any other temp files
        "temp.py",
        "test.py",
        "scratch.py"
    ]
    
    # Files that should definitely stay
    essential_files = {
        "main.py",
        "README.md", 
        "requirements.txt",
        ".gitignore",
        "LICENSE"
    }
    
    print("\n🔍 Scanning for files to remove...")
    
    removed_count = 0
    moved_db_count = 0
    
    for filename in files_to_remove:
        filepath = project_root / filename
        
        if filepath.exists():
            # Special handling for database files - move to storage instead of delete
            if filename.endswith(('.db', '.sqlite', '.sqlite3')):
                storage_dir = project_root / "storage"
                storage_dir.mkdir(exist_ok=True)
                target_path = storage_dir / filename
                
                try:
                    if not target_path.exists():
                        filepath.rename(target_path)
                        print(f"📦 Moved to storage: {filename}")
                        moved_db_count += 1
                    else:
                        filepath.unlink()
                        print(f"🗑️  Removed duplicate: {filename}")
                        removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to handle {filename}: {e}")
            else:
                # Regular file removal
                try:
                    filepath.unlink()
                    print(f"🗑️  Removed: {filename}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove {filename}: {e}")
        else:
            print(f"⏭️  Not found: {filename}")
    
    # Check for any other Python files that might be clutter
    print(f"\n🔍 Checking for other Python files...")
    other_py_files = []
    
    for item in project_root.iterdir():
        if (item.is_file() and 
            item.suffix == '.py' and 
            item.name not in essential_files and
            item.name not in files_to_remove):
            other_py_files.append(item.name)
    
    if other_py_files:
        print(f"❓ Found additional Python files:")
        for filename in other_py_files:
            print(f"   - {filename}")
        print("   (Review these manually)")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files removed: {removed_count}")
    print(f"   Database files moved to storage: {moved_db_count}")
    print(f"   Additional Python files found: {len(other_py_files)}")
    
    # Show final root contents
    print(f"\n📋 Final root directory contents:")
    
    root_items = []
    for item in sorted(project_root.iterdir()):
        if item.is_file():
            status = "✅" if item.name in essential_files else "❓"
            root_items.append(f"   {status} {item.name}")
        elif item.is_dir() and not item.name.startswith('.'):
            root_items.append(f"   📁 {item.name}/")
    
    for item in root_items[:15]:  # Show first 15 items
        print(item)
    
    if len(root_items) > 15:
        print(f"   ... and {len(root_items) - 15} more items")
    
    print(f"\n✨ Root directory cleanup complete!")
    
    if removed_count > 0 or moved_db_count > 0:
        print("🎉 Cleanup successful! Root directory is now organized.")
        print("\n📝 Next steps:")
        print("   1. Test the application: python main.py test")
        print("   2. Launch with data: python main.py launch") 
    else:
        print("✅ Root directory was already clean!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())