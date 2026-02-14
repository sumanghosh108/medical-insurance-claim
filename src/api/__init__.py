"""
API Module for Insurance Claims System

Provides REST API endpoints for claims submission, retrieval, and management.
Built for AWS Lambda + API Gateway integration with FastAPI compatibility.

Components:
    - handlers: Lambda function handlers for API Gateway
    - models: Request/response Pydantic models
    - middleware: Authentication, rate limiting, CORS
    - routes: API route definitions
    - validators: Request validation logic
"""

from .handlers import (
    health_check_handler,
    submit_claim_handler,
    get_claim_handler,
    update_claim_handler,
    list_claims_handler,
    upload_document_handler,
    get_document_handler,
)

from .models import (
    ClaimSubmissionRequest,
    ClaimResponse,
    ClaimListResponse,
    DocumentUploadRequest,
    DocumentResponse,
    ErrorResponse,
    HealthCheckResponse,
)

from .middleware import (
    authenticate_request,
    check_rate_limit,
    cors_handler,
)

__version__ = "1.0.0"
__all__ = [
    # Handlers
    "health_check_handler",
    "submit_claim_handler",
    "get_claim_handler",
    "update_claim_handler",
    "list_claims_handler",
    "upload_document_handler",
    "get_document_handler",
    
    # Models
    "ClaimSubmissionRequest",
    "ClaimResponse",
    "ClaimListResponse",
    "DocumentUploadRequest",
    "DocumentResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    
    # Middleware
    "authenticate_request",
    "check_rate_limit",
    "cors_handler",
]