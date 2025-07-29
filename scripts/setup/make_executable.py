#!/usr/bin/env python3
"""
Make Scripts Executable - Setup utility for shell scripts
"""

import os
import stat
from pathlib import Path


def main():
    """Make all project scripts executable and clean up old files."""
    project_root = Path(__file__).parent.parent.parent
    
    print("🔧 Making Scripts Executable")
    print("=" * 30)
    
    # Make scripts executable
    scripts = [
        project_root / "scripts/testing/verify-agent-settings.sh",
        project_root / "scripts/setup/install-agent-settings-robust.sh",
        project_root / "scripts/maintenance/quick-fix-agent-settings.sh",
        project_root / "cleanup-old-scripts.sh"
    ]

    for script_path in scripts:
        if script_path.exists():
            current_permissions = script_path.stat().st_mode
            script_path.chmod(current_permissions | stat.S_IEXEC)
            print(f"✅ Made {script_path.name} executable")
        else:
            print(f"❌ {script_path} not found")

    # Remove old scripts from root if they exist
    old_scripts = [
        project_root / "verify-agent-settings.sh",
        project_root / "install-agent-settings-robust.sh",
        project_root / "quick-fix-agent-settings.sh"
    ]

    removed = 0
    for script in old_scripts:
        if script.exists():
            script.unlink()
            print(f"🗑️  Removed old script: {script.name}")
            removed += 1

    # Remove old Python files from root
    old_python_files = [
        project_root / "check_database.py",
        project_root / "fix_database_paths.py", 
        project_root / "fix_gui_database.py",
        project_root / "final_cleanup.py",
        project_root / "test_gui_imports.py",
        project_root / "test_login.py",
        project_root / "extract_now.py"
    ]
    
    py_removed = 0
    for py_file in old_python_files:
        if py_file.exists():
            py_file.unlink()
            print(f"🗑️  Removed old Python file: {py_file.name}")
            py_removed += 1

    print(f"\n📊 Summary:")
    if removed > 0:
        print(f"   Shell scripts removed: {removed}")
    if py_removed > 0:
        print(f"   Python files removed: {py_removed}")
    
    if removed > 0 or py_removed > 0:
        print(f"🎉 Cleanup complete! Root directory is now organized.")
    else:
        print("✅ Root directory already clean.")
    
    print(f"\n📁 Scripts are now organized in:")
    print(f"   • scripts/testing/")
    print(f"   • scripts/setup/")
    print(f"   • scripts/maintenance/")
    
    return 0


if __name__ == "__main__":
    exit(main())
