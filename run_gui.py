#!/usr/bin/env python3
"""
Quick GUI Launcher - Simple script to launch the GUI application
Automatically activates virtual environment if not already active
"""

import sys
import os
import subprocess
import platform

def check_venv():
    """Check if we're in a virtual environment."""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def activate_venv_and_rerun():
    """Activate virtual environment and rerun this script."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the correct activation script and python executable
    if platform.system() == "Windows":
        activate_script = os.path.join(project_root, "venv", "Scripts", "activate.bat")
        python_exe = os.path.join(project_root, "venv", "Scripts", "python.exe")
        venv_check = os.path.join(project_root, "venv", "Scripts")
    else:
        activate_script = os.path.join(project_root, "venv", "bin", "activate")
        python_exe = os.path.join(project_root, "venv", "bin", "python")
        venv_check = os.path.join(project_root, "venv", "bin")
    
    # Check if virtual environment exists
    if not os.path.exists(venv_check):
        print("❌ Virtual environment not found!")
        print("\n💡 Please run the setup script first:")
        if platform.system() == "Windows":
            print("   setup.bat")
        else:
            print("   ./setup.sh")
        print("   # or")
        print("   python setup.py")
        sys.exit(1)
    
    # Check if python executable exists in venv
    if not os.path.exists(python_exe):
        print("❌ Python executable not found in virtual environment!")
        print("Please recreate the virtual environment by running setup again.")
        sys.exit(1)
    
    print("🔧 Activating virtual environment and launching GUI...")
    
    # Re-run this script with the virtual environment's Python
    try:
        # Use the venv's python to run this script again
        result = subprocess.run([python_exe, __file__], check=True)
        sys.exit(result.returncode)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run with virtual environment: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Python executable not found: {python_exe}")
        print("Please check your virtual environment setup.")
        sys.exit(1)

def main():
    """Main function to launch the GUI."""
    # Check if we're in a virtual environment
    if not check_venv():
        print("⚠️  Not running in virtual environment, switching...")
        activate_venv_and_rerun()
        return  # This shouldn't be reached
    
    print("✅ Running in virtual environment")
    
    # Add src directory to path
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

    try:
        from gui.main_window import run_gui
        
        print("🚀 Starting Poe.com Conversation Manager GUI...")
        sys.exit(run_gui())
        
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        print("\n💡 This usually means PyQt6 is not installed in the virtual environment.")
        print("Please run the setup script again:")
        if platform.system() == "Windows":
            print("   setup.bat")
        else:
            print("   ./setup.sh")
        print("\nOr manually install requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()