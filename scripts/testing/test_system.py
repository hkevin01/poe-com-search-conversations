#!/usr/bin/env python3
"""
Database Test Suite - Moved from test_setup.py in root
Comprehensive testing for database functionality and setup verification
"""

import os
import sys
from datetime import datetime

# Get project root (three levels up from this script)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add src to path
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

try:
    from database import ConversationDatabase, Conversation
except ImportError as e:
    print(f"❌ Failed to import database module: {e}")
    print("Make sure you're running from the project root with proper setup.")
    sys.exit(1)

def test_database():
    """Test database functionality."""
    print("🧪 Testing Database Functionality")
    print("=" * 40)
    
    # Test database path
    db_path = os.path.join(PROJECT_ROOT, "storage", "conversations.db")
    print(f"💾 Database path: {db_path}")
    
    # Create storage directory
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        # Initialize database
        db = ConversationDatabase(db_path)
        print("✅ Database initialized successfully")
        
        # Get stats
        stats = db.get_stats()
        print("📊 Current stats:")
        print(f"   Total conversations: {stats['total_conversations']}")
        print(f"   Unique bots: {stats['unique_bots']}")
        print(f"   Total messages: {stats['total_messages']}")
        
        if stats['total_conversations'] == 0:
            print("\n💡 Database is empty. You can populate it with:")
            print("   python scripts/development/populate_database.py")
            print("   # or")
            print("   python scripts/development/launch_with_data.py")
        else:
            print("\n✅ Database has content!")
            
            # Show recent conversations
            recent = db.get_recent_conversations(3)
            print("\n📋 Recent conversations:")
            for i, conv in enumerate(recent, 1):
                title_short = conv.title[:50] + "..." if len(conv.title) > 50 else conv.title
                print(f"   {i}. {title_short}")
                print(f"      Bot: {conv.bot_name}, Messages: {conv.message_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_quick_getter():
    """Test if quick_conversation_getter can run."""
    print("\n🔧 Testing Quick Conversation Getter")
    print("=" * 40)
    
    getter_path = os.path.join(PROJECT_ROOT, "src", "quick_conversation_getter.py")
    config_path = os.path.join(PROJECT_ROOT, "config", "poe_tokens.json")
    
    if not os.path.exists(getter_path):
        print(f"❌ Getter script not found: {getter_path}")
        return False
    
    if not os.path.exists(config_path):
        print(f"❌ Config file not found: {config_path}")
        print("💡 Create config file:")
        print("   cp config/poe_tokens.json.example config/poe_tokens.json")
        print("   # Then edit with your Poe.com tokens")
        return False
    
    print(f"✅ Getter script found: {getter_path}")
    print(f"✅ Config file found: {config_path}")
    
    # Test dry run (just check imports)
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-c", 
            f"import sys; sys.path.append('{os.path.join(PROJECT_ROOT, 'src')}'); "
            "import quick_conversation_getter; print('✅ Imports successful')"
        ], capture_output=True, text=True, timeout=10, cwd=PROJECT_ROOT)
        
        if result.returncode == 0:
            print("✅ Quick getter imports successfully")
            return True
        else:
            print(f"❌ Quick getter import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Quick getter test failed: {e}")
        return False

def test_gui_imports():
    """Test if GUI components can be imported."""
    print("\n🖥️  Testing GUI Components")
    print("=" * 40)
    
    try:
        # Test PyQt6 import
        import subprocess
        result = subprocess.run([
            sys.executable, "-c", 
            "import PyQt6; print('✅ PyQt6 available')"
        ], capture_output=True, text=True, timeout=10, cwd=PROJECT_ROOT)
        
        if result.returncode == 0:
            print("✅ PyQt6 is available")
            
            # Test GUI module import
            gui_result = subprocess.run([
                sys.executable, "-c",
                f"import sys; sys.path.append('{os.path.join(PROJECT_ROOT, 'src')}'); "
                "from gui.main_window import MainWindow; print('✅ GUI imports successful')"
            ], capture_output=True, text=True, timeout=10, cwd=PROJECT_ROOT)
            
            if gui_result.returncode == 0:
                print("✅ GUI components import successfully")
                return True
            else:
                print(f"❌ GUI import failed: {gui_result.stderr}")
                return False
        else:
            print("❌ PyQt6 not available - GUI will not work")
            print("💡 Install PyQt6: pip install PyQt6")
            return False
            
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🎯 Poe.com Conversation Manager - System Test Suite")
    print("=" * 60)
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    # Run tests
    db_ok = test_database()
    getter_ok = test_quick_getter()
    gui_ok = test_gui_imports()
    
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print(f"   Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"   Quick Getter: {'✅ OK' if getter_ok else '❌ FAILED'}")
    print(f"   GUI Components: {'✅ OK' if gui_ok else '❌ FAILED'}")
    
    if db_ok and getter_ok and gui_ok:
        print("\n🎉 All tests passed! Ready to use:")
        print("   python scripts/development/launch_with_data.py")
        print("   # or")
        print("   python scripts/development/launch_gui.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\n💡 Common solutions:")
        print("   - Run setup: python scripts/setup/create_environment.py")
        print("   - Activate venv: source venv/bin/activate (Linux/Mac)")
        print("   - Check config: ls -la config/poe_tokens.json")
    
    return 0 if (db_ok and getter_ok) else 1

if __name__ == "__main__":
    sys.exit(main())