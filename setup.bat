@echo off
REM Setup script for Poe.com Conversation Manager (Windows)
REM Creates virtual environment and installs dependencies

echo 🚀 Setting up Poe.com Conversation Manager...
echo ================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.8 or later and try again.
    pause
    exit /b 1
)

REM Show Python version
echo 🐍 Python version:
python --version

REM Create virtual environment
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo 📦 Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📋 Installing requirements...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Requirements installed successfully
) else (
    echo ❌ requirements.txt not found!
    pause
    exit /b 1
)

echo.
echo 🎉 Setup complete!
echo.
echo To use the application:
echo   1. Activate the virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Run the GUI application:
echo      python run_gui.py
echo.
echo   3. Or use the CLI:
echo      python src\cli.py search "your query"
echo.
echo   4. For first-time setup, create your config file:
echo      copy config\poe_tokens.json.example config\poe_tokens.json
echo      REM Then edit config\poe_tokens.json with your Poe.com tokens
echo.
echo 📚 See README.md for detailed usage instructions.
pause