-- ============================================================
-- Test Data: Minimal dataset for integration tests
-- Run after schema creation to populate test tables.
-- ============================================================

-- Test hospital
INSERT INTO hospitals (id, name, npi, address, city, state, zip_code, license_number)
VALUES (
    'hosp-test-0001-0001-000000000001',
    'Test General Hospital',
    '9999999901',
    '100 Test Drive',
    'Testville', 'TX', '75001',
    'TX-TEST-001'
) ON CONFLICT (npi) DO NOTHING;

-- Test patient
INSERT INTO patients (id, mrn, first_name, last_name, date_of_birth, gender, email, insurance_provider, insurance_id)
VALUES (
    'pt-test-0001-0001-000000000001',
    'MRN-TEST-00001',
    'John', 'Doe',
    '1985-06-15', 'Male',
    'john.doe@test.com',
    'Test Insurance Co', 'TIC-001234'
) ON CONFLICT (mrn) DO NOTHING;

-- Test claims (various statuses)
INSERT INTO claims (id, claim_number, patient_id, hospital_id, claim_amount, treatment_type, diagnosis_code, procedure_code, claim_date, service_date, status) VALUES
    ('clm-test-0001-0001-000000000001', 'CLM-TEST-000001', 'pt-test-0001-0001-000000000001', 'hosp-test-0001-0001-000000000001', 5500.00, 'Emergency Room Visit', 'R10.9', '99285', '2025-01-15 08:30:00', '2025-01-15 08:00:00', 'SUBMITTED'),
    ('clm-test-0001-0001-000000000002', 'CLM-TEST-000002', 'pt-test-0001-0001-000000000001', 'hosp-test-0001-0001-000000000001', 25000.00, 'Surgery', 'K35.80', '44970', '2025-01-20 10:00:00', '2025-01-20 07:00:00', 'APPROVED'),
    ('clm-test-0001-0001-000000000003', 'CLM-TEST-000003', 'pt-test-0001-0001-000000000001', 'hosp-test-0001-0001-000000000001', 75000.00, 'Cardiac Surgery', 'I25.10', '33533', '2025-01-25 14:00:00', '2025-01-25 06:00:00', 'REJECTED')
ON CONFLICT (claim_number) DO NOTHING;

-- Test document
INSERT INTO documents (id, claim_id, document_type, file_name, s3_key, file_size, mime_type, upload_user)
VALUES (
    'doc-test-0001-0001-000000000001',
    'clm-test-0001-0001-000000000001',
    'medical_record',
    'test_report.pdf',
    'claims/CLM-TEST-000001/test_report.pdf',
    245000,
    'application/pdf',
    'test_user'
) ON CONFLICT (s3_key) DO NOTHING;

-- Test fraud score
INSERT INTO fraud_scores (id, claim_id, model_version, fraud_score, is_fraud, confidence, risk_level)
VALUES (
    'fs-test-0001-0001-000000000001',
    'clm-test-0001-0001-000000000003',
    'v2.1.0',
    0.92, TRUE, 0.96, 'CRITICAL'
) ON CONFLICT (claim_id) DO NOTHING;

-- Test admin user
INSERT INTO users (id, username, email, password_hash, full_name, role, is_admin)
VALUES (
    'usr-test-0001-0001-000000000001',
    'test_admin',
    'admin@test.com',
    '$2b$12$testhashedpassword000000000000000000000000000000000',
    'Test Admin',
    'admin',
    TRUE
) ON CONFLICT (username) DO NOTHING;
