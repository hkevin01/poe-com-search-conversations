#!/usr/bin/env python3
"""
Quick Setup Script - Python version for cross-platform compatibility
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
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
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"🐍 Python version: {python_version}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or later is required!")
        sys.exit(1)
    
    # Determine Python command
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    # Create virtual environment
    if not os.path.exists("venv"):
        print("📦 Creating virtual environment...")
        if not run_command(f"{python_cmd} -m venv venv", "Creating virtual environment"):
            sys.exit(1)
        print("✅ Virtual environment created")
    else:
        print("📦 Virtual environment already exists")
    
    # Determine activation command and pip path
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate.bat"
        pip_cmd = "venv\\Scripts\\pip.exe"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        print("⚠️  Warning: Could not upgrade pip, continuing anyway...")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        print("📋 Installing requirements...")
        if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
            print("❌ Failed to install requirements!")
            sys.exit(1)
        print("✅ Requirements installed successfully")
    else:
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Success message
    print("\n🎉 Setup complete!\n")
    
    print("To use the application:")
    
    if platform.system() == "Windows":
        print("  1. Activate the virtual environment:")
        print("     venv\\Scripts\\activate.bat")
        print("\n  2. Run the GUI application:")
        print("     python run_gui.py")
        print("\n  3. Or use the CLI:")
        print("     python src\\cli.py search \"your query\"")
        print("\n  4. For first-time setup, create your config file:")
        print("     copy config\\poe_tokens.json.example config\\poe_tokens.json")
    else:
        print("  1. Activate the virtual environment:")
        print("     source venv/bin/activate")
        print("\n  2. Run the GUI application:")
        print("     python run_gui.py")
        print("\n  3. Or use the CLI:")
        print("     python src/cli.py search 'your query'")
        print("\n  4. For first-time setup, create your config file:")
        print("     cp config/poe_tokens.json.example config/poe_tokens.json")
    
    print("     # Then edit config/poe_tokens.json with your Poe.com tokens")
    print("\n📚 See README.md for detailed usage instructions.")

if __name__ == "__main__":
    main()