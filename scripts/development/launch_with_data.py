#!/usr/bin/env python3
"""
Launch with Data - Moved from root directory
Ensures database is populated before launching GUI
"""

import os
import sys
import subprocess
import argparse

# Get project root (three levels up from this script)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add src directory to path
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

try:
    from database import ConversationDatabase
except ImportError:
    # Fallback - we'll handle this in the functions
    ConversationDatabase = None

def check_database_content(db_path):
    """Check if database has conversations."""
    try:
        if not os.path.exists(db_path):
            return False, 0
        
        if ConversationDatabase is None:
            # Import failed, assume empty
            return False, 0
        
        db = ConversationDatabase(db_path)
        stats = db.get_stats()
        return stats['total_conversations'] > 0, stats['total_conversations']
    except Exception as e:
        print(f"⚠️  Database check failed: {e}")
        return False, 0

def run_quick_getter(limit=10):
    """Run the quick conversation getter to populate database."""
    print(f"📊 Populating database with {limit} conversations...")
    
    try:
        getter_script = os.path.join(PROJECT_ROOT, "src", "quick_conversation_getter.py")
        
        # Run the getter script from project root
        result = subprocess.run([
            sys.executable, getter_script, 
            "--limit", str(limit)
        ], check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        
        print("✅ Database populated successfully")
        # Show last few lines of output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines[-3:]:
            if line.strip():
                print(f"   {line}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to populate database: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout[-500:])  # Last 500 chars
        if e.stderr:
            print("STDERR:", e.stderr[-500:])
        return False
    except Exception as e:
        print(f"❌ Error running getter: {e}")
        return False

def launch_gui():
    """Launch the GUI application."""
    print("🚀 Launching GUI application...")
    
    try:
        gui_launcher = os.path.join(PROJECT_ROOT, "scripts", "development", "launch_gui.py")
        
        # Launch GUI (don't capture output, let it run normally)
        result = subprocess.run([sys.executable, gui_launcher], cwd=PROJECT_ROOT)
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        return False

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(description="Launch GUI with Data Population")
    parser.add_argument(
        "--skip-populate", action="store_true",
        help="Skip database population, launch GUI directly"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=10,
        help="Number of conversations to populate (default: 10)"
    )
    parser.add_argument(
        "--force-populate", action="store_true",
        help="Force population even if database has content"
    )
    
    args = parser.parse_args()
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    print("🎯 Poe.com Conversation Manager - Smart Launcher")
    print("=" * 55)
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Database path
    db_path = os.path.join(PROJECT_ROOT, "storage", "conversations.db")
    print(f"💾 Database: {db_path}")
    
    # Check if we need to populate database
    has_data, count = check_database_content(db_path)
    
    if not args.skip_populate:
        if not has_data or args.force_populate:
            status = "is empty" if not has_data else "forced refresh"
            print(f"📊 Database {status}")
            print(f"🔄 Populating with {args.limit} conversations...")
            
            if not run_quick_getter(args.limit):
                print("❌ Failed to populate database")
                print("💡 You can try launching the GUI anyway with:")
                print("   python scripts/development/launch_gui.py")
                return 1
        else:
            print(f"✅ Database has {count} conversations, skipping population")
    else:
        print("⏩ Skipping database population as requested")
    
    # Launch GUI
    print("\n" + "=" * 55)
    success = launch_gui()
    
    if not success:
        print("❌ GUI launch failed")
        print("💡 Try running manually:")
        print("   python scripts/development/launch_gui.py")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        sys.exit(1)