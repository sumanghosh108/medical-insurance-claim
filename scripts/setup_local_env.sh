#!/usr/bin/env bash
# Set up local development environment
# Usage: ./setup_local_env.sh

set -euo pipefail

echo "=== Setting Up Local Development Environment ==="

# Check Python
echo "[1/7] Checking Python..."
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python --version 2>&1)
echo "  Found: ${PYTHON_VERSION}"

# Create/activate virtual environment
echo "[2/7] Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "  Created venv."
fi
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
echo "  Activated: $(which python)"

# Install dependencies
echo "[3/7] Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .

# Copy env file
echo "[4/7] Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp config/dev.env .env
    echo "  Copied config/dev.env to .env"
else
    echo "  .env already exists, skipping."
fi

# Create directories
echo "[5/7] Creating directories..."
mkdir -p logs reports ml_models/model ml_models/models

# Install pre-commit hooks
echo "[6/7] Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "  Pre-commit hooks installed."
else
    echo "  WARN: pre-commit not found, skipping."
fi

# Check Docker
echo "[7/7] Checking Docker..."
if command -v docker &> /dev/null; then
    echo "  Docker found: $(docker --version)"
    echo "  Start services with: docker-compose up -d"
else
    echo "  WARN: Docker not installed. Install Docker Desktop for local DB."
fi

echo ""
echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Start database:  docker-compose up -d postgres"
echo "  2. Run tests:       pytest tests/unit/ -v"
echo "  3. Start API:       uvicorn src.api:app --reload"
