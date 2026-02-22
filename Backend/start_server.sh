#!/bin/bash
# Start script for MedCompanion server

set -e

echo "Starting MedCompanion Server..."
echo "================================"

# Check if virtual environment exists
if [ ! -d "medgemma-env" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: python3 -m venv medgemma-env"
    exit 1
fi

# Activate virtual environment
source medgemma-env/bin/activate

# Check if requirements are installed
echo "Checking dependencies..."
python -c "import fastapi" 2>/dev/null || {
    echo "Installing dependencies..."
    pip install -r requirements.txt
}

echo "Starting server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo "================================"
echo ""

# Set FORCE_CPU to avoid MPS threading issues (comment out to use MPS/GPU)
# export FORCE_CPU=true

# Start the server
python -m server.main
