#!/bin/bash
# AI Dev Agent - Quick Setup Script

echo "🤖 AI Dev Agent Setup"
echo "====================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OpenAI API key"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Quick start:"
echo "  source venv/bin/activate"
echo "  python -m src.cli.main status"
echo "  python -m src.cli.main index"
echo "  python -m src.cli.main chat"
