#!/bin/bash

echo "=========================================="
echo "Local Data Extractor - Setup Script"
echo "=========================================="
echo ""

# Check if Ollama is installed
echo "[1/5] Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama is not installed locally. Downloading and installing..."
    curl -fsSL https://ollama.ai/install.sh | sh
    if ! command -v ollama &> /dev/null; then
        echo "❌ Failed to automatically install Ollama. Please install manually if needed."
        echo "If you plan to use a remote Ollama, you can ignore this."
    else
        echo "✅ Ollama installed successfully"
    fi
else
    echo "✅ Ollama is installed"
fi

# Check if Ollama is running
echo ""
echo "[2/5] Checking if local Ollama server is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "⚠️  Local Ollama server is not running or not accessible."
    echo "If you are using a local instance, please start Ollama with: ollama serve"
    echo "If you are using a remote instance, ensure it is properly configured in the .env file later."
else
    echo "✅ Ollama server is running"
fi

# Model configuration details
echo ""
echo "[3/5] Model Configuration..."
echo "ℹ️  No models are downloaded automatically by this setup."
echo "If you use a remote Ollama, ensure your models are available there."
echo "For local execution, we recommend downloading a model from the qwen3.5 family,"
echo "choosing a size appropriate for your hardware capacity (e.g. smaller sizes if you don't have a GPU)."
echo "Example: ollama pull qwen! (replace with the exact model name and tag)"

# Check Python dependencies
echo ""
echo "[4/5] Setting up Python environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
fi

# Check if we're already in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not activated."
    echo "Please run: source .venv/bin/activate"
    echo "Then install dependencies with: pip install -r requirements.txt"
else
    echo "Installing Python dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ Python dependencies installed"
    else
        echo "❌ Failed to install Python dependencies"
        exit 1
    fi
fi

# Check for poppler (required for pdf2image)
echo ""
echo "[5/5] Checking poppler-utils (required for PDF processing)..."
if ! command -v pdftoppm &> /dev/null; then
    echo "⚠️  poppler-utils not found."
    echo "Please install it:"
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS: brew install poppler"
    echo "  Fedora: sudo dnf install poppler-utils"
else
    echo "✅ poppler-utils is installed"
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
fi

echo ""
echo "=========================================="
echo "✅ Setup complete!"
echo "=========================================="
echo ""
if [ -z "$VIRTUAL_ENV" ]; then
    echo "To start the application:"
    echo "  1. Activate virtual environment: source .venv/bin/activate"
    echo "  2. Run the app: python src/app.py"
    echo "  3. Open browser at: http://localhost:5000"
else
    echo "Virtual environment is active!"
    echo "To start the application:"
    echo "  1. Run the app: python src/app.py"
    echo "  2. Open browser at: http://localhost:5000"
fi
echo ""
