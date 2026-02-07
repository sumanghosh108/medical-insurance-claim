"""Database Module - PostgreSQL, ORM Models, and Database Operations."""

from .connection import (
    DatabaseConnection,
    ConnectionPool,
    init_database,
    get_db_connection,
)

from .models import (
    Base,
    User,
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
    # Models
    "Base",
    "User",
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
    # Migrations
    "MigrationManager",
    "migrate_database",
    # Transactions
    "TransactionManager",
    "transaction",
]