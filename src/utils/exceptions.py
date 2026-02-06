"""Custom Exceptions Module - Application Specific Exceptions."""


class InsuranceClaimsException(Exception):
    """Base exception for the insurance claims system."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        """Initialize exception."""
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
        }


class ValidationError(InsuranceClaimsException):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: str):
        """Initialize validation error."""
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class ConfigurationError(InsuranceClaimsException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str):
        """Initialize configuration error."""
        super().__init__(message, "CONFIG_ERROR")


class DatabaseError(InsuranceClaimsException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str):
        """Initialize database error."""
        super().__init__(message, "DATABASE_ERROR")


class S3Error(InsuranceClaimsException):
    """Raised when S3 operation fails."""
    
    def __init__(self, message: str):
        """Initialize S3 error."""
        super().__init__(message, "S3_ERROR")


class ModelError(InsuranceClaimsException):
    """Raised when ML model operation fails."""
    
    def __init__(self, message: str):
        """Initialize model error."""
        super().__init__(message, "MODEL_ERROR")


class ModelNotTrainedError(ModelError):
    """Raised when model is used before training."""
    
    def __init__(self):
        """Initialize not trained error."""
        super().__init__("Model not trained. Call train() first.")


class FeatureEngineeringError(ModelError):
    """Raised when feature engineering fails."""
    
    def __init__(self, message: str):
        """Initialize feature engineering error."""
        super().__init__(message, "FEATURE_ENGINEERING_ERROR")


class PredictionError(ModelError):
    """Raised when prediction fails."""
    
    def __init__(self, message: str):
        """Initialize prediction error."""
        super().__init__(message, "PREDICTION_ERROR")


class WorkflowError(InsuranceClaimsException):
    """Raised when workflow operation fails."""
    
    def __init__(self, message: str):
        """Initialize workflow error."""
        super().__init__(message, "WORKFLOW_ERROR")


class LambdaError(InsuranceClaimsException):
    """Raised when Lambda operation fails."""
    
    def __init__(self, message: str):
        """Initialize Lambda error."""
        super().__init__(message, "LAMBDA_ERROR")


class SNSError(InsuranceClaimsException):
    """Raised when SNS operation fails."""
    
    def __init__(self, message: str):
        """Initialize SNS error."""
        super().__init__(message, "SNS_ERROR")


class AuthenticationError(InsuranceClaimsException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error."""
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(InsuranceClaimsException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed"):
        """Initialize authorization error."""
        super().__init__(message, "AUTHZ_ERROR")


class NotFoundError(InsuranceClaimsException):
    """Raised when resource is not found."""
    
    def __init__(self, resource: str, identifier: str):
        """Initialize not found error."""
        message = f"{resource} not found: {identifier}"
        super().__init__(message, "NOT_FOUND")


class ConflictError(InsuranceClaimsException):
    """Raised when resource already exists."""
    
    def __init__(self, resource: str, identifier: str):
        """Initialize conflict error."""
        message = f"{resource} already exists: {identifier}"
        super().__init__(message, "CONFLICT")


class TimeoutError(InsuranceClaimsException):
    """Raised when operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        """Initialize timeout error."""
        message = f"{operation} timed out after {timeout_seconds}s"
        super().__init__(message, "TIMEOUT")


class RateLimitError(InsuranceClaimsException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: int):
        """Initialize rate limit error."""
        self.retry_after = retry_after
        super().__init__(message, "RATE_LIMIT")


class ExternalServiceError(InsuranceClaimsException):
    """Raised when external service fails."""
    
    def __init__(self, service: str, message: str):
        """Initialize external service error."""
        full_message = f"{service} error: {message}"
        super().__init__(full_message, "EXTERNAL_SERVICE_ERROR")







# import sys
# import traceback

# def error_message_details(error,error_details):
#     if error_details:
#         tb=traceback.extract_tb(sys.exc_info()[2])
        
#         if not tb:
#             return str(error)
        
#         last_trace=tb[-1]
#         file_name=last_trace.filename
#         line_number=last_trace.lineno
        
#         return (
#             f"Error in script [{file_name}]"
#             f"line no [{line_number}]"
#             f"error [{str(error)}]"
#         )

# class CustomException(Exception):
#     def __init__(self,error_message,error_detail):
#         super().__init__(error_message)
#         self.error_message=error_message_details(error_message,error_details=error_detail)
    
#     def __str__(self):
#         return self.error_message