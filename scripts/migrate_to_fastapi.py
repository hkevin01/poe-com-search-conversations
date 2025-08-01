"""
Migration script to update the project from PyQt6 to FastAPI
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path


def update_requirements():
    """Update requirements.txt for FastAPI"""
    requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
aiofiles==23.2.1
selenium==4.15.0
webdriver-manager==4.0.1
beautifulsoup4==4.12.2
requests==2.31.0
'''

    with open('requirements_fastapi.txt', 'w') as f:
        f.write(requirements.strip())


def create_launch_script():
    """Create a new launch script for FastAPI"""
    launch_script = '''#!/usr/bin/env python3
"""
FastAPI Launch Script for Poe.com Conversation Search Tool
"""
import subprocess
import sys
import os
from pathlib import Path


def main():
    """Launch the FastAPI web application"""
    # Ensure we're in the right directory
    os.chdir(Path(__file__).parent)

    # Install requirements if needed
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("Installing FastAPI dependencies...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements_fastapi.txt'
        ], check=True)

    # Launch FastAPI
    print("Launching FastAPI server...")
    print("Access the application at: http://localhost:8000")

    subprocess.run([
        sys.executable, '-m', 'uvicorn',
        'src.fastapi_gui:app',
        '--host', '0.0.0.0',
        '--port', '8000',
        '--reload'
    ], check=False)


if __name__ == "__main__":
    main()
'''

    with open('launch_fastapi.py', 'w') as f:
        f.write(launch_script)

    # Make executable on Unix systems
    if os.name != 'nt':
        os.chmod('launch_fastapi.py', 0o755)


def update_main_py():
    """Update main.py to include FastAPI options"""
    main_update = '''
# Add to main.py after existing commands

elif command == "web":
    """Launch FastAPI web interface"""
    try:
        from src.fastapi_gui import app
        import uvicorn

        print("Starting FastAPI web server...")
        print("Access at: http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("FastAPI dependencies not installed.")
        print("Run: pip install -r requirements_fastapi.txt")
        sys.exit(1)

elif command == "setup-web":
    """Setup for web interface"""
    from src.fastapi_gui import create_templates
    create_templates()
    print("Web interface templates created successfully!")
'''

    print("Add the following to your main.py file:")
    print(main_update)


def create_docker_support():
    """Create Docker files for deployment"""
    dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements_fastapi.txt .
RUN pip install --no-cache-dir -r requirements_fastapi.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.fastapi_gui:app", "--host", "0.0.0.0", "--port", "8000"]
'''

    docker_compose = '''version: '3.8'

services:
  poe-search:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./storage:/app/storage
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app
'''

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile)

    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)


def main():
    """Run the migration"""
    print("🚀 Migrating Poe.com Search Tool to FastAPI...")

    # Update requirements
    print("📦 Updating requirements...")
    update_requirements()

    # Create launch script
    print("🔧 Creating launch script...")
    create_launch_script()

    # Update main.py instructions
    print("📝 Main.py update instructions...")
    update_main_py()

    # Create Docker support
    print("🐳 Creating Docker files...")
    create_docker_support()

    print("\n✅ Migration complete!")
    print("\n📋 Next steps:")
    print("1. Install new requirements: pip install -r requirements_fastapi.txt")
    print("2. Run the web interface: python launch_fastapi.py")
    print("3. Access at: http://localhost:8000")
    print("4. Configure authentication in the Settings page")


if __name__ == "__main__":
    main()
