#!/bin/bash

echo "============================================================================"
echo "   AI STOCK PRICE PREDICTOR - SETUP SCRIPT"
echo "============================================================================"
echo ""

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi
python3 --version
echo "[OK] Python is installed"
echo ""

echo "[2/4] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi
echo "[OK] Virtual environment created"
echo ""

echo "[3/4] Activating virtual environment..."
source venv/bin/activate
echo "[OK] Virtual environment activated"
echo ""

echo "[4/4] Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo "[OK] All dependencies installed successfully"
echo ""

echo "============================================================================"
echo "   SETUP COMPLETE!"
echo "============================================================================"
echo ""
echo "To start the application:"
echo "  1. Run: ./start_app.sh"
echo "  2. Open browser: http://localhost:5000"
echo ""