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


def migrate_database(db_connection: DatabaseConnection) -> None:
    """Run all migrations."""
    manager = MigrationManager(db_connection)
    
    # Register migrations
    manager.register(InitialSchemaMigration())
    manager.register(AddFraudScoresIndexMigration())
    
    # Apply migrations
    manager.migrate_up()
    
    # Show status
    status = manager.status()
    logger.info(f"Migration status: {status}")