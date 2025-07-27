#!/usr/bin/env python3
"""
Environment Creator and Requirement Installer
This script creates the virtual environment and installs requirements
"""

import os
import sys
import subprocess
import shutil

def create_venv_and_install():
    """Create virtual environment and install requirements."""
    project_root = "/home/kevin/Projects/poe-com-search-conversations"
    
    print("🚀 Creating virtual environment and installing requirements...")
    print("=" * 60)
    
    # Change to project directory
    os.chdir(project_root)
    print(f"📁 Working directory: {project_root}")
    
    # Remove existing venv if it exists
    if os.path.exists("venv"):
        print("🗑️  Removing existing virtual environment...")
        shutil.rmtree("venv")
    
    # Create virtual environment
    print("📦 Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
        python_path = os.path.join("venv", "Scripts", "python")
    else:  # Unix/Linux/Mac
        pip_path = os.path.join("venv", "bin", "pip")
        python_path = os.path.join("venv", "bin", "python")
    
    # Upgrade pip
    print("⬆️  Upgrading pip...")
    try:
        subprocess.run([python_path, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ Pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Could not upgrade pip: {e}")
    
    # Install requirements
    if os.path.exists("requirements.txt"):
        print("📋 Installing requirements from requirements.txt...")
        try:
            subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
            print("✅ Requirements installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    else:
        print("❌ requirements.txt not found!")
        return False
    
    # Verify key installations
    print("🔍 Verifying installations...")
    try:
        # Test PyQt6
        subprocess.run([python_path, "-c", "import PyQt6; print('PyQt6: OK')"], check=True)
        
        # Test Selenium
        subprocess.run([python_path, "-c", "import selenium; print('Selenium: OK')"], check=True)
        
        # Test other key packages
        subprocess.run([python_path, "-c", "import sqlite3; print('SQLite3: OK')"], check=True)
        
        print("✅ All key packages verified")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Some packages may not be properly installed: {e}")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate.bat")
    else:
        print("   source venv/bin/activate")
    
    print("2. Configure your tokens:")
    print("   cp config/poe_tokens.json.example config/poe_tokens.json")
    print("   # Edit config/poe_tokens.json with your Poe.com tokens")
    
    print("3. Run the application:")
    print("   python run_gui.py")
    
    return True

if __name__ == "__main__":
    success = create_venv_and_install()
    sys.exit(0 if success else 1)