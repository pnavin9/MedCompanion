#!/bin/bash
# Script to run MedASR tests in the medasr-test-env environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/medasr-test-env"
PYTHON_SCRIPT="$SCRIPT_DIR/test_medasr_direct.py"

echo "========================================"
echo "MedASR Test Runner"
echo "========================================"
echo ""

# Check if environment exists
if [ ! -d "$ENV_DIR" ]; then
    echo "❌ Error: medasr-test-env not found at $ENV_DIR"
    echo ""
    echo "Please create the environment first:"
    echo "  python3 -m venv medasr-test-env"
    echo "  source medasr-test-env/bin/activate"
    echo "  pip install torch transformers librosa soundfile torchaudio"
    echo "  pip install git+https://github.com/huggingface/transformers.git"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Test script not found at $PYTHON_SCRIPT"
    exit 1
fi

echo "✅ Found environment: $ENV_DIR"
echo "✅ Found test script: $PYTHON_SCRIPT"
echo ""

# Activate environment and run test
echo "Activating medasr-test-env..."
source "$ENV_DIR/bin/activate"

echo "Running MedASR tests..."
echo ""

python3 "$PYTHON_SCRIPT" "$@"

echo ""
echo "========================================"
echo "Test run completed"
echo "========================================"
