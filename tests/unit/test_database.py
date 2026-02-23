"""Unit Tests — Database Models and Connection."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.database.models import (
    User, Patient, Hospital, Claim, Document, FraudScore,
)
from src.database.connection import (
    DatabaseConnection, ConnectionPool, Base,
)


# ----------------------------------------------------------------
# Model Instantiation & Defaults
# ----------------------------------------------------------------
class TestUserModel:
    """Tests for the User ORM model."""

    def test_create_user(self):
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_pw',
            full_name='Test User',
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        # Column defaults only apply on session flush, verify they are declared
        assert User.__table__.c.role.default.arg == 'user'
        assert User.__table__.c.is_active.default.arg is True
        assert User.__table__.c.is_admin.default.arg is False

    def test_tablename(self):
        assert User.__tablename__ == 'users'


class TestPatientModel:
    """Tests for the Patient ORM model."""

    def test_create_patient(self):
        patient = Patient(
            mrn='MRN-001',
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime(1985, 6, 15),
        )
        assert patient.mrn == 'MRN-001'
        assert patient.first_name == 'John'
        assert Patient.__table__.c.is_active.default.arg is True

    def test_tablename(self):
        assert Patient.__tablename__ == 'patients'


class TestHospitalModel:
    """Tests for the Hospital ORM model."""

    def test_create_hospital(self):
        hospital = Hospital(
            name='Test Hospital',
            npi='1234567890',
            address='123 Main St',
            city='Test City',
            state='TX',
            zip_code='75001',
            license_number='TX-001',
        )
        assert hospital.name == 'Test Hospital'
        assert Hospital.__table__.c.is_active.default.arg is True

    def test_tablename(self):
        assert Hospital.__tablename__ == 'hospitals'


class TestClaimModel:
    """Tests for the Claim ORM model."""

    def test_create_claim(self):
        claim = Claim(
            claim_number='CLM-001',
            patient_id='patient-uuid',
            hospital_id='hospital-uuid',
            claim_amount=5000.00,
            treatment_type='Surgery',
            diagnosis_code='K35.80',
            claim_date=datetime.now(),
            service_date=datetime.now(),
        )
        assert claim.claim_number == 'CLM-001'
        assert claim.claim_amount == 5000.00
        assert Claim.__table__.c.status.default.arg == 'SUBMITTED'
        assert Claim.__table__.c.priority.default.arg == 'NORMAL'

    def test_tablename(self):
        assert Claim.__tablename__ == 'claims'

    def test_check_constraint_name(self):
        constraints = {c.name for c in Claim.__table__.constraints if hasattr(c, 'name') and c.name}
        assert 'ck_claim_amount_positive' in constraints


class TestDocumentModel:
    """Tests for the Document ORM model."""

    def test_create_document(self):
        doc = Document(
            claim_id='claim-uuid',
            document_type='medical_record',
            file_name='report.pdf',
            s3_key='claims/CLM-001/report.pdf',
            file_size=245000,
            mime_type='application/pdf',
        )
        assert doc.document_type == 'medical_record'
        assert Document.__table__.c.is_verified.default.arg is False

    def test_tablename(self):
        assert Document.__tablename__ == 'documents'


class TestFraudScoreModel:
    """Tests for the FraudScore ORM model."""

    def test_create_fraud_score(self):
        score = FraudScore(
            claim_id='claim-uuid',
            model_version='v2.1.0',
            fraud_score=0.85,
            is_fraud=True,
            confidence=0.92,
        )
        assert score.fraud_score == 0.85
        assert score.is_fraud is True
        assert FraudScore.__table__.c.risk_level.default.arg == 'LOW'
        assert FraudScore.__table__.c.manual_review.default.arg is False

    def test_tablename(self):
        assert FraudScore.__tablename__ == 'fraud_scores'


# ----------------------------------------------------------------
# DatabaseConnection
# ----------------------------------------------------------------
class TestDatabaseConnection:
    """Tests for the DatabaseConnection class."""

    def test_init(self):
        conn = DatabaseConnection(
            database_url='postgresql://user:pass@localhost/testdb',
            pool_size=5,
        )
        assert conn.database_url == 'postgresql://user:pass@localhost/testdb'
        assert conn.pool_size == 5
        assert conn.engine is None
        assert conn.session_factory is None

    def test_health_check_returns_false_when_not_connected(self):
        conn = DatabaseConnection('postgresql://user:pass@localhost/testdb')
        assert conn.health_check() is False

    def test_disconnect_without_connection(self):
        conn = DatabaseConnection('postgresql://user:pass@localhost/testdb')
        conn.disconnect()  # Should not raise


# ----------------------------------------------------------------
# ConnectionPool
# ----------------------------------------------------------------
class TestConnectionPool:
    """Tests for the ConnectionPool manager."""

    def test_init(self):
        pool = ConnectionPool()
        assert pool.connections == {}
        assert pool.default_key is None

    def test_get_nonexistent_raises(self):
        pool = ConnectionPool()
        with pytest.raises(ValueError):
            pool.get('nonexistent')

    def test_close_all_empty_pool(self):
        pool = ConnectionPool()
        pool.close_all()  # Should not raise


# ----------------------------------------------------------------
# Base
# ----------------------------------------------------------------
class TestBase:
    """Tests for SQLAlchemy Base."""

    def test_base_exists(self):
        assert Base is not None
        assert hasattr(Base, 'metadata')
