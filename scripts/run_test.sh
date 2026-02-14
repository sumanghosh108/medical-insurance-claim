#!/usr/bin/env bash
# Run tests — wrapper for pytest with common configurations
# Usage: ./run_test.sh [unit|integration|smoke|load|all]

set -euo pipefail

TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

echo "=== Running Tests: ${TEST_TYPE} ==="

case "${TEST_TYPE}" in
    unit)
        echo "Running unit tests..."
        pytest tests/unit/ -v --tb=short \
            --cov=src --cov-report=term-missing \
            -m "not slow" ${EXTRA_ARGS}
        ;;

    integration)
        echo "Running integration tests..."
        pytest tests/integration/ -v --tb=short \
            -m integration ${EXTRA_ARGS}
        ;;

    smoke)
        echo "Running smoke tests..."
        pytest tests/smoke/ -v --tb=short \
            -m smoke ${EXTRA_ARGS}
        ;;

    load)
        echo "Running load tests..."
        if [ -z "${API_BASE_URL:-}" ]; then
            echo "WARNING: API_BASE_URL not set, using localhost:8000"
            export API_BASE_URL="http://localhost:8000"
        fi
        locust -f tests/load/locustfile.py \
            --host "${API_BASE_URL}" \
            --users 10 --spawn-rate 2 --run-time 1m \
            --headless \
            --csv=reports/load_test \
            --html=reports/load_test_report.html
        ;;

    all)
        echo "Running full test suite..."
        pytest tests/ -v --tb=short \
            --cov=src --cov-report=term-missing --cov-report=html \
            --junitxml=reports/junit.xml \
            ${EXTRA_ARGS}
        ;;

    *)
        echo "Usage: ./run_test.sh [unit|integration|smoke|load|all]"
        exit 1
        ;;
esac

echo "=== Tests Complete ==="
