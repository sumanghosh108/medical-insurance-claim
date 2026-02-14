-- ============================================================
-- Function: update_claim_status
-- Atomically updates a claim's status with validation,
-- audit logging, and side-effect handling.
-- ============================================================

-- Valid status transitions
CREATE TABLE IF NOT EXISTS valid_status_transitions (
    from_status VARCHAR(50) NOT NULL,
    to_status   VARCHAR(50) NOT NULL,
    PRIMARY KEY (from_status, to_status)
);

INSERT INTO valid_status_transitions (from_status, to_status) VALUES
    ('SUBMITTED',     'PROCESSING'),
    ('SUBMITTED',     'REJECTED'),
    ('SUBMITTED',     'ERROR'),
    ('PROCESSING',    'TEXT_EXTRACTED'),
    ('PROCESSING',    'ENTITIES_EXTRACTED'),
    ('PROCESSING',    'FRAUD_SCORED'),
    ('PROCESSING',    'APPROVED'),
    ('PROCESSING',    'REJECTED'),
    ('PROCESSING',    'MANUAL_REVIEW'),
    ('PROCESSING',    'ERROR'),
    ('TEXT_EXTRACTED', 'ENTITIES_EXTRACTED'),
    ('TEXT_EXTRACTED', 'ERROR'),
    ('ENTITIES_EXTRACTED', 'FRAUD_SCORED'),
    ('ENTITIES_EXTRACTED', 'ERROR'),
    ('FRAUD_SCORED',  'APPROVED'),
    ('FRAUD_SCORED',  'REJECTED'),
    ('FRAUD_SCORED',  'MANUAL_REVIEW'),
    ('FRAUD_SCORED',  'ERROR'),
    ('MANUAL_REVIEW', 'APPROVED'),
    ('MANUAL_REVIEW', 'REJECTED'),
    ('MANUAL_REVIEW', 'ERROR'),
    ('ERROR',         'PROCESSING'),
    ('ERROR',         'MANUAL_REVIEW')
ON CONFLICT DO NOTHING;


-- Main function
CREATE OR REPLACE FUNCTION update_claim_status(
    p_claim_id     VARCHAR(36),
    p_new_status   VARCHAR(50),
    p_changed_by   VARCHAR(255) DEFAULT 'system',
    p_notes        TEXT         DEFAULT NULL,
    p_details      JSONB        DEFAULT NULL
)
RETURNS TABLE (
    success          BOOLEAN,
    previous_status  VARCHAR(50),
    current_status   VARCHAR(50),
    message          TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_status VARCHAR(50);
    v_valid          BOOLEAN;
    v_claim          RECORD;
BEGIN
    -- Lock the row to prevent race conditions
    SELECT * INTO v_claim
    FROM claims
    WHERE id = p_claim_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RETURN QUERY SELECT
            FALSE, NULL::VARCHAR(50), NULL::VARCHAR(50),
            format('Claim not found: %s', p_claim_id)::TEXT;
        RETURN;
    END IF;

    v_current_status := v_claim.status;

    -- No-op if already in target status
    IF v_current_status = p_new_status THEN
        RETURN QUERY SELECT
            TRUE, v_current_status, p_new_status,
            'Status unchanged (already in target state)'::TEXT;
        RETURN;
    END IF;

    -- Validate transition
    SELECT EXISTS (
        SELECT 1 FROM valid_status_transitions
        WHERE from_status = v_current_status
          AND to_status   = p_new_status
    ) INTO v_valid;

    IF NOT v_valid THEN
        -- Log the rejected transition attempt
        INSERT INTO claim_audit_log (claim_id, event_type, previous_status, new_status, changed_by, details, source)
        VALUES (
            p_claim_id, 'STATUS_TRANSITION_REJECTED',
            v_current_status, p_new_status,
            p_changed_by,
            COALESCE(p_details, '{}'::JSONB) || jsonb_build_object('reason', 'invalid_transition'),
            'update_claim_status'
        );

        RETURN QUERY SELECT
            FALSE, v_current_status, v_current_status,
            format('Invalid transition: %s → %s', v_current_status, p_new_status)::TEXT;
        RETURN;
    END IF;

    -- Perform the update
    UPDATE claims SET
        status           = p_new_status,
        processing_notes = CASE
            WHEN p_notes IS NOT NULL
            THEN COALESCE(processing_notes || E'\n', '') || p_notes
            ELSE processing_notes
        END,
        approval_date    = CASE
            WHEN p_new_status = 'APPROVED' THEN NOW()
            ELSE approval_date
        END,
        rejection_reason = CASE
            WHEN p_new_status = 'REJECTED' THEN COALESCE(p_notes, rejection_reason)
            ELSE rejection_reason
        END,
        updated_at       = NOW()
    WHERE id = p_claim_id;

    -- Record audit event
    INSERT INTO claim_audit_log (claim_id, event_type, previous_status, new_status, changed_by, details, source)
    VALUES (
        p_claim_id, 'STATUS_CHANGED',
        v_current_status, p_new_status,
        p_changed_by,
        COALESCE(p_details, '{}'::JSONB) || jsonb_build_object('notes', COALESCE(p_notes, '')),
        'update_claim_status'
    );

    RETURN QUERY SELECT
        TRUE, v_current_status, p_new_status,
        format('Status updated: %s → %s', v_current_status, p_new_status)::TEXT;
END;
$$;


COMMENT ON FUNCTION update_claim_status(VARCHAR, VARCHAR, VARCHAR, TEXT, JSONB) IS
    'Atomically updates claim status with transition validation, row locking, and audit logging.';
