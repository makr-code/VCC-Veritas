"""
Checklist Constants
==================

Shared constants for the checklist generation system.

Author: VERITAS Development Team
Date: December 2025
"""

from typing import List, Dict, Any


# Checklist Types
CHECKLIST_TYPES: List[Dict[str, str]] = [
    {
        "type": "general",
        "name": "Allgemeine Checkliste",
        "description": "Universelle Checkliste für verschiedene Zwecke"
    },
    {
        "type": "compliance",
        "name": "Compliance-Checkliste",
        "description": "Prüfung der Vorschriftenkonformität"
    },
    {
        "type": "construction",
        "name": "Bau-Checkliste",
        "description": "Bauanträge und Bauvorhaben"
    },
    {
        "type": "environmental",
        "name": "Umwelt-Checkliste",
        "description": "Umweltrechtliche Anforderungen"
    },
    {
        "type": "safety",
        "name": "Sicherheits-Checkliste",
        "description": "Sicherheitsanforderungen und -prüfungen"
    },
    {
        "type": "quality",
        "name": "Qualitäts-Checkliste",
        "description": "Qualitätsmanagement und -sicherung"
    },
    {
        "type": "administrative",
        "name": "Verwaltungs-Checkliste",
        "description": "Verwaltungsabläufe und -prozesse"
    },
    {
        "type": "approval",
        "name": "Genehmigungs-Checkliste",
        "description": "Genehmigungsverfahren"
    },
    {
        "type": "process",
        "name": "Prozess-Checkliste",
        "description": "Geschäftsprozesse und Workflows"
    },
    {
        "type": "audit",
        "name": "Audit-Checkliste",
        "description": "Prüfungen und Audits"
    }
]

# Get allowed types as list
ALLOWED_CHECKLIST_TYPES: List[str] = [ct["type"] for ct in CHECKLIST_TYPES]

# Default fallback source
DEFAULT_FALLBACK_SOURCE = "Template-Based"

# Default configuration
DEFAULT_MODEL = "llama3.2"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 2000
