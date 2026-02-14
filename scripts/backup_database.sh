#!/usr/bin/env bash
# Backup PostgreSQL database
# Usage: ./backup_database.sh [environment]

set -euo pipefail

ENVIRONMENT="${1:-development}"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/claims_db_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"

# Load env
if [ -f "config/${ENVIRONMENT}.env" ]; then
    set -a; source "config/${ENVIRONMENT}.env"; set +a
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-claims_db}"
DB_USER="${DB_USER:-postgres}"

echo "=== Database Backup: ${ENVIRONMENT} ==="
echo "  Host: ${DB_HOST}:${DB_PORT}"
echo "  Database: ${DB_NAME}"

mkdir -p "${BACKUP_DIR}"

# Create backup
echo "[1/3] Creating backup..."
PGPASSWORD="${DB_PASSWORD:-Admin}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    --verbose \
    2>/dev/null | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "  ✅ Backup: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Upload to S3 (if AWS configured)
echo "[2/3] Uploading to S3..."
S3_BUCKET="claims-processing-backups-${ENVIRONMENT}"
if aws s3 ls "s3://${S3_BUCKET}" 2>/dev/null; then
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/db-backups/$(basename ${BACKUP_FILE})"
    echo "  ✅ Uploaded to s3://${S3_BUCKET}/"
else
    echo "  ⚠️  S3 bucket not found, skipping upload."
fi

# Cleanup old local backups (keep last 7)
echo "[3/3] Cleaning up old backups..."
ls -t "${BACKUP_DIR}"/claims_db_*.sql.gz 2>/dev/null | tail -n +8 | xargs rm -f
REMAINING=$(ls "${BACKUP_DIR}"/claims_db_*.sql.gz 2>/dev/null | wc -l)
echo "  Local backups retained: ${REMAINING}"

echo "=== Backup Complete ==="
