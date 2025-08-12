#!/bin/bash

# Clean up moved shell scripts and Python files from root directory

echo "🧹 Cleaning up moved scripts and Python files from root directory..."

# List of shell scripts that were moved
OLD_SCRIPTS=(
    "verify-agent-settings.sh"
    "install-agent-settings-robust.sh" 
    "quick-fix-agent-settings.sh"
)

# List of Python files that were moved
OLD_PYTHON_FILES=(
    "check_database.py"
    "fix_database_paths.py"
    "fix_gui_database.py"
    "final_cleanup.py"
    "test_gui_imports.py"
    "test_login.py"
    "extract_now.py"
    "make_executable.py"
)

REMOVED=0

# Remove old shell scripts
for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "🗑️  Removing shell script: $script"
        rm "$script"
        REMOVED=$((REMOVED + 1))
    else
        echo "✅ Already clean: $script"
    fi
done

# Remove old Python files
for py_file in "${OLD_PYTHON_FILES[@]}"; do
    if [ -f "$py_file" ]; then
        echo "🗑️  Removing Python file: $py_file"
        rm "$py_file"
        REMOVED=$((REMOVED + 1))
    else
        echo "✅ Already clean: $py_file"
    fi
done

echo ""
echo "🎉 Cleanup complete! Removed $REMOVED old file(s) from root directory."
echo ""
echo "📁 Files are now organized in:"
echo "   • scripts/testing/ - Testing and verification scripts"
echo "   • scripts/setup/ - Installation and setup utilities"
echo "   • scripts/maintenance/ - Database and cleanup utilities"
echo "   • src/ - Main application code"
