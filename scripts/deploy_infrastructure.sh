#!/usr/bin/env bash
# Deploy infrastructure via CloudFormation
# Usage: ./deploy_infrastructure.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-ap-south-1}"

echo "=== Deploying Infrastructure: ${ENVIRONMENT} ==="

# Step 1: Validate templates
echo "[1/4] Validating CloudFormation templates..."
bash infrastructure/scripts/validation_template.sh

# Step 2: Deploy CloudFormation stack
echo "[2/4] Deploying CloudFormation stack..."
cd infrastructure/scripts
bash deploy_stack.sh "${ENVIRONMENT}"
cd ../..

# Step 3: Initialize database
echo "[3/4] Running database migrations..."
RDS_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name "${PROJECT_NAME}-${ENVIRONMENT}" \
    --query "Stacks[0].Outputs[?OutputKey=='RDSEndpoint'].OutputValue" \
    --output text --region "${REGION}")
echo "  RDS Endpoint: ${RDS_ENDPOINT}"

if [ -n "${RDS_ENDPOINT}" ] && [ "${RDS_ENDPOINT}" != "None" ]; then
    echo "  Run database init manually:"
    echo "    psql -h ${RDS_ENDPOINT} -U postgres -f database/init.sql"
    echo "    psql -h ${RDS_ENDPOINT} -U postgres -d claims_db -f database/schema.sql"
fi

# Step 4: Deploy Lambda functions
echo "[4/4] Deploying Lambda functions..."
bash scripts/deploy_lambdas.sh "${ENVIRONMENT}"

echo "=== Infrastructure Deployment Complete ==="
