#!/usr/bin/env python3
"""
Update Project Paths - Script to update all hardcoded paths to correct project location
"""

import os
import re

def update_file_paths(file_path, old_path, new_path):
    """Update paths in a specific file."""
    if not os.path.exists(file_path):
        print(f"⚠️  File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace old path with new path
        updated_content = content.replace(old_path, new_path)
        
        # Also handle expanduser versions
        old_expanduser = f'os.path.expanduser("~/Projects/poe-search/'
        new_expanduser = f'os.path.expanduser("~/Projects/poe-com-search-conversations/'
        updated_content = updated_content.replace(old_expanduser, new_expanduser)
        
        if updated_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Updated paths in: {file_path}")
            return True
        else:
            print(f"📝 No changes needed in: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def main():
    """Update all project paths."""
    project_root = "/home/kevin/Projects/poe-com-search-conversations"
    old_project_path = "/home/kevin/Projects/poe-search"
    new_project_path = "/home/kevin/Projects/poe-com-search-conversations"
    
    print("🔧 Updating project paths...")
    print("=" * 50)
    
    # Files to update
    files_to_update = [
        "src/enhanced_extractor.py",
        "src/quick_list_conversations.py", 
        "src/cli.py",
        "src/database.py",
        "demo_database.py",
        "run_gui.py",
        "README.md",
        "docs/DEVELOPMENT.md",
        "docs/WORKFLOW.md"
    ]
    
    updated_count = 0
    
    for file_path in files_to_update:
        full_path = os.path.join(project_root, file_path)
        if update_file_paths(full_path, old_project_path, new_project_path):
            updated_count += 1
    
    print(f"\n🎉 Updated {updated_count} files")
    print(f"📁 Project location: {new_project_path}")
    print(f"🔑 Token file: {new_project_path}/config/poe_tokens.json")

if __name__ == "__main__":
    main()