#!/usr/bin/env python3
"""
Environment Setup Script - Moved from root
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import platform

# Get project root (two levels up from this script)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"   {e.stderr.strip()}")
        return False

def main():
    """Main setup function."""
    print("🚀 Setting up Poe.com Conversation Manager...")
    print("=" * 50)
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    # Change to project root
    os.chdir(PROJECT_ROOT)
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"🐍 Python version: {python_version}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or later is required!")
        return 1
    
    # Determine Python command
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    # Create virtual environment
    if not os.path.exists("venv"):
        print("📦 Creating virtual environment...")
        if not run_command(f"{python_cmd} -m venv venv", "Creating virtual environment"):
            return 1
        print("✅ Virtual environment created")
    else:
        print("📦 Virtual environment already exists")
    
    # Determine pip path
    if platform.system() == "Windows":
        pip_cmd = "venv\\Scripts\\pip.exe"
    else:
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        print("⚠️  Warning: Could not upgrade pip, continuing anyway...")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        print("📋 Installing requirements...")
        if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
            print("❌ Failed to install requirements!")
            return 1
        print("✅ Requirements installed successfully")
    else:
        print("❌ requirements.txt not found!")
        return 1
    
    # Success message
    print("\n🎉 Setup complete!\n")
    
    print("To use the application:")
    
    if platform.system() == "Windows":
        print("  1. Activate the virtual environment:")
        print("     venv\\Scripts\\activate.bat")
        print("\n  2. Run the GUI application:")
        print("     python scripts/development/launch_gui.py")
        print("\n  3. Or populate database and launch:")
        print("     python scripts/development/launch_with_data.py")
    else:
        print("  1. Activate the virtual environment:")
        print("     source venv/bin/activate")
        print("\n  2. Run the GUI application:")
        print("     python scripts/development/launch_gui.py")
        print("\n  3. Or populate database and launch:")
        print("     python scripts/development/launch_with_data.py")
    
    print("\n  4. For first-time setup, create your config file:")
    print("     cp config/poe_tokens.json.example config/poe_tokens.json")
    print("     # Then edit config/poe_tokens.json with your Poe.com tokens")
    print("\n📚 See README.md for detailed usage instructions.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())