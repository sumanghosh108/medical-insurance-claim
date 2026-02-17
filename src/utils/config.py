"""Configuration Module - Multi-environment Support with Validation."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class with all default values."""
    
    # Project Information
    PROJECT_NAME = "insurance-claims-system"
    VERSION = "1.0.0"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # AWS Configuration
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
    AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
    AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "123456789012")
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "claims_db")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres123")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # S3 Configuration
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "claims-processing-local")
    S3_REGION = os.getenv("S3_REGION", AWS_REGION)
    S3_PREFIX = os.getenv("S3_PREFIX", "claims/")
    S3_KMS_ENABLED = os.getenv("S3_KMS_ENABLED", "True").lower() == "true"
    
    # Redis Cache Configuration
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_WORKERS = int(os.getenv("API_WORKERS", "4"))
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "120"))
    
    # ML Model Configuration
    MODEL_PATH = os.getenv("MODEL_PATH", "./src/ml_models/models/fraud_detection_v1.0.pkl")
    FEATURE_TRANSFORMER_PATH = os.getenv(
        "FEATURE_TRANSFORMER_PATH",
        "./src/ml_models/models/feature_transformer_v1.0.pkl"
    )
    MODEL_THRESHOLD = float(os.getenv("MODEL_THRESHOLD", "0.5"))
    
    # SageMaker Configuration
    SAGEMAKER_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT", "fraud-detection-endpoint")
    SAGEMAKER_ROLE = os.getenv(
        "SAGEMAKER_ROLE",
        "arn:aws:iam::123456789012:role/SageMakerRole"
    )
    
    # Testing Configuration
    TEST_DATA_PATH = os.getenv("TEST_DATA_PATH", "./tests/fixtures/")
    TEST_DB_URL = os.getenv("TEST_DB_URL", "sqlite:///:memory:")
    
    # Feature Flags
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "True").lower() == "true"
    ENABLE_ASYNC = os.getenv("ENABLE_ASYNC", "True").lower() == "true"
    ENABLE_AUTH = os.getenv("ENABLE_AUTH", "False").lower() == "true"
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL database URL from components."""
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL from components."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def S3_DOCUMENTS_BUCKET(self) -> str:
        """S3 bucket name for storing claim documents."""
        return self.S3_BUCKET_NAME
    
    @property
    def S3_MODELS_BUCKET(self) -> str:
        """S3 bucket name for storing ML models."""
        return f"{self.S3_BUCKET_NAME}-models"
    
    @property
    def S3_METADATA_BUCKET(self) -> str:
        """S3 bucket name for storing metadata."""
        return f"{self.S3_BUCKET_NAME}-metadata"
    
    def get_database_url(self, driver: str = "postgresql") -> str:
        """
        Get database URL with specific driver.
        
        Args:
            driver: Database driver type ('postgresql' or 'sqlite').
            
        Returns:
            Database connection URL.
            
        Raises:
            ValueError: If unsupported driver is specified.
        """
        if driver == "postgresql":
            return self.DATABASE_URL
        elif driver == "sqlite":
            return "sqlite:///:memory:"
        else:
            raise ValueError(f"Unsupported driver: {driver}")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    ENVIRONMENT = "development"
    ENABLE_CACHING = False
    ENABLE_MONITORING = False
    DB_NAME = "claims_db_dev"
    S3_BUCKET_NAME = "claims-processing-dev"
    MODEL_THRESHOLD = 0.5
    API_WORKERS = 1


class StagingConfig(Config):
    """Staging environment configuration."""
    
    DEBUG = False
    LOG_LEVEL = "INFO"
    ENVIRONMENT = "staging"
    ENABLE_CACHING = True
    DB_NAME = "claims_db_staging"
    S3_BUCKET_NAME = "claims-processing-staging"
    MODEL_THRESHOLD = 0.7
    API_WORKERS = 4


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    LOG_LEVEL = "WARNING"
    ENVIRONMENT = "production"
    ENABLE_CACHING = True
    ENABLE_MONITORING = True
    DB_POOL_SIZE = 50
    DB_MAX_OVERFLOW = 50
    API_WORKERS = 8
    CACHE_TTL = 7200
    MODEL_THRESHOLD = 0.75
    S3_KMS_ENABLED = True


class TestConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    ENVIRONMENT = "test"
    DATABASE_URL = "sqlite:///:memory:"
    S3_BUCKET_NAME = "claims-processing-test"
    ENABLE_CACHING = False
    ENABLE_MONITORING = False
    API_WORKERS = 1


def get_config(environment: Optional[str] = None) -> Config:
    """
    Get configuration object based on environment.
    
    Args:
        environment: Environment name (development, staging, production, test).
                    If not provided, uses ENVIRONMENT env variable.
    
    Returns:
        Configuration object for the specified environment.
    
    Raises:
        ValueError: If environment is not recognized.
        
    Examples:
        >>> config = get_config('production')
        >>> print(config.DATABASE_URL)
        >>> 
        >>> dev_config = get_config()  # Uses ENVIRONMENT env var
    """
    env = environment or os.getenv("ENVIRONMENT", "development").lower()
    
    config_mapping = {
        "development": DevelopmentConfig,
        "staging": StagingConfig,
        "production": ProductionConfig,
        "test": TestConfig,
    }
    
    if env not in config_mapping:
        available = ", ".join(config_mapping.keys())
        raise ValueError(
            f"Unknown environment: {env}. Must be one of: {available}"
        )
    
    return config_mapping[env]()


# Export default configuration instance
config = get_config()