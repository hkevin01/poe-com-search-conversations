#!/usr/bin/env python3
"""
Root Cleanup Script - Remove old files that were moved to organized directories
This script removes the old root-level Python files that have been moved to scripts/
"""

import os
import sys
from pathlib import Path

def main():
    """Clean up root directory by removing moved files."""
    # Get actual project root (three levels up from this script)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    print("🧹 Cleaning up root directory...")
    print("=" * 50)
    print(f"📁 Project root: {project_root}")
    print(f"📁 Script location: {script_path}")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Files to remove (these have been moved to scripts/)
    files_to_remove = [
        "setup.py",
        "setup.sh", 
        "setup.bat",
        "create_env.py",
        "activate.sh",
        "run_gui.py",
        "launch_with_data.py",
        "test_setup.py",
        "test_uniqueness.py",
        "update_paths.py"
    ]
    
    removed_count = 0
    kept_count = 0
    
    for filename in files_to_remove:
        filepath = project_root / filename
        
        if filepath.exists():
            try:
                filepath.unlink()
                print(f"🗑️  Removed: {filename}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {filename}: {e}")
                kept_count += 1
        else:
            print(f"⏭️  Not found: {filename} (already removed)")
    
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files removed: {removed_count}")
    print(f"   Files kept/failed: {kept_count}")
    
    # Show what's left in root
    print(f"\n📋 Remaining root-level files:")
    root_files = []
    for item in project_root.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            root_files.append(item.name)
    
    for filename in sorted(root_files):
        print(f"   📄 {filename}")
    
    print(f"\n✨ Root directory cleanup complete!")
    print(f"💡 Use the new launcher: python main.py --help")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())