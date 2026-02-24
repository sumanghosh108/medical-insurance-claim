"""Database Module - PostgreSQL, ORM Models, and Database Operations."""

from .connection import (
    DatabaseConnection,
    ConnectionPool,
    init_database,
    get_db_connection,
    LambdaConnectionManager,
    init_database_for_lambda,
    get_lambda_connection,
)

from .models import (
    Base,
    User,
    CustomerUser,
    StaffUser,
    Patient,
    Hospital,
    Claim,
    Document,
    FraudScore,
)

from .operations import (
    DatabaseOperations,
    ClaimOperations,
    PatientOperations,
    HospitalOperations,
)

from .auth_operations import (
    CustomerUserOperations,
    StaffUserOperations,
    hash_password,
    verify_password,
)

from .migrations import (
    MigrationManager,
    migrate_database,
)

from .transactions import (
    TransactionManager,
    transaction,
)

__all__ = [
    # Connection
    "DatabaseConnection",
    "ConnectionPool",
    "init_database",
    "get_db_connection",
    # Lambda Connection
    "LambdaConnectionManager",
    "init_database_for_lambda",
    "get_lambda_connection",
    # Models
    "Base",
    "User",
    "CustomerUser",
    "StaffUser",
    "Patient",
    "Hospital",
    "Claim",
    "Document",
    "FraudScore",
    # Operations
    "DatabaseOperations",
    "ClaimOperations",
    "PatientOperations",
    "HospitalOperations",
    # Auth Operations
    "CustomerUserOperations",
    "StaffUserOperations",
    "hash_password",
    "verify_password",
    # Migrations
    "MigrationManager",
    "migrate_database",
    # Transactions
    "TransactionManager",
    "transaction",
]
