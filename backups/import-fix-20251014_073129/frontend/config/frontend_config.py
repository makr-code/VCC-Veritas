"""
VERITAS Frontend Configuration
===============================

Zentrale Konfiguration für das VERITAS Frontend.
"""

import os
from typing import Optional

# ============================================================================
# Backend Configuration
# ============================================================================

# Backend-URL (kann via Environment-Variable überschrieben werden)
BACKEND_URL = os.getenv("VERITAS_BACKEND_URL", "http://localhost:5000")

# Backend-Port (für Konsistenz)
BACKEND_PORT = int(os.getenv("VERITAS_BACKEND_PORT", "5000"))

# API-Endpoints
API_ENDPOINTS = {
    "query": f"{BACKEND_URL}/query",
    "upload": f"{BACKEND_URL}/upload",
    "feedback": f"{BACKEND_URL}/api/feedback/submit",
    "feedback_stats": f"{BACKEND_URL}/api/feedback/stats",
    "feedback_list": f"{BACKEND_URL}/api/feedback/list",
    "export_word": f"{BACKEND_URL}/api/export/word",
    "export_excel": f"{BACKEND_URL}/api/export/excel",
}

# ============================================================================
# UI Configuration
# ============================================================================

# Fenster-Konfiguration
WINDOW_TITLE = "VERITAS - Verwaltungsprozess-Assistent"
WINDOW_GEOMETRY = "1400x900"
WINDOW_MIN_SIZE = (1200, 700)

# Theme
THEME = {
    "bg_main": "#1a1d23",
    "bg_sidebar": "#24272e",
    "bg_chat": "#2b2e36",
    "text_primary": "#e0e0e0",
    "text_secondary": "#b0b0b0",
    "accent_primary": "#4a9eff",
    "accent_secondary": "#5cb85c",
    "border": "#3a3d44",
    "error": "#d9534f",
    "warning": "#f0ad4e",
    "success": "#5cb85c",
}

# ============================================================================
# API Configuration
# ============================================================================

# Request-Konfiguration
REQUEST_TIMEOUT = int(os.getenv("VERITAS_REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("VERITAS_MAX_RETRIES", "3"))
RETRY_DELAY = float(os.getenv("VERITAS_RETRY_DELAY", "1.0"))

# Upload-Konfiguration
MAX_FILE_SIZE_MB = int(os.getenv("VERITAS_MAX_FILE_SIZE_MB", "50"))
MAX_FILES_PER_UPLOAD = int(os.getenv("VERITAS_MAX_FILES_PER_UPLOAD", "10"))

SUPPORTED_FILE_TYPES = [
    # Dokumente
    ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt",
    # Tabellen
    ".xlsx", ".xls", ".csv", ".ods",
    # Präsentationen
    ".pptx", ".ppt", ".odp",
    # Bilder
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg",
    # Code
    ".py", ".js", ".html", ".css", ".json", ".xml", ".yaml", ".yml",
    # Andere
    ".md", ".log", ".ini", ".cfg", ".conf",
]

# ============================================================================
# Feedback Configuration
# ============================================================================

FEEDBACK_CATEGORIES = [
    "relevanz",       # Antwort-Relevanz
    "vollständigkeit", # Vollständigkeit der Antwort
    "genauigkeit",    # Faktische Genauigkeit
    "verständlichkeit", # Verständlichkeit
    "quellen",        # Quellenqualität
    "sonstiges",      # Andere Kategorien
]

# ============================================================================
# Export Configuration
# ============================================================================

EXPORT_FORMATS = ["word", "excel", "json"]
EXPORT_DEFAULT_DIR = os.path.expanduser("~/Documents/VERITAS_Exports")

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_LEVEL = os.getenv("VERITAS_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.getenv("VERITAS_LOG_FILE", None)  # None = nur Console

# ============================================================================
# Development/Debug
# ============================================================================

DEBUG_MODE = os.getenv("VERITAS_DEBUG", "false").lower() == "true"
MOCK_BACKEND = os.getenv("VERITAS_MOCK_BACKEND", "false").lower() == "true"

# ============================================================================
# Helper Functions
# ============================================================================

def get_backend_url() -> str:
    """Gibt die aktuelle Backend-URL zurück"""
    return BACKEND_URL

def get_api_endpoint(name: str) -> Optional[str]:
    """Gibt einen API-Endpoint zurück"""
    return API_ENDPOINTS.get(name)

def is_file_type_supported(filename: str) -> bool:
    """Prüft ob Dateityp unterstützt wird"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_FILE_TYPES)

def get_theme_color(key: str, default: str = "#ffffff") -> str:
    """Gibt eine Theme-Farbe zurück"""
    return THEME.get(key, default)


# ============================================================================
# Configuration Validation
# ============================================================================

def validate_config():
    """Validiert die Konfiguration"""
    errors = []
    
    # Backend-URL prüfen
    if not BACKEND_URL.startswith(("http://", "https://")):
        errors.append(f"Invalid BACKEND_URL: {BACKEND_URL}")
    
    # Port prüfen
    if not (1 <= BACKEND_PORT <= 65535):
        errors.append(f"Invalid BACKEND_PORT: {BACKEND_PORT}")
    
    # Timeout prüfen
    if REQUEST_TIMEOUT <= 0:
        errors.append(f"Invalid REQUEST_TIMEOUT: {REQUEST_TIMEOUT}")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True


# Validierung beim Import
validate_config()


# ============================================================================
# Export Configuration Summary
# ============================================================================

def print_config_summary():
    """Druckt eine Konfigurations-Übersicht"""
    print("=" * 60)
    print("VERITAS Frontend Configuration")
    print("=" * 60)
    print(f"Backend URL:      {BACKEND_URL}")
    print(f"Backend Port:     {BACKEND_PORT}")
    print(f"Request Timeout:  {REQUEST_TIMEOUT}s")
    print(f"Max Retries:      {MAX_RETRIES}")
    print(f"Max File Size:    {MAX_FILE_SIZE_MB}MB")
    print(f"Debug Mode:       {DEBUG_MODE}")
    print(f"Mock Backend:     {MOCK_BACKEND}")
    print("=" * 60)


if __name__ == "__main__":
    print_config_summary()
