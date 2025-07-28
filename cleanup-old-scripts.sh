#!/bin/bash

# Clean up moved shell scripts from root directory

echo "🧹 Cleaning up moved shell scripts from root directory..."

# List of scripts that were moved
OLD_SCRIPTS=(
    "verify-agent-settings.sh"
    "install-agent-settings-robust.sh" 
    "quick-fix-agent-settings.sh"
)

REMOVED=0

for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "🗑️  Removing: $script"
        rm "$script"
        REMOVED=$((REMOVED + 1))
    else
        echo "✅ Already clean: $script"
    fi
done

echo ""
echo "🎉 Cleanup complete! Removed $REMOVED old script(s) from root directory."
echo ""
echo "📁 Scripts are now organized in:"
echo "   • scripts/testing/verify-agent-settings.sh"
echo "   • scripts/setup/install-agent-settings-robust.sh"
echo "   • scripts/maintenance/quick-fix-agent-settings.sh"
