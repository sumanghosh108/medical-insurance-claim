-- ============================================================
-- Function: calculate_fraud_score
-- Computes a composite fraud risk score for a given claim
-- based on heuristic rules. This complements the ML model
-- and can be used as a fallback or for real-time screening.
-- ============================================================

CREATE OR REPLACE FUNCTION calculate_fraud_score(
    p_claim_id VARCHAR(36)
)
RETURNS TABLE (
    composite_score  NUMERIC,
    risk_level       VARCHAR(20),
    risk_factors     JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_score         NUMERIC := 0.0;
    v_factors       JSONB := '[]'::JSONB;
    v_claim         RECORD;
    v_patient_claims INTEGER;
    v_recent_claims  INTEGER;
    v_avg_amount     NUMERIC;
    v_duplicate_diag INTEGER;
BEGIN
    -- Fetch claim data
    SELECT c.*, p.date_of_birth, p.insurance_provider,
           h.name AS hospital_name, h.state AS hospital_state
    INTO v_claim
    FROM claims c
    JOIN patients p  ON p.id = c.patient_id
    JOIN hospitals h ON h.id = c.hospital_id
    WHERE c.id = p_claim_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Claim not found: %', p_claim_id;
    END IF;

    -- -------------------------------------------------------
    -- Rule 1: High claim amount (>$25,000 adds risk)
    -- -------------------------------------------------------
    IF v_claim.claim_amount > 50000 THEN
        v_score := v_score + 0.20;
        v_factors := v_factors || '["very_high_amount_over_50k"]'::JSONB;
    ELSIF v_claim.claim_amount > 25000 THEN
        v_score := v_score + 0.10;
        v_factors := v_factors || '["high_amount_over_25k"]'::JSONB;
    END IF;

    -- -------------------------------------------------------
    -- Rule 2: Excessive claims by same patient (last 90 days)
    -- -------------------------------------------------------
    SELECT COUNT(*) INTO v_recent_claims
    FROM claims
    WHERE patient_id = v_claim.patient_id
      AND claim_date >= (v_claim.claim_date - INTERVAL '90 days')
      AND id != p_claim_id;

    IF v_recent_claims > 5 THEN
        v_score := v_score + 0.25;
        v_factors := v_factors || format('["excessive_recent_claims_%s"]', v_recent_claims)::JSONB;
    ELSIF v_recent_claims > 3 THEN
        v_score := v_score + 0.10;
        v_factors := v_factors || format('["elevated_recent_claims_%s"]', v_recent_claims)::JSONB;
    END IF;

    -- -------------------------------------------------------
    -- Rule 3: Duplicate diagnosis code from same patient
    -- -------------------------------------------------------
    SELECT COUNT(*) INTO v_duplicate_diag
    FROM claims
    WHERE patient_id = v_claim.patient_id
      AND diagnosis_code = v_claim.diagnosis_code
      AND id != p_claim_id
      AND claim_date >= (v_claim.claim_date - INTERVAL '180 days');

    IF v_duplicate_diag > 2 THEN
        v_score := v_score + 0.20;
        v_factors := v_factors || '["repeated_diagnosis_code"]'::JSONB;
    ELSIF v_duplicate_diag > 0 THEN
        v_score := v_score + 0.05;
        v_factors := v_factors || '["duplicate_diagnosis_recent"]'::JSONB;
    END IF;

    -- -------------------------------------------------------
    -- Rule 4: Claim amount far above patient average
    -- -------------------------------------------------------
    SELECT AVG(claim_amount) INTO v_avg_amount
    FROM claims
    WHERE patient_id = v_claim.patient_id
      AND id != p_claim_id;

    IF v_avg_amount IS NOT NULL AND v_avg_amount > 0 THEN
        IF v_claim.claim_amount > (v_avg_amount * 5) THEN
            v_score := v_score + 0.15;
            v_factors := v_factors || '["amount_5x_patient_average"]'::JSONB;
        ELSIF v_claim.claim_amount > (v_avg_amount * 3) THEN
            v_score := v_score + 0.08;
            v_factors := v_factors || '["amount_3x_patient_average"]'::JSONB;
        END IF;
    END IF;

    -- -------------------------------------------------------
    -- Rule 5: Service date after claim date (temporal anomaly)
    -- -------------------------------------------------------
    IF v_claim.service_date > v_claim.claim_date THEN
        v_score := v_score + 0.15;
        v_factors := v_factors || '["service_after_claim_date"]'::JSONB;
    END IF;

    -- -------------------------------------------------------
    -- Rule 6: Weekend/holiday submission pattern
    -- -------------------------------------------------------
    IF EXTRACT(DOW FROM v_claim.submission_date) IN (0, 6) THEN
        v_score := v_score + 0.05;
        v_factors := v_factors || '["weekend_submission"]'::JSONB;
    END IF;

    -- Cap score at 1.0
    v_score := LEAST(v_score, 1.0);

    -- Determine risk level
    RETURN QUERY SELECT
        ROUND(v_score, 4),
        CASE
            WHEN v_score >= 0.8 THEN 'CRITICAL'::VARCHAR(20)
            WHEN v_score >= 0.6 THEN 'HIGH'::VARCHAR(20)
            WHEN v_score >= 0.3 THEN 'MEDIUM'::VARCHAR(20)
            ELSE 'LOW'::VARCHAR(20)
        END,
        v_factors;
END;
$$;

COMMENT ON FUNCTION calculate_fraud_score(VARCHAR) IS
    'Computes a heuristic fraud score (0.0–1.0) based on claim patterns, amounts, and temporal anomalies. Complements the ML model.';
