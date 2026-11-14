#!/bin/bash

echo "Starting Khmer Dubbing Studio..."

# Check virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Virtual environment not found!"
    echo "Please run setup.sh first:"
    echo "  chmod +x setup.sh && ./setup.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Fix Qt display issues on some Linux systems
export QT_QPA_PLATFORM=xcb
export QT_XCB_NO_XI2=1

# Run the app
python main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Application exited with an error."
    echo "Check the error message above."
fi
