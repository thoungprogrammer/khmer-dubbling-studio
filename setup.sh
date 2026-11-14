#!/bin/bash

echo "====================================================="
echo "   Khmer Dubbing Studio - Linux Setup"
echo "====================================================="
echo ""

# Check Python 3.11
if ! python3.11 --version &>/dev/null; then
    echo "ERROR: Python 3.11 not found!"
    echo ""
    echo "Install it with:"
    echo "  Ubuntu/Debian : sudo apt install python3.11 python3.11-venv python3.11-dev"
    echo "  Fedora        : sudo dnf install python3.11 python3.11-devel"
    exit 1
fi

echo "[1/4] Python 3.11 found: $(python3.11 --version)"

# Check FFmpeg
if ! ffmpeg -version &>/dev/null; then
    echo "ERROR: FFmpeg not found!"
    echo ""
    echo "Install it with:"
    echo "  Ubuntu/Debian : sudo apt install ffmpeg"
    echo "  Fedora        : sudo dnf install ffmpeg"
    exit 1
fi

echo "[2/4] FFmpeg found: $(ffmpeg -version 2>&1 | head -1)"

# Create virtual environment
echo "[3/4] Creating virtual environment..."
python3.11 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment."
    exit 1
fi

# Activate and install dependencies
echo "[4/4] Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "====================================================="
echo "   Setup Complete!"
echo "====================================================="
echo ""
echo "To run the application:"
echo "  ./run.sh"
echo ""
