#!/usr/bin/env bash
# Bootstrap AWS Deployment
# Prepares the environment (buckets) and triggers the full deployment.
# Usage: ./bootstrap_deployment.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-ap-south-1}"
TEMPLATE_BUCKET="${PROJECT_NAME}-templates"

echo "=== Bootstrapping Deployment for ${ENVIRONMENT} in ${REGION} ==="

# 1. Create Template Bucket
echo "[1/3] Ensuring template bucket exists: ${TEMPLATE_BUCKET}"
if aws s3api head-bucket --bucket "${TEMPLATE_BUCKET}" 2>/dev/null; then
    echo "  ✅ Bucket exists."
else
    echo "  Creating bucket..."
    aws s3api create-bucket --bucket "${TEMPLATE_BUCKET}" --region "${REGION}" \
        --create-bucket-configuration LocationConstraint="${REGION}" 2>/dev/null || \
    aws s3api create-bucket --bucket "${TEMPLATE_BUCKET}" --region "${REGION}"
    
    aws s3api put-bucket-versioning --bucket "${TEMPLATE_BUCKET}" \
        --versioning-configuration Status=Enabled
    echo "  ✅ Created bucket."
fi

# 2. Upload Templates (Pre-validation check)
echo "[2/3] Syncing templates..."
aws s3 sync infrastructure/templates/ "s3://${TEMPLATE_BUCKET}/templates/" --region "${REGION}"

# 3. Run Infrastructure Deployment
echo "[3/3] Launching infrastructure deployment..."
bash scripts/deploy_infrastructure.sh "${ENVIRONMENT}"

echo "=== Bootstrap Complete ==="
echo "If this was a fresh deployment, remember to:"
echo "1. Run database initialization scripts (printed in logs)."
echo "2. Configure any external secrets not managed by CloudFormation."
