#!/usr/bin/env bash
# Deploy to ECS (Fargate)
# Usage: ./deploy_ecs.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-us-east-1}"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"

echo "=== Deploying to ECS: ${ENVIRONMENT} ==="

# Login to ECR
echo "[1/5] Logging into ECR..."
aws ecr get-login-password --region "${REGION}" | \
    docker login --username AWS --password-stdin "${ECR_REGISTRY}"

# Build image
echo "[2/5] Building Docker image..."
docker build -f docker/Dockerfile -t "${PROJECT_NAME}:${IMAGE_TAG}" .

# Tag and push
echo "[3/5] Pushing image to ECR..."
docker tag "${PROJECT_NAME}:${IMAGE_TAG}" "${ECR_REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}"
docker tag "${PROJECT_NAME}:${IMAGE_TAG}" "${ECR_REGISTRY}/${PROJECT_NAME}:latest"
docker push "${ECR_REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}"
docker push "${ECR_REGISTRY}/${PROJECT_NAME}:latest"

# Update ECS service
echo "[4/5] Updating ECS service..."
CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
SERVICE_NAME="${PROJECT_NAME}-api-${ENVIRONMENT}"

aws ecs update-service \
    --cluster "${CLUSTER_NAME}" \
    --service "${SERVICE_NAME}" \
    --force-new-deployment \
    --region "${REGION}" > /dev/null

# Wait for stability
echo "[5/5] Waiting for service to stabilize..."
aws ecs wait services-stable \
    --cluster "${CLUSTER_NAME}" \
    --services "${SERVICE_NAME}" \
    --region "${REGION}"

echo "=== ECS Deployment Complete ==="
echo "Image: ${ECR_REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}"
