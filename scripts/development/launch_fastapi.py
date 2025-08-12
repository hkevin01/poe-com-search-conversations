#!/usr/bin/env python3
"""
FastAPI Launch Script for Poe.com Conversation Search Tool
Legacy launcher - use 'python main.py launch' or './run.sh' instead
"""
import os
import subprocess
import sys
from pathlib import Path


def main():
    """Launch the FastAPI web application"""
    # Ensure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Check if virtual environment exists
    if not Path('venv').exists():
        print("Setting up virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'])

        # Install requirements
        if os.name == 'nt':  # Windows
            pip_path = 'venv/Scripts/pip'
        else:  # Linux/Mac
            pip_path = 'venv/bin/pip'

        subprocess.run([pip_path, 'install', '-r', 'requirements.txt'])

    # Launch FastAPI
    if os.name == 'nt':  # Windows
        python_path = 'venv/Scripts/python'
    else:  # Linux/Mac
        python_path = 'venv/bin/python'

    print("Launching FastAPI server...")
    print("Access the application at: http://localhost:8000")

    subprocess.run([
        python_path, '-m', 'uvicorn',
        'src.fastapi_gui:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ])


if __name__ == "__main__":
    main()
