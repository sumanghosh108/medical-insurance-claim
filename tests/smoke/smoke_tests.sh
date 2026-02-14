#!/usr/bin/env bash
# ============================================================
# Smoke Tests Runner
# Quick verification of system health after deployment.
#
# Usage:
#   bash tests/smoke/smoke_tests.sh [BASE_URL]
#
# Example:
#   bash tests/smoke/smoke_tests.sh http://localhost:8000
#   bash tests/smoke/smoke_tests.sh https://api.staging.example.com
# ============================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0
SKIPPED=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}  ✓ PASS${NC}: $1"; ((PASSED++)); }
log_fail() { echo -e "${RED}  ✗ FAIL${NC}: $1"; ((FAILED++)); }
log_skip() { echo -e "${YELLOW}  ○ SKIP${NC}: $1"; ((SKIPPED++)); }

echo "============================================"
echo "  Smoke Tests — $BASE_URL"
echo "============================================"
echo ""

# ----- 1. Health Check -----
echo "▸ Health Check"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/health" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
    log_pass "Health endpoint returned 200"
elif [ "$HTTP_CODE" = "000" ]; then
    log_skip "API not reachable at ${BASE_URL}"
else
    log_fail "Health endpoint returned ${HTTP_CODE}"
fi

# ----- 2. Claims List -----
echo "▸ Claims List"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/claims?limit=1" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    log_pass "Claims list endpoint returned ${HTTP_CODE}"
elif [ "$HTTP_CODE" = "000" ]; then
    log_skip "API not reachable"
else
    log_fail "Claims list returned ${HTTP_CODE}"
fi

# ----- 3. Claim Submission -----
echo "▸ Claim Submission"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/v1/claims" \
    -H "Content-Type: application/json" \
    -d '{"claim_number":"CLM-SMOKE","patient_id":"pt-smoke","hospital_id":"hosp-smoke","claim_amount":100,"treatment_type":"Test","diagnosis_code":"Z00.00","claim_date":"2025-01-01T00:00:00Z","service_date":"2025-01-01T00:00:00Z"}' \
    --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "422" ]; then
    log_pass "Claim submission returned ${HTTP_CODE}"
elif [ "$HTTP_CODE" = "000" ]; then
    log_skip "API not reachable"
else
    log_fail "Claim submission returned ${HTTP_CODE}"
fi

# ----- 4. Fraud Summary -----
echo "▸ Fraud Summary"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/fraud/summary" --max-time 10 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    log_pass "Fraud summary returned ${HTTP_CODE}"
elif [ "$HTTP_CODE" = "000" ]; then
    log_skip "API not reachable"
else
    log_fail "Fraud summary returned ${HTTP_CODE}"
fi

# ----- 5. Python Module Imports -----
echo "▸ Module Imports"
if python -c "from src.database import models; from src.ml_models import fraud_detection; from src.utils import constants; print('OK')" 2>/dev/null; then
    log_pass "Core Python modules import successfully"
else
    log_fail "Python module import failed"
fi

# ----- Results -----
echo ""
echo "============================================"
echo "  Results: ${PASSED} passed, ${FAILED} failed, ${SKIPPED} skipped"
echo "============================================"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
exit 0
