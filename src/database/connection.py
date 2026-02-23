"""Database Connection Management - PostgreSQL with SQLAlchemy."""

import logging
from typing import Optional, Generator, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError

logger = logging.getLogger(__name__)

# Base declarative class for all models
Base = declarative_base()


class DatabaseConnection:
    """Manage PostgreSQL database connections."""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        use_static_pool: bool = False,
    ):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection URL
            pool_size: Number of connections to keep in pool
            max_overflow: Additional connections beyond pool_size
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
            echo: Whether to log SQL statements
            use_static_pool: Use StaticPool (for testing)
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.use_static_pool = use_static_pool
        
        self.engine: Optional[Engine] = None
        self.session_factory: Optional[sessionmaker] = None
    
    def connect(self) -> Engine:
        """
        Create database engine and establish connection.
        
        Returns:
            SQLAlchemy Engine instance
            
        Raises:
            OperationalError: If connection fails
        """
        try:
            # Choose connection pool
            if self.use_static_pool:
                pool_class = StaticPool
                pool_kwargs = {}
            else:
                pool_class = QueuePool
                pool_kwargs = {
                    'pool_size': self.pool_size,
                    'max_overflow': self.max_overflow,
                    'timeout': self.pool_timeout,
                    'recycle': self.pool_recycle,
                }
            
            # Create engine
            self.engine = create_engine(
                self.database_url,
                poolclass=pool_class,
                echo=self.echo,
                **pool_kwargs,
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'claims_system',
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Create session factory
            self.session_factory = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                autocommit=False,
            )
            
            logger.info(f"Database connected: {self.database_url}")
            return self.engine
        
        except SQLAlchemyError as e:
            logger.error(f"Database connection failed: {e}", exc_info=True)
            raise
    
    def disconnect(self) -> None:
        """Close database connection and dispose of engine."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database disconnected")
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        if not self.session_factory:
            raise RuntimeError("Database not connected")
        
        return self.session_factory()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup.
        
        Yields:
            SQLAlchemy Session instance
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            if not self.engine:
                return False
            
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            return True
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def create_all_tables(self) -> None:
        """Create all tables from ORM models."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise
    
    def drop_all_tables(self) -> None:
        """Drop all tables (DANGEROUS!)."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("All tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        if not self.engine or not self.engine.pool:
            return {}
        
        pool = self.engine.pool
        
        if isinstance(pool, QueuePool):
            return {
                'type': 'QueuePool',
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
            }
        
        return {'type': type(pool).__name__}


class ConnectionPool:
    """Manage multiple database connections."""
    
    def __init__(self):
        """Initialize connection pool manager."""
        self.connections: Dict[str, DatabaseConnection] = {}
        self.default_key: Optional[str] = None
    
    def register(
        self,
        name: str,
        database_url: str,
        pool_size: int = 10,
        is_default: bool = False,
    ) -> DatabaseConnection:
        """
        Register a database connection.
        
        Args:
            name: Connection name
            database_url: Connection URL
            pool_size: Connection pool size
            is_default: Set as default connection
            
        Returns:
            DatabaseConnection instance
        """
        conn = DatabaseConnection(database_url, pool_size=pool_size)
        conn.connect()
        self.connections[name] = conn
        
        if is_default or not self.default_key:
            self.default_key = name
        
        logger.info(f"Registered connection: {name}")
        return conn
    
    def get(self, name: Optional[str] = None) -> DatabaseConnection:
        """Get database connection by name."""
        key = name or self.default_key
        
        if not key or key not in self.connections:
            raise ValueError(f"Connection not found: {key}")
        
        return self.connections[key]
    
    def get_session(self, name: Optional[str] = None) -> Session:
        """Get database session."""
        return self.get(name).get_session()
    
    def close_all(self) -> None:
        """Close all connections."""
        for conn in self.connections.values():
            conn.disconnect()
        
        logger.info("All connections closed")


# Global connection instance
_db_connection: Optional[DatabaseConnection] = None


def init_database(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
) -> DatabaseConnection:
    """Initialize global database connection."""
    global _db_connection
    
    _db_connection = DatabaseConnection(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
    )
    _db_connection.connect()
    
    return _db_connection


def get_db_connection() -> DatabaseConnection:
    """Get global database connection."""
    if not _db_connection:
        raise RuntimeError("Database not initialized")
    
    return _db_connection


class LambdaConnectionManager:
    """
    Lambda-optimized database connection manager.
    
    Solves the RDS bottleneck for serverless environments:
    - Minimal local pool (pool_size=1) — RDS Proxy handles real pooling
    - Aggressive connection recycling (pool_recycle=300s)
    - pool_pre_ping=True to detect stale connections
    - Read/write splitting: writes → RDS Proxy, reads → Read Replica
    """
    
    def __init__(
        self,
        write_url: str,
        read_url: Optional[str] = None,
        pool_size: int = 1,
        max_overflow: int = 2,
        pool_recycle: int = 300,
        pool_timeout: int = 10,
        echo: bool = False,
    ):
        """
        Initialize Lambda connection manager.
        
        Args:
            write_url: RDS Proxy endpoint URL (for writes and default reads)
            read_url: Read Replica endpoint URL (optional, for read-heavy queries)
            pool_size: Local pool size (keep small; RDS Proxy handles pooling)
            max_overflow: Max extra connections beyond pool_size
            pool_recycle: Recycle connections after this many seconds
            pool_timeout: Timeout for getting connection from local pool
            echo: Log SQL statements
        """
        self.write_url = write_url
        self.read_url = read_url or write_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.pool_timeout = pool_timeout
        self.echo = echo
        
        self._write_engine: Optional[Engine] = None
        self._read_engine: Optional[Engine] = None
        self._write_session_factory: Optional[sessionmaker] = None
        self._read_session_factory: Optional[sessionmaker] = None
    
    def _create_engine(self, url: str) -> Engine:
        """Create a Lambda-optimized SQLAlchemy engine."""
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,
            echo=self.echo,
            connect_args={
                'connect_timeout': 5,
                'application_name': 'claims_lambda',
                'options': '-c statement_timeout=30000',
            },
        )
        return engine
    
    def connect(self) -> None:
        """Create write and read engines."""
        try:
            # Write engine (RDS Proxy)
            self._write_engine = self._create_engine(self.write_url)
            self._write_session_factory = sessionmaker(
                bind=self._write_engine,
                expire_on_commit=False,
                autocommit=False,
            )
            
            # Read engine (Read Replica or same as write)
            if self.read_url != self.write_url:
                self._read_engine = self._create_engine(self.read_url)
                self._read_session_factory = sessionmaker(
                    bind=self._read_engine,
                    expire_on_commit=False,
                    autocommit=False,
                )
                logger.info(
                    f"Lambda DB connected: write={self.write_url}, "
                    f"read={self.read_url}"
                )
            else:
                self._read_engine = self._write_engine
                self._read_session_factory = self._write_session_factory
                logger.info(
                    f"Lambda DB connected (single endpoint): {self.write_url}"
                )
            
            # Verify write connection
            with self._write_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
        except SQLAlchemyError as e:
            logger.error(f"Lambda DB connection failed: {e}", exc_info=True)
            raise
    
    def disconnect(self) -> None:
        """Dispose of all engines."""
        if self._write_engine:
            self._write_engine.dispose()
        if self._read_engine and self._read_engine is not self._write_engine:
            self._read_engine.dispose()
        logger.info("Lambda DB disconnected")
    
    def get_write_session(self) -> Session:
        """Get session routed to the write endpoint (RDS Proxy)."""
        if not self._write_session_factory:
            raise RuntimeError("Lambda DB not connected")
        return self._write_session_factory()
    
    def get_read_session(self) -> Session:
        """Get session routed to the read endpoint (Read Replica)."""
        if not self._read_session_factory:
            raise RuntimeError("Lambda DB not connected")
        return self._read_session_factory()
    
    @contextmanager
    def write_scope(self) -> Generator[Session, None, None]:
        """Context manager for write transactions."""
        session = self.get_write_session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Write transaction error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    @contextmanager
    def read_scope(self) -> Generator[Session, None, None]:
        """Context manager for read-only queries (routes to replica)."""
        session = self.get_read_session()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Read query error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """Check both write and read connections."""
        result = {'write': False, 'read': False}
        
        try:
            if self._write_engine:
                with self._write_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                result['write'] = True
        except Exception as e:
            logger.warning(f"Write health check failed: {e}")
        
        try:
            if self._read_engine:
                with self._read_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                result['read'] = True
        except Exception as e:
            logger.warning(f"Read health check failed: {e}")
        
        return result
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool stats for both engines."""
        stats = {}
        
        for name, engine in [('write', self._write_engine), ('read', self._read_engine)]:
            if engine and isinstance(engine.pool, QueuePool):
                stats[name] = {
                    'size': engine.pool.size(),
                    'checked_in': engine.pool.checkedin(),
                    'checked_out': engine.pool.checkedout(),
                    'overflow': engine.pool.overflow(),
                }
            elif engine:
                stats[name] = {'type': type(engine.pool).__name__}
        
        return stats


# Global Lambda connection instance
_lambda_connection: Optional[LambdaConnectionManager] = None


def init_database_for_lambda(
    write_url: Optional[str] = None,
    read_url: Optional[str] = None,
) -> LambdaConnectionManager:
    """
    Initialize database connection optimized for AWS Lambda.
    
    Auto-detects Lambda environment and reads config from env vars:
      - DATABASE_URL → write endpoint (RDS Proxy)
      - DATABASE_READ_URL → read endpoint (Read Replica)
      - DB_USE_PROXY → enables Lambda-optimized pooling
    
    Falls back to init_database() if not in Lambda / proxy not configured.
    """
    import os
    global _lambda_connection
    
    write = write_url or os.environ.get('DATABASE_URL', '')
    read = read_url or os.environ.get('DATABASE_READ_URL', '') or write
    use_proxy = os.environ.get('DB_USE_PROXY', 'false').lower() == 'true'
    is_lambda = bool(os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    
    if not write:
        raise RuntimeError(
            "DATABASE_URL must be set for Lambda database initialization"
        )
    
    if is_lambda or use_proxy:
        _lambda_connection = LambdaConnectionManager(
            write_url=write,
            read_url=read,
            pool_size=1,
            max_overflow=2,
            pool_recycle=300,
        )
        _lambda_connection.connect()
        logger.info("Initialized Lambda-optimized DB connection")
    else:
        # Fallback: use standard connection with slightly larger pool
        _lambda_connection = LambdaConnectionManager(
            write_url=write,
            read_url=read,
            pool_size=5,
            max_overflow=10,
            pool_recycle=900,
        )
        _lambda_connection.connect()
        logger.info("Initialized standard DB connection (non-Lambda)")
    
    return _lambda_connection


def get_lambda_connection() -> LambdaConnectionManager:
    """Get global Lambda connection manager."""
    if not _lambda_connection:
        raise RuntimeError("Lambda DB not initialized. Call init_database_for_lambda() first.")
    
    return _lambda_connection
