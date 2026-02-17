"""
API Utilities

Helper functions for API handlers including response formatting,
request parsing, ID generation, and other common operations.
"""

import json
import logging
import random
import string
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


def create_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create standardized API Gateway response
    
    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers
        
    Returns:
        API Gateway response dict
    """
    response_headers = {
        'Content-Type': 'application/json',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
    }
    
    if headers:
        response_headers.update(headers)
    
    # Serialize body to JSON
    if isinstance(body, (dict, list)):
        response_body = json.dumps(body, default=json_serializer)
    elif isinstance(body, str):
        response_body = body
    else:
        response_body = json.dumps(body, default=json_serializer)
    
    return {
        'statusCode': status_code,
        'headers': response_headers,
        'body': response_body
    }


def json_serializer(obj: Any) -> str:
    """
    Custom JSON serializer for objects not serializable by default
    
    Handles datetime, date, and other common types.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)


def parse_request_body(event: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Parse and validate request body using Pydantic model
    
    Args:
        event: Lambda event dict
        model_class: Pydantic model class for validation
        
    Returns:
        Validated model instance
        
    Raises:
        ValidationError: If validation fails
        
    Example:
        claim_data = parse_request_body(event, ClaimSubmissionRequest)
    """
    # Extract body from event
    body = event.get('body', '{}')
    
    # Parse JSON if body is string
    if isinstance(body, str):
        try:
            body_dict = json.loads(body)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in request body: {e}")
            raise ValidationError([{
                'loc': ('body',),
                'msg': 'Invalid JSON format',
                'type': 'value_error.jsondecode'
            }], model_class)
    else:
        body_dict = body
    
    # Validate and parse with Pydantic model
    return model_class(**body_dict)


def extract_query_params(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract query string parameters from event
    
    Args:
        event: Lambda event dict
        
    Returns:
        Dict of query parameters
    """
    return event.get('queryStringParameters') or {}


def extract_path_params(event: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract path parameters from event
    
    Args:
        event: Lambda event dict
        
    Returns:
        Dict of path parameters
    """
    return event.get('pathParameters') or {}


def extract_user_info(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from authenticated request
    
    Args:
        event: Lambda event dict
        
    Returns:
        Dict with user information
    """
    authorizer = event.get('requestContext', {}).get('authorizer', {})
    
    return {
        'user_id': authorizer.get('user_id', 'unknown'),
        'email': authorizer.get('email'),
        'role': authorizer.get('role', 'user'),
        'permissions': authorizer.get('permissions', []),
        'auth_method': authorizer.get('auth_method', 'unknown')
    }


def generate_claim_number() -> str:
    """
    Generate unique claim number
    
    Format: CLM-YYYYMMDD-XXXXXX
    Where XXXXXX is a random alphanumeric string
    
    Returns:
        Claim number string
        
    Example:
        'CLM-20240315-A1B2C3'
    """
    date_part = datetime.utcnow().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return f"CLM-{date_part}-{random_part}"


def generate_document_id() -> str:
    """
    Generate unique document ID
    
    Format: DOC-YYYYMMDD-XXXXXX
    
    Returns:
        Document ID string
    """
    date_part = datetime.utcnow().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return f"DOC-{date_part}-{random_part}"


def generate_api_key() -> str:
    """
    Generate secure API key
    
    Returns:
        32-character API key
    """
    return ''.join(random.choices(
        string.ascii_letters + string.digits,
        k=32
    ))


def paginate_results(
    items: list,
    offset: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Paginate list of items
    
    Args:
        items: List of items to paginate
        offset: Number of items to skip
        limit: Maximum number of items to return
        
    Returns:
        Dict with paginated results and metadata
    """
    total_count = len(items)
    
    # Apply offset and limit
    paginated_items = items[offset:offset + limit]
    
    has_more = (offset + limit) < total_count
    
    return {
        'items': paginated_items,
        'total_count': total_count,
        'offset': offset,
        'limit': limit,
        'has_more': has_more,
        'next_offset': offset + limit if has_more else None
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Replace dangerous characters
    dangerous_chars = ['..', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:255]
    
    return filename


def validate_s3_uri(uri: str) -> bool:
    """
    Validate S3 URI format
    
    Args:
        uri: S3 URI string
        
    Returns:
        True if valid, False otherwise
    """
    if not uri.startswith('s3://'):
        return False
    
    parts = uri[5:].split('/', 1)
    
    # Must have bucket and key
    if len(parts) != 2:
        return False
    
    bucket, key = parts
    
    # Validate bucket name (simplified)
    if not bucket or len(bucket) < 3 or len(bucket) > 63:
        return False
    
    # Validate key
    if not key:
        return False
    
    return True


def calculate_file_hash(content: bytes, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file content
    
    Args:
        content: File content as bytes
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of hash
    """
    import hashlib
    
    if algorithm == 'md5':
        h = hashlib.md5()
    elif algorithm == 'sha1':
        h = hashlib.sha1()
    else:
        h = hashlib.sha256()
    
    h.update(content)
    return h.hexdigest()


def format_amount(amount: float, currency: str = 'USD') -> str:
    """
    Format monetary amount for display
    
    Args:
        amount: Amount value
        currency: Currency code
        
    Returns:
        Formatted amount string
        
    Example:
        format_amount(1234.56, 'USD') -> '$1,234.56'
    """
    if currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'EUR':
        return f"€{amount:,.2f}"
    elif currency == 'GBP':
        return f"£{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def parse_date_range(
    start_date: Optional[str],
    end_date: Optional[str]
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse date range from string inputs
    
    Args:
        start_date: Start date string (ISO format)
        end_date: End date string (ISO format)
        
    Returns:
        Tuple of (start_datetime, end_datetime)
    """
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid start_date format: {start_date}")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"Invalid end_date format: {end_date}")
    
    return start_dt, end_dt


def build_filter_expression(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build DynamoDB filter expression from filters dict
    
    Args:
        filters: Dict of filter key-value pairs
        
    Returns:
        Dict with FilterExpression, ExpressionAttributeNames, ExpressionAttributeValues
    """
    if not filters:
        return {}
    
    filter_parts = []
    attr_names = {}
    attr_values = {}
    
    for i, (key, value) in enumerate(filters.items()):
        if value is None:
            continue
        
        # Handle nested attributes (e.g., 'personal_info.email')
        if '.' in key:
            parts = key.split('.')
            attr_path = '.'.join([f'#{p}' for p in parts])
            for part in parts:
                attr_names[f'#{part}'] = part
        else:
            attr_path = f'#{key}'
            attr_names[f'#{key}'] = key
        
        value_key = f':val{i}'
        attr_values[value_key] = value
        
        filter_parts.append(f'{attr_path} = {value_key}')
    
    if not filter_parts:
        return {}
    
    return {
        'FilterExpression': ' AND '.join(filter_parts),
        'ExpressionAttributeNames': attr_names,
        'ExpressionAttributeValues': attr_values
    }


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display
    
    Args:
        data: Sensitive data string
        visible_chars: Number of characters to leave visible at end
        
    Returns:
        Masked string
        
    Example:
        mask_sensitive_data('1234567890', 4) -> '******7890'
    """
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    mask_length = len(data) - visible_chars
    return ('*' * mask_length) + data[-visible_chars:]


def get_client_ip(event: Dict[str, Any]) -> str:
    """
    Extract client IP address from event
    
    Checks X-Forwarded-For header first, then falls back to sourceIp.
    
    Args:
        event: Lambda event dict
        
    Returns:
        Client IP address
    """
    # Check X-Forwarded-For header (API Gateway sets this)
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    forwarded_for = headers.get('x-forwarded-for', '')
    
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first (client)
        return forwarded_for.split(',')[0].strip()
    
    # Fallback to sourceIp
    return event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')


def get_user_agent(event: Dict[str, Any]) -> str:
    """
    Extract User-Agent from event
    
    Args:
        event: Lambda event dict
        
    Returns:
        User-Agent string
    """
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    return headers.get('user-agent', 'unknown')


def is_valid_email(email: str) -> bool:
    """
    Basic email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_correlation_id() -> str:
    """
    Generate correlation ID for request tracking
    
    Returns:
        UUID string
    """
    import uuid
    return str(uuid.uuid4())


def chunk_list(items: list, chunk_size: int) -> list:
    """
    Split list into chunks of specified size
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
        
    Example:
        chunk_list([1,2,3,4,5], 2) -> [[1,2], [3,4], [5]]
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


# Export all utility functions
__all__ = [
    'create_response',
    'json_serializer',
    'parse_request_body',
    'extract_query_params',
    'extract_path_params',
    'extract_user_info',
    'generate_claim_number',
    'generate_document_id',
    'generate_api_key',
    'paginate_results',
    'sanitize_filename',
    'validate_s3_uri',
    'calculate_file_hash',
    'format_amount',
    'parse_date_range',
    'build_filter_expression',
    'truncate_text',
    'mask_sensitive_data',
    'get_client_ip',
    'get_user_agent',
    'is_valid_email',
    'generate_correlation_id',
    'chunk_list',
    'merge_dicts',
]