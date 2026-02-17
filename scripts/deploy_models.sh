#!/usr/bin/env bash
# Deploy ML models to SageMaker
# Usage: ./deploy_models.sh [environment] [model_version]

set -euo pipefail

ENVIRONMENT="${1:-development}"
MODEL_VERSION="${2:-v2.1.0}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-ap-south-1}"
MODEL_BUCKET="${PROJECT_NAME}-models-${ENVIRONMENT}"

echo "=== Deploying ML Models: ${MODEL_VERSION} (${ENVIRONMENT}) ==="

# Package model
echo "[1/4] Packaging model..."
MODEL_DIR="ml_models/model"
if [ ! -d "${MODEL_DIR}" ]; then
    echo "ERROR: Model directory '${MODEL_DIR}' not found."
    exit 1
fi

TARBALL="/tmp/model-${MODEL_VERSION}.tar.gz"
cd "${MODEL_DIR}"
tar -czf "${TARBALL}" .
cd - > /dev/null
echo "  Package: ${TARBALL} ($(du -h ${TARBALL} | cut -f1))"

# Upload to S3
echo "[2/4] Uploading to S3..."
S3_KEY="models/fraud/${MODEL_VERSION}.tar.gz"
aws s3 cp "${TARBALL}" "s3://${MODEL_BUCKET}/${S3_KEY}" --region "${REGION}"
echo "  ✅ Uploaded to s3://${MODEL_BUCKET}/${S3_KEY}"

# Update SageMaker endpoint
echo "[3/4] Updating SageMaker endpoint..."
ENDPOINT_NAME="fraud-detection-${ENVIRONMENT}"
if aws sagemaker describe-endpoint --endpoint-name "${ENDPOINT_NAME}" --region "${REGION}" 2>/dev/null; then
    echo "  Endpoint exists, updating model..."
    echo "  NOTE: Update SageMaker model & endpoint config via CloudFormation or console."
else
    echo "  ⚠️  Endpoint '${ENDPOINT_NAME}' not found."
    echo "  Deploy infrastructure first: ./deploy_infrastructure.sh ${ENVIRONMENT}"
fi

# Cleanup
echo "[4/4] Cleanup..."
rm -f "${TARBALL}"

echo "=== Model Deployment Complete ==="
