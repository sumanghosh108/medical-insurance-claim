#!/usr/bin/env bash
# Deploy Lambda functions
# Usage: ./deploy_lambdas.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-ap-south-1}"

echo "=== Deploying Lambda Functions: ${ENVIRONMENT} ==="

FUNCTIONS=(
    "ingestion:src.lambda_functions.claim_ingestion_handler.lambda_handler"
    "extraction:src.lambda_functions.document_extraction_orchestrator.lambda_handler"
    "entity:src.lambda_functions.entity_extraction_processor.lambda_handler"
    "fraud:src.lambda_functions.fraud_detection_inference.lambda_handler"
    "workflow:src.lambda_functions.workflow_state_manager.lambda_handler"
)

# Package code
echo "[1/3] Packaging code..."
PACKAGE_DIR=$(mktemp -d)
cp -r src/ "${PACKAGE_DIR}/"
cp -r config/ "${PACKAGE_DIR}/"
pip install -r requirements.txt -t "${PACKAGE_DIR}/" --quiet

cd "${PACKAGE_DIR}"
zip -r9 "/tmp/lambda-package.zip" . -x "*.pyc" "__pycache__/*" > /dev/null
cd - > /dev/null
echo "  Package size: $(du -h /tmp/lambda-package.zip | cut -f1)"

# Deploy each function
echo "[2/3] Deploying functions..."
for func_entry in "${FUNCTIONS[@]}"; do
    FUNC_NAME="${func_entry%%:*}"
    HANDLER="${func_entry#*:}"
    FULL_NAME="${PROJECT_NAME}-${FUNC_NAME}-${ENVIRONMENT}"

    echo "  Deploying ${FULL_NAME}..."
    if aws lambda get-function --function-name "${FULL_NAME}" --region "${REGION}" 2>/dev/null; then
        aws lambda update-function-code \
            --function-name "${FULL_NAME}" \
            --zip-file "fileb:///tmp/lambda-package.zip" \
            --region "${REGION}" > /dev/null
        echo "    ✅ Updated"
    else
        echo "    ⚠️  Function not found — deploy via CloudFormation first."
    fi
done

# Cleanup
echo "[3/3] Cleaning up..."
rm -rf "${PACKAGE_DIR}" /tmp/lambda-package.zip

echo "=== Lambda Deployment Complete ==="
