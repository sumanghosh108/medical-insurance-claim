-- ============================================================
-- Seed Data: Sample Claims, Documents, and Fraud Scores
-- End-to-end sample data for development and testing.
-- Depends on: hospitals.sql, patients.sql
-- ============================================================

-- -----------------------------------------------------------
-- Claims
-- -----------------------------------------------------------
INSERT INTO claims (id, claim_number, patient_id, hospital_id, claim_amount, treatment_type, diagnosis_code, procedure_code, claim_date, service_date, status, priority, metadata)
VALUES
    -- Normal approved claim
    (
        'clm-000001-0001-0001-000000000001',
        'CLM-2024-000001',
        'pt-000001-0001-0001-000000000001',
        'hosp-0001-0001-0001-000000000001',
        2500.00, 'Emergency Room Visit', 'R10.9', '99285',
        '2024-11-15 08:30:00', '2024-11-15 08:00:00',
        'APPROVED', 'HIGH',
        '{"admission_type": "emergency", "los_days": 1}'
    ),
    -- High-value claim under review
    (
        'clm-000001-0001-0001-000000000002',
        'CLM-2024-000002',
        'pt-000001-0001-0001-000000000002',
        'hosp-0001-0001-0001-000000000002',
        45000.00, 'Cardiac Surgery', 'I25.10', '33533',
        '2024-12-01 10:00:00', '2024-12-01 07:00:00',
        'MANUAL_REVIEW', 'HIGH',
        '{"admission_type": "scheduled", "los_days": 5, "icu_days": 2}'
    ),
    -- Rejected fraudulent claim
    (
        'clm-000001-0001-0001-000000000003',
        'CLM-2024-000003',
        'pt-000001-0001-0001-000000000003',
        'hosp-0001-0001-0001-000000000003',
        18750.00, 'Orthopedic Surgery', 'M17.11', '27447',
        '2024-12-10 14:00:00', '2024-12-10 06:00:00',
        'REJECTED', 'NORMAL',
        '{"admission_type": "scheduled", "los_days": 3}'
    ),
    -- New claim (submitted, awaiting processing)
    (
        'clm-000001-0001-0001-000000000004',
        'CLM-2024-000004',
        'pt-000001-0001-0001-000000000004',
        'hosp-0001-0001-0001-000000000004',
        850.00, 'Dermatology Consultation', 'L70.0', '99213',
        '2025-01-05 09:15:00', '2025-01-05 09:00:00',
        'SUBMITTED', 'NORMAL',
        '{"admission_type": "outpatient"}'
    ),
    -- Processing claim
    (
        'clm-000001-0001-0001-000000000005',
        'CLM-2024-000005',
        'pt-000001-0001-0001-000000000005',
        'hosp-0001-0001-0001-000000000005',
        32000.00, 'Cardiovascular Stent Placement', 'I25.10', '92928',
        '2025-01-10 11:00:00', '2025-01-10 07:30:00',
        'PROCESSING', 'HIGH',
        '{"admission_type": "emergency", "los_days": 4}'
    ),
    -- Low-value routine claim
    (
        'clm-000001-0001-0001-000000000006',
        'CLM-2024-000006',
        'pt-000001-0001-0001-000000000006',
        'hosp-0001-0001-0001-000000000006',
        275.00, 'Annual Physical Exam', 'Z00.00', '99395',
        '2025-01-12 10:00:00', '2025-01-12 10:00:00',
        'APPROVED', 'LOW',
        '{"admission_type": "outpatient"}'
    ),
    -- Medicare claim (elderly patient)
    (
        'clm-000001-0001-0001-000000000007',
        'CLM-2024-000007',
        'pt-000001-0001-0001-000000000007',
        'hosp-0001-0001-0001-000000000007',
        12500.00, 'Total Hip Replacement', 'M16.11', '27130',
        '2025-01-15 07:00:00', '2025-01-15 06:00:00',
        'SUBMITTED', 'NORMAL',
        '{"admission_type": "scheduled", "los_days": 3}'
    ),
    -- Behavioral health claim
    (
        'clm-000001-0001-0001-000000000008',
        'CLM-2024-000008',
        'pt-000001-0001-0001-000000000008',
        'hosp-0001-0001-0001-000000000008',
        5200.00, 'Psychiatric Inpatient', 'F33.1', '90837',
        '2025-01-18 12:00:00', '2025-01-14 09:00:00',
        'SUBMITTED', 'NORMAL',
        '{"admission_type": "inpatient", "los_days": 7}'
    )
ON CONFLICT (claim_number) DO NOTHING;


-- -----------------------------------------------------------
-- Documents
-- -----------------------------------------------------------
INSERT INTO documents (id, claim_id, document_type, file_name, s3_key, file_size, mime_type, upload_user, is_verified)
VALUES
    ('doc-000001-0001-0001-000000000001', 'clm-000001-0001-0001-000000000001', 'medical_record', 'er_visit_report.pdf',     'claims/CLM-2024-000001/er_visit_report.pdf',     245000, 'application/pdf', 'system', TRUE),
    ('doc-000001-0001-0001-000000000002', 'clm-000001-0001-0001-000000000001', 'invoice',        'hospital_invoice.pdf',    'claims/CLM-2024-000001/hospital_invoice.pdf',    128000, 'application/pdf', 'system', TRUE),
    ('doc-000001-0001-0001-000000000003', 'clm-000001-0001-0001-000000000002', 'medical_record', 'cardiac_surgery_notes.pdf','claims/CLM-2024-000002/cardiac_surgery_notes.pdf',890000, 'application/pdf', 'system', TRUE),
    ('doc-000001-0001-0001-000000000004', 'clm-000001-0001-0001-000000000002', 'lab_report',     'pre_op_labs.pdf',         'claims/CLM-2024-000002/pre_op_labs.pdf',          340000, 'application/pdf', 'system', FALSE),
    ('doc-000001-0001-0001-000000000005', 'clm-000001-0001-0001-000000000003', 'medical_record', 'ortho_report.pdf',        'claims/CLM-2024-000003/ortho_report.pdf',         560000, 'application/pdf', 'system', TRUE),
    ('doc-000001-0001-0001-000000000006', 'clm-000001-0001-0001-000000000003', 'prescription',   'rx_scan.jpg',             'claims/CLM-2024-000003/rx_scan.jpg',              1200000,'image/jpeg',      'system', FALSE),
    ('doc-000001-0001-0001-000000000007', 'clm-000001-0001-0001-000000000004', 'referral',       'derm_referral.pdf',       'claims/CLM-2024-000004/derm_referral.pdf',         95000, 'application/pdf', 'system', FALSE),
    ('doc-000001-0001-0001-000000000008', 'clm-000001-0001-0001-000000000005', 'medical_record', 'cath_lab_report.pdf',     'claims/CLM-2024-000005/cath_lab_report.pdf',      720000, 'application/pdf', 'system', FALSE)
ON CONFLICT (s3_key) DO NOTHING;


-- -----------------------------------------------------------
-- Fraud Scores
-- -----------------------------------------------------------
INSERT INTO fraud_scores (id, claim_id, model_version, fraud_score, is_fraud, confidence, risk_level, risk_factors, processing_time_ms)
VALUES
    -- Low risk (approved claim)
    (
        'fs-000001-0001-0001-000000000001',
        'clm-000001-0001-0001-000000000001',
        'v2.1.0', 0.12, FALSE, 0.88, 'LOW',
        '{"factors": ["normal_amount", "known_provider", "consistent_history"]}',
        145
    ),
    -- Medium risk (under review)
    (
        'fs-000001-0001-0001-000000000002',
        'clm-000001-0001-0001-000000000002',
        'v2.1.0', 0.62, FALSE, 0.71, 'HIGH',
        '{"factors": ["high_amount", "procedure_frequency", "short_interval"]}',
        210
    ),
    -- High risk (rejected)
    (
        'fs-000001-0001-0001-000000000003',
        'clm-000001-0001-0001-000000000003',
        'v2.1.0', 0.91, TRUE, 0.95, 'CRITICAL',
        '{"factors": ["duplicate_billing", "upcoding", "phantom_services"]}',
        185
    ),
    -- Low risk (routine)
    (
        'fs-000001-0001-0001-000000000006',
        'clm-000001-0001-0001-000000000006',
        'v2.1.0', 0.05, FALSE, 0.95, 'LOW',
        '{"factors": ["routine_visit", "known_patient", "low_amount"]}',
        98
    )
ON CONFLICT (claim_id) DO NOTHING;


-- -----------------------------------------------------------
-- Sample admin user (password: "admin123" — bcrypt hash)
-- -----------------------------------------------------------
INSERT INTO users (id, username, email, password_hash, full_name, role, is_admin)
VALUES (
    'usr-000001-0001-0001-000000000001',
    'admin',
    'admin@claimssystem.com',
    '$2b$12$LJ3m4ys3Sz8lXxYz0eGRheO7e8S1vGkD9hK3mN5uW7xQ2pA4fB6Wy',
    'System Administrator',
    'admin',
    TRUE
)
ON CONFLICT (username) DO NOTHING;
