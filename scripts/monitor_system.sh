#!/usr/bin/env bash
# Monitor system health
# Usage: ./monitor_system.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
PROJECT_NAME="claims-processing"
REGION="${AWS_REGION:-ap-south-1}"

echo "=== System Health Monitor: ${ENVIRONMENT} ==="
echo "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# 1. Lambda function status
echo "-- Lambda Functions --"
FUNCTIONS=("ingestion" "extraction" "entity" "fraud" "workflow")
for func in "${FUNCTIONS[@]}"; do
    FUNC_NAME="${PROJECT_NAME}-${func}-${ENVIRONMENT}"
    STATUS=$(aws lambda get-function --function-name "${FUNC_NAME}" \
        --query 'Configuration.State' --output text --region "${REGION}" 2>/dev/null || echo "NOT_FOUND")
    LAST_MODIFIED=$(aws lambda get-function --function-name "${FUNC_NAME}" \
        --query 'Configuration.LastModified' --output text --region "${REGION}" 2>/dev/null || echo "N/A")
    printf "  %-30s  Status: %-10s  Modified: %s\n" "${func}" "${STATUS}" "${LAST_MODIFIED}"
done
echo ""

# 2. RDS status
echo "-- RDS Database --"
DB_ID="${PROJECT_NAME}-${ENVIRONMENT}"
RDS_STATUS=$(aws rds describe-db-instances --db-instance-identifier "${DB_ID}" \
    --query 'DBInstances[0].DBInstanceStatus' --output text --region "${REGION}" 2>/dev/null || echo "NOT_FOUND")
RDS_CPU=$(aws cloudwatch get-metric-statistics \
    --namespace AWS/RDS --metric-name CPUUtilization \
    --dimensions Name=DBInstanceIdentifier,Value="${DB_ID}" \
    --start-time "$(date -u -d '5 minutes ago' '+%Y-%m-%dT%H:%M:%S')" \
    --end-time "$(date -u '+%Y-%m-%dT%H:%M:%S')" \
    --period 300 --statistics Average \
    --query 'Datapoints[0].Average' --output text --region "${REGION}" 2>/dev/null || echo "N/A")
echo "  Status: ${RDS_STATUS}"
echo "  CPU (5min avg): ${RDS_CPU}%"
echo ""

# 3. S3 bucket sizes
echo "-- S3 Buckets --"
for bucket_type in documents models results; do
    BUCKET="${PROJECT_NAME}-${bucket_type}-${ENVIRONMENT}"
    OBJ_COUNT=$(aws s3api list-objects-v2 --bucket "${BUCKET}" \
        --query 'KeyCount' --output text --region "${REGION}" 2>/dev/null || echo "N/A")
    printf "  %-40s  Objects: %s\n" "${BUCKET}" "${OBJ_COUNT}"
done
echo ""

# 4. Recent Lambda errors
echo "-- Recent Errors (last 15 min) --"
for func in "${FUNCTIONS[@]}"; do
    FUNC_NAME="${PROJECT_NAME}-${func}-${ENVIRONMENT}"
    ERRORS=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/Lambda --metric-name Errors \
        --dimensions Name=FunctionName,Value="${FUNC_NAME}" \
        --start-time "$(date -u -d '15 minutes ago' '+%Y-%m-%dT%H:%M:%S')" \
        --end-time "$(date -u '+%Y-%m-%dT%H:%M:%S')" \
        --period 900 --statistics Sum \
        --query 'Datapoints[0].Sum' --output text --region "${REGION}" 2>/dev/null || echo "0")
    if [ "${ERRORS}" != "0" ] && [ "${ERRORS}" != "None" ] && [ "${ERRORS}" != "N/A" ]; then
        echo "  WARNING: ${func}: ${ERRORS} errors"
    fi
done
echo "  (no errors shown = all clear)"
echo ""
echo "=== Health Check Complete ==="
