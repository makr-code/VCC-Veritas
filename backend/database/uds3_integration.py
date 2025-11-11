"""
UDS3 Direct Integration for VERITAS Agent Framework
Updated: 24. Oktober 2025 - Direct UDS3 v3.1.0 Integration (No Wrappers!)

DIREKTE Integration - Keine Wrapper, Stubs oder Fallbacks!
- Production: UDS3 shared instance from app.py
- Testing: Direct UnifiedDatabaseStrategy initialization
"""
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
_uds3_instance = None

# Add UDS3 to path
uds3_path = Path(__file__).parent.parent.parent.parent / "uds3"
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))


def set_uds3_instance(uds3):
    """Set shared UDS3 instance from app.py (production mode)."""
    global _uds3_instance
    _uds3_instance = uds3
    logger.info("✅ UDS3 shared instance set (production mode)")


def get_uds3_client():
    """
    Get UDS3 UnifiedDatabaseStrategy instance - DIRECT, NO WRAPPERS!

    Returns shared instance from app.py or raises error.
    No fallbacks, no stubs, no standalone mode!
    """
    global _uds3_instance

    if _uds3_instance is None:
        raise RuntimeError(
            "UDS3 not initialized! " "Must be initialized via app.py lifespan context. " "Call set_uds3_instance() first."
        )

    return _uds3_instance


def get_database_manager():
    """Get database manager from UDS3 - DIRECT ACCESS!"""
    uds3 = get_uds3_client()
    if not hasattr(uds3, "db_manager"):
        raise AttributeError("UDS3 has no db_manager attribute")
    return uds3.db_manager
