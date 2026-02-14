#!/usr/bin/env bash
# Restore PostgreSQL database from backup
# Usage: ./restore_database.sh <backup_file> [environment]

set -euo pipefail

BACKUP_FILE="${1:-}"
ENVIRONMENT="${2:-development}"

if [ -z "${BACKUP_FILE}" ]; then
    echo "Usage: ./restore_database.sh <backup_file> [environment]"
    echo ""
    echo "Available backups:"
    ls -lth backups/claims_db_*.sql.gz 2>/dev/null || echo "  No local backups found."
    exit 1
fi

if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Load env
if [ -f "config/${ENVIRONMENT}.env" ]; then
    set -a; source "config/${ENVIRONMENT}.env"; set +a
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-claims_db}"
DB_USER="${DB_USER:-postgres}"

echo "=== Database Restore: ${ENVIRONMENT} ==="
echo "  Backup:   ${BACKUP_FILE}"
echo "  Host:     ${DB_HOST}:${DB_PORT}"
echo "  Database: ${DB_NAME}"

# Safety check
if [ "${ENVIRONMENT}" = "production" ]; then
    echo ""
    echo "⚠️  WARNING: Restoring to PRODUCTION database!"
    read -p "Type 'RESTORE' to confirm: " confirm
    if [ "${confirm}" != "RESTORE" ]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create backup of current state first
echo "[1/3] Creating pre-restore backup..."
PGPASSWORD="${DB_PASSWORD:-Admin}" pg_dump \
    -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
    --format=custom 2>/dev/null | gzip > "backups/pre_restore_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz" || true

# Terminate existing connections
echo "[2/3] Terminating existing connections..."
PGPASSWORD="${DB_PASSWORD:-Admin}" psql \
    -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" 2>/dev/null || true

# Restore
echo "[3/3] Restoring database..."
gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${DB_PASSWORD:-Admin}" pg_restore \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --clean \
    --if-exists \
    --no-owner \
    --verbose 2>/dev/null || true

echo "=== Restore Complete ==="
echo "Verify: psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -c 'SELECT COUNT(*) FROM claims;'"
