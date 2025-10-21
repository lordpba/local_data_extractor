#!/bin/bash

echo "=========================================="
echo "Local Data Extractor - Setup Script"
echo "=========================================="
echo ""

# Check if Ollama is installed
echo "[1/5] Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo "Please install Ollama from: https://ollama.ai"
    echo "Or run: curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
else
    echo "✅ Ollama is installed"
fi

# Check if Ollama is running
echo ""
echo "[2/5] Checking if Ollama server is running..."
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "❌ Ollama server is not running."
    echo "Please start Ollama with: ollama serve"
    exit 1
else
    echo "✅ Ollama server is running"
fi

# Pull the multimodal model
echo ""
echo "[3/5] Pulling multimodal model (llama3.2-vision)..."
echo "This may take a while depending on your internet connection..."
ollama pull llama3.2-vision

if [ $? -eq 0 ]; then
    echo "✅ Model pulled successfully"
else
    echo "❌ Failed to pull model"
    exit 1
fi

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
    echo "  2. Run the app: python app.py"
    echo "  3. Open browser at: http://localhost:5000"
else
    echo "Virtual environment is active!"
    echo "To start the application:"
    echo "  1. Run the app: python app.py"
    echo "  2. Open browser at: http://localhost:5000"
fi
echo ""
