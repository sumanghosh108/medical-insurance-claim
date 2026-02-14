"""Integration Tests — Database Operations.

Tests the database CRUD operations and business logic
using an in-memory SQLite database.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.connection import Base
from src.database.models import User, Patient, Hospital, Claim, Document, FraudScore
from src.database.operations import (
    DatabaseOperations,
    PatientOperations,
    HospitalOperations,
    ClaimOperations,
    DocumentOperations,
    FraudScoreOperations,
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def seed_hospital(db_session):
    """Seed a test hospital."""
    hospital = Hospital(
        id='hosp-test-001',
        name='Test Hospital',
        npi='9999999901',
        address='100 Test Drive',
        city='Testville',
        state='TX',
        zip_code='75001',
        license_number='TX-TEST-001',
    )
    db_session.add(hospital)
    db_session.commit()
    return hospital


@pytest.fixture
def seed_patient(db_session):
    """Seed a test patient."""
    patient = Patient(
        id='pt-test-001',
        mrn='MRN-TEST-001',
        first_name='John',
        last_name='Doe',
        date_of_birth=datetime(1985, 6, 15),
        email='john.doe@test.com',
    )
    db_session.add(patient)
    db_session.commit()
    return patient


@pytest.fixture
def seed_claim(db_session, seed_patient, seed_hospital):
    """Seed a test claim."""
    claim = Claim(
        id='clm-test-001',
        claim_number='CLM-TEST-001',
        patient_id=seed_patient.id,
        hospital_id=seed_hospital.id,
        claim_amount=5500.00,
        treatment_type='Emergency Room Visit',
        diagnosis_code='R10.9',
        claim_date=datetime.now(),
        service_date=datetime.now(),
    )
    db_session.add(claim)
    db_session.commit()
    return claim


# ----------------------------------------------------------------
# PatientOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestPatientOperations:
    """Tests for patient CRUD operations."""

    def test_create_patient(self, db_session):
        ops = PatientOperations(session=db_session)
        patient = ops.create_patient(
            mrn='MRN-NEW-001',
            first_name='Jane',
            last_name='Smith',
            date_of_birth=datetime(1990, 1, 1),
        )
        assert patient.id is not None
        assert patient.mrn == 'MRN-NEW-001'

    def test_find_by_mrn(self, db_session, seed_patient):
        ops = PatientOperations(session=db_session)
        found = ops.find_by_mrn('MRN-TEST-001')
        assert found is not None
        assert found.first_name == 'John'

    def test_find_by_mrn_not_found(self, db_session):
        ops = PatientOperations(session=db_session)
        found = ops.find_by_mrn('NONEXISTENT')
        assert found is None

    def test_find_by_email(self, db_session, seed_patient):
        ops = PatientOperations(session=db_session)
        found = ops.find_by_email('john.doe@test.com')
        assert found is not None

    def test_search_patients(self, db_session, seed_patient):
        ops = PatientOperations(session=db_session)
        results = ops.search_patients('John')
        assert len(results) >= 1

    def test_get_patient_claims(self, db_session, seed_claim):
        ops = PatientOperations(session=db_session)
        claims = ops.get_patient_claims('pt-test-001')
        assert len(claims) >= 1


# ----------------------------------------------------------------
# HospitalOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestHospitalOperations:
    """Tests for hospital CRUD operations."""

    def test_create_hospital(self, db_session):
        ops = HospitalOperations(session=db_session)
        hospital = ops.create_hospital(
            name='New Hospital',
            npi='1111111111',
            address='200 Medical Blvd',
            city='Medtown',
            state='CA',
            zip_code='90001',
            license_number='CA-NEW-001',
        )
        assert hospital.id is not None

    def test_find_by_npi(self, db_session, seed_hospital):
        ops = HospitalOperations(session=db_session)
        found = ops.find_by_npi('9999999901')
        assert found is not None
        assert found.name == 'Test Hospital'

    def test_find_by_license(self, db_session, seed_hospital):
        ops = HospitalOperations(session=db_session)
        found = ops.find_by_license('TX-TEST-001')
        assert found is not None

    def test_get_active_hospitals(self, db_session, seed_hospital):
        ops = HospitalOperations(session=db_session)
        active = ops.get_active_hospitals()
        assert len(active) >= 1


# ----------------------------------------------------------------
# ClaimOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestClaimOperations:
    """Tests for claim CRUD operations."""

    def test_create_claim(self, db_session, seed_patient, seed_hospital):
        ops = ClaimOperations(session=db_session)
        claim = ops.create_claim(
            claim_number='CLM-NEW-001',
            patient_id=seed_patient.id,
            hospital_id=seed_hospital.id,
            claim_amount=3000.00,
            treatment_type='Consultation',
            diagnosis_code='Z00.00',
            claim_date=datetime.now(),
            service_date=datetime.now(),
        )
        assert claim.id is not None
        assert claim.status == 'SUBMITTED'

    def test_find_by_number(self, db_session, seed_claim):
        ops = ClaimOperations(session=db_session)
        found = ops.find_by_number('CLM-TEST-001')
        assert found is not None

    def test_update_claim_status(self, db_session, seed_claim):
        ops = ClaimOperations(session=db_session)
        updated = ops.update_claim_status(
            seed_claim.id, 'PROCESSING', notes='Starting processing'
        )
        assert updated.status == 'PROCESSING'

    def test_get_by_status(self, db_session, seed_claim):
        ops = ClaimOperations(session=db_session)
        results = ops.get_by_status('SUBMITTED')
        assert len(results) >= 1

    def test_get_high_value_claims(self, db_session, seed_claim):
        ops = ClaimOperations(session=db_session)
        results = ops.get_high_value_claims(amount=5000.0)
        assert len(results) >= 1

    def test_get_claim_summary(self, db_session, seed_claim):
        ops = ClaimOperations(session=db_session)
        summary = ops.get_claim_summary(seed_claim.id)
        assert summary['number'] == 'CLM-TEST-001'
        assert 'patient' in summary
        assert 'hospital' in summary


# ----------------------------------------------------------------
# DocumentOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestDocumentOperations:
    """Tests for document CRUD operations."""

    def test_add_document(self, db_session, seed_claim):
        ops = DocumentOperations(session=db_session)
        doc = ops.add_document(
            claim_id=seed_claim.id,
            document_type='medical_record',
            file_name='test.pdf',
            s3_key='claims/CLM-TEST-001/test.pdf',
            file_size=100000,
            mime_type='application/pdf',
            upload_user='test_user',
        )
        assert doc.id is not None
        assert doc.is_verified is False

    def test_verify_document(self, db_session, seed_claim):
        ops = DocumentOperations(session=db_session)
        doc = ops.add_document(
            claim_id=seed_claim.id,
            document_type='invoice',
            file_name='invoice.pdf',
            s3_key='claims/CLM-TEST-001/invoice.pdf',
            file_size=50000,
            mime_type='application/pdf',
            upload_user='test_user',
        )
        verified = ops.verify_document(doc.id, verified_by='admin')
        assert verified.is_verified is True

    def test_get_unverified_documents(self, db_session, seed_claim):
        ops = DocumentOperations(session=db_session)
        ops.add_document(
            claim_id=seed_claim.id,
            document_type='lab_report',
            file_name='labs.pdf',
            s3_key='claims/CLM-TEST-001/labs.pdf',
            file_size=80000,
            mime_type='application/pdf',
            upload_user='test_user',
        )
        unverified = ops.get_unverified_documents()
        assert len(unverified) >= 1


# ----------------------------------------------------------------
# FraudScoreOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestFraudScoreOperations:
    """Tests for fraud score CRUD operations."""

    def test_save_fraud_score(self, db_session, seed_claim):
        ops = FraudScoreOperations(session=db_session)
        score = ops.save_fraud_score(
            claim_id=seed_claim.id,
            model_version='v2.1.0',
            fraud_score=0.75,
            is_fraud=False,
            confidence=0.82,
        )
        assert score.id is not None
        assert score.risk_level == 'HIGH'

    def test_risk_level_calculation(self, db_session):
        ops = FraudScoreOperations(session=db_session)
        assert ops._calculate_risk_level(0.1) == 'LOW'
        assert ops._calculate_risk_level(0.4) == 'MEDIUM'
        assert ops._calculate_risk_level(0.7) == 'HIGH'
        assert ops._calculate_risk_level(0.9) == 'CRITICAL'

    def test_get_high_risk_claims(self, db_session, seed_claim):
        ops = FraudScoreOperations(session=db_session)
        ops.save_fraud_score(
            claim_id=seed_claim.id,
            model_version='v2.1.0',
            fraud_score=0.88,
            is_fraud=True,
            confidence=0.95,
        )
        high_risk = ops.get_high_risk_claims(threshold=0.7)
        assert len(high_risk) >= 1


# ----------------------------------------------------------------
# Generic DatabaseOperations
# ----------------------------------------------------------------
@pytest.mark.integration
class TestDatabaseOperations:
    """Tests for base CRUD operations."""

    def test_count(self, db_session, seed_patient):
        ops = DatabaseOperations(session=db_session)
        count = ops.count(Patient)
        assert count >= 1

    def test_get_all(self, db_session, seed_patient):
        ops = DatabaseOperations(session=db_session)
        results = ops.get_all(Patient, limit=10)
        assert len(results) >= 1

    def test_get_by_id(self, db_session, seed_patient):
        ops = DatabaseOperations(session=db_session)
        found = ops.get_by_id(Patient, seed_patient.id)
        assert found is not None

    def test_delete(self, db_session, seed_patient):
        ops = DatabaseOperations(session=db_session)
        result = ops.delete(Patient, seed_patient.id)
        assert result is True
        assert ops.get_by_id(Patient, seed_patient.id) is None
