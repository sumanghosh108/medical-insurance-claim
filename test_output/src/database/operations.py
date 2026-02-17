"""Database Operations - High-level CRUD and Business Logic."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .models import Claim, Patient, Hospital, Document, FraudScore, User
from .connection import get_db_connection

import logging

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Base database operations."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize database operations."""
        self.session = session
    
    def _get_session(self) -> Session:
        """Get session (use provided or get new one)."""
        if self.session:
            return self.session
        return get_db_connection().get_session()
    
    def create(self, model_class, **kwargs):
        """Create and save a new record."""
        session = self._get_session()
        obj = model_class(**kwargs)
        session.add(obj)
        session.commit()
        logger.info(f"Created {model_class.__name__}: {obj.id}")
        return obj
    
    def update(self, model_class, obj_id: str, **kwargs):
        """Update a record."""
        session = self._get_session()
        obj = session.query(model_class).filter(model_class.id == obj_id).first()
        
        if obj:
            for key, value in kwargs.items():
                setattr(obj, key, value)
            session.commit()
            logger.info(f"Updated {model_class.__name__}: {obj_id}")
        
        return obj
    
    def delete(self, model_class, obj_id: str) -> bool:
        """Delete a record."""
        session = self._get_session()
        obj = session.query(model_class).filter(model_class.id == obj_id).first()
        
        if obj:
            session.delete(obj)
            session.commit()
            logger.info(f"Deleted {model_class.__name__}: {obj_id}")
            return True
        
        return False
    
    def get_by_id(self, model_class, obj_id: str):
        """Get record by ID."""
        session = self._get_session()
        return session.query(model_class).filter(model_class.id == obj_id).first()
    
    def get_all(self, model_class, limit: int = 100, offset: int = 0):
        """Get all records with pagination."""
        session = self._get_session()
        return session.query(model_class).limit(limit).offset(offset).all()
    
    def count(self, model_class) -> int:
        """Count total records."""
        session = self._get_session()
        return session.query(model_class).count()


class PatientOperations(DatabaseOperations):
    """Patient-specific operations."""
    
    def create_patient(
        self,
        mrn: str,
        first_name: str,
        last_name: str,
        date_of_birth: datetime,
        **kwargs
    ) -> Patient:
        """Create a new patient."""
        return self.create(
            Patient,
            mrn=mrn,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            **kwargs
        )
    
    def find_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Find patient by Medical Record Number."""
        session = self._get_session()
        return session.query(Patient).filter(Patient.mrn == mrn).first()
    
    def find_by_email(self, email: str) -> Optional[Patient]:
        """Find patient by email."""
        session = self._get_session()
        return session.query(Patient).filter(Patient.email == email).first()
    
    def search_patients(self, query: str) -> List[Patient]:
        """Search patients by name or email."""
        session = self._get_session()
        search_term = f"%{query}%"
        return session.query(Patient).filter(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.email.ilike(search_term),
                Patient.mrn.ilike(search_term)
            )
        ).all()
    
    def get_patient_claims(self, patient_id: str) -> List[Claim]:
        """Get all claims for a patient."""
        session = self._get_session()
        return session.query(Claim).filter(Claim.patient_id == patient_id).all()


class HospitalOperations(DatabaseOperations):
    """Hospital-specific operations."""
    
    def create_hospital(
        self,
        name: str,
        npi: str,
        address: str,
        city: str,
        state: str,
        zip_code: str,
        license_number: str,
        **kwargs
    ) -> Hospital:
        """Create a new hospital."""
        return self.create(
            Hospital,
            name=name,
            npi=npi,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            license_number=license_number,
            **kwargs
        )
    
    def find_by_npi(self, npi: str) -> Optional[Hospital]:
        """Find hospital by NPI."""
        session = self._get_session()
        return session.query(Hospital).filter(Hospital.npi == npi).first()
    
    def find_by_license(self, license_number: str) -> Optional[Hospital]:
        """Find hospital by license number."""
        session = self._get_session()
        return session.query(Hospital).filter(
            Hospital.license_number == license_number
        ).first()
    
    def get_active_hospitals(self) -> List[Hospital]:
        """Get all active hospitals."""
        session = self._get_session()
        return session.query(Hospital).filter(Hospital.is_active == True).all()


class ClaimOperations(DatabaseOperations):
    """Claim-specific operations."""
    
    def create_claim(
        self,
        claim_number: str,
        patient_id: str,
        hospital_id: str,
        claim_amount: float,
        treatment_type: str,
        diagnosis_code: str,
        claim_date: datetime,
        service_date: datetime,
        **kwargs
    ) -> Claim:
        """Create a new claim."""
        return self.create(
            Claim,
            claim_number=claim_number,
            patient_id=patient_id,
            hospital_id=hospital_id,
            claim_amount=claim_amount,
            treatment_type=treatment_type,
            diagnosis_code=diagnosis_code,
            claim_date=claim_date,
            service_date=service_date,
            **kwargs
        )
    
    def find_by_number(self, claim_number: str) -> Optional[Claim]:
        """Find claim by claim number."""
        session = self._get_session()
        return session.query(Claim).filter(Claim.claim_number == claim_number).first()
    
    def get_by_status(self, status: str) -> List[Claim]:
        """Get claims by status."""
        session = self._get_session()
        return session.query(Claim).filter(Claim.status == status).all()
    
    def get_pending_claims(self) -> List[Claim]:
        """Get all pending claims."""
        return self.get_by_status('SUBMITTED')
    
    def get_approved_claims(self) -> List[Claim]:
        """Get all approved claims."""
        return self.get_by_status('APPROVED')
    
    def get_rejected_claims(self) -> List[Claim]:
        """Get all rejected claims."""
        return self.get_by_status('REJECTED')
    
    def update_claim_status(
        self,
        claim_id: str,
        status: str,
        notes: Optional[str] = None,
    ) -> Optional[Claim]:
        """Update claim status."""
        kwargs = {'status': status}
        
        if notes:
            kwargs['processing_notes'] = notes
        
        if status == 'APPROVED':
            kwargs['approval_date'] = datetime.now()
        
        return self.update(Claim, claim_id, **kwargs)
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Claim]:
        """Get claims within date range."""
        session = self._get_session()
        return session.query(Claim).filter(
            and_(
                Claim.claim_date >= start_date,
                Claim.claim_date <= end_date
            )
        ).all()
    
    def get_high_value_claims(self, amount: float = 10000.0) -> List[Claim]:
        """Get claims above a certain amount."""
        session = self._get_session()
        return session.query(Claim).filter(Claim.claim_amount >= amount).all()
    
    def get_claim_summary(self, claim_id: str) -> Dict[str, Any]:
        """Get comprehensive claim summary."""
        claim = self.get_by_id(Claim, claim_id)
        
        if not claim:
            return {}
        
        return {
            'id': claim.id,
            'number': claim.claim_number,
            'patient': {
                'id': claim.patient.id,
                'name': f"{claim.patient.first_name} {claim.patient.last_name}",
                'mrn': claim.patient.mrn,
            },
            'hospital': {
                'id': claim.hospital.id,
                'name': claim.hospital.name,
            },
            'amount': claim.claim_amount,
            'status': claim.status,
            'created': claim.created_at.isoformat(),
            'documents': [
                {
                    'id': doc.id,
                    'type': doc.document_type,
                    'name': doc.file_name,
                    'verified': doc.is_verified,
                }
                for doc in claim.documents
            ],
            'fraud_score': claim.fraud_score.fraud_score if claim.fraud_score else None,
            'is_fraud': claim.fraud_score.is_fraud if claim.fraud_score else False,
        }


class DocumentOperations(DatabaseOperations):
    """Document-specific operations."""
    
    def add_document(
        self,
        claim_id: str,
        document_type: str,
        file_name: str,
        s3_key: str,
        file_size: int,
        mime_type: str,
        upload_user: str,
        **kwargs
    ) -> Document:
        """Add document to claim."""
        return self.create(
            Document,
            claim_id=claim_id,
            document_type=document_type,
            file_name=file_name,
            s3_key=s3_key,
            file_size=file_size,
            mime_type=mime_type,
            upload_user=upload_user,
            **kwargs
        )
    
    def get_claim_documents(self, claim_id: str) -> List[Document]:
        """Get all documents for a claim."""
        session = self._get_session()
        return session.query(Document).filter(Document.claim_id == claim_id).all()
    
    def verify_document(
        self,
        doc_id: str,
        verified_by: str,
        notes: Optional[str] = None,
    ) -> Optional[Document]:
        """Mark document as verified."""
        return self.update(
            Document,
            doc_id,
            is_verified=True,
            verification_user=verified_by,
            verification_notes=notes,
            verified_at=datetime.utcnow()
        )
    
    def get_unverified_documents(self) -> List[Document]:
        """Get all unverified documents."""
        session = self._get_session()
        return session.query(Document).filter(Document.is_verified == False).all()


class FraudScoreOperations(DatabaseOperations):
    """Fraud Score-specific operations."""
    
    def save_fraud_score(
        self,
        claim_id: str,
        model_version: str,
        fraud_score: float,
        is_fraud: bool,
        confidence: float,
        **kwargs
    ) -> FraudScore:
        """Save fraud detection results."""
        risk_level = self._calculate_risk_level(fraud_score)
        
        return self.create(
            FraudScore,
            claim_id=claim_id,
            model_version=model_version,
            fraud_score=fraud_score,
            is_fraud=is_fraud,
            confidence=confidence,
            risk_level=risk_level,
            **kwargs
        )
    
    @staticmethod
    def _calculate_risk_level(score: float) -> str:
        """Calculate risk level from score."""
        if score < 0.3:
            return "LOW"
        elif score < 0.6:
            return "MEDIUM"
        elif score < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def get_high_risk_claims(self, threshold: float = 0.7) -> List[FraudScore]:
        """Get high-risk fraud scores."""
        session = self._get_session()
        return session.query(FraudScore).filter(
            FraudScore.fraud_score >= threshold
        ).all()
    
    def get_fraud_cases(self) -> List[FraudScore]:
        """Get all flagged fraud cases."""
        session = self._get_session()
        return session.query(FraudScore).filter(
            FraudScore.is_fraud == True
        ).all()