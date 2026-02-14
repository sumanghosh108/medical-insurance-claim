-- ============================================================
-- Seed Data: Hospitals
-- Sample healthcare providers for development/testing.
-- ============================================================

INSERT INTO hospitals (id, name, npi, address, city, state, zip_code, phone, email, license_number, accreditation_level)
VALUES
    (
        'hosp-0001-0001-0001-000000000001',
        'Metropolitan General Hospital',
        '1234567890',
        '100 Medical Center Drive',
        'New York', 'NY', '10001',
        '212-555-0100', 'admin@metrogen.org',
        'NY-MED-2020-001',
        'Level I Trauma'
    ),
    (
        'hosp-0001-0001-0001-000000000002',
        'Sunrise Community Medical Center',
        '2345678901',
        '250 Sunrise Boulevard',
        'Los Angeles', 'CA', '90001',
        '310-555-0200', 'info@sunrisemedical.org',
        'CA-MED-2019-042',
        'Level II Trauma'
    ),
    (
        'hosp-0001-0001-0001-000000000003',
        'Midwest Regional Health System',
        '3456789012',
        '500 Health Parkway',
        'Chicago', 'IL', '60601',
        '312-555-0300', 'contact@midwesthealth.org',
        'IL-MED-2021-015',
        'Level II Trauma'
    ),
    (
        'hosp-0001-0001-0001-000000000004',
        'Bayview Specialty Clinic',
        '4567890123',
        '75 Harbor View Road',
        'San Francisco', 'CA', '94102',
        '415-555-0400', 'admin@bayviewclinic.org',
        'CA-MED-2020-087',
        'Specialty'
    ),
    (
        'hosp-0001-0001-0001-000000000005',
        'Southern Heart & Vascular Institute',
        '5678901234',
        '1200 Cardiac Lane',
        'Houston', 'TX', '77001',
        '713-555-0500', 'info@southernheart.org',
        'TX-MED-2018-033',
        'Level I Trauma'
    ),
    (
        'hosp-0001-0001-0001-000000000006',
        'Pine Valley Family Medicine',
        '6789012345',
        '88 Pine Valley Road',
        'Denver', 'CO', '80201',
        '303-555-0600', 'office@pinevalleyfm.org',
        'CO-MED-2022-009',
        'Primary Care'
    ),
    (
        'hosp-0001-0001-0001-000000000007',
        'Atlantic Orthopedic Associates',
        '7890123456',
        '400 Atlantic Avenue',
        'Miami', 'FL', '33101',
        '305-555-0700', 'scheduling@atlanticortho.org',
        'FL-MED-2021-051',
        'Specialty'
    ),
    (
        'hosp-0001-0001-0001-000000000008',
        'Cedar Ridge Psychiatric Center',
        '8901234567',
        '150 Cedar Ridge Drive',
        'Seattle', 'WA', '98101',
        '206-555-0800', 'intake@cedarridgepsych.org',
        'WA-MED-2020-028',
        'Behavioral Health'
    )
ON CONFLICT (npi) DO NOTHING;
