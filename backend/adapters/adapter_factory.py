"""
Database Adapter Factory with Environment-Controlled Fallback
Primary: ThemisDB → Fallback: UDS3 Polyglot
"""
import logging
import os
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DatabaseAdapterType(str, Enum):
    """Supported database adapter types"""

    THEMIS = "themis"
    UDS3 = "uds3"


def get_database_adapter(adapter_type: Optional[DatabaseAdapterType] = None, enable_fallback: bool = True) -> Any:
    """
    Get database adapter with environment-controlled selection and fallback.

    Strategy:
    ---------
    1. **Primary:** ThemisDB (if THEMIS_ENABLED=true or THEMIS_HOST set)
    2. **Fallback:** UDS3 Polyglot (if ThemisDB unavailable and enable_fallback=True)

    Environment Variables:
    ----------------------
    - THEMIS_ENABLED: Enable ThemisDB adapter (default: true)
    - THEMIS_HOST: ThemisDB server host (default: localhost)
    - THEMIS_PORT: ThemisDB server port (default: 8765)
    - THEMIS_API_TOKEN: Optional API token for authentication
    - USE_UDS3_FALLBACK: Enable UDS3 fallback (default: true)

    Args:
        adapter_type: Force specific adapter type (overrides env detection)
        enable_fallback: Enable fallback to UDS3 if ThemisDB fails (default: True)

    Returns:
        Database adapter instance (ThemisDBAdapter or UDS3VectorSearchAdapter)

    Raises:
        RuntimeError: If no adapter can be initialized

    Usage:
    ------
    ```python
    # Auto-detection with fallback (recommended)
    adapter = get_database_adapter()

    # Force ThemisDB (no fallback)
    adapter = get_database_adapter(
        adapter_type=DatabaseAdapterType.THEMIS,
        enable_fallback=False
    )

    # Force UDS3
    adapter = get_database_adapter(
        adapter_type=DatabaseAdapterType.UDS3,
        enable_fallback=False
    )
    ```
    """

    # Check environment configuration
    themis_enabled = os.getenv("THEMIS_ENABLED", "true").lower() == "true"
    themis_host = os.getenv("THEMIS_HOST", "localhost")
    themis_port = int(os.getenv("THEMIS_PORT", "8765"))
    use_uds3_fallback = os.getenv("USE_UDS3_FALLBACK", "true").lower() == "true"
    # Themis fail policy controls behavior when Themis health checks fail:
    # - 'disable' (default): if health check fails, do not use Themis and fall back to UDS3
    # - 'degrade': keep adapter but mark unhealthy, continue in degraded mode
    # - 'retry': attempt synchronous retries before falling back
    themis_fail_policy = os.getenv("THEMIS_FAIL_POLICY", "disable").lower()
    themis_retry_count = int(os.getenv("THEMIS_RETRY_COUNT", "3"))
    themis_retry_backoff = float(os.getenv("THEMIS_RETRY_BACKOFF", "2"))

    # Override with explicit adapter_type
    if adapter_type == DatabaseAdapterType.THEMIS:
        themis_enabled = True
        use_uds3_fallback = enable_fallback
    elif adapter_type == DatabaseAdapterType.UDS3:
        themis_enabled = False

    # Quick TCP probe: if Themis host:port is not reachable at TCP level
    # we treat Themis as disabled to avoid long background retries and
    # ensure UDS3 acts as the immediate fallback.
    if themis_enabled:
        try:
            import socket

            sock = socket.create_connection((themis_host, themis_port), timeout=2)
            sock.close()
        except Exception:
            logger.warning(
                "⚠️ Themis host %s:%s not reachable via TCP — treating Themis as disabled",
                themis_host,
                themis_port,
            )
            themis_enabled = False
            # Explicit, user-friendly log explaining fallback behaviour
            if use_uds3_fallback and enable_fallback:
                logger.info(
                    "🔄 Themis scheint nicht erreichbar zu sein (%s:%s). UDS3 wird als Fallback aktiviert.",
                    themis_host,
                    themis_port,
                )

    # Try ThemisDB first (if enabled)
    if themis_enabled:
        try:
            adapter = _init_themisdb_adapter()
            if adapter:
                # If policy == 'degrade' accept adapter immediately and rely on background
                # health check to mark `_healthy` for consumers.
                if themis_fail_policy == "degrade":
                    logger.info("✅ Using ThemisDB adapter (primary, degrade-on-fail)")
                    return adapter

                # For 'disable' or 'retry' policies we perform a synchronous health check
                # before committing to Themis as primary. This avoids leaving the system
                # in a confused state when Themis is clearly unreachable.
                import asyncio
                import time

                def _sync_health_check_once() -> bool:
                    try:
                        ok = _run_coroutine_sync(adapter.health_check(), timeout=30)
                        try:
                            setattr(adapter, "_healthy", bool(ok))
                        except Exception:
                            pass
                        return bool(ok)
                    except Exception:
                        try:
                            setattr(adapter, "_healthy", False)
                        except Exception:
                            pass
                        return False

                if themis_fail_policy == "disable":
                    ok = _sync_health_check_once()
                    if ok:
                        logger.info("✅ Using ThemisDB adapter (primary)")
                        return adapter
                    else:
                        logger.warning("⚠️ ThemisDB health check failed (policy=disable) - falling back to UDS3")

                elif themis_fail_policy == "retry":
                    ok = False
                    for attempt in range(1, themis_retry_count + 1):
                        ok = _sync_health_check_once()
                        if ok:
                            logger.info(f"✅ ThemisDB health check succeeded on attempt {attempt}")
                            break
                        logger.warning(f"⚠️ ThemisDB health check attempt {attempt} failed")
                        time.sleep(themis_retry_backoff * attempt)

                    if ok:
                        logger.info("✅ Using ThemisDB adapter (primary)")
                        return adapter
                    else:
                        logger.warning("⚠️ ThemisDB health check failed after retries - falling back to UDS3")
                else:
                    # Unknown policy — default to degrade behavior
                    logger.warning(f"⚠️ Unknown THEMIS_FAIL_POLICY='{themis_fail_policy}', defaulting to 'degrade'")
                    return adapter
        except Exception as e:
            logger.warning(f"⚠️ ThemisDB initialization failed: {e}")

            # Fallback to UDS3 if enabled
            if use_uds3_fallback and enable_fallback:
                logger.info(
                    "🔄 Themis-Adapter konnte nicht initialisiert werden oder ist nicht gesund: %s. UDS3 wird jetzt als Fallback verwendet.",
                    str(e),
                )
            else:
                raise RuntimeError(f"ThemisDB adapter failed and fallback disabled: {e}")

    # Try UDS3 fallback
    if use_uds3_fallback and enable_fallback:
        try:
            adapter = _init_uds3_adapter()
            if adapter:
                logger.info("✅ Using UDS3 Polyglot adapter (fallback)")
                return adapter
        except Exception as e:
            logger.error(f"❌ UDS3 adapter initialization failed: {e}")
            raise RuntimeError(
                f"Both ThemisDB and UDS3 adapters failed. " f"ThemisDB: {themis_enabled}, UDS3 fallback: {use_uds3_fallback}"
            )

    # No adapter available
    raise RuntimeError("No database adapter available. " "Set THEMIS_ENABLED=true or USE_UDS3_FALLBACK=true")


def _init_themisdb_adapter() -> Optional[Any]:
    """
    Initialize ThemisDB adapter with health check.

    Returns:
        ThemisDBAdapter instance if successful, None otherwise
    """
    try:
        from backend.adapters.themisdb_adapter import ThemisDBAdapter, ThemisDBConfig

        # Load config from environment
        config = ThemisDBConfig.from_env()
        adapter = ThemisDBAdapter(config)

        # Health check to verify connectivity
        import asyncio

        async def _check_health():
            try:
                health = await adapter.health_check()
                logger.info(f"✅ ThemisDB health check passed: {health}")
                try:
                    setattr(adapter, "_healthy", True)
                except Exception:
                    pass
                return True
            except Exception as e:
                # Don't close the adapter here; mark as unhealthy and
                # allow the system to continue in degraded mode. Individual
                # requests will fail if they attempt to use ThemisDB.
                logger.warning(f"⚠️ ThemisDB health check failed: {e}")
                try:
                    setattr(adapter, "_healthy", False)
                except Exception:
                    pass
                return False

        # Run health check asynchronously in a dedicated background thread.
        # This avoids trying to run a new event loop on the current thread
        # when an asyncio loop (e.g., uvicorn) is already running, which
        # causes "This event loop is already running" errors and
        # 'coroutine was never awaited' warnings.
        import asyncio as _asyncio
        import threading

        def _run_health_check_in_thread(adpt: Any) -> None:
            """Run a health check in a dedicated event loop thread.

            This will mark the adapter as healthy/degraded but will not force-close
            the adapter on a failed health check. Services should handle transient
            ThemisDB errors themselves (requests will fail gracefully).
            """
            loop = _asyncio.new_event_loop()
            try:
                _asyncio.set_event_loop(loop)
                try:
                    ok = loop.run_until_complete(_check_health())
                    # attach a runtime flag for consumers to inspect if needed
                    try:
                        setattr(adpt, "_healthy", bool(ok))
                    except Exception:
                        pass
                    if not ok:
                        # log but do NOT forcibly close the adapter; keep it available
                        logger.warning("⚠️ ThemisDB reported unhealthy during background check; continuing in degraded mode")
                except Exception as e:
                    logger.warning(f"⚠️ ThemisDB background health check failed: {e}")
                    try:
                        setattr(adpt, "_healthy", False)
                    except Exception:
                        pass
            finally:
                try:
                    loop.close()
                except Exception:
                    pass

        # Start health check in background and return adapter immediately.
        t = threading.Thread(target=_run_health_check_in_thread, args=(adapter,), daemon=True)
        t.start()
        return adapter

    except ImportError as e:
        logger.error(f"❌ ThemisDB adapter import failed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ ThemisDB adapter initialization error: {e}")
        return None


def _init_uds3_adapter() -> Optional[Any]:
    """
    Initialize UDS3 Polyglot adapter.

    Returns:
        UDS3VectorSearchAdapter instance if successful, None otherwise
    """
    try:
        from uds3.core.polyglot_manager import UDS3PolyglotManager

        from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter

        # Initialize UDS3 with backend config. Only enable file backend if
        # the optional `couchdb` package is available locally. This prevents
        # noisy import errors when running in environments without the driver.
        file_enabled = True
        try:
            import importlib

            importlib.import_module("couchdb")
        except Exception:
            file_enabled = False
            logger.info("ℹ️ Optional driver 'couchdb' not importable - File-Backend will be disabled in UDS3 backend_config")

        backend_config = {
            "relational": {"enabled": True},  # PostgreSQL
            "vector": {"enabled": True},  # ChromaDB
            "graph": {"enabled": True},  # Neo4j
            "file": {"enabled": bool(file_enabled)},  # CouchDB (optional)
        }

        # Ensure environment signals that CouchDB/file backend is disabled when
        # the optional driver is not importable. Some UDS3 versions read env-vars
        # at startup and may still attempt imports; make the intent explicit.
        if not file_enabled:
            os.environ.setdefault("COUCHDB_ENABLED", "false")
            os.environ.setdefault("UDS3_FILE_ENABLED", "false")

        uds3_manager = UDS3PolyglotManager(backend_config=backend_config, enable_rag=False)  # RAG logic handled by Veritas

        # Wrap in adapter
        adapter = UDS3VectorSearchAdapter(uds3_manager)
        logger.info("✅ UDS3 Polyglot adapter initialized")

        return adapter

    except ImportError as e:
        logger.error(f"❌ UDS3 adapter import failed: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ UDS3 adapter initialization error: {e}")
        return None


def get_adapter_type() -> DatabaseAdapterType:
    """
    Get currently active adapter type from environment.

    Returns:
        DatabaseAdapterType enum value
    """
    themis_enabled = os.getenv("THEMIS_ENABLED", "true").lower() == "true"

    if themis_enabled:
        return DatabaseAdapterType.THEMIS
    else:
        return DatabaseAdapterType.UDS3


def is_themisdb_available() -> bool:
    """
    Check if ThemisDB adapter is available and healthy.

    Returns:
        True if ThemisDB is reachable, False otherwise
    """
    try:
        adapter = _init_themisdb_adapter()
        if adapter:
            try:
                _run_coroutine_sync(adapter.close(), timeout=10)
                return True
            except Exception:
                return False
        return False
    except Exception:
        return False


def is_uds3_available() -> bool:
    """
    Check if UDS3 adapter is available.

    Returns:
        True if UDS3 can be initialized, False otherwise
    """
    try:
        adapter = _init_uds3_adapter()
        return adapter is not None
    except Exception:
        return False


def get_persistence_adapter() -> Optional[Any]:
    """
    Return the adapter intended for persistence operations.

    Preference: ThemisDB (authoritative). If Themis cannot be initialized
    this function returns None so callers can decide (enqueue/retry/fail).
    """
    try:
        # Try Themis only for persistence
        if os.getenv("THEMIS_ENABLED", "true").lower() != "true":
            logger.info("ℹ️ THEMIS_ENABLED!=true - persistence adapter disabled")
            return None

        adapter = _init_themisdb_adapter()
        if adapter:
            # perform a lightweight sync health check if possible
            try:
                ok = _run_coroutine_sync(adapter.health_check(), timeout=30)
                try:
                    setattr(adapter, "_healthy", bool(ok))
                except Exception:
                    pass
            except Exception:
                # ignore health-check failures here; caller may handle
                try:
                    setattr(adapter, "_healthy", False)
                except Exception:
                    pass

            return adapter

        return None
    except Exception as e:
        logger.warning(f"⚠️ get_persistence_adapter failed: {e}")
        return None


def get_retrieval_adapter() -> Any:
    """
    Return the adapter intended for retrieval operations.

    Preference: UDS3 Polyglot (fast hybrid/vector retrieval). Fall back to
    ThemisDB if UDS3 is not available.
    """
    # Prefer UDS3 for retrieval
    try:
        adapter = _init_uds3_adapter()
        if adapter:
            logger.info("✅ get_retrieval_adapter: using UDS3 for retrieval")
            return adapter
    except Exception as e:
        logger.warning(f"⚠️ UDS3 retrieval init failed: {e}")

    # Fallback to Themis if UDS3 not available
    try:
        adapter = _init_themisdb_adapter()
        if adapter:
            logger.info("ℹ️ get_retrieval_adapter: falling back to Themis for retrieval")
            return adapter
    except Exception as e:
        logger.warning(f"⚠️ Themis retrieval init failed: {e}")

    raise RuntimeError("No retrieval adapter available (UDS3/Themis)")
