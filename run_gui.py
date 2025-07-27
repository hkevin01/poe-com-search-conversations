#!/usr/bin/env python3
"""
Quick GUI Launcher - Simple script to launch the GUI application
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from gui.main_window import run_gui
    
    if __name__ == "__main__":
        print("🚀 Starting Poe.com Conversation Manager GUI...")
        sys.exit(run_gui())
        
except ImportError as e:
    print(f"❌ Failed to import GUI components: {e}")
    print("\n💡 Make sure PyQt6 is installed:")
    print("   pip install PyQt6")
    print("\nOr install all requirements:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting GUI: {e}")
    sys.exit(1)