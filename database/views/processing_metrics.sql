-- ============================================================
-- View: Processing Metrics
-- Pipeline throughput, latency, and status breakdown views.
-- ============================================================

-- Daily claims processing throughput
CREATE OR REPLACE VIEW v_processing_daily AS
SELECT
    DATE(submission_date)               AS processing_date,
    COUNT(*)                            AS total_submitted,
    COUNT(*) FILTER (WHERE status = 'APPROVED')      AS approved,
    COUNT(*) FILTER (WHERE status = 'REJECTED')      AS rejected,
    COUNT(*) FILTER (WHERE status = 'MANUAL_REVIEW') AS manual_review,
    COUNT(*) FILTER (WHERE status = 'PROCESSING')    AS in_processing,
    COUNT(*) FILTER (WHERE status = 'ERROR')          AS errors,

    ROUND(AVG(claim_amount)::NUMERIC, 2)              AS avg_claim_amount,
    ROUND(SUM(claim_amount)::NUMERIC, 2)              AS total_claim_amount,

    ROUND(AVG(
        CASE WHEN approval_date IS NOT NULL
        THEN EXTRACT(EPOCH FROM (approval_date - submission_date)) / 3600.0
        ELSE NULL END
    )::NUMERIC, 2) AS avg_processing_hours

FROM claims
GROUP BY DATE(submission_date)
ORDER BY processing_date DESC;


-- Current pipeline status breakdown
CREATE OR REPLACE VIEW v_pipeline_status AS
SELECT
    status,
    COUNT(*)                               AS claim_count,
    ROUND(AVG(claim_amount)::NUMERIC, 2)   AS avg_amount,
    ROUND(SUM(claim_amount)::NUMERIC, 2)   AS total_amount,
    MIN(submission_date)                   AS oldest_claim,
    MAX(submission_date)                   AS newest_claim,

    ROUND(AVG(
        EXTRACT(DAY FROM (NOW() - submission_date))
    )::NUMERIC, 1) AS avg_age_days

FROM claims
GROUP BY status
ORDER BY claim_count DESC;


-- Document verification metrics
CREATE OR REPLACE VIEW v_document_metrics AS
SELECT
    document_type,
    COUNT(*)                                         AS total_documents,
    COUNT(*) FILTER (WHERE is_verified)               AS verified_count,
    COUNT(*) FILTER (WHERE NOT is_verified)            AS unverified_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_verified) / NULLIF(COUNT(*), 0), 2
    ) AS verification_rate_pct,
    ROUND(AVG(file_size)::NUMERIC, 0)                 AS avg_file_size_bytes,
    ROUND(SUM(file_size)::NUMERIC / (1024.0 * 1024.0), 2) AS total_size_mb

FROM documents
GROUP BY document_type
ORDER BY total_documents DESC;


-- SLA compliance — claims exceeding target processing time
CREATE OR REPLACE VIEW v_sla_compliance AS
SELECT
    c.id             AS claim_id,
    c.claim_number,
    c.status,
    c.priority,
    c.claim_amount,
    c.submission_date,
    EXTRACT(DAY FROM (NOW() - c.submission_date)) AS age_days,

    CASE c.priority
        WHEN 'HIGH' THEN 1
        WHEN 'NORMAL' THEN 3
        WHEN 'LOW' THEN 7
        ELSE 5
    END AS sla_target_days,

    CASE
        WHEN EXTRACT(DAY FROM (NOW() - c.submission_date)) >
            CASE c.priority WHEN 'HIGH' THEN 1 WHEN 'NORMAL' THEN 3 WHEN 'LOW' THEN 7 ELSE 5 END
        THEN TRUE
        ELSE FALSE
    END AS sla_breached

FROM claims c
WHERE c.status NOT IN ('APPROVED', 'REJECTED')
ORDER BY age_days DESC;


-- Grant read access
GRANT SELECT ON v_processing_daily  TO claims_readonly;
GRANT SELECT ON v_pipeline_status   TO claims_readonly;
GRANT SELECT ON v_document_metrics  TO claims_readonly;
GRANT SELECT ON v_sla_compliance    TO claims_readonly;

COMMENT ON VIEW v_processing_daily  IS 'Daily claims throughput with status breakdown and processing latency.';
COMMENT ON VIEW v_pipeline_status   IS 'Current pipeline snapshot showing claim counts and age by status.';
COMMENT ON VIEW v_document_metrics  IS 'Document verification metrics grouped by document type.';
COMMENT ON VIEW v_sla_compliance    IS 'SLA compliance tracker for open claims based on priority targets.';
