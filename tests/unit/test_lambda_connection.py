"""Unit Tests — LambdaConnectionManager and Read/Write Splitting."""

import os
import sys
import pytest
import importlib.util
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Load connection.py directly to avoid the database __init__.py which
# triggers pre-existing SQLAlchemy model registration errors.
# ---------------------------------------------------------------------------
_mod_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "database", "connection.py")
)
_spec = importlib.util.spec_from_file_location("_connection", _mod_path)
_conn_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conn_mod)

LambdaConnectionManager = _conn_mod.LambdaConnectionManager
init_database_for_lambda = _conn_mod.init_database_for_lambda
get_lambda_connection = _conn_mod.get_lambda_connection

# Patch target — the create_engine reference *inside* the loaded module
_PATCH_TARGET = "_connection.create_engine"


def _mock_engine():
    """Create a mock engine whose .connect() works as a context manager."""
    engine = MagicMock()
    ctx = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=ctx)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)
    return engine


# ----------------------------------------------------------------
# Initialization
# ----------------------------------------------------------------
class TestLambdaConnectionManagerInit:
    def test_init_defaults(self):
        mgr = LambdaConnectionManager(
            write_url="postgresql://user:pass@proxy.rds.amazonaws.com/claims_db",
        )
        assert mgr.write_url == "postgresql://user:pass@proxy.rds.amazonaws.com/claims_db"
        assert mgr.read_url == mgr.write_url  # falls back to write
        assert mgr.pool_size == 1
        assert mgr.max_overflow == 2
        assert mgr.pool_recycle == 300
        assert mgr.pool_timeout == 10
        assert mgr._write_engine is None
        assert mgr._read_engine is None

    def test_init_with_read_url(self):
        mgr = LambdaConnectionManager(
            write_url="postgresql://user:pass@proxy/db",
            read_url="postgresql://user:pass@replica/db",
        )
        assert mgr.write_url != mgr.read_url
        assert "proxy" in mgr.write_url
        assert "replica" in mgr.read_url

    def test_init_custom_pool_settings(self):
        mgr = LambdaConnectionManager(
            write_url="postgresql://user:pass@host/db",
            pool_size=5,
            max_overflow=10,
            pool_recycle=900,
            pool_timeout=30,
        )
        assert mgr.pool_size == 5
        assert mgr.max_overflow == 10
        assert mgr.pool_recycle == 900
        assert mgr.pool_timeout == 30


# ----------------------------------------------------------------
# Read/Write Splitting
# ----------------------------------------------------------------
class TestReadWriteSplitting:
    def test_write_session_not_connected_raises(self):
        mgr = LambdaConnectionManager(write_url="postgresql://user:pass@host/db")
        with pytest.raises(RuntimeError, match="Lambda DB not connected"):
            mgr.get_write_session()

    def test_read_session_not_connected_raises(self):
        mgr = LambdaConnectionManager(write_url="postgresql://user:pass@host/db")
        with pytest.raises(RuntimeError, match="Lambda DB not connected"):
            mgr.get_read_session()

    def test_single_endpoint_shares_engine(self):
        """When no read_url, both read and write should use the same engine."""
        with patch.object(_conn_mod, "create_engine", return_value=_mock_engine()):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
            assert mgr._write_engine is mgr._read_engine
            assert mgr._write_session_factory is mgr._read_session_factory

    def test_dual_endpoint_creates_separate_engines(self):
        """When read_url differs, two separate engines are created."""
        engines_created = []

        def fake_create_engine(url, **kw):
            e = _mock_engine()
            engines_created.append(url)
            return e

        with patch.object(_conn_mod, "create_engine", side_effect=fake_create_engine):
            mgr = LambdaConnectionManager(
                write_url="postgresql://u:p@proxy/db",
                read_url="postgresql://u:p@replica/db",
            )
            mgr.connect()
            assert len(engines_created) == 2


# ----------------------------------------------------------------
# Fallback Behavior
# ----------------------------------------------------------------
class TestFallbackSingleEndpoint:
    def test_read_url_defaults_to_write(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
        assert mgr.read_url == mgr.write_url

    def test_none_read_url_defaults_to_write(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db", read_url=None)
        assert mgr.read_url == mgr.write_url

    def test_empty_string_read_url_defaults_to_write(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db", read_url="")
        assert mgr.read_url == mgr.write_url


# ----------------------------------------------------------------
# Pool Stats
# ----------------------------------------------------------------
class TestPoolStats:
    def test_pool_stats_empty_when_not_connected(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
        assert mgr.get_pool_stats() == {}

    def test_pool_stats_returns_write_and_read(self):
        from sqlalchemy.pool import QueuePool

        mock_pool = MagicMock(spec=QueuePool)
        mock_pool.size.return_value = 1
        mock_pool.checkedin.return_value = 1
        mock_pool.checkedout.return_value = 0
        mock_pool.overflow.return_value = 0

        engine = _mock_engine()
        engine.pool = mock_pool

        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
            stats = mgr.get_pool_stats()
            assert "write" in stats
            assert stats["write"]["size"] == 1
            assert stats["write"]["checked_in"] == 1
            assert stats["write"]["checked_out"] == 0


# ----------------------------------------------------------------
# Health Check
# ----------------------------------------------------------------
class TestHealthCheck:
    def test_health_check_when_not_connected(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
        assert mgr.health_check() == {"write": False, "read": False}


# ----------------------------------------------------------------
# Disconnect
# ----------------------------------------------------------------
class TestDisconnect:
    def test_disconnect_when_not_connected(self):
        mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
        mgr.disconnect()  # should not raise

    def test_disconnect_disposes_engines(self):
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
            mgr.disconnect()
            engine.dispose.assert_called_once()


# ----------------------------------------------------------------
# init_database_for_lambda
# ----------------------------------------------------------------
class TestInitDatabaseForLambda:
    def test_raises_without_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="DATABASE_URL must be set"):
                init_database_for_lambda()

    def test_lambda_env_uses_small_pool(self):
        with patch.object(_conn_mod, "create_engine", return_value=_mock_engine()):
            env = {
                "DATABASE_URL": "postgresql://u:p@proxy/db",
                "AWS_LAMBDA_FUNCTION_NAME": "my-function",
            }
            with patch.dict(os.environ, env, clear=True):
                mgr = init_database_for_lambda()
                assert mgr.pool_size == 1
                assert mgr.max_overflow == 2
                assert mgr.pool_recycle == 300

    def test_non_lambda_env_uses_larger_pool(self):
        with patch.object(_conn_mod, "create_engine", return_value=_mock_engine()):
            env = {"DATABASE_URL": "postgresql://u:p@proxy/db"}
            with patch.dict(os.environ, env, clear=True):
                mgr = init_database_for_lambda()
                assert mgr.pool_size == 5
                assert mgr.max_overflow == 10
                assert mgr.pool_recycle == 900

    def test_proxy_flag_overrides_lambda_detection(self):
        with patch.object(_conn_mod, "create_engine", return_value=_mock_engine()):
            env = {
                "DATABASE_URL": "postgresql://u:p@proxy/db",
                "DB_USE_PROXY": "true",
            }
            with patch.dict(os.environ, env, clear=True):
                mgr = init_database_for_lambda()
                assert mgr.pool_size == 1


# ----------------------------------------------------------------
# get_lambda_connection
# ----------------------------------------------------------------
class TestGetLambdaConnection:
    def test_raises_when_not_initialized(self):
        original = _conn_mod._lambda_connection
        try:
            _conn_mod._lambda_connection = None
            with pytest.raises(RuntimeError, match="Lambda DB not initialized"):
                get_lambda_connection()
        finally:
            _conn_mod._lambda_connection = original


# ----------------------------------------------------------------
# Health Check — Connected positive path
# ----------------------------------------------------------------
class TestHealthCheckConnected:
    def test_both_true_when_engines_respond(self):
        """Engines that successfully execute SELECT 1 → both write and read True."""
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
        # Simulate successful SELECT 1 on both endpoints
        conn_ctx = MagicMock()
        engine.connect.return_value.__enter__ = MagicMock(return_value=conn_ctx)
        engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        result = mgr.health_check()
        assert result["write"] is True
        assert result["read"] is True

    def test_false_when_engine_raises(self):
        """An engine that raises on connect → health_check returns False for that endpoint."""
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
        engine.connect.side_effect = Exception("connection refused")
        result = mgr.health_check()
        assert result["write"] is False
        assert result["read"] is False


# ----------------------------------------------------------------
# Disconnect — dual endpoint disposes both engines
# ----------------------------------------------------------------
class TestDisconnectDualEndpoint:
    def test_both_engines_disposed_independently(self):
        """With separate read/write URLs, disconnect must dispose both engines."""
        write_engine = _mock_engine()
        read_engine = _mock_engine()
        call_count = [0]

        def fake_create(url, **kw):
            call_count[0] += 1
            return write_engine if call_count[0] == 1 else read_engine

        with patch.object(_conn_mod, "create_engine", side_effect=fake_create):
            mgr = LambdaConnectionManager(
                write_url="postgresql://u:p@proxy/db",
                read_url="postgresql://u:p@replica/db",
            )
            mgr.connect()

        mgr.disconnect()
        write_engine.dispose.assert_called_once()
        read_engine.dispose.assert_called_once()

    def test_single_engine_disposed_once(self):
        """With a single endpoint, dispose is only called once."""
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
        mgr.disconnect()
        engine.dispose.assert_called_once()


# ----------------------------------------------------------------
# write_scope / read_scope context managers
# ----------------------------------------------------------------
class TestWriteScope:
    def _connected_mgr(self):
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()
        return mgr

    def test_write_scope_commits_on_success(self):
        mgr = self._connected_mgr()
        mock_session = MagicMock()
        mgr._write_session_factory = MagicMock(return_value=mock_session)

        with mgr.write_scope():
            pass

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    def test_write_scope_rollback_on_sqlalchemy_error(self):
        from sqlalchemy.exc import SQLAlchemyError

        mgr = self._connected_mgr()
        mock_session = MagicMock()
        mgr._write_session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(SQLAlchemyError):
            with mgr.write_scope():
                raise SQLAlchemyError("forced error")

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


class TestReadScope:
    def test_read_scope_closes_session_on_success(self):
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()

        mock_session = MagicMock()
        mgr._read_session_factory = MagicMock(return_value=mock_session)

        with mgr.read_scope():
            pass

        mock_session.close.assert_called_once()

    def test_read_scope_closes_session_on_error(self):
        from sqlalchemy.exc import SQLAlchemyError

        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
            mgr.connect()

        mock_session = MagicMock()
        mgr._read_session_factory = MagicMock(return_value=mock_session)

        with pytest.raises(SQLAlchemyError):
            with mgr.read_scope():
                raise SQLAlchemyError("read error")

        mock_session.close.assert_called_once()
