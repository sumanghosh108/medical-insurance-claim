-- ============================================================
-- Insurance Claims Processing System — Full Database Schema
-- Database: PostgreSQL 14+
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================
-- 1. Users Table
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    username        VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50)  NOT NULL DEFAULT 'user',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_admin        BOOLEAN      NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMP    NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email    UNIQUE (email)
);


-- ============================================================
-- 2. Patients Table
-- ============================================================
CREATE TABLE IF NOT EXISTS patients (
    id                  VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    mrn                 VARCHAR(50)  NOT NULL,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    date_of_birth       TIMESTAMP    NOT NULL,
    gender              VARCHAR(10)  NULL,
    email               VARCHAR(255) NULL,
    phone               VARCHAR(20)  NULL,
    address             TEXT         NULL,
    city                VARCHAR(100) NULL,
    state               VARCHAR(50)  NULL,
    zip_code            VARCHAR(10)  NULL,
    insurance_provider  VARCHAR(255) NULL,
    insurance_id        VARCHAR(100) NULL,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_patients_mrn UNIQUE (mrn)
);


-- ============================================================
-- 3. Hospitals Table
-- ============================================================
CREATE TABLE IF NOT EXISTS hospitals (
    id                  VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    name                VARCHAR(255) NOT NULL,
    npi                 VARCHAR(50)  NOT NULL,
    address             TEXT         NOT NULL,
    city                VARCHAR(100) NOT NULL,
    state               VARCHAR(50)  NOT NULL,
    zip_code            VARCHAR(10)  NOT NULL,
    phone               VARCHAR(20)  NULL,
    email               VARCHAR(255) NULL,
    license_number      VARCHAR(100) NOT NULL,
    accreditation_level VARCHAR(50)  NULL,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_hospitals_name    UNIQUE (name),
    CONSTRAINT uq_hospitals_npi     UNIQUE (npi),
    CONSTRAINT uq_hospitals_license UNIQUE (license_number)
);


-- ============================================================
-- 4. Claims Table
-- ============================================================
CREATE TABLE IF NOT EXISTS claims (
    id                VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    claim_number      VARCHAR(50)  NOT NULL,
    patient_id        VARCHAR(36)  NOT NULL,
    hospital_id       VARCHAR(36)  NOT NULL,
    claim_amount      FLOAT        NOT NULL,
    treatment_type    VARCHAR(100) NOT NULL,
    diagnosis_code    VARCHAR(20)  NOT NULL,
    procedure_code    VARCHAR(20)  NULL,
    claim_date        TIMESTAMP    NOT NULL,
    service_date      TIMESTAMP    NOT NULL,
    submission_date   TIMESTAMP    NOT NULL DEFAULT NOW(),
    status            VARCHAR(50)  NOT NULL DEFAULT 'SUBMITTED',
    priority          VARCHAR(20)  NOT NULL DEFAULT 'NORMAL',
    approval_amount   FLOAT        NULL,
    approval_date     TIMESTAMP    NULL,
    rejection_reason  TEXT         NULL,
    processing_notes  TEXT         NULL,
    metadata          JSONB        NULL,
    created_at        TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_claims_number        UNIQUE (claim_number),
    CONSTRAINT ck_claim_amount_positive CHECK  (claim_amount > 0),
    CONSTRAINT fk_claims_patient       FOREIGN KEY (patient_id)  REFERENCES patients(id) ON DELETE CASCADE,
    CONSTRAINT fk_claims_hospital      FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);


-- ============================================================
-- 5. Documents Table
-- ============================================================
CREATE TABLE IF NOT EXISTS documents (
    id                  VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    claim_id            VARCHAR(36)  NOT NULL,
    document_type       VARCHAR(50)  NOT NULL,
    file_name           VARCHAR(255) NOT NULL,
    s3_key              VARCHAR(500) NOT NULL,
    file_size           INTEGER      NOT NULL,
    mime_type           VARCHAR(100) NOT NULL,
    ocr_text            TEXT         NULL,
    is_verified         BOOLEAN      NOT NULL DEFAULT FALSE,
    verification_user   VARCHAR(255) NULL,
    verification_notes  TEXT         NULL,
    upload_user         VARCHAR(255) NULL,
    uploaded_at         TIMESTAMP    NOT NULL DEFAULT NOW(),
    verified_at         TIMESTAMP    NULL,
    created_at          TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_documents_s3_key UNIQUE (s3_key),
    CONSTRAINT fk_documents_claim  FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);


-- ============================================================
-- 6. Fraud Scores Table
-- ============================================================
CREATE TABLE IF NOT EXISTS fraud_scores (
    id                   VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    claim_id             VARCHAR(36)  NOT NULL,
    model_version        VARCHAR(20)  NOT NULL,
    fraud_score          FLOAT        NOT NULL,
    is_fraud             BOOLEAN      NOT NULL DEFAULT FALSE,
    confidence           FLOAT        NOT NULL,
    risk_level           VARCHAR(20)  NOT NULL DEFAULT 'LOW',
    risk_factors         JSONB        NULL,
    feature_importance   JSONB        NULL,
    model_inputs         JSONB        NULL,
    processing_time_ms   INTEGER      NULL,
    reviewed_by          VARCHAR(255) NULL,
    manual_review        BOOLEAN      NOT NULL DEFAULT FALSE,
    manual_determination VARCHAR(20)  NULL,
    review_notes         TEXT         NULL,
    reviewed_at          TIMESTAMP    NULL,
    created_at           TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_fraud_scores_claim UNIQUE (claim_id),
    CONSTRAINT fk_fraud_scores_claim FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);


-- ============================================================
-- Trigger: Auto-update updated_at on row changes
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT unnest(ARRAY['users','patients','hospitals','claims','documents','fraud_scores'])
    LOOP
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON %I
             FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();',
            tbl, tbl
        );
    END LOOP;
END;
$$;
