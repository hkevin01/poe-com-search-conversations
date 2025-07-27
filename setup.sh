#!/bin/bash
# Setup script for Poe.com Conversation Manager
# Creates virtual environment and installs dependencies

set -e  # Exit on any error

echo "🚀 Setting up Poe.com Conversation Manager..."
echo "================================================"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or later and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python version: $PYTHON_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📦 Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing requirements..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Requirements installed successfully"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo ""
echo "🎉 Setup complete! "
echo ""
echo "To use the application:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Run the GUI application:"
echo "     python run_gui.py"
echo ""
echo "  3. Or use the CLI:"
echo "     python src/cli.py search 'your query'"
echo ""
echo "  4. For first-time setup, create your config file:"
echo "     cp config/poe_tokens.json.example config/poe_tokens.json"
echo "     # Then edit config/poe_tokens.json with your Poe.com tokens"
echo "     # See config/README.md for detailed token extraction instructions"
echo ""
echo "📚 See README.md for detailed usage instructions."