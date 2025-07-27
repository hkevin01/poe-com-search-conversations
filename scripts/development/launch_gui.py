#!/usr/bin/env python3
"""
GUI Launcher - Moved from run_gui.py in root
Simple script to launch the GUI application with automatic venv detection
"""

import sys
import os
import subprocess
import platform

# Get project root (three levels up from this script)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_venv():
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def activate_venv_and_rerun():
    """Activate virtual environment and rerun this script."""
    # Determine the correct activation script and python executable
    if platform.system() == "Windows":
        python_exe = os.path.join(PROJECT_ROOT, "venv", "Scripts", "python.exe")
        venv_check = os.path.join(PROJECT_ROOT, "venv", "Scripts")
    else:
        python_exe = os.path.join(PROJECT_ROOT, "venv", "bin", "python")
        venv_check = os.path.join(PROJECT_ROOT, "venv", "bin")
    
    # Check if virtual environment exists
    if not os.path.exists(venv_check):
        print("❌ Virtual environment not found!")
        print("\n💡 Please run the setup script first:")
        print("   python scripts/setup/create_environment.py")
        sys.exit(1)
    
    # Check if python executable exists in venv
    if not os.path.exists(python_exe):
        print("❌ Python executable not found in virtual environment!")
        print("Please recreate the virtual environment by running setup again.")
        sys.exit(1)
    
    print("🔧 Activating virtual environment and launching GUI...")
    
    # Re-run the actual GUI launcher with the virtual environment's Python
    try:
        gui_script = os.path.join(PROJECT_ROOT, "src", "gui", "main_window.py")
        result = subprocess.run([python_exe, gui_script], check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run GUI: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Python executable not found: {python_exe}")
        print("Please check your virtual environment setup.")
        sys.exit(1)

def main():
    """Main function to launch the GUI."""
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    # Check if we're in a virtual environment
    if not check_venv():
        print("⚠️  Not running in virtual environment, switching...")
        activate_venv_and_rerun()
        return  # This shouldn't be reached
    
    print("✅ Running in virtual environment")
    
    # Add src directory to path
    sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

    try:
        from gui.main_window import run_gui
        
        print("🚀 Starting Poe.com Conversation Manager GUI...")
        sys.exit(run_gui())
        
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        print("\n💡 This usually means PyQt6 is not installed in the virtual environment.")
        print("Please run the setup script:")
        print("   python scripts/setup/create_environment.py")
        print("\nOr manually install requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()