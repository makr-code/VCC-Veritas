"""
VQB Frontend - API Configuration

Configuration for backend API communication.
"""

import os
from typing import Optional


class APIConfig:
    """Backend API configuration"""
    
    # Base URL
    BASE_URL: str = os.getenv("VERITAS_BACKEND_URL", "http://localhost:5000")
    
    # API Version
    API_VERSION: str = "v3"
    
    # Timeouts (seconds)
    CONNECT_TIMEOUT: int = 5
    READ_TIMEOUT: int = 30
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 0.5  # seconds
    
    # Endpoints
    @classmethod
    def get_endpoint(cls, path: str) -> str:
        """Get full endpoint URL"""
        return f"{cls.BASE_URL}/api/{cls.API_VERSION}/{path.lstrip('/')}"
    
    # Common Endpoints
    ENDPOINT_VPB_QUERY = "vpb/query"
    ENDPOINT_VPB_DOCUMENTS = "vpb/documents"
    ENDPOINT_VPB_ANALYSIS = "vpb/analysis"
    ENDPOINT_DOCUMENTS_RELATED = "documents/related"
    ENDPOINT_AI_PARSE_FILTER = "ai/parse_filter"
    ENDPOINT_AI_RECOMMEND = "ai/recommend"
    
    # Session
    SESSION_ID: Optional[str] = None
    
    @classmethod
    def set_session_id(cls, session_id: str):
        """Set session ID for all requests"""
        cls.SESSION_ID = session_id


# Convenience functions
def get_vpb_query_url() -> str:
    """Get VPB query endpoint URL"""
    return APIConfig.get_endpoint(APIConfig.ENDPOINT_VPB_QUERY)


def get_vpb_documents_url() -> str:
    """Get VPB documents endpoint URL"""
    return APIConfig.get_endpoint(APIConfig.ENDPOINT_VPB_DOCUMENTS)


def get_vpb_analysis_url() -> str:
    """Get VPB analysis endpoint URL"""
    return APIConfig.get_endpoint(APIConfig.ENDPOINT_VPB_ANALYSIS)
