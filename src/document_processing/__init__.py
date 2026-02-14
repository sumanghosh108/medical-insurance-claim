"""
Document Processing Module for Insurance Claims System

This module provides OCR, entity extraction, and document validation
capabilities for processing insurance claim documents.

Components:
    - text_extraction: AWS Textract & Tesseract OCR
    - entity_extraction: spaCy & HuggingFace NLP
    - document_validation: Business rule validation
    - utils: Helper functions and utilities
"""

from .text_extraction import (
    TextExtractor,
    TextractExtractor,
    TesseractExtractor,
    extract_text_from_document
)
from .entity_extraction import (
    EntityExtractor,
    ClaimEntityExtractor,
    extract_claim_entities
)
from .document_validation import (
    DocumentValidator,
    ValidationResult,
    validate_claim_document
)
from .utils import (
    convert_pdf_to_images,
    preprocess_image,
    sanitize_extracted_text,
    calculate_confidence_score
)

__version__ = "1.0.0"
__all__ = [
    # Text Extraction
    "TextExtractor",
    "TextractExtractor", 
    "TesseractExtractor",
    "extract_text_from_document",
    
    # Entity Extraction
    "EntityExtractor",
    "ClaimEntityExtractor",
    "extract_claim_entities",
    
    # Document Validation
    "DocumentValidator",
    "ValidationResult",
    "validate_claim_document",
    
    # Utilities
    "convert_pdf_to_images",
    "preprocess_image",
    "sanitize_extracted_text",
    "calculate_confidence_score",
]