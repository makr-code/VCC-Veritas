"""
Database Adapter Factory with Environment-Controlled Fallback
Primary: ThemisDB → Fallback: UDS3 Polyglot
"""
import os
import logging
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DatabaseAdapterType(str, Enum):
    """Supported database adapter types"""
    THEMIS = "themis"
    UDS3 = "uds3"


def get_database_adapter(
    adapter_type: Optional[DatabaseAdapterType] = None,
    enable_fallback: bool = True
) -> Any:
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
    use_uds3_fallback = os.getenv("USE_UDS3_FALLBACK", "true").lower() == "true"
    
    # Override with explicit adapter_type
    if adapter_type == DatabaseAdapterType.THEMIS:
        themis_enabled = True
        use_uds3_fallback = enable_fallback
    elif adapter_type == DatabaseAdapterType.UDS3:
        themis_enabled = False
    
    # Try ThemisDB first (if enabled)
    if themis_enabled:
        try:
            adapter = _init_themisdb_adapter()
            if adapter:
                logger.info("✅ Using ThemisDB adapter (primary)")
                return adapter
        except Exception as e:
            logger.warning(f"⚠️ ThemisDB initialization failed: {e}")
            
            # Fallback to UDS3 if enabled
            if use_uds3_fallback and enable_fallback:
                logger.info("🔄 Falling back to UDS3 Polyglot adapter")
            else:
                raise RuntimeError(
                    f"ThemisDB adapter failed and fallback disabled: {e}"
                )
    
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
                f"Both ThemisDB and UDS3 adapters failed. "
                f"ThemisDB: {themis_enabled}, UDS3 fallback: {use_uds3_fallback}"
            )
    
    # No adapter available
    raise RuntimeError(
        "No database adapter available. "
        "Set THEMIS_ENABLED=true or USE_UDS3_FALLBACK=true"
    )


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
                return True
            except Exception as e:
                logger.warning(f"⚠️ ThemisDB health check failed: {e}")
                await adapter.close()
                return False
        
        # Run health check (sync wrapper for async health check)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.run_until_complete(_check_health()):
            return adapter
        else:
            return None
            
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
        
        # Initialize UDS3 with backend config
        backend_config = {
            "relational": {"enabled": True},  # PostgreSQL
            "vector": {"enabled": True},      # ChromaDB
            "graph": {"enabled": True},       # Neo4j
            "file": {"enabled": True}         # CouchDB
        }
        
        uds3_manager = UDS3PolyglotManager(
            backend_config=backend_config,
            enable_rag=False  # RAG logic handled by Veritas
        )
        
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
            import asyncio
            
            async def _close():
                await adapter.close()
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(_close())
            return True
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
