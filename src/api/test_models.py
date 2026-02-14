"""
Unit tests for API models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from api.models import (
    PersonalInformation,
    PolicyInformation,
    IncidentInformation,
    MedicalInformation,
    ClaimAmount,
    ClaimSubmissionRequest,
    ClaimUpdateRequest,
    DocumentUploadRequest,
    ClaimQueryParams,
    ClaimType,
    ClaimStatus,
    DocumentType,
)


class TestPersonalInformation:
    """Tests for PersonalInformation model"""
    
    def test_valid_personal_info(self):
        """Test valid personal information"""
        
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15T00:00:00Z",
            "email": "john@example.com",
            "phone": "5551234567",
            "address": "123 Main St"
        }
        
        info = PersonalInformation(**data)
        
        assert info.first_name == "John"
        assert info.last_name == "Doe"
        assert info.email == "john@example.com"
        assert info.phone == "5551234567"
    
    def test_ssn_normalization(self):
        """Test SSN normalization (removes hyphens)"""
        
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15T00:00:00Z",
            "ssn": "123-45-6789",
            "email": "john@example.com",
            "phone": "5551234567",
            "address": "123 Main St"
        }
        
        info = PersonalInformation(**data)
        
        # SSN should have hyphens removed
        assert info.ssn == "123456789"
    
    def test_phone_normalization(self):
        """Test phone number normalization"""
        
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15T00:00:00Z",
            "email": "john@example.com",
            "phone": "+1-555-123-4567",
            "address": "123 Main St"
        }
        
        info = PersonalInformation(**data)
        
        # Phone should have non-numeric characters removed
        assert info.phone == "15551234567"
    
    def test_invalid_email(self):
        """Test invalid email format"""
        
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-01-15T00:00:00Z",
            "email": "not-an-email",
            "phone": "5551234567",
            "address": "123 Main St"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PersonalInformation(**data)
        
        errors = exc_info.value.errors()
        assert any(e['loc'] == ('email',) for e in errors)


class TestPolicyInformation:
    """Tests for PolicyInformation model"""
    
    def test_valid_policy_info(self):
        """Test valid policy information"""
        
        data = {
            "policy_number": "AB1234567",
            "policy_holder_name": "John Doe",
            "coverage_type": "Health",
            "effective_date": "2024-01-01T00:00:00Z",
            "expiration_date": "2025-01-01T00:00:00Z"
        }
        
        policy = PolicyInformation(**data)
        
        assert policy.policy_number == "AB1234567"
        assert policy.coverage_type == "Health"
    
    def test_invalid_policy_number_format(self):
        """Test invalid policy number format"""
        
        data = {
            "policy_number": "INVALID",
            "policy_holder_name": "John Doe",
            "coverage_type": "Health",
            "effective_date": "2024-01-01T00:00:00Z"
        }
        
        with pytest.raises(ValidationError):
            PolicyInformation(**data)
    
    def test_expiration_before_effective(self):
        """Test expiration date before effective date"""
        
        data = {
            "policy_number": "AB1234567",
            "policy_holder_name": "John Doe",
            "coverage_type": "Health",
            "effective_date": "2025-01-01T00:00:00Z",
            "expiration_date": "2024-01-01T00:00:00Z"  # Before effective
        }
        
        with pytest.raises(ValidationError) as exc_info:
            PolicyInformation(**data)
        
        assert "after effective date" in str(exc_info.value)


class TestIncidentInformation:
    """Tests for IncidentInformation model"""
    
    def test_valid_incident_info(self):
        """Test valid incident information"""
        
        data = {
            "incident_date": "2024-03-15T14:30:00Z",
            "incident_location": "123 Main St",
            "description": "Vehicle collision at intersection"
        }
        
        incident = IncidentInformation(**data)
        
        assert incident.description == "Vehicle collision at intersection"
    
    def test_future_incident_date(self):
        """Test incident date in the future"""
        
        future_date = datetime.now().replace(year=datetime.now().year + 1)
        
        data = {
            "incident_date": future_date.isoformat(),
            "incident_location": "123 Main St",
            "description": "Test incident"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IncidentInformation(**data)
        
        assert "cannot be in the future" in str(exc_info.value)
    
    def test_very_old_incident_date(self):
        """Test incident date more than 10 years old"""
        
        old_date = datetime.now().replace(year=datetime.now().year - 11)
        
        data = {
            "incident_date": old_date.isoformat(),
            "incident_location": "123 Main St",
            "description": "Old incident"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            IncidentInformation(**data)
        
        assert "10 years old" in str(exc_info.value)


class TestMedicalInformation:
    """Tests for MedicalInformation model"""
    
    def test_valid_medical_info(self):
        """Test valid medical information"""
        
        data = {
            "provider_name": "Dr. Smith",
            "diagnosis_codes": ["E11.9", "I10"],
            "treatment_date": "2024-03-15T00:00:00Z"
        }
        
        medical = MedicalInformation(**data)
        
        assert len(medical.diagnosis_codes) == 2
        assert "E11.9" in medical.diagnosis_codes
    
    def test_invalid_icd_code_format(self):
        """Test invalid ICD-10 code format"""
        
        data = {
            "provider_name": "Dr. Smith",
            "diagnosis_codes": ["INVALID"],
            "treatment_date": "2024-03-15T00:00:00Z"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MedicalInformation(**data)
        
        assert "Invalid ICD-10 code" in str(exc_info.value)
    
    def test_empty_diagnosis_codes(self):
        """Test empty diagnosis codes"""
        
        data = {
            "provider_name": "Dr. Smith",
            "diagnosis_codes": [],
            "treatment_date": "2024-03-15T00:00:00Z"
        }
        
        with pytest.raises(ValidationError):
            MedicalInformation(**data)


class TestClaimAmount:
    """Tests for ClaimAmount model"""
    
    def test_valid_amount(self):
        """Test valid claim amount"""
        
        data = {
            "claimed_amount": 5000.00,
            "currency": "USD"
        }
        
        amount = ClaimAmount(**data)
        
        assert amount.claimed_amount == 5000.00
        assert amount.currency == "USD"
    
    def test_amount_rounding(self):
        """Test amount rounding to 2 decimal places"""
        
        data = {
            "claimed_amount": 5000.12345,
            "currency": "USD"
        }
        
        amount = ClaimAmount(**data)
        
        # Should round to 2 decimals
        assert amount.claimed_amount == 5000.12
    
    def test_negative_amount(self):
        """Test negative amount (should fail)"""
        
        data = {
            "claimed_amount": -100.00,
            "currency": "USD"
        }
        
        with pytest.raises(ValidationError):
            ClaimAmount(**data)
    
    def test_amount_too_large(self):
        """Test amount exceeding maximum"""
        
        data = {
            "claimed_amount": 20000000.00,  # > 10M
            "currency": "USD"
        }
        
        with pytest.raises(ValidationError):
            ClaimAmount(**data)


class TestClaimSubmissionRequest:
    """Tests for complete claim submission"""
    
    def test_valid_health_claim(self):
        """Test valid health claim submission"""
        
        data = {
            "claim_type": "health",
            "personal_info": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-01-15T00:00:00Z",
                "email": "john@example.com",
                "phone": "5551234567",
                "address": "123 Main St"
            },
            "policy_info": {
                "policy_number": "AB1234567",
                "policy_holder_name": "John Doe",
                "coverage_type": "Health",
                "effective_date": "2024-01-01T00:00:00Z"
            },
            "incident_info": {
                "incident_date": "2024-03-15T00:00:00Z",
                "incident_location": "Hospital",
                "description": "Medical treatment"
            },
            "amount": {
                "claimed_amount": 5000.00,
                "currency": "USD"
            },
            "medical_info": {
                "provider_name": "Dr. Smith",
                "diagnosis_codes": ["E11.9"],
                "treatment_date": "2024-03-15T00:00:00Z"
            }
        }
        
        claim = ClaimSubmissionRequest(**data)
        
        assert claim.claim_type == ClaimType.HEALTH
        assert claim.personal_info.first_name == "John"
        assert claim.medical_info.provider_name == "Dr. Smith"
    
    def test_health_claim_without_medical_info(self):
        """Test health claim requires medical info"""
        
        data = {
            "claim_type": "health",
            "personal_info": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-01-15T00:00:00Z",
                "email": "john@example.com",
                "phone": "5551234567",
                "address": "123 Main St"
            },
            "policy_info": {
                "policy_number": "AB1234567",
                "policy_holder_name": "John Doe",
                "coverage_type": "Health",
                "effective_date": "2024-01-01T00:00:00Z"
            },
            "incident_info": {
                "incident_date": "2024-03-15T00:00:00Z",
                "incident_location": "Hospital",
                "description": "Medical treatment"
            },
            "amount": {
                "claimed_amount": 5000.00,
                "currency": "USD"
            }
            # Missing medical_info
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ClaimSubmissionRequest(**data)
        
        assert "Medical information is required" in str(exc_info.value)


class TestDocumentUploadRequest:
    """Tests for document upload request"""
    
    def test_valid_upload_request(self):
        """Test valid document upload request"""
        
        data = {
            "claim_id": "CLM-1234567890",
            "document_type": "medical_record",
            "file_name": "record.pdf",
            "file_size": 1024000,
            "content_type": "application/pdf"
        }
        
        upload = DocumentUploadRequest(**data)
        
        assert upload.claim_id == "CLM-1234567890"
        assert upload.document_type == DocumentType.MEDICAL_RECORD
    
    def test_invalid_claim_id_format(self):
        """Test invalid claim ID format"""
        
        data = {
            "claim_id": "INVALID",
            "document_type": "medical_record",
            "file_name": "record.pdf",
            "file_size": 1024000,
            "content_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError):
            DocumentUploadRequest(**data)
    
    def test_file_too_large(self):
        """Test file size exceeds maximum"""
        
        data = {
            "claim_id": "CLM-1234567890",
            "document_type": "medical_record",
            "file_name": "record.pdf",
            "file_size": 60 * 1024 * 1024,  # 60MB > 50MB limit
            "content_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError):
            DocumentUploadRequest(**data)
    
    def test_invalid_filename(self):
        """Test invalid filename format"""
        
        data = {
            "claim_id": "CLM-1234567890",
            "document_type": "medical_record",
            "file_name": "../../../etc/passwd",  # Path traversal attempt
            "file_size": 1024000,
            "content_type": "application/pdf"
        }
        
        with pytest.raises(ValidationError):
            DocumentUploadRequest(**data)


class TestClaimQueryParams:
    """Tests for claim query parameters"""
    
    def test_default_params(self):
        """Test default query parameters"""
        
        params = ClaimQueryParams()
        
        assert params.limit == 20
        assert params.offset == 0
        assert params.sort_by == "created_at"
        assert params.sort_order == "desc"
    
    def test_custom_params(self):
        """Test custom query parameters"""
        
        data = {
            "status": "processing",
            "claim_type": "health",
            "limit": 50,
            "offset": 20,
            "sort_by": "updated_at",
            "sort_order": "asc"
        }
        
        params = ClaimQueryParams(**data)
        
        assert params.status == ClaimStatus.PROCESSING
        assert params.claim_type == ClaimType.HEALTH
        assert params.limit == 50
    
    def test_limit_constraints(self):
        """Test limit constraints (1-100)"""
        
        # Too high
        with pytest.raises(ValidationError):
            ClaimQueryParams(limit=150)
        
        # Too low
        with pytest.raises(ValidationError):
            ClaimQueryParams(limit=0)
    
    def test_invalid_sort_by(self):
        """Test invalid sort_by field"""
        
        with pytest.raises(ValidationError):
            ClaimQueryParams(sort_by="invalid_field")


def test_enum_values():
    """Test enum values"""
    
    assert ClaimType.HEALTH.value == "health"
    assert ClaimStatus.PROCESSING.value == "processing"
    assert DocumentType.MEDICAL_RECORD.value == "medical_record"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])