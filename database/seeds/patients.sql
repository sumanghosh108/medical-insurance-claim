-- ============================================================
-- Seed Data: Patients
-- Sample patient records for development/testing.
-- ============================================================

INSERT INTO patients (id, mrn, first_name, last_name, date_of_birth, gender, email, phone, address, city, state, zip_code, insurance_provider, insurance_id)
VALUES
    (
        'pt-000001-0001-0001-000000000001',
        'MRN-2024-00001',
        'James', 'Anderson',
        '1985-03-15', 'Male',
        'james.anderson@email.com', '212-555-1001',
        '45 Oak Street, Apt 3B',
        'New York', 'NY', '10002',
        'Blue Cross Blue Shield', 'BCBS-NY-884521'
    ),
    (
        'pt-000001-0001-0001-000000000002',
        'MRN-2024-00002',
        'Maria', 'Garcia',
        '1990-07-22', 'Female',
        'maria.garcia@email.com', '310-555-1002',
        '1200 Wilshire Blvd, Unit 7',
        'Los Angeles', 'CA', '90010',
        'Kaiser Permanente', 'KP-CA-339201'
    ),
    (
        'pt-000001-0001-0001-000000000003',
        'MRN-2024-00003',
        'Robert', 'Chen',
        '1978-11-08', 'Male',
        'robert.chen@email.com', '312-555-1003',
        '800 Michigan Avenue',
        'Chicago', 'IL', '60605',
        'Aetna', 'AET-IL-772104'
    ),
    (
        'pt-000001-0001-0001-000000000004',
        'MRN-2024-00004',
        'Sarah', 'Williams',
        '1992-01-30', 'Female',
        'sarah.williams@email.com', '415-555-1004',
        '22 Marina Green Drive',
        'San Francisco', 'CA', '94123',
        'United Healthcare', 'UHC-CA-551893'
    ),
    (
        'pt-000001-0001-0001-000000000005',
        'MRN-2024-00005',
        'David', 'Patel',
        '1965-09-12', 'Male',
        'david.patel@email.com', '713-555-1005',
        '3100 Fannin Street',
        'Houston', 'TX', '77004',
        'Cigna', 'CIG-TX-998472'
    ),
    (
        'pt-000001-0001-0001-000000000006',
        'MRN-2024-00006',
        'Emily', 'Johnson',
        '2000-04-18', 'Female',
        'emily.johnson@email.com', '303-555-1006',
        '675 Pearl Street',
        'Denver', 'CO', '80203',
        'Humana', 'HUM-CO-223167'
    ),
    (
        'pt-000001-0001-0001-000000000007',
        'MRN-2024-00007',
        'Michael', 'Brown',
        '1955-12-05', 'Male',
        'michael.brown@email.com', '305-555-1007',
        '900 Brickell Avenue',
        'Miami', 'FL', '33131',
        'Medicare', 'MCR-FL-667890'
    ),
    (
        'pt-000001-0001-0001-000000000008',
        'MRN-2024-00008',
        'Lisa', 'Kim',
        '1988-06-25', 'Female',
        'lisa.kim@email.com', '206-555-1008',
        '1550 Eastlake Avenue',
        'Seattle', 'WA', '98102',
        'Premera Blue Cross', 'PBC-WA-445231'
    ),
    (
        'pt-000001-0001-0001-000000000009',
        'MRN-2024-00009',
        'Thomas', 'Martinez',
        '1972-08-14', 'Male',
        'thomas.martinez@email.com', '602-555-1009',
        '2200 East Camelback Road',
        'Phoenix', 'AZ', '85016',
        'Blue Cross Blue Shield', 'BCBS-AZ-119834'
    ),
    (
        'pt-000001-0001-0001-000000000010',
        'MRN-2024-00010',
        'Jennifer', 'Taylor',
        '1995-02-28', 'Female',
        'jennifer.taylor@email.com', '404-555-1010',
        '350 Peachtree Street NE',
        'Atlanta', 'GA', '30308',
        'Anthem', 'ANT-GA-887654'
    )
ON CONFLICT (mrn) DO NOTHING;
