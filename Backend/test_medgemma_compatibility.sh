#!/bin/bash
# Test if MedGemma can run in the medasr-test-env environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_DIR="$SCRIPT_DIR/medasr-test-env"
PYTHON_SCRIPT="$SCRIPT_DIR/test_medgemma_in_medasr_env.py"

echo "========================================"
echo "MedGemma Compatibility Test"
echo "========================================"
echo ""
echo "Testing if MedGemma can run in medasr-test-env..."
echo ""

# Check if environment exists
if [ ! -d "$ENV_DIR" ]; then
    echo "❌ Error: medasr-test-env not found at $ENV_DIR"
    exit 1
fi

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: Test script not found at $PYTHON_SCRIPT"
    exit 1
fi

# Activate environment and run test
source "$ENV_DIR/bin/activate"

echo "Running compatibility test..."
echo ""

python3 "$PYTHON_SCRIPT"

exit_code=$?

echo ""
echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo "✅ Test passed: Both models compatible!"
else
    echo "❌ Test failed: Models incompatible"
fi
echo "========================================"

exit $exit_code
