#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Frontend Services Package
Zentrale Services für Theme, Backend-API, etc.
"""

from .backend_api_client import BackendAPIClient, QueryMode, QueryRequest, QueryResponse
from .theme_manager import ThemeManager, ThemeType, get_colors, get_theme_manager

__all__ = [
    # Theme Manager
    "ThemeManager",
    "ThemeType",
    "get_theme_manager",
    "get_colors",
    # Backend API Client
    "BackendAPIClient",
    "QueryMode",
    "QueryRequest",
    "QueryResponse",
]
