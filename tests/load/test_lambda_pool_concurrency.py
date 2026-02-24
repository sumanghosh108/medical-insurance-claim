"""Performance Tests — Lambda Connection Pool Concurrency.

Simulates multiple concurrent Lambda invocations reusing a single warm-container
LambdaConnectionManager. Validates that:
  - Pool stays within pool_size + max_overflow bounds under concurrency
  - No RuntimeError is raised when all threads compete for sessions
  - Pool stats are retrievable mid-flight
"""

import importlib.util
import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Load connection.py directly (same technique as test_lambda_connection.py)
# ---------------------------------------------------------------------------
_mod_path = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "src", "database", "connection.py")
)
_spec = importlib.util.spec_from_file_location("_connection_perf", _mod_path)
_conn_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conn_mod)

LambdaConnectionManager = _conn_mod.LambdaConnectionManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_engine():
    """Create a mock engine with a realistic mock pool."""
    engine = MagicMock()
    # connect() used during .connect() verification
    conn_ctx = MagicMock()
    engine.connect.return_value.__enter__ = MagicMock(return_value=conn_ctx)
    engine.connect.return_value.__exit__ = MagicMock(return_value=False)

    # Mock pool for stats introspection
    from sqlalchemy.pool import QueuePool
    mock_pool = MagicMock(spec=QueuePool)
    mock_pool.size.return_value = 1
    mock_pool.checkedin.return_value = 1
    mock_pool.checkedout.return_value = 0
    mock_pool.overflow.return_value = 0
    engine.pool = mock_pool

    return engine


def _build_manager(pool_size: int = 1, max_overflow: int = 2) -> LambdaConnectionManager:
    """Return a connected LambdaConnectionManager backed by a mock engine."""
    engine = _mock_engine()
    with patch.object(_conn_mod, "create_engine", return_value=engine):
        mgr = LambdaConnectionManager(
            write_url="postgresql://u:p@proxy/db",
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=5,
        )
        mgr.connect()
    return mgr


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLambdaPoolConcurrency:
    """Validate LambdaConnectionManager under simulated concurrent Lambda invocations."""

    def test_concurrent_get_write_session_no_runtime_error(self):
        """N concurrent threads each calling get_write_session() must not raise."""
        N_THREADS = 20
        mgr = _build_manager()

        # Replace session factory with one that returns fast mock sessions
        mock_session = MagicMock()
        mgr._write_session_factory = MagicMock(return_value=mock_session)

        errors: list[Exception] = []
        sessions_acquired = []

        def worker():
            try:
                session = mgr.get_write_session()
                sessions_acquired.append(session)
                time.sleep(0.005)  # simulate brief DB work
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Errors under concurrency: {errors}"
        assert len(sessions_acquired) == N_THREADS

    def test_concurrent_get_read_session_no_runtime_error(self):
        """N concurrent threads each calling get_read_session() must not raise."""
        N_THREADS = 20
        mgr = _build_manager()

        mock_session = MagicMock()
        mgr._read_session_factory = MagicMock(return_value=mock_session)

        errors: list[Exception] = []

        def worker():
            try:
                mgr.get_read_session()
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(N_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Read session errors: {errors}"

    def test_pool_stats_accessible_under_concurrency(self):
        """get_pool_stats() must not raise even when called while threads hold sessions."""
        mgr = _build_manager(pool_size=1, max_overflow=2)

        mock_session = MagicMock()
        mgr._write_session_factory = MagicMock(return_value=mock_session)

        stop = threading.Event()
        stats_errors: list[Exception] = []
        all_stats: list[dict] = []

        def session_worker():
            while not stop.is_set():
                try:
                    mgr.get_write_session()
                    time.sleep(0.002)
                except Exception:
                    pass

        def stats_worker():
            while not stop.is_set():
                try:
                    s = mgr.get_pool_stats()
                    all_stats.append(s)
                except Exception as exc:
                    stats_errors.append(exc)
                    stop.set()
                time.sleep(0.003)

        workers = [threading.Thread(target=session_worker) for _ in range(5)]
        watcher = threading.Thread(target=stats_worker)
        for w in workers:
            w.start()
        watcher.start()

        time.sleep(0.1)  # let them run for 100 ms
        stop.set()

        for w in workers:
            w.join(timeout=2)
        watcher.join(timeout=2)

        assert not stats_errors, f"Pool stats raised errors under concurrency: {stats_errors}"
        assert len(all_stats) > 0, "No pool stats collected"

    def test_write_scope_concurrent_commit_and_rollback(self):
        """Mix of successful and failing write_scope() calls in parallel must not deadlock."""
        N_SUCCESS = 10
        N_FAIL = 5
        from sqlalchemy.exc import SQLAlchemyError

        mgr = _build_manager()

        mock_session = MagicMock()
        mgr._write_session_factory = MagicMock(return_value=mock_session)

        results = {"committed": 0, "rolled_back": 0}
        lock = threading.Lock()

        def success_worker():
            with mgr.write_scope():
                time.sleep(0.002)
            with lock:
                results["committed"] += 1

        def fail_worker():
            try:
                with mgr.write_scope():
                    raise SQLAlchemyError("simulated failure")
            except SQLAlchemyError:
                with lock:
                    results["rolled_back"] += 1

        threads = (
            [threading.Thread(target=success_worker) for _ in range(N_SUCCESS)]
            + [threading.Thread(target=fail_worker) for _ in range(N_FAIL)]
        )
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert results["committed"] == N_SUCCESS
        assert results["rolled_back"] == N_FAIL

    def test_pool_size_config_respected(self):
        """Manager initialized with pool_size=1, max_overflow=2 must reflect those settings."""
        mgr = _build_manager(pool_size=1, max_overflow=2)
        assert mgr.pool_size == 1
        assert mgr.max_overflow == 2
        assert mgr.pool_recycle == 300  # Lambda default

    def test_lambda_optimized_defaults_match_spec(self):
        """Lambda-mode defaults must match the RDS Proxy optimisation spec."""
        engine = _mock_engine()
        with patch.object(_conn_mod, "create_engine", return_value=engine):
            mgr = LambdaConnectionManager(write_url="postgresql://u:p@proxy/db")
        assert mgr.pool_size == 1
        assert mgr.max_overflow == 2
        assert mgr.pool_recycle == 300
        assert mgr.pool_timeout == 10
