#!/bin/bash

echo "======================================"
echo "Code Fixing Agent - Setup Script"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "Installing requirements..."
pip install -r requirements.txt

# Check Docker
echo ""
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
    docker --version

    echo ""
    echo "Pulling Python Docker image..."
    docker pull python:3.10-slim
    echo "✓ Docker image ready"
else
    echo "⚠ Docker is not installed"
    echo "  The system will use subprocess for code execution"
    echo "  For better sandboxing, install Docker:"
    echo "  - macOS: brew install --cask docker"
    echo "  - Ubuntu: sudo apt-get install docker.io"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p data
mkdir -p results
echo "✓ Directories created"

# Setup complete
echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. (Optional) Set API keys for cloud LLMs:"
echo "   export OPENAI_API_KEY='your-key'"
echo "   export ANTHROPIC_API_KEY='your-key'"
echo ""
echo "3. Configure your LLM provider in config.py"
echo ""
echo "4. Run the evaluation:"
echo "   python main.py"
echo ""
echo "5. Or try the example:"
echo "   python example_usage.py"
echo ""
