-- ============================================================
-- View: Fraud Statistics
-- Aggregated fraud detection metrics for analytics dashboards.
-- ============================================================

-- Per-claim fraud detail
CREATE OR REPLACE VIEW v_fraud_detail AS
SELECT
    fs.id               AS fraud_id,
    fs.claim_id,
    c.claim_number,
    c.claim_amount,
    c.treatment_type,
    c.diagnosis_code,
    c.status            AS claim_status,

    p.first_name || ' ' || p.last_name AS patient_name,
    p.insurance_provider,

    h.name              AS hospital_name,
    h.state             AS hospital_state,

    fs.fraud_score,
    fs.is_fraud,
    fs.confidence,
    fs.risk_level,
    fs.risk_factors,
    fs.model_version,
    fs.processing_time_ms,
    fs.manual_review,
    fs.manual_determination,
    fs.reviewed_by,
    fs.reviewed_at,

    fs.created_at       AS scored_at

FROM fraud_scores fs
JOIN claims c    ON c.id  = fs.claim_id
JOIN patients p  ON p.id  = c.patient_id
JOIN hospitals h ON h.id  = c.hospital_id;


-- Overall fraud summary statistics
CREATE OR REPLACE VIEW v_fraud_summary AS
SELECT
    COUNT(*)                                          AS total_scored,
    COUNT(*) FILTER (WHERE is_fraud)                  AS total_flagged,
    COUNT(*) FILTER (WHERE risk_level = 'CRITICAL')   AS critical_count,
    COUNT(*) FILTER (WHERE risk_level = 'HIGH')       AS high_count,
    COUNT(*) FILTER (WHERE risk_level = 'MEDIUM')     AS medium_count,
    COUNT(*) FILTER (WHERE risk_level = 'LOW')        AS low_count,

    ROUND(AVG(fraud_score)::NUMERIC, 4)               AS avg_fraud_score,
    ROUND(MAX(fraud_score)::NUMERIC, 4)               AS max_fraud_score,
    ROUND(MIN(fraud_score)::NUMERIC, 4)               AS min_fraud_score,
    ROUND(STDDEV(fraud_score)::NUMERIC, 4)            AS stddev_fraud_score,

    ROUND(AVG(confidence)::NUMERIC, 4)                AS avg_confidence,
    ROUND(AVG(processing_time_ms)::NUMERIC, 0)        AS avg_processing_ms,

    COUNT(*) FILTER (WHERE manual_review)              AS pending_reviews,
    COUNT(*) FILTER (WHERE manual_determination IS NOT NULL) AS completed_reviews,

    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_fraud) / NULLIF(COUNT(*), 0), 2
    ) AS fraud_rate_pct

FROM fraud_scores;


-- Fraud stats by hospital
CREATE OR REPLACE VIEW v_fraud_by_hospital AS
SELECT
    h.id                  AS hospital_id,
    h.name                AS hospital_name,
    h.state               AS hospital_state,
    COUNT(*)              AS total_claims_scored,
    COUNT(*) FILTER (WHERE fs.is_fraud) AS fraud_count,
    ROUND(AVG(fs.fraud_score)::NUMERIC, 4)  AS avg_fraud_score,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE fs.is_fraud) / NULLIF(COUNT(*), 0), 2
    ) AS fraud_rate_pct,
    SUM(c.claim_amount) FILTER (WHERE fs.is_fraud)  AS total_fraud_amount

FROM fraud_scores fs
JOIN claims c    ON c.id  = fs.claim_id
JOIN hospitals h ON h.id  = c.hospital_id
GROUP BY h.id, h.name, h.state
ORDER BY avg_fraud_score DESC;


-- Fraud stats by model version
CREATE OR REPLACE VIEW v_fraud_by_model AS
SELECT
    model_version,
    COUNT(*)                                    AS total_predictions,
    COUNT(*) FILTER (WHERE is_fraud)            AS fraud_flagged,
    ROUND(AVG(fraud_score)::NUMERIC, 4)         AS avg_score,
    ROUND(AVG(confidence)::NUMERIC, 4)          AS avg_confidence,
    ROUND(AVG(processing_time_ms)::NUMERIC, 0)  AS avg_latency_ms,
    MIN(created_at)                             AS first_used,
    MAX(created_at)                             AS last_used

FROM fraud_scores
GROUP BY model_version
ORDER BY last_used DESC;


-- Grant read access
GRANT SELECT ON v_fraud_detail      TO claims_readonly;
GRANT SELECT ON v_fraud_summary     TO claims_readonly;
GRANT SELECT ON v_fraud_by_hospital TO claims_readonly;
GRANT SELECT ON v_fraud_by_model    TO claims_readonly;

COMMENT ON VIEW v_fraud_detail      IS 'Per-claim fraud detection detail with patient and hospital context.';
COMMENT ON VIEW v_fraud_summary     IS 'Aggregate fraud detection statistics across all scored claims.';
COMMENT ON VIEW v_fraud_by_hospital IS 'Fraud detection stats grouped by healthcare provider.';
COMMENT ON VIEW v_fraud_by_model    IS 'Model performance comparison across versions.';
