-- ============================================================
-- Migration 002: Add Performance Indexes
-- Adds indexes for common query patterns and search operations.
-- ============================================================

BEGIN;

-- -----------------------------------------------------------
-- Users indexes
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_user_username   ON users (username);
CREATE INDEX IF NOT EXISTS ix_user_email      ON users (email);
CREATE INDEX IF NOT EXISTS ix_user_role       ON users (role);
CREATE INDEX IF NOT EXISTS ix_user_active     ON users (is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- Patients indexes
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_patient_mrn     ON patients (mrn);
CREATE INDEX IF NOT EXISTS ix_patient_name    ON patients (first_name, last_name);
CREATE INDEX IF NOT EXISTS ix_patient_email   ON patients (email);
CREATE INDEX IF NOT EXISTS ix_patient_active  ON patients (is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS ix_patient_insurance ON patients (insurance_provider)
    WHERE insurance_provider IS NOT NULL;

-- -----------------------------------------------------------
-- Hospitals indexes
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_hospital_name     ON hospitals (name);
CREATE INDEX IF NOT EXISTS ix_hospital_npi      ON hospitals (npi);
CREATE INDEX IF NOT EXISTS ix_hospital_license  ON hospitals (license_number);
CREATE INDEX IF NOT EXISTS ix_hospital_state    ON hospitals (state);
CREATE INDEX IF NOT EXISTS ix_hospital_active   ON hospitals (is_active) WHERE is_active = TRUE;

-- -----------------------------------------------------------
-- Claims indexes (high-traffic table)
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_claim_number      ON claims (claim_number);
CREATE INDEX IF NOT EXISTS ix_claim_patient     ON claims (patient_id);
CREATE INDEX IF NOT EXISTS ix_claim_hospital    ON claims (hospital_id);
CREATE INDEX IF NOT EXISTS ix_claim_status      ON claims (status);
CREATE INDEX IF NOT EXISTS ix_claim_date        ON claims (claim_date);
CREATE INDEX IF NOT EXISTS ix_claim_submission  ON claims (submission_date);
CREATE INDEX IF NOT EXISTS ix_claim_priority    ON claims (priority);
CREATE INDEX IF NOT EXISTS ix_claim_diagnosis   ON claims (diagnosis_code);
CREATE INDEX IF NOT EXISTS ix_claim_treatment   ON claims (treatment_type);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_claim_status_date
    ON claims (status, claim_date DESC);

CREATE INDEX IF NOT EXISTS ix_claim_patient_status
    ON claims (patient_id, status);

CREATE INDEX IF NOT EXISTS ix_claim_hospital_status
    ON claims (hospital_id, status);

CREATE INDEX IF NOT EXISTS ix_claim_amount_range
    ON claims (claim_amount)
    WHERE claim_amount >= 10000;

-- Partial index for pending/processing claims (most queried)
CREATE INDEX IF NOT EXISTS ix_claim_pending
    ON claims (submission_date DESC)
    WHERE status IN ('SUBMITTED', 'PROCESSING');

-- -----------------------------------------------------------
-- Documents indexes
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_document_claim    ON documents (claim_id);
CREATE INDEX IF NOT EXISTS ix_document_type     ON documents (document_type);
CREATE INDEX IF NOT EXISTS ix_document_s3       ON documents (s3_key);
CREATE INDEX IF NOT EXISTS ix_document_unverified
    ON documents (claim_id)
    WHERE is_verified = FALSE;

-- -----------------------------------------------------------
-- Fraud Scores indexes
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_fraud_claim       ON fraud_scores (claim_id);
CREATE INDEX IF NOT EXISTS ix_fraud_score       ON fraud_scores (fraud_score);
CREATE INDEX IF NOT EXISTS ix_fraud_flag        ON fraud_scores (is_fraud);
CREATE INDEX IF NOT EXISTS ix_fraud_level       ON fraud_scores (risk_level);
CREATE INDEX IF NOT EXISTS ix_fraud_model       ON fraud_scores (model_version);

-- High-risk claims fast lookup
CREATE INDEX IF NOT EXISTS ix_fraud_high_risk
    ON fraud_scores (fraud_score DESC)
    WHERE fraud_score >= 0.7;

-- Pending review
CREATE INDEX IF NOT EXISTS ix_fraud_pending_review
    ON fraud_scores (created_at DESC)
    WHERE manual_review = TRUE AND manual_determination IS NULL;

-- -----------------------------------------------------------
-- Record migration
-- -----------------------------------------------------------
INSERT INTO schema_migrations (version, description)
VALUES ('002', 'Add performance indexes for all tables')
ON CONFLICT (version) DO NOTHING;

COMMIT;
