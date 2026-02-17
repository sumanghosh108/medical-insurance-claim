"""Transaction Management - ACID transaction support."""

import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager
from functools import wraps

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_db_connection

logger = logging.getLogger(__name__)


class TransactionManager:
    """Manage database transactions."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize transaction manager."""
        self.session = session
    
    def _get_session(self) -> Session:
        """Get session (use provided or get new one)."""
        if self.session:
            return self.session
        return get_db_connection().get_session()
    
    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.
        
        Yields:
            SQLAlchemy Session
        """
        session = self._get_session()
        
        try:
            yield session
            session.commit()
            logger.debug("Transaction committed")
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Transaction rollback: {e}", exc_info=True)
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error in transaction: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def savepoint(self, name: str):
        """
        Create a savepoint.
        
        Args:
            name: Savepoint name
        """
        session = self._get_session()
        sp = session.begin_nested()
        logger.debug(f"Savepoint created: {name}")
        return sp
    
    def rollback_to_savepoint(self, savepoint: Any) -> None:
        """Rollback to savepoint."""
        savepoint.rollback()
        logger.debug("Rollback to savepoint")
    
    def execute_in_transaction(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function within transaction.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
        """
        session = self._get_session()
        
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction execution failed: {e}", exc_info=True)
            raise
        finally:
            session.close()


def transaction(func: Callable) -> Callable:
    """
    Decorator for automatic transaction management.
    
    The decorated function receives session as first argument.
    
    Example:
        @transaction
        def process_claim(session, claim_id):
            claim = session.query(Claim).get(claim_id)
            claim.status = 'PROCESSED'
            return claim
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        manager = TransactionManager()
        
        def inner(session):
            return func(session, *args, **kwargs)
        
        return manager.execute_in_transaction(inner)
    
    return wrapper


def atomic_transaction(func: Callable) -> Callable:
    """
    Decorator for atomic operations (all or nothing).
    
    Example:
        @atomic_transaction
        def bulk_update_claims(claim_ids, status):
            session = get_db_connection().get_session()
            for claim_id in claim_ids:
                claim = session.query(Claim).get(claim_id)
                claim.status = status
            return len(claim_ids)
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        manager = TransactionManager()
        
        def inner(session):
            return func(session, *args, **kwargs)
        
        return manager.execute_in_transaction(inner)
    
    return wrapper


class Batch:
    """Batch operations helper."""
    
    def __init__(self, session: Session, batch_size: int = 100):
        """
        Initialize batch helper.
        
        Args:
            session: Database session
            batch_size: Batch size for commits
        """
        self.session = session
        self.batch_size = batch_size
        self.count = 0
    
    def add(self, obj: Any) -> None:
        """Add object to batch."""
        self.session.add(obj)
        self.count += 1
        
        if self.count % self.batch_size == 0:
            self.flush()
    
    def add_all(self, objs: list) -> None:
        """Add multiple objects to batch."""
        for obj in objs:
            self.add(obj)
    
    def flush(self) -> None:
        """Flush current batch."""
        self.session.flush()
        logger.debug(f"Flushed {self.count} objects")
    
    def commit(self) -> None:
        """Commit all batches."""
        self.session.commit()
        logger.info(f"Committed {self.count} objects")
    
    def rollback(self) -> None:
        """Rollback batch."""
        self.session.rollback()
        logger.warning(f"Rolled back {self.count} objects")