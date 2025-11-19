"""
VQB Frontend - Application Configuration

Central configuration for the Visual Query Builder application.
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class AppConfig:
    """Main application configuration"""
    
    # Application Info
    APP_NAME: str = "VCC-Veritas Visual Query Builder"
    APP_VERSION: str = "0.1.0"
    
    # Window Settings
    WINDOW_WIDTH: int = 1400
    WINDOW_HEIGHT: int = 900
    WINDOW_MIN_WIDTH: int = 1024
    WINDOW_MIN_HEIGHT: int = 768
    
    # Layout Settings
    FILTER_PANEL_WIDTH: int = 250
    TIMELINE_HEIGHT_RATIO: float = 0.4  # 40% of content area
    
    # Performance Settings
    ASYNC_WORKER_THREADS: int = 4
    CACHE_SIZE_MB: int = 100
    AUTO_REFRESH_INTERVAL_MS: int = 5000  # 5 seconds
    
    # UI Settings
    ANIMATION_ENABLED: bool = True
    TOOLTIPS_ENABLED: bool = True
    DEBUG_MODE: bool = bool(os.getenv("VQB_DEBUG", False))
    
    # Data Settings
    MAX_PROCESSES_DISPLAY: int = 100
    MAX_DOCUMENTS_DISPLAY: int = 500
    LAZY_LOAD_THRESHOLD: int = 50
    
    # Search Settings
    SEARCH_DEBOUNCE_MS: int = 500
    MIN_SEARCH_LENGTH: int = 3
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config from environment variables"""
        config = cls()
        
        # Override from environment if present
        if width := os.getenv("VQB_WINDOW_WIDTH"):
            config.WINDOW_WIDTH = int(width)
        if height := os.getenv("VQB_WINDOW_HEIGHT"):
            config.WINDOW_HEIGHT = int(height)
        
        return config


# Global config instance
config = AppConfig.from_env()
