"""Database Models - SQLAlchemy ORM Definitions."""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint,
)
from sqlalchemy.orm import relationship

from .connection import Base


class User(Base):
    """User/Admin model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_user_username', 'username'),
        Index('ix_user_email', 'email'),
        {'extend_existing': True},
    )


class Patient(Base):
    """Patient model."""
    __tablename__ = "patients"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mrn = Column(String(50), unique=True, nullable=False, index=True)  # Medical Record Number
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    gender = Column(String(10), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    insurance_provider = Column(String(255), nullable=True)
    insurance_id = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claims = relationship("Claim", back_populates="patient", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_patient_mrn', 'mrn'),
        Index('ix_patient_name', 'first_name', 'last_name'),
        Index('ix_patient_email', 'email'),
        {'extend_existing': True},
    )


class Hospital(Base):
    """Hospital/Healthcare Provider model."""
    __tablename__ = "hospitals"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    npi = Column(String(50), unique=True, nullable=False, index=True)  # National Provider ID
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(50), nullable=False)
    zip_code = Column(String(10), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    license_number = Column(String(100), unique=True, nullable=False)
    accreditation_level = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claims = relationship("Claim", back_populates="hospital", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_hospital_name', 'name'),
        Index('ix_hospital_npi', 'npi'),
        Index('ix_hospital_license', 'license_number'),
        {'extend_existing': True},
    )


class Claim(Base):
    """Insurance Claim model."""
    __tablename__ = "claims"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_number = Column(String(50), unique=True, nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False)
    hospital_id = Column(String(36), ForeignKey('hospitals.id'), nullable=False)
    claim_amount = Column(Float, nullable=False)
    treatment_type = Column(String(100), nullable=False)
    diagnosis_code = Column(String(20), nullable=False)  # ICD-10 code
    procedure_code = Column(String(20), nullable=True)  # CPT code
    claim_date = Column(DateTime, nullable=False, index=True)
    service_date = Column(DateTime, nullable=False)
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String(50), default='SUBMITTED', nullable=False, index=True)
    priority = Column(String(20), default='NORMAL', nullable=False)
    approval_amount = Column(Float, nullable=True)
    approval_date = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    processing_notes = Column(Text, nullable=True)
    claim_metadata = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="claims")
    hospital = relationship("Hospital", back_populates="claims")
    documents = relationship("Document", back_populates="claim", cascade="all, delete-orphan")
    fraud_score = relationship("FraudScore", back_populates="claim", uselist=False)
    
    __table_args__ = (
        Index('ix_claim_number', 'claim_number'),
        Index('ix_claim_patient', 'patient_id'),
        Index('ix_claim_hospital', 'hospital_id'),
        Index('ix_claim_status', 'status'),
        Index('ix_claim_date', 'claim_date'),
        Index('ix_claim_submission', 'submission_date'),
        CheckConstraint('claim_amount > 0', name='ck_claim_amount_positive'),
        {'extend_existing': True},
    )


class Document(Base):
    """Supporting Document model."""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey('claims.id'), nullable=False)
    document_type = Column(String(50), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    ocr_text = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_user = Column(String(255), nullable=True)
    verification_notes = Column(Text, nullable=True)
    upload_user = Column(String(255), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claim = relationship("Claim", back_populates="documents")
    
    __table_args__ = (
        Index('ix_document_claim', 'claim_id'),
        Index('ix_document_type', 'document_type'),
        Index('ix_document_s3', 's3_key'),
        {'extend_existing': True},
    )


class FraudScore(Base):
    """Fraud Detection Results model."""
    __tablename__ = "fraud_scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(36), ForeignKey('claims.id'), nullable=False, unique=True)
    model_version = Column(String(20), nullable=False)
    fraud_score = Column(Float, nullable=False)
    is_fraud = Column(Boolean, nullable=False, default=False, index=True)
    confidence = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    model_inputs = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    reviewed_by = Column(String(255), nullable=True)
    manual_review = Column(Boolean, default=False, nullable=False)
    manual_determination = Column(String(20), nullable=True)  # FRAUD, NOT_FRAUD
    review_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    claim = relationship("Claim", back_populates="fraud_score")
    
    __table_args__ = (
        Index('ix_fraud_claim', 'claim_id'),
        Index('ix_fraud_score', 'fraud_score'),
        Index('ix_fraud_flag', 'is_fraud'),
        Index('ix_fraud_level', 'risk_level'),
        {'extend_existing': True},
    )