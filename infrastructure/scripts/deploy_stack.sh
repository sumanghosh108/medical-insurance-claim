#!/usr/bin/env bash
# Deploy CloudFormation stack
# Usage: ./deploy_stack.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
TEMPLATE_FILE="../cloudformation.yaml"
PARAMS_FILE="../parameters.json"
REGION="${AWS_REGION:-ap-south-1}"

echo "=== Deploying ${STACK_NAME} to ${REGION} ==="

# Upload nested templates to S3
TEMPLATE_BUCKET="${PROJECT_NAME}-templates"
echo "[1/4] Uploading templates to s3://${TEMPLATE_BUCKET}/"
aws s3 sync ../templates/ "s3://${TEMPLATE_BUCKET}/templates/" --region "${REGION}"

# Validate main template
echo "[2/4] Validating template..."
aws cloudformation validate-template \
    --template-body "file://${TEMPLATE_FILE}" \
    --region "${REGION}"

# Deploy/Update stack
echo "[3/4] Deploying stack..."
aws cloudformation deploy \
    --stack-name "${STACK_NAME}" \
    --template-file "${TEMPLATE_FILE}" \
    --parameter-overrides "file://${PARAMS_FILE}" \
    --capabilities CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND \
    --region "${REGION}" \
    --tags \
        "Project=${PROJECT_NAME}" \
        "Environment=${ENVIRONMENT}" \
    --no-fail-on-empty-changeset

# Show outputs
echo "[4/4] Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${REGION}" \
    --query "Stacks[0].Outputs" \
    --output table

echo "=== Deployment complete ==="
