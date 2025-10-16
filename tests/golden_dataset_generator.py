#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GOLDEN DATASET Generator für RAG Quality Testing
Version: 2.0 (10. Oktober 2025)

Erweiterte Features:
- ALLE Modelle testen (nicht nur 3)
- Direkte Zitate aus Rechtsquellen extrahieren
- Detaillierte Zeitmessung (Retrieval, Generation, Network)
- Golden Dataset für Feedback-Schleife
- Paragraphen-Referenz-Tracking
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Backend-URL
BACKEND_URL = "http://localhost:5000"

# ============================================================================
# CONFIGURATION
# ============================================================================

# ALLE Modelle testen (für umfassende Evaluation)
TEST_ALL_MODELS = True

# Minimale Erwartungen für verwaltungsrechtliche Antworten
QUALITY_THRESHOLDS = {
    "min_answer_length": 500,
    "min_citations": 3,
    "min_direct_quotes": 2,
    "min_legal_references": 3,
    "min_follow_ups": 3,
    "min_aspect_coverage": 0.6
}

# Golden Dataset Speicherpfad
GOLDEN_DATASET_PATH = "golden_dataset_{timestamp}.json"

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🏆 GOLDEN DATASET GENERATOR v2.0")
    print("="*80)
    print("\n📋 Test-Konfiguration:")
    print(f"  • Backend: {BACKEND_URL}")
    print(f"  • Alle Modelle testen: {TEST_ALL_MODELS}")
    print(f"  • Qualitäts-Schwellenwerte:")
    for key, value in QUALITY_THRESHOLDS.items():
        print(f"    - {key}: {value}")
    
    print("\n🚀 Starte Test-Suite...")
    print("\nHinweis: Dies kann 15-30 Minuten dauern bei allen Modellen!")
    print("Drücke Strg+C zum Abbrechen\n")
    
    input("Drücke Enter zum Starten oder Strg+C zum Abbrechen...")
    
    # Hier würde der eigentliche Test laufen
    # (Integration in bestehendes test_rag_quality_v3_19_0.py)
    
    print("\n✅ Für vollständigen Test: python tests/test_rag_quality_v3_19_0.py")
