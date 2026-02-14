#!/usr/bin/env bash
# Set up AWS environment (S3 buckets, DynamoDB tables, SNS topics)
# Usage: ./setup_aws_env.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-us-east-1}"

echo "=== Setting Up AWS Environment: ${ENVIRONMENT} ==="

# Verify AWS credentials
echo "[1/5] Verifying AWS credentials..."
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "  Account: ${AWS_ACCOUNT}"

# Create S3 buckets
echo "[2/5] Creating S3 buckets..."
for bucket in documents models results; do
    BUCKET_NAME="${PROJECT_NAME}-${bucket}-${ENVIRONMENT}"
    if aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>/dev/null; then
        echo "  Bucket ${BUCKET_NAME} already exists."
    else
        aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${REGION}" \
            --create-bucket-configuration LocationConstraint="${REGION}" 2>/dev/null || \
        aws s3api create-bucket --bucket "${BUCKET_NAME}" --region "${REGION}"
        aws s3api put-bucket-versioning --bucket "${BUCKET_NAME}" \
            --versioning-configuration Status=Enabled
        echo "  ✅ Created ${BUCKET_NAME}"
    fi
done

# Create DynamoDB tables
echo "[3/5] Creating DynamoDB tables..."
for table_suffix in metadata audit fraud-scores; do
    TABLE_NAME="${PROJECT_NAME}-${table_suffix}-${ENVIRONMENT}"
    if aws dynamodb describe-table --table-name "${TABLE_NAME}" --region "${REGION}" 2>/dev/null; then
        echo "  Table ${TABLE_NAME} already exists."
    else
        aws dynamodb create-table \
            --table-name "${TABLE_NAME}" \
            --attribute-definitions AttributeName=id,AttributeType=S \
            --key-schema AttributeName=id,KeyType=HASH \
            --billing-mode PAY_PER_REQUEST \
            --region "${REGION}" > /dev/null
        echo "  ✅ Created ${TABLE_NAME}"
    fi
done

# Create SNS topic
echo "[4/5] Creating SNS topic..."
TOPIC_NAME="${PROJECT_NAME}-alerts-${ENVIRONMENT}"
TOPIC_ARN=$(aws sns create-topic --name "${TOPIC_NAME}" --region "${REGION}" --query TopicArn --output text)
echo "  ✅ Topic: ${TOPIC_ARN}"

# Show summary
echo "[5/5] Summary:"
echo "  Region:   ${REGION}"
echo "  Account:  ${AWS_ACCOUNT}"
echo "  Env:      ${ENVIRONMENT}"
echo ""
echo "=== AWS Setup Complete ==="
