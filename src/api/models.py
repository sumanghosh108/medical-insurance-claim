"""
API Models

Pydantic models for request validation and response serialization.
Ensures type safety and automatic validation for all API operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, EmailStr, validator, root_validator


# Enums for constrained values
class ClaimType(str, Enum):
    """Types of insurance claims"""
    HEALTH = "health"
    AUTO = "auto"
    PROPERTY = "property"
    LIFE = "life"


class ClaimStatus(str, Enum):
    """Claim processing status"""
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING_DOCUMENTS = "pending_documents"
    PAID = "paid"
    CLOSED = "closed"


class DocumentType(str, Enum):
    """Types of claim documents"""
    CLAIM_FORM = "claim_form"
    MEDICAL_RECORD = "medical_record"
    INVOICE = "invoice"
    POLICE_REPORT = "police_report"
    PROOF_OF_LOSS = "proof_of_loss"
    ID_VERIFICATION = "id_verification"
    OTHER = "other"


class Priority(str, Enum):
    """Claim priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Request Models
class PersonalInformation(BaseModel):
    """Personal information for claimant"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: datetime
    ssn: Optional[str] = Field(None, regex=r'^\d{3}-\d{2}-\d{4}$|^\d{9}$')
    email: EmailStr
    phone: str = Field(..., regex=r'^\+?1?\d{10,15}$')
    address: str = Field(..., min_length=5, max_length=500)
    
    @validator('ssn')
    def validate_ssn(cls, v):
        if v:
            # Remove hyphens for storage
            return v.replace('-', '')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove non-numeric characters
        return ''.join(filter(str.isdigit, v))
    
    class Config:
        schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1980-01-15T00:00:00Z",
                "ssn": "123-45-6789",
                "email": "john.doe@example.com",
                "phone": "+15551234567",
                "address": "123 Main St, Anytown, ST 12345"
            }
        }


class PolicyInformation(BaseModel):
    """Insurance policy information"""
    policy_number: str = Field(..., regex=r'^[A-Z]{2,3}\d{6,10}$|^POL-\d{6,10}$')
    policy_holder_name: str = Field(..., min_length=1, max_length=200)
    coverage_type: str = Field(..., min_length=1, max_length=100)
    effective_date: datetime
    expiration_date: Optional[datetime] = None
    
    @validator('expiration_date')
    def validate_dates(cls, v, values):
        if v and 'effective_date' in values:
            if v <= values['effective_date']:
                raise ValueError('Expiration date must be after effective date')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "policy_number": "AB1234567",
                "policy_holder_name": "John Doe",
                "coverage_type": "Comprehensive Health",
                "effective_date": "2024-01-01T00:00:00Z",
                "expiration_date": "2025-01-01T00:00:00Z"
            }
        }


class IncidentInformation(BaseModel):
    """Information about the incident/claim event"""
    incident_date: datetime
    incident_location: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10, max_length=5000)
    incident_type: Optional[str] = Field(None, max_length=100)
    police_report_number: Optional[str] = None
    witnesses: Optional[List[str]] = None
    
    @validator('incident_date')
    def validate_incident_date(cls, v):
        if v > datetime.now():
            raise ValueError('Incident date cannot be in the future')
        # Check if incident is too old (>10 years)
        ten_years_ago = datetime.now().replace(year=datetime.now().year - 10)
        if v < ten_years_ago:
            raise ValueError('Incident date is more than 10 years old')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "incident_date": "2024-03-15T14:30:00Z",
                "incident_location": "123 Main St, Anytown, ST 12345",
                "description": "Vehicle collision at intersection",
                "incident_type": "Auto Accident",
                "police_report_number": "PR-2024-12345"
            }
        }


class MedicalInformation(BaseModel):
    """Medical information for health claims"""
    provider_name: str = Field(..., min_length=1, max_length=200)
    provider_npi: Optional[str] = Field(None, regex=r'^\d{10}$')
    facility_name: Optional[str] = Field(None, max_length=200)
    diagnosis_codes: List[str] = Field(..., min_items=1)
    procedure_codes: Optional[List[str]] = None
    treatment_date: datetime
    treatment_description: Optional[str] = Field(None, max_length=2000)
    
    @validator('diagnosis_codes', each_item=True)
    def validate_icd_codes(cls, v):
        # Basic ICD-10 format validation
        import re
        if not re.match(r'^[A-Z]\d{2}(\.\d{1,2})?$', v):
            raise ValueError(f'Invalid ICD-10 code format: {v}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "provider_name": "Dr. Sarah Johnson, MD",
                "provider_npi": "1234567890",
                "facility_name": "City General Hospital",
                "diagnosis_codes": ["E11.9", "I10"],
                "procedure_codes": ["99213", "36415"],
                "treatment_date": "2024-03-15T00:00:00Z",
                "treatment_description": "Office visit for diabetes management"
            }
        }


class ClaimAmount(BaseModel):
    """Financial information for the claim"""
    claimed_amount: float = Field(..., gt=0, le=10000000)
    currency: str = Field(default="USD", regex=r'^[A-Z]{3}$')
    breakdown: Optional[Dict[str, float]] = None
    
    @validator('claimed_amount')
    def validate_amount(cls, v):
        # Ensure 2 decimal places
        return round(v, 2)
    
    class Config:
        schema_extra = {
            "example": {
                "claimed_amount": 5000.00,
                "currency": "USD",
                "breakdown": {
                    "medical_services": 4000.00,
                    "prescription_drugs": 800.00,
                    "other": 200.00
                }
            }
        }


class ClaimSubmissionRequest(BaseModel):
    """Request model for claim submission"""
    claim_type: ClaimType
    personal_info: PersonalInformation
    policy_info: PolicyInformation
    incident_info: IncidentInformation
    amount: ClaimAmount
    medical_info: Optional[MedicalInformation] = None
    priority: Optional[Priority] = Priority.MEDIUM
    additional_notes: Optional[str] = Field(None, max_length=5000)
    attachments: Optional[List[str]] = None  # S3 URIs or document IDs
    
    @root_validator
    def validate_medical_info(cls, values):
        claim_type = values.get('claim_type')
        medical_info = values.get('medical_info')
        
        if claim_type == ClaimType.HEALTH and not medical_info:
            raise ValueError('Medical information is required for health claims')
        
        return values
    
    class Config:
        schema_extra = {
            "example": {
                "claim_type": "health",
                "personal_info": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1980-01-15T00:00:00Z",
                    "email": "john.doe@example.com",
                    "phone": "5551234567",
                    "address": "123 Main St, Anytown, ST 12345"
                },
                "policy_info": {
                    "policy_number": "AB1234567",
                    "policy_holder_name": "John Doe",
                    "coverage_type": "Health",
                    "effective_date": "2024-01-01T00:00:00Z"
                },
                "incident_info": {
                    "incident_date": "2024-03-15T00:00:00Z",
                    "incident_location": "City General Hospital",
                    "description": "Medical treatment for diabetes"
                },
                "amount": {
                    "claimed_amount": 5000.00,
                    "currency": "USD"
                },
                "medical_info": {
                    "provider_name": "Dr. Johnson",
                    "diagnosis_codes": ["E11.9"],
                    "treatment_date": "2024-03-15T00:00:00Z"
                },
                "priority": "medium"
            }
        }


class ClaimUpdateRequest(BaseModel):
    """Request model for updating a claim"""
    status: Optional[ClaimStatus] = None
    additional_notes: Optional[str] = Field(None, max_length=5000)
    attachments: Optional[List[str]] = None
    assigned_to: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "under_review",
                "additional_notes": "Requested additional documentation",
                "assigned_to": "adjuster_123"
            }
        }


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    claim_id: str = Field(..., regex=r'^CLM-\d{10,12}$')
    document_type: DocumentType
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0, le=50*1024*1024)  # Max 50MB
    content_type: str = Field(..., regex=r'^[a-z]+/[a-z0-9\-\+\.]+$')
    
    @validator('file_name')
    def validate_filename(cls, v):
        # Basic filename sanitization
        import re
        if not re.match(r'^[\w\-. ]+\.[a-zA-Z0-9]+$', v):
            raise ValueError('Invalid filename format')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "claim_id": "CLM-1234567890",
                "document_type": "medical_record",
                "file_name": "medical_record.pdf",
                "file_size": 1024000,
                "content_type": "application/pdf"
            }
        }


class ClaimQueryParams(BaseModel):
    """Query parameters for listing claims"""
    status: Optional[ClaimStatus] = None
    claim_type: Optional[ClaimType] = None
    policy_number: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="created_at", regex=r'^(created_at|updated_at|claim_id|status)$')
    sort_order: str = Field(default="desc", regex=r'^(asc|desc)$')
    
    class Config:
        schema_extra = {
            "example": {
                "status": "processing",
                "claim_type": "health",
                "limit": 20,
                "offset": 0,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


# Response Models
class ClaimMetadata(BaseModel):
    """Metadata about the claim"""
    claim_id: str
    claim_number: str
    status: ClaimStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    created_by: str
    assigned_to: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    
    class Config:
        schema_extra = {
            "example": {
                "claim_id": "claim_abc123",
                "claim_number": "CLM-1234567890",
                "status": "processing",
                "priority": "medium",
                "created_at": "2024-03-15T10:00:00Z",
                "updated_at": "2024-03-15T10:05:00Z",
                "created_by": "user_123",
                "processing_time_seconds": 45.5
            }
        }


class ValidationResult(BaseModel):
    """Validation results for the claim"""
    is_valid: bool
    validation_score: float = Field(..., ge=0, le=100)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        schema_extra = {
            "example": {
                "is_valid": True,
                "validation_score": 92.5,
                "errors": [],
                "warnings": [
                    {
                        "code": "AMOUNT_HIGH",
                        "message": "Claimed amount is higher than typical"
                    }
                ]
            }
        }


class FraudScore(BaseModel):
    """Fraud detection results"""
    fraud_probability: float = Field(..., ge=0, le=1)
    risk_level: str = Field(..., regex=r'^(low|medium|high|very_high)$')
    contributing_factors: List[str] = Field(default_factory=list)
    model_version: str
    
    class Config:
        schema_extra = {
            "example": {
                "fraud_probability": 0.15,
                "risk_level": "low",
                "contributing_factors": [],
                "model_version": "1.0.0"
            }
        }


class ProcessingResult(BaseModel):
    """Document processing results"""
    documents_processed: int
    text_extraction_confidence: Optional[float] = None
    entities_extracted: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "documents_processed": 3,
                "text_extraction_confidence": 95.5,
                "entities_extracted": 15
            }
        }


class ClaimResponse(BaseModel):
    """Response model for claim operations"""
    metadata: ClaimMetadata
    claim_data: Optional[ClaimSubmissionRequest] = None
    validation: Optional[ValidationResult] = None
    fraud_score: Optional[FraudScore] = None
    processing: Optional[ProcessingResult] = None
    next_steps: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "claim_id": "claim_abc123",
                    "claim_number": "CLM-1234567890",
                    "status": "processing",
                    "priority": "medium",
                    "created_at": "2024-03-15T10:00:00Z",
                    "updated_at": "2024-03-15T10:05:00Z",
                    "created_by": "user_123"
                },
                "validation": {
                    "is_valid": True,
                    "validation_score": 92.5,
                    "errors": [],
                    "warnings": []
                },
                "fraud_score": {
                    "fraud_probability": 0.15,
                    "risk_level": "low",
                    "contributing_factors": [],
                    "model_version": "1.0.0"
                },
                "next_steps": [
                    "Document processing in progress",
                    "Fraud detection analysis complete",
                    "Awaiting adjuster review"
                ]
            }
        }


class ClaimListResponse(BaseModel):
    """Response model for claim listing"""
    claims: List[ClaimResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool
    
    class Config:
        schema_extra = {
            "example": {
                "claims": [],
                "total_count": 150,
                "limit": 20,
                "offset": 0,
                "has_more": True
            }
        }


class DocumentMetadata(BaseModel):
    """Metadata about uploaded document"""
    document_id: str
    claim_id: str
    document_type: DocumentType
    file_name: str
    file_size: int
    content_type: str
    s3_uri: str
    uploaded_at: datetime
    uploaded_by: str
    processing_status: str
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_xyz789",
                "claim_id": "CLM-1234567890",
                "document_type": "medical_record",
                "file_name": "medical_record.pdf",
                "file_size": 1024000,
                "content_type": "application/pdf",
                "s3_uri": "s3://claims-documents/doc_xyz789.pdf",
                "uploaded_at": "2024-03-15T10:00:00Z",
                "uploaded_by": "user_123",
                "processing_status": "completed"
            }
        }


class DocumentResponse(BaseModel):
    """Response model for document operations"""
    metadata: DocumentMetadata
    presigned_url: Optional[str] = None
    extraction_results: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "metadata": {
                    "document_id": "doc_xyz789",
                    "claim_id": "CLM-1234567890",
                    "document_type": "medical_record",
                    "file_name": "medical_record.pdf",
                    "uploaded_at": "2024-03-15T10:00:00Z"
                },
                "presigned_url": "https://s3.amazonaws.com/...",
                "extraction_results": {
                    "text": "Extracted text content",
                    "entities": []
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: str
    timestamp: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "error_code": "INVALID_INPUT",
                "message": "Required field 'policy_number' is missing",
                "details": {
                    "field": "policy_number",
                    "constraint": "required"
                },
                "request_id": "req_abc123",
                "timestamp": "2024-03-15T10:00:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., regex=r'^(healthy|degraded|unhealthy)$')
    version: str
    timestamp: datetime
    dependencies: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-03-15T10:00:00Z",
                "dependencies": {
                    "database": "healthy",
                    "s3": "healthy",
                    "sagemaker": "healthy"
                }
            }
        }


# Export all models
__all__ = [
    # Enums
    "ClaimType",
    "ClaimStatus",
    "DocumentType",
    "Priority",
    
    # Request Models
    "PersonalInformation",
    "PolicyInformation",
    "IncidentInformation",
    "MedicalInformation",
    "ClaimAmount",
    "ClaimSubmissionRequest",
    "ClaimUpdateRequest",
    "DocumentUploadRequest",
    "ClaimQueryParams",
    
    # Response Models
    "ClaimMetadata",
    "ValidationResult",
    "FraudScore",
    "ProcessingResult",
    "ClaimResponse",
    "ClaimListResponse",
    "DocumentMetadata",
    "DocumentResponse",
    "ErrorResponse",
    "HealthCheckResponse",
]