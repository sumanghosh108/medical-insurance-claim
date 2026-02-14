-- ============================================================
-- Migration 004: Add Database Views
-- Creates reporting and analytical views.
-- ============================================================

BEGIN;

-- Import the view definitions
\i ../views/claims_summary.sql
\i ../views/fraud_statistics.sql
\i ../views/processing_metrics.sql

-- -----------------------------------------------------------
-- Record migration
-- -----------------------------------------------------------
INSERT INTO schema_migrations (version, description)
VALUES ('004', 'Add reporting views: claims_summary, fraud_statistics, processing_metrics')
ON CONFLICT (version) DO NOTHING;

COMMIT;
