"""Validators Module - Input Validation Functions."""

import re
from typing import Any, List, Tuple
from datetime import datetime
import uuid as uuid_lib

from .exceptions import ValidationError
from .constants import (
    MIN_CLAIM_AMOUNT,
    MAX_CLAIM_AMOUNT,
    CLAIM_TYPES,
    DOCUMENT_TYPES,
)


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_uuid(value: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        value: UUID string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        uuid_lib.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_claim_amount(amount: float) -> bool:
    """
    Validate claim amount is within acceptable range.
    
    Args:
        amount: Claim amount to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        num_amount = float(amount)
        return MIN_CLAIM_AMOUNT <= num_amount <= MAX_CLAIM_AMOUNT
    except (ValueError, TypeError):
        return False


def validate_date_format(date_str: str) -> bool:
    """
    Validate date format (ISO 8601).
    
    Args:
        date_str: Date string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        # Try ISO format with Z suffix
        if date_str.endswith('Z'):
            datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            datetime.fromisoformat(date_str)
        return True
    except (ValueError, TypeError):
        return False


def validate_claim_type(claim_type: str) -> bool:
    """
    Validate claim type is known.
    
    Args:
        claim_type: Claim type to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    return claim_type in CLAIM_TYPES


def validate_document_type(doc_type: str) -> bool:
    """
    Validate document type is supported.
    
    Args:
        doc_type: Document type to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    return doc_type.lower() in DOCUMENT_TYPES


def validate_claim_payload(data: dict) -> Tuple[bool, List[str]]:
    """
    Validate complete claim payload.
    
    Args:
        data: Claim data dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required fields
    required_fields = [
        'patient_id',
        'hospital_id',
        'claim_amount',
        'treatment_type',
        'diagnosis_code',
        'claim_date',
    ]
    
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate patient_id
    if 'patient_id' in data:
        if not validate_uuid(data['patient_id']):
            errors.append("patient_id must be valid UUID")
    
    # Validate hospital_id
    if 'hospital_id' in data:
        if not validate_uuid(data['hospital_id']):
            errors.append("hospital_id must be valid UUID")
    
    # Validate claim_amount
    if 'claim_amount' in data:
        if not validate_claim_amount(data['claim_amount']):
            errors.append(
                f"claim_amount must be between {MIN_CLAIM_AMOUNT} and {MAX_CLAIM_AMOUNT}"
            )
    
    # Validate treatment_type
    if 'treatment_type' in data:
        if not validate_claim_type(data['treatment_type']):
            errors.append(f"treatment_type must be one of {CLAIM_TYPES}")
    
    # Validate claim_date
    if 'claim_date' in data:
        if not validate_date_format(data['claim_date']):
            errors.append("claim_date must be ISO 8601 format")
    
    # Validate document if present
    if 'document_type' in data:
        if not validate_document_type(data['document_type']):
            errors.append(f"document_type must be one of {DOCUMENT_TYPES}")
    
    return (len(errors) == 0, errors)


def validate_required_fields(data: dict, fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate required fields are present.
    
    Args:
        data: Dictionary to validate.
        fields: List of required field names.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    for field in fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    return (len(errors) == 0, errors)


def validate_string_length(
    value: str,
    min_length: int = 0,
    max_length: int = 1000,
) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate.
        min_length: Minimum length.
        max_length: Maximum length.
        
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return min_length <= len(value) <= max_length


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    # Remove common separators
    clean_phone = re.sub(r'[\s\-\(\).]', '', phone)
    
    # Check if it's all digits and reasonable length (7-15)
    return re.match(r'^[0-9]{7,15}$', clean_phone) is not None


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input.
    
    Args:
        value: String to sanitize.
        max_length: Maximum allowed length.
        
    Returns:
        Sanitized string.
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace
    value = value.strip()
    
    # Limit length
    if len(value) > max_length:
        value = value[:max_length]
    
    return value