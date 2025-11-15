#!/bin/bash
#
# Test runner for Linux Agentic Copilot
# Runs all tests with coverage reporting
#

set -e

echo "==================================="
echo "Linux Agentic Copilot - Test Suite"
echo "==================================="
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found, installing test dependencies..."
    pip install pytest pytest-asyncio pytest-cov
fi

echo ""
echo "Running tests..."
echo ""

# Run tests with coverage
pytest tests/ \
    -v \
    --cov=src \
    --cov-report=html \
    --cov-report=term \
    --asyncio-mode=auto

echo ""
echo "==================================="
echo "Test execution completed"
echo "==================================="
echo ""
echo "Coverage report generated in htmlcov/index.html"
echo ""
