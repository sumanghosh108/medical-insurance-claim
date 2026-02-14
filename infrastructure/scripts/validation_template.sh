#!/usr/bin/env bash
# Validate all CloudFormation templates
# Usage: ./validation_template.sh

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
TEMPLATE_DIR="$(dirname "$0")/../templates"
ERRORS=0

echo "=== Validating CloudFormation Templates ==="

# Validate master template
echo "[INFO] Validating cloudformation.yaml..."
if aws cloudformation validate-template \
    --template-body "file://$(dirname "$0")/../cloudformation.yaml" \
    --region "${REGION}" > /dev/null 2>&1; then
    echo "  ✅ cloudformation.yaml — VALID"
else
    echo "  ❌ cloudformation.yaml — INVALID"
    ERRORS=$((ERRORS + 1))
fi

# Validate nested templates
for template in "${TEMPLATE_DIR}"/*.yaml; do
    name=$(basename "${template}")
    echo "[INFO] Validating ${name}..."
    if aws cloudformation validate-template \
        --template-body "file://${template}" \
        --region "${REGION}" > /dev/null 2>&1; then
        echo "  ✅ ${name} — VALID"
    else
        echo "  ❌ ${name} — INVALID"
        aws cloudformation validate-template \
            --template-body "file://${template}" \
            --region "${REGION}" 2>&1 || true
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
if [ "${ERRORS}" -eq 0 ]; then
    echo "=== All templates valid ✅ ==="
else
    echo "=== ${ERRORS} template(s) failed validation ❌ ==="
    exit 1
fi
