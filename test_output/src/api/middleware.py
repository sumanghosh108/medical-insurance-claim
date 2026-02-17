"""
API Middleware

Middleware functions for authentication, rate limiting, CORS, and other cross-cutting concerns.
Implemented as decorators for Lambda handlers.
"""

import functools
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

import boto3
import jwt
from botocore.exceptions import ClientError


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')
secrets_manager = boto3.client('secretsmanager')

# Configuration
import os
JWT_SECRET_NAME = os.getenv('JWT_SECRET_NAME', 'insurance-claims-jwt-secret')
RATE_LIMIT_TABLE = os.getenv('RATE_LIMIT_TABLE', 'api-rate-limits')
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

# Cache for JWT secret
_jwt_secret_cache = {'secret': None, 'expires_at': 0}


def get_jwt_secret() -> str:
    """Get JWT secret from Secrets Manager with caching"""
    current_time = time.time()
    
    # Check cache (cache for 1 hour)
    if _jwt_secret_cache['secret'] and current_time < _jwt_secret_cache['expires_at']:
        return _jwt_secret_cache['secret']
    
    try:
        response = secrets_manager.get_secret_value(SecretId=JWT_SECRET_NAME)
        secret = response['SecretString']
        
        # Update cache
        _jwt_secret_cache['secret'] = secret
        _jwt_secret_cache['expires_at'] = current_time + 3600  # 1 hour
        
        return secret
    except ClientError as e:
        logger.error(f"Failed to retrieve JWT secret: {e}")
        # Fallback to environment variable (not recommended for production)
        return os.getenv('JWT_SECRET', 'dev-secret-change-in-production')


def cors_handler(func: Callable) -> Callable:
    """
    CORS middleware decorator
    
    Adds appropriate CORS headers to responses.
    Handles preflight OPTIONS requests.
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        # Handle OPTIONS preflight request
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': get_cors_headers(),
                'body': ''
            }
        
        # Call the actual handler
        response = func(event, context)
        
        # Add CORS headers to response
        if 'headers' not in response:
            response['headers'] = {}
        
        response['headers'].update(get_cors_headers())
        
        return response
    
    return wrapper


def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers configuration"""
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    return {
        'Access-Control-Allow-Origin': allowed_origins[0] if len(allowed_origins) == 1 else '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Api-Key,X-Request-ID',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
        'Access-Control-Max-Age': '86400',
        'Access-Control-Allow-Credentials': 'true'
    }


def authenticate_request(func: Callable) -> Callable:
    """
    Authentication middleware decorator
    
    Validates JWT token or API key from request headers.
    Adds user information to event context.
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        
        # Extract authentication credentials
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        auth_header = headers.get('authorization', '')
        api_key = headers.get('x-api-key', '')
        
        user_info = None
        
        # Try JWT authentication first
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            user_info = validate_jwt_token(token, request_id)
        
        # Fallback to API key authentication
        elif api_key:
            user_info = validate_api_key(api_key, request_id)
        
        # No authentication provided
        else:
            logger.warning(f"[{request_id}] No authentication credentials provided")
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'error_code': 'MISSING_AUTHENTICATION',
                    'message': 'Authentication credentials required',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Authentication failed
        if not user_info:
            logger.warning(f"[{request_id}] Authentication failed")
            return {
                'statusCode': 401,
                'headers': get_cors_headers(),
                'body': json.dumps({
                    'error': 'Unauthorized',
                    'error_code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid authentication credentials',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Add user info to event context
        if 'requestContext' not in event:
            event['requestContext'] = {}
        event['requestContext']['authorizer'] = user_info
        
        logger.info(f"[{request_id}] Authenticated user: {user_info.get('user_id')}")
        
        # Call the actual handler
        return func(event, context)
    
    return wrapper


def validate_jwt_token(token: str, request_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate JWT token
    
    Args:
        token: JWT token string
        request_id: Request ID for logging
        
    Returns:
        User information dict if valid, None otherwise
    """
    try:
        secret = get_jwt_secret()
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            secret,
            algorithms=['HS256'],
            options={'verify_exp': True}
        )
        
        # Extract user information
        user_info = {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'role': payload.get('role', 'user'),
            'permissions': payload.get('permissions', []),
            'auth_method': 'jwt'
        }
        
        return user_info
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"[{request_id}] JWT token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"[{request_id}] Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"[{request_id}] JWT validation error: {e}")
        return None


def validate_api_key(api_key: str, request_id: str) -> Optional[Dict[str, Any]]:
    """
    Validate API key
    
    Args:
        api_key: API key string
        request_id: Request ID for logging
        
    Returns:
        User information dict if valid, None otherwise
    """
    try:
        # Hash API key for lookup
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Look up in DynamoDB (assuming API_KEYS table exists)
        # This is simplified - in production, use proper key management
        table_name = os.getenv('API_KEYS_TABLE', 'api-keys')
        table = dynamodb.Table(table_name)
        
        response = table.get_item(Key={'key_hash': key_hash})
        
        if 'Item' not in response:
            logger.warning(f"[{request_id}] API key not found")
            return None
        
        key_data = response['Item']
        
        # Check if key is active
        if not key_data.get('is_active', False):
            logger.warning(f"[{request_id}] API key is inactive")
            return None
        
        # Check expiration
        if 'expires_at' in key_data:
            expires_at = datetime.fromisoformat(key_data['expires_at'])
            if datetime.utcnow() > expires_at:
                logger.warning(f"[{request_id}] API key expired")
                return None
        
        # Return user information
        user_info = {
            'user_id': key_data.get('user_id'),
            'email': key_data.get('email'),
            'role': key_data.get('role', 'user'),
            'permissions': key_data.get('permissions', []),
            'auth_method': 'api_key',
            'key_id': key_data.get('key_id')
        }
        
        return user_info
        
    except ClientError as e:
        logger.error(f"[{request_id}] API key lookup error: {e}")
        return None
    except Exception as e:
        logger.error(f"[{request_id}] API key validation error: {e}")
        return None


def check_rate_limit(func: Callable) -> Callable:
    """
    Rate limiting middleware decorator
    
    Implements token bucket algorithm for rate limiting.
    Limits requests per user/IP within a time window.
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        
        # Extract identifier for rate limiting
        user_info = event.get('requestContext', {}).get('authorizer', {})
        user_id = user_info.get('user_id', 'anonymous')
        
        # Fallback to IP address if no user ID
        if user_id == 'anonymous':
            source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
            identifier = f"ip:{source_ip}"
        else:
            identifier = f"user:{user_id}"
        
        # Check rate limit
        if not check_rate_limit_allowed(identifier, request_id):
            logger.warning(f"[{request_id}] Rate limit exceeded for {identifier}")
            
            return {
                'statusCode': 429,
                'headers': {
                    **get_cors_headers(),
                    'Retry-After': str(RATE_LIMIT_WINDOW),
                    'X-RateLimit-Limit': str(RATE_LIMIT_REQUESTS),
                    'X-RateLimit-Reset': str(int(time.time()) + RATE_LIMIT_WINDOW)
                },
                'body': json.dumps({
                    'error': 'TooManyRequests',
                    'error_code': 'RATE_LIMIT_EXCEEDED',
                    'message': f'Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds',
                    'request_id': request_id,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        # Call the actual handler
        response = func(event, context)
        
        # Add rate limit headers to response
        if 'headers' not in response:
            response['headers'] = {}
        
        response['headers'].update({
            'X-RateLimit-Limit': str(RATE_LIMIT_REQUESTS),
            'X-RateLimit-Remaining': str(get_rate_limit_remaining(identifier)),
            'X-RateLimit-Reset': str(int(time.time()) + RATE_LIMIT_WINDOW)
        })
        
        return response
    
    return wrapper


def check_rate_limit_allowed(identifier: str, request_id: str) -> bool:
    """
    Check if request is allowed based on rate limit
    
    Uses DynamoDB for distributed rate limiting.
    Implements sliding window counter algorithm.
    
    Args:
        identifier: User/IP identifier
        request_id: Request ID for logging
        
    Returns:
        True if allowed, False if rate limit exceeded
    """
    try:
        table = dynamodb.Table(RATE_LIMIT_TABLE)
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW
        
        # Get or create rate limit entry
        try:
            response = table.get_item(Key={'identifier': identifier})
            item = response.get('Item', {})
        except ClientError:
            item = {}
        
        # Clean up old requests (outside window)
        requests = item.get('requests', [])
        requests = [r for r in requests if r > window_start]
        
        # Check if limit exceeded
        if len(requests) >= RATE_LIMIT_REQUESTS:
            logger.warning(f"[{request_id}] Rate limit check failed: {len(requests)}/{RATE_LIMIT_REQUESTS}")
            return False
        
        # Add current request
        requests.append(current_time)
        
        # Update DynamoDB
        table.put_item(
            Item={
                'identifier': identifier,
                'requests': requests,
                'updated_at': current_time,
                'ttl': current_time + RATE_LIMIT_WINDOW  # Auto-cleanup with TTL
            }
        )
        
        logger.debug(f"[{request_id}] Rate limit check passed: {len(requests)}/{RATE_LIMIT_REQUESTS}")
        return True
        
    except Exception as e:
        logger.error(f"[{request_id}] Rate limit check error: {e}")
        # On error, allow request (fail open)
        return True


def get_rate_limit_remaining(identifier: str) -> int:
    """
    Get remaining requests in current window
    
    Args:
        identifier: User/IP identifier
        
    Returns:
        Number of remaining requests
    """
    try:
        table = dynamodb.Table(RATE_LIMIT_TABLE)
        current_time = int(time.time())
        window_start = current_time - RATE_LIMIT_WINDOW
        
        response = table.get_item(Key={'identifier': identifier})
        item = response.get('Item', {})
        
        requests = item.get('requests', [])
        requests = [r for r in requests if r > window_start]
        
        remaining = max(0, RATE_LIMIT_REQUESTS - len(requests))
        return remaining
        
    except Exception as e:
        logger.error(f"Error getting rate limit remaining: {e}")
        return RATE_LIMIT_REQUESTS


def require_permission(permission: str) -> Callable:
    """
    Permission check decorator
    
    Requires specific permission to access endpoint.
    
    Args:
        permission: Required permission string
        
    Example:
        @require_permission('claims:write')
        def submit_claim_handler(event, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            request_id = event.get('requestContext', {}).get('requestId', 'unknown')
            
            # Get user permissions
            user_info = event.get('requestContext', {}).get('authorizer', {})
            user_permissions = user_info.get('permissions', [])
            user_role = user_info.get('role', 'user')
            
            # Admin has all permissions
            if user_role == 'admin':
                return func(event, context)
            
            # Check if user has required permission
            if permission not in user_permissions:
                logger.warning(
                    f"[{request_id}] Permission denied: user lacks '{permission}' permission"
                )
                
                return {
                    'statusCode': 403,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'error': 'Forbidden',
                        'error_code': 'INSUFFICIENT_PERMISSIONS',
                        'message': f"Required permission '{permission}' not granted",
                        'request_id': request_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            
            return func(event, context)
        
        return wrapper
    return decorator


def request_logger(func: Callable) -> Callable:
    """
    Request logging middleware decorator
    
    Logs request details and execution time.
    """
    @functools.wraps(func)
    def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
        request_id = event.get('requestContext', {}).get('requestId', 'unknown')
        
        # Log request
        http_method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', 'UNKNOWN')
        source_ip = event.get('requestContext', {}).get('identity', {}).get('sourceIp', 'unknown')
        
        logger.info(f"[{request_id}] {http_method} {path} from {source_ip}")
        
        # Execute handler
        start_time = time.time()
        
        try:
            response = func(event, context)
            
            # Log response
            execution_time = (time.time() - start_time) * 1000  # ms
            status_code = response.get('statusCode', 'UNKNOWN')
            
            logger.info(
                f"[{request_id}] Response: {status_code} "
                f"({execution_time:.2f}ms)"
            )
            
            # Add execution time header
            if 'headers' not in response:
                response['headers'] = {}
            response['headers']['X-Execution-Time'] = f"{execution_time:.2f}ms"
            
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] Error after {execution_time:.2f}ms: {e}",
                exc_info=True
            )
            raise
    
    return wrapper


def validate_content_type(allowed_types: list) -> Callable:
    """
    Content-Type validation decorator
    
    Args:
        allowed_types: List of allowed content types
        
    Example:
        @validate_content_type(['application/json'])
        def submit_claim_handler(event, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            request_id = event.get('requestContext', {}).get('requestId', 'unknown')
            
            # Extract Content-Type header
            headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
            content_type = headers.get('content-type', '').split(';')[0].strip()
            
            # Check if Content-Type is allowed
            if content_type not in allowed_types:
                logger.warning(
                    f"[{request_id}] Invalid Content-Type: {content_type}. "
                    f"Allowed: {', '.join(allowed_types)}"
                )
                
                return {
                    'statusCode': 415,
                    'headers': get_cors_headers(),
                    'body': json.dumps({
                        'error': 'UnsupportedMediaType',
                        'error_code': 'INVALID_CONTENT_TYPE',
                        'message': f"Content-Type must be one of: {', '.join(allowed_types)}",
                        'request_id': request_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            
            return func(event, context)
        
        return wrapper
    return decorator


# Export all middleware functions
__all__ = [
    "cors_handler",
    "authenticate_request",
    "check_rate_limit",
    "require_permission",
    "request_logger",
    "validate_content_type",
    "get_cors_headers",
]