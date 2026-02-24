"""Database Migrations - Schema versioning and management."""

import logging
from typing import List, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session
from sqlalchemy import text

from .connection import DatabaseConnection, Base

logger = logging.getLogger(__name__)


class Migration(ABC):
    """Base migration class."""
    
    version: str
    description: str
    
    @abstractmethod
    def up(self, session: Session) -> None:
        """Run migration up (forward)."""
        pass
    
    @abstractmethod
    def down(self, session: Session) -> None:
        """Run migration down (rollback)."""
        pass


class MigrationManager:
    """Manage database migrations."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """Initialize migration manager."""
        self.db_connection = db_connection
        self.migrations: List[Migration] = []
    
    def register(self, migration: Migration) -> None:
        """Register a migration."""
        self.migrations.append(migration)
        logger.info(f"Registered migration: {migration.version} - {migration.description}")
    
    def _ensure_migrations_table(self, session: Session) -> None:
        """Ensure migrations tracking table exists."""
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    description VARCHAR(255),
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def get_applied_migrations(self, session: Session) -> List[str]:
        """Get list of applied migration versions."""
        try:
            self._ensure_migrations_table(session)
            
            result = session.execute(
                text("SELECT version FROM schema_migrations ORDER BY version")
            )
            return [row[0] for row in result]
        except Exception as e:
            logger.warning(f"Could not get applied migrations: {e}")
            return []
    
    def migrate_up(self) -> None:
        """Apply all pending migrations."""
        session = self.db_connection.get_session()
        
        try:
            self._ensure_migrations_table(session)
            applied = self.get_applied_migrations(session)
            
            for migration in self.migrations:
                if migration.version not in applied:
                    logger.info(f"Applying migration: {migration.version}")
                    
                    migration.up(session)
                    
                    session.execute(
                        text("""
                            INSERT INTO schema_migrations (version, description)
                            VALUES (:version, :description)
                        """),
                        {"version": migration.version, "description": migration.description}
                    )
                    session.commit()
                    logger.info(f"Applied migration: {migration.version}")
            
            logger.info("All migrations applied successfully")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Migration failed: {e}", exc_info=True)
            raise
        
        finally:
            session.close()
    
    def migrate_down(self, steps: int = 1) -> None:
        """Revert migrations."""
        session = self.db_connection.get_session()
        
        try:
            applied = self.get_applied_migrations(session)
            
            for migration in reversed(self.migrations[-steps:]):
                if migration.version in applied:
                    logger.info(f"Reverting migration: {migration.version}")
                    
                    migration.down(session)
                    
                    session.execute(
                        text("DELETE FROM schema_migrations WHERE version = :version"),
                        {"version": migration.version}
                    )
                    session.commit()
                    logger.info(f"Reverted migration: {migration.version}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Migration revert failed: {e}", exc_info=True)
            raise
        
        finally:
            session.close()
    
    def status(self) -> dict:
        """Get migration status."""
        session = self.db_connection.get_session()
        
        try:
            applied = self.get_applied_migrations(session)
            pending = [m for m in self.migrations if m.version not in applied]
            
            return {
                'total': len(self.migrations),
                'applied': len(applied),
                'pending': len(pending),
                'applied_versions': applied,
                'pending_versions': [m.version for m in pending],
            }
        finally:
            session.close()


class InitialSchemaMigration(Migration):
    """001: Create initial schema."""
    
    version = "001"
    description = "Create initial schema"
    
    def up(self, session: Session) -> None:
        """Create all tables."""
        Base.metadata.create_all(bind=session.bind)
        logger.info("Initial schema created")
    
    def down(self, session: Session) -> None:
        """Drop all tables."""
        Base.metadata.drop_all(bind=session.bind)
        logger.info("Initial schema dropped")


class AddFraudScoresIndexMigration(Migration):
    """002: Add indexes for fraud detection."""
    
    version = "002"
    description = "Add fraud detection indexes"
    
    def up(self, session: Session) -> None:
        """Add indexes."""
        try:
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_fraud_scores_score 
                ON fraud_scores(fraud_score DESC)
            """))
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_fraud_scores_risk 
                ON fraud_scores(risk_level)
            """))
            session.commit()
            logger.info("Fraud detection indexes created")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise
    
    def down(self, session: Session) -> None:
        """Drop indexes."""
        try:
            session.execute(text("DROP INDEX IF EXISTS ix_fraud_scores_score"))
            session.execute(text("DROP INDEX IF EXISTS ix_fraud_scores_risk"))
            session.commit()
        except Exception as e:
            logger.error(f"Failed to drop indexes: {e}")


class AddUserTablesMigration(Migration):
    """003: Create customer_users and staff_users tables."""

    version = "003"
    description = "Create customer_users and staff_users tables"

    def up(self, session: Session) -> None:
        """Create new user tables."""
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS customer_users (
                    id VARCHAR(36) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    father_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(30) NOT NULL,
                    gender VARCHAR(20) NOT NULL,
                    marital_status VARCHAR(20) NOT NULL,
                    permanent_address TEXT NOT NULL,
                    current_address TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_customer_email ON customer_users(email)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_customer_phone ON customer_users(phone)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_customer_name ON customer_users(full_name)"))

            session.execute(text("""
                CREATE TABLE IF NOT EXISTS staff_users (
                    id VARCHAR(36) PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    phone VARCHAR(30),
                    employee_id VARCHAR(50) UNIQUE NOT NULL,
                    department VARCHAR(100) NOT NULL,
                    designation VARCHAR(100),
                    role VARCHAR(50) DEFAULT 'adjuster' NOT NULL,
                    access_level INTEGER DEFAULT 1 NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    last_login TIMESTAMP,
                    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
                    locked_until TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_username ON staff_users(username)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_email ON staff_users(email)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_employee_id ON staff_users(employee_id)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_department ON staff_users(department)"))
            session.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_role ON staff_users(role)"))

            session.commit()
            logger.info("customer_users and staff_users tables created")
        except Exception as e:
            logger.error(f"Failed to create user tables: {e}")
            raise

    def down(self, session: Session) -> None:
        """Drop user tables."""
        try:
            session.execute(text("DROP TABLE IF EXISTS customer_users"))
            session.execute(text("DROP TABLE IF EXISTS staff_users"))
            session.commit()
        except Exception as e:
            logger.error(f"Failed to drop user tables: {e}")


def migrate_database(db_connection: DatabaseConnection) -> None:
    """Run all migrations."""
    manager = MigrationManager(db_connection)

    # Register migrations
    manager.register(InitialSchemaMigration())
    manager.register(AddFraudScoresIndexMigration())
    manager.register(AddUserTablesMigration())

    # Apply migrations
    manager.migrate_up()

    # Show status
    status = manager.status()
    logger.info(f"Migration status: {status}")