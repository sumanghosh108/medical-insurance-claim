"""
API Module for Insurance Claims System

Provides REST API endpoints for claims submission, retrieval, and management.
Built for AWS Lambda + API Gateway integration with FastAPI compatibility.

Components:
    - handlers: Lambda function handlers for API Gateway
    - models: Request/response Pydantic models
    - middleware: Authentication, rate limiting, CORS
"""

import logging
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# FastAPI application — used by `uvicorn src.api:app`
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Insurance Claims Processing API",
    description="AI-powered insurance claims processing system",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


# ---- Routes ---------------------------------------------------------------

@app.get("/health")
async def health():
    """Health-check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Insurance Claims Processing API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ---------------------------------------------------------------------------
# Re-exports (keeping backward compat for anything that imports from here)
# ---------------------------------------------------------------------------

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
    "app",
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