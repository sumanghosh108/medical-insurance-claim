-- ============================================================
-- View: Claims Summary
-- Comprehensive view joining claims with patient, hospital,
-- document, and fraud data for dashboards and reporting.
-- ============================================================

CREATE OR REPLACE VIEW v_claims_summary AS
SELECT
    c.id                AS claim_id,
    c.claim_number,
    c.claim_date,
    c.submission_date,
    c.status,
    c.priority,
    c.claim_amount,
    c.approval_amount,
    c.approval_date,
    c.treatment_type,
    c.diagnosis_code,
    c.procedure_code,
    c.rejection_reason,

    -- Patient info
    p.id                AS patient_id,
    p.mrn               AS patient_mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.date_of_birth     AS patient_dob,
    p.insurance_provider,
    p.insurance_id,

    -- Hospital info
    h.id                AS hospital_id,
    h.name              AS hospital_name,
    h.npi               AS hospital_npi,
    h.city              AS hospital_city,
    h.state             AS hospital_state,

    -- Fraud info
    fs.fraud_score,
    fs.is_fraud,
    fs.confidence       AS fraud_confidence,
    fs.risk_level       AS fraud_risk_level,
    fs.manual_review    AS fraud_manual_review,
    fs.manual_determination,
    fs.model_version    AS fraud_model_version,

    -- Document counts
    COALESCE(doc_stats.total_documents, 0)    AS total_documents,
    COALESCE(doc_stats.verified_documents, 0) AS verified_documents,

    -- Computed fields
    CASE
        WHEN c.approval_amount IS NOT NULL AND c.claim_amount > 0
        THEN ROUND((c.approval_amount / c.claim_amount * 100)::NUMERIC, 2)
        ELSE NULL
    END AS approval_percentage,

    EXTRACT(DAY FROM (COALESCE(c.approval_date, NOW()) - c.submission_date))
        AS days_in_pipeline,

    c.created_at,
    c.updated_at

FROM claims c
JOIN patients p  ON c.patient_id  = p.id
JOIN hospitals h ON c.hospital_id = h.id
LEFT JOIN fraud_scores fs ON fs.claim_id = c.id
LEFT JOIN (
    SELECT
        claim_id,
        COUNT(*)                           AS total_documents,
        COUNT(*) FILTER (WHERE is_verified) AS verified_documents
    FROM documents
    GROUP BY claim_id
) doc_stats ON doc_stats.claim_id = c.id;

-- Grant read access
GRANT SELECT ON v_claims_summary TO claims_readonly;

COMMENT ON VIEW v_claims_summary IS
    'Comprehensive claim view joining patient, hospital, document, and fraud data.';
