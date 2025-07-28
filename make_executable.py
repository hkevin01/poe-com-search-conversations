import os
import stat

# Make scripts executable
scripts = [
    "/home/kevin/Projects/poe-com-search-conversations/scripts/testing/verify-agent-settings.sh",
    "/home/kevin/Projects/poe-com-search-conversations/scripts/setup/install-agent-settings-robust.sh", 
    "/home/kevin/Projects/poe-com-search-conversations/scripts/maintenance/quick-fix-agent-settings.sh",
    "/home/kevin/Projects/poe-com-search-conversations/cleanup-old-scripts.sh"
]

for script_path in scripts:
    if os.path.exists(script_path):
        current_permissions = os.stat(script_path).st_mode
        os.chmod(script_path, current_permissions | stat.S_IEXEC)
        print(f"✅ Made {os.path.basename(script_path)} executable")
    else:
        print(f"❌ {script_path} not found")

# Also remove old scripts from root if they exist
old_scripts = [
    "/home/kevin/Projects/poe-com-search-conversations/verify-agent-settings.sh",
    "/home/kevin/Projects/poe-com-search-conversations/install-agent-settings-robust.sh",
    "/home/kevin/Projects/poe-com-search-conversations/quick-fix-agent-settings.sh"
]

removed = 0
for script in old_scripts:
    if os.path.exists(script):
        os.remove(script)
        print(f"🗑️  Removed old script: {os.path.basename(script)}")
        removed += 1

if removed > 0:
    print(f"\n🎉 Cleanup complete! Removed {removed} old script(s) from root directory.")
else:
    print("\n✅ Root directory already clean - no old scripts found.")
