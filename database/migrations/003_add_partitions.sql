-- ============================================================
-- Migration 003: Add Table Partitioning
-- Partitions claims table by submission_date for better
-- query performance on large datasets.
-- ============================================================

BEGIN;

-- -----------------------------------------------------------
-- Audit log table (partitioned by month)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS claim_audit_log (
    id              BIGSERIAL,
    claim_id        VARCHAR(36)  NOT NULL,
    event_timestamp TIMESTAMP    NOT NULL DEFAULT NOW(),
    event_type      VARCHAR(50)  NOT NULL,
    previous_status VARCHAR(50)  NULL,
    new_status      VARCHAR(50)  NULL,
    changed_by      VARCHAR(255) NULL,
    details         JSONB        NULL,
    source          VARCHAR(100) NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, event_timestamp)
) PARTITION BY RANGE (event_timestamp);

-- Create monthly partitions for the current and next year
DO $$
DECLARE
    start_date DATE;
    end_date   DATE;
    partition_name TEXT;
BEGIN
    FOR y IN 2025..2027 LOOP
        FOR m IN 1..12 LOOP
            start_date := make_date(y, m, 1);
            end_date   := start_date + INTERVAL '1 month';
            partition_name := format('claim_audit_log_%s_%s', y, lpad(m::TEXT, 2, '0'));

            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF claim_audit_log
                 FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
        END LOOP;
    END LOOP;
END;
$$;

-- Default partition for out-of-range data
CREATE TABLE IF NOT EXISTS claim_audit_log_default
    PARTITION OF claim_audit_log DEFAULT;

-- Indexes on audit log
CREATE INDEX IF NOT EXISTS ix_audit_claim_id
    ON claim_audit_log (claim_id);
CREATE INDEX IF NOT EXISTS ix_audit_event_type
    ON claim_audit_log (event_type);
CREATE INDEX IF NOT EXISTS ix_audit_timestamp
    ON claim_audit_log (event_timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_audit_claim_time
    ON claim_audit_log (claim_id, event_timestamp DESC);


-- -----------------------------------------------------------
-- Processing metrics table (partitioned by day)
-- Stores pipeline step timing and throughput data.
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS processing_events (
    id              BIGSERIAL,
    claim_id        VARCHAR(36)  NOT NULL,
    step_name       VARCHAR(100) NOT NULL,
    started_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMP    NULL,
    duration_ms     INTEGER      NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'STARTED',
    error_message   TEXT         NULL,
    metadata        JSONB        NULL,

    PRIMARY KEY (id, started_at)
) PARTITION BY RANGE (started_at);

-- Create daily partitions for 90 days
DO $$
DECLARE
    start_date DATE := '2025-01-01';
    end_date   DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..365 LOOP
        end_date := start_date + INTERVAL '1 day';
        partition_name := format('processing_events_%s', to_char(start_date, 'YYYY_MM_DD'));

        BEGIN
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF processing_events
                 FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
        EXCEPTION WHEN OTHERS THEN
            -- Partition may already exist, skip
            NULL;
        END;

        start_date := end_date;
    END LOOP;
END;
$$;

CREATE TABLE IF NOT EXISTS processing_events_default
    PARTITION OF processing_events DEFAULT;

-- Indexes on processing events
CREATE INDEX IF NOT EXISTS ix_proc_claim
    ON processing_events (claim_id);
CREATE INDEX IF NOT EXISTS ix_proc_step
    ON processing_events (step_name);
CREATE INDEX IF NOT EXISTS ix_proc_status
    ON processing_events (status);


-- -----------------------------------------------------------
-- Record migration
-- -----------------------------------------------------------
INSERT INTO schema_migrations (version, description)
VALUES ('003', 'Add partitioned audit log and processing events tables')
ON CONFLICT (version) DO NOTHING;

COMMIT;
