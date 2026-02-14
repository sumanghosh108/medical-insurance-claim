#!/usr/bin/env bash
# Cleanup script — remove temp files, caches, and old artifacts
# Usage: ./cleanup.sh [--deep]

set -euo pipefail

DEEP="${1:-}"

echo "=== Project Cleanup ==="

# Python caches
echo "[1/6] Removing Python caches..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "  ✅ Python caches removed"

# Test artifacts
echo "[2/6] Removing test artifacts..."
rm -rf .pytest_cache htmlcov .coverage coverage.xml reports/ 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
echo "  ✅ Test artifacts removed"

# Build artifacts
echo "[3/6] Removing build artifacts..."
rm -rf build/ dist/ *.egg-info 2>/dev/null || true
rm -rf mlproject.egg-info/ 2>/dev/null || true
echo "  ✅ Build artifacts removed"

# Lint caches
echo "[4/6] Removing lint caches..."
rm -rf .mypy_cache .ruff_cache .dmypy.json 2>/dev/null || true
echo "  ✅ Lint caches removed"

# Logs
echo "[5/6] Cleaning logs..."
if [ "${DEEP}" = "--deep" ]; then
    rm -rf logs/*.log logs/*.json 2>/dev/null || true
    echo "  ✅ All logs removed (deep clean)"
else
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    echo "  ✅ Logs older than 7 days removed"
fi

# Docker (deep clean only)
echo "[6/6] Docker cleanup..."
if [ "${DEEP}" = "--deep" ]; then
    if command -v docker &> /dev/null; then
        docker system prune -f 2>/dev/null || true
        echo "  ✅ Docker resources pruned"
    else
        echo "  ⚠️  Docker not installed, skipping."
    fi
else
    echo "  Skipped (use --deep for Docker cleanup)"
fi

echo ""
echo "=== Cleanup Complete ==="
