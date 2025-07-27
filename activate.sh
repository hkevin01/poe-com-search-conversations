#!/bin/bash
# Quick activation script for the virtual environment

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run setup.sh first to create the environment."
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo ""
echo "Available commands:"
echo "  python run_gui.py                    # Launch GUI"
echo "  python src/cli.py search 'query'    # CLI search"
echo "  python src/enhanced_extractor.py    # Extract conversations"
echo "  python demo_database.py             # Database demo"
echo ""
echo "To deactivate when done: deactivate"

# Keep the shell active
exec bash