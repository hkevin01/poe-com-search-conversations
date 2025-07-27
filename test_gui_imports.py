#!/usr/bin/env python3
"""
Quick GUI Test - Test if the GUI launches properly
"""

import sys
import os

def test_gui_import():
    """Test if GUI components can be imported."""
    try:
        # Add src to path
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        print("🧪 Testing GUI imports...")
        
        # Test PyQt6 import
        try:
            from PyQt6.QtWidgets import QApplication
            print("✅ PyQt6 is available")
        except ImportError as e:
            print(f"❌ PyQt6 import failed: {e}")
            return False
        
        # Test GUI module import
        try:
            from gui.main_window import run_gui, MainWindow
            print("✅ GUI modules imported successfully")
            print("✅ run_gui function found")
            print("✅ MainWindow class found")
        except ImportError as e:
            print(f"❌ GUI module import failed: {e}")
            return False
        
        # Test database import
        try:
            from database import ConversationDatabase
            print("✅ Database module imported successfully")
        except ImportError as e:
            print(f"❌ Database import failed: {e}")
            return False
        
        print("\n🎉 All GUI imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main test function."""
    print("🔧 GUI Import Test")
    print("=" * 30)
    
    success = test_gui_import()
    
    if success:
        print("\n✅ GUI is ready to launch!")
        print("💡 You can now run: python main.py launch")
    else:
        print("\n❌ GUI has import issues")
        print("💡 Try: pip install PyQt6")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())