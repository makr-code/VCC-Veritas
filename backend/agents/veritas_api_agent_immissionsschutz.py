#!/usr/bin/env python3
"""
VERITAS AGENT: IMMISSIONSSCHUTZ
=================================

Spezialisierter Agent für Immissionsschutz, Luftqualität und Lärmschutz.

HAUPTFUNKTIONEN:
- Luftqualität und Schadstoffgrenzwerte
- Lärmschutz und Lärmgrenzwerte
- TA Luft, TA Lärm
- Emissionsberechnung
- Immissionsschutzrechtliche Anforderungen

CAPABILITIES:
- Grenzwerte für Luftschadstoffe
- Lärmgrenzwerte für verschiedene Gebiete
- TA Luft Anforderungen
- TA Lärm Anforderungen
- Immissionsschutzrechtliche Genehmigungen

INTEGRATION:
- Registriert im AgentRegistry als "ImmissionsschutzAgent"
- Domain: AgentDomain.ENVIRONMENTAL
- Capabilities: ["immissionsschutz", "luftqualität", "lärm", "ta_luft", ...]

Author: VERITAS Development Team
Date: 2025-10-16
Version: 1.0 (Production)
"""

import os
import sys
import logging
import json
import uuid
import asyncio
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import traceback

# VERITAS Core Imports
try:
    from backend.agents.veritas_api_agent_registry import (
        get_agent_registry, AgentCapability, AgentStatus
    )
    AGENT_SYSTEM_AVAILABLE = True
except ImportError as e:
    AGENT_SYSTEM_AVAILABLE = False
    logging.warning(f"⚠️ Agent System nicht verfügbar: {e}")

logger = logging.getLogger(__name__)

# ==========================================
# IMMISSIONSSCHUTZ CONFIGURATION
# ==========================================

AGENT_DOMAIN = "environmental"
AGENT_NAME = "immissionsschutz_agent"
AGENT_VERSION = "1.0"

AGENT_CAPABILITIES = [
    AgentCapability.QUERY_PROCESSING,
    AgentCapability.DATA_ANALYSIS,
]

# ==========================================
# DATA CLASSES & TYPES
# ==========================================

class ImmissionsschutzCategory(Enum):
    """Kategorien des Immissionsschutzes"""
    LUFTQUALITAET = "luftqualitaet"
    LAERMSCHUTZ = "laermschutz"
    TA_LUFT = "ta_luft"
    TA_LAERM = "ta_laerm"
    GRENZWERTE = "grenzwerte"
    EMISSIONEN = "emissionen"
    UNBEKANNT = "unbekannt"

class Schadstoff(Enum):
    """Luftschadstoffe"""
    NO2 = "NO2"           # Stickstoffdioxid
    PM10 = "PM10"         # Feinstaub
    PM25 = "PM2.5"        # Feinstaub (fein)
    O3 = "O3"             # Ozon
    SO2 = "SO2"           # Schwefeldioxid
    CO = "CO"             # Kohlenmonoxid
    BENZOL = "Benzol"

class Gebietstyp(Enum):
    """Gebietstypen für Lärmschutz"""
    INDUSTRIEGEBIET = "Industriegebiet"
    GEWERBEGEBIET = "Gewerbegebiet"
    MISCHGEBIET = "Mischgebiet"
    WOHNGEBIET = "Wohngebiet"
    REINES_WOHNGEBIET = "Reines Wohngebiet"
    KURGEBIET = "Kurgebiet"

@dataclass
class ImmissionsschutzAgentConfig:
    """Konfiguration für ImmissionsschutzAgent"""
    enable_luftqualitaet: bool = True
    enable_laermschutz: bool = True
    enable_ta_luft: bool = True
    enable_ta_laerm: bool = True
    enable_caching: bool = True
    enable_logging: bool = True
    
    min_confidence_threshold: float = 0.6
    max_retries: int = 2
    timeout_seconds: int = 30

@dataclass
class ImmissionsschutzQueryRequest:
    """Query-Request für ImmissionsschutzAgent"""
    query_id: str
    query_text: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Immissionsschutz-spezifisch
    category: Optional[ImmissionsschutzCategory] = None
    schadstoff: Optional[Schadstoff] = None
    gebietstyp: Optional[Gebietstyp] = None
    
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5
    max_results: int = 10

@dataclass
class ImmissionsschutzQueryResponse:
    """Query-Response für ImmissionsschutzAgent"""
    query_id: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    category: Optional[ImmissionsschutzCategory] = None
    
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

# ==========================================
# IMMISSIONSSCHUTZ AGENT
# ==========================================

class ImmissionsschutzAgent:
    """
    Spezialisierter Agent für Immissionsschutz, Luftqualität und Lärmschutz.
    
    Dieser Agent beantwortet Fragen zu:
    - Luftqualität und Schadstoffgrenzwerte
    - Lärmschutz und Lärmgrenzwerte
    - TA Luft (Technische Anleitung zur Reinhaltung der Luft)
    - TA Lärm (Technische Anleitung zum Schutz gegen Lärm)
    - Emissionsberechnungen
    
    Usage:
        >>> agent = ImmissionsschutzAgent()
        >>> request = ImmissionsschutzQueryRequest(
        ...     query_id="12345",
        ...     query_text="Welche Grenzwerte gelten für NO2?"
        ... )
        >>> response = agent.process_query(request)
        >>> print(response.results)
    
    Example Queries:
        - "Welche Grenzwerte gelten für NO2?"
        - "Lärmgrenzwerte für Wohngebiete"
        - "Was regelt die TA Luft?"
        - "Feinstaub PM10 Grenzwerte"
        - "Nachtzeit Lärmschutz"
    """
    
    def __init__(self, config: Optional[ImmissionsschutzAgentConfig] = None):
        """Initialisiere ImmissionsschutzAgent"""
        self.config = config or ImmissionsschutzAgentConfig()
        self.agent_id = str(uuid.uuid4())
        self.name = AGENT_NAME
        self.version = AGENT_VERSION
        self.status = AgentStatus.IDLE if AGENT_SYSTEM_AVAILABLE else "IDLE"
        
        self._init_knowledge_base()
        
        logger.info(f"✅ {self.__class__.__name__} initialisiert (ID: {self.agent_id})")
    
    def _init_knowledge_base(self):
        """Initialisiere Wissensbasis mit Immissionsschutz-Wissen"""
        
        # Luftqualitäts-Grenzwerte (39. BImSchV)
        self.luftqualitaet_grenzwerte = {
            "NO2": {
                "schadstoff": "Stickstoffdioxid (NO2)",
                "jahresgrenzwert": "40 µg/m³",
                "stundengrenzwert": "200 µg/m³ (max. 18 Überschreitungen/Jahr)",
                "quelle": "39. BImSchV",
                "gesundheit": "Atemwegsreizungen, erhöhte Anfälligkeit für Infektionen"
            },
            "PM10": {
                "schadstoff": "Feinstaub PM10",
                "jahresgrenzwert": "40 µg/m³",
                "tagesgrenzwert": "50 µg/m³ (max. 35 Überschreitungen/Jahr)",
                "quelle": "39. BImSchV",
                "gesundheit": "Atemwegs- und Herz-Kreislauf-Erkrankungen"
            },
            "PM2.5": {
                "schadstoff": "Feinstaub PM2.5",
                "jahresgrenzwert": "25 µg/m³",
                "quelle": "39. BImSchV",
                "gesundheit": "Lungenschäden, erhöhtes Krebsrisiko"
            },
            "O3": {
                "schadstoff": "Ozon (O3)",
                "zielwert": "120 µg/m³ (8-Stunden-Mittelwert, max. 25 Tage/Jahr)",
                "informationsschwelle": "180 µg/m³",
                "alarmschwelle": "240 µg/m³",
                "quelle": "39. BImSchV",
                "gesundheit": "Atemwegsreizungen, Kopfschmerzen"
            },
            "SO2": {
                "schadstoff": "Schwefeldioxid (SO2)",
                "stundengrenzwert": "350 µg/m³ (max. 24 Überschreitungen/Jahr)",
                "tagesgrenzwert": "125 µg/m³ (max. 3 Überschreitungen/Jahr)",
                "quelle": "39. BImSchV",
                "gesundheit": "Atemwegsreizungen, Verschlimmerung von Asthma"
            },
        }
        
        # Lärmschutz-Grenzwerte (TA Lärm)
        self.laermschutz_grenzwerte = {
            "Industriegebiet": {
                "gebietstyp": "Industriegebiet",
                "tag": "70 dB(A)",
                "nacht": "70 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Gebiete, die vorwiegend durch Gewerbebetriebe geprägt sind"
            },
            "Gewerbegebiet": {
                "gebietstyp": "Gewerbegebiet",
                "tag": "65 dB(A)",
                "nacht": "50 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Gebiete mit gewerblichen Anlagen"
            },
            "Mischgebiet": {
                "gebietstyp": "Mischgebiet/Dorfgebiet",
                "tag": "60 dB(A)",
                "nacht": "45 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Gebiete mit Wohnen und Gewerbe"
            },
            "Wohngebiet": {
                "gebietstyp": "Allgemeines Wohngebiet",
                "tag": "55 dB(A)",
                "nacht": "40 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Vorwiegend dem Wohnen dienende Gebiete"
            },
            "Reines Wohngebiet": {
                "gebietstyp": "Reines Wohngebiet",
                "tag": "50 dB(A)",
                "nacht": "35 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Ausschließlich dem Wohnen dienende Gebiete"
            },
            "Kurgebiet": {
                "gebietstyp": "Kurgebiet/Krankenhaus",
                "tag": "45 dB(A)",
                "nacht": "35 dB(A)",
                "quelle": "TA Lärm Nr. 6.1",
                "beschreibung": "Gebiete mit besonderem Schutzbedürfnis"
            },
        }
        
        # TA Luft Anforderungen
        self.ta_luft_knowledge = {
            "Genehmigungsverfahren": {
                "titel": "Genehmigungsbedürftige Anlagen nach TA Luft",
                "beschreibung": "Die TA Luft regelt Anforderungen zur Vorsorge gegen schädliche Umwelteinwirkungen durch Luftverunreinigungen für genehmigungsbedürftige Anlagen nach § 4 BImSchG.",
                "anforderungen": [
                    "Emissionsbegrenzungen",
                    "Immissionswerte",
                    "Messung und Überwachung",
                    "Ableitbedingungen (Schornsteinhöhe)"
                ],
                "quelle": "TA Luft 2021"
            },
            "Emissionsgrenzwerte": {
                "titel": "Emissionsgrenzwerte für Anlagen",
                "beschreibung": "Festlegung von Emissionsgrenzwerten für verschiedene Anlagenarten (z.B. Feuerungsanlagen, Müllverbrennungsanlagen)",
                "beispiele": [
                    "Staub: 10-20 mg/m³",
                    "NOx: 100-500 mg/m³",
                    "SO2: 200-400 mg/m³"
                ],
                "quelle": "TA Luft 2021 Nr. 5"
            },
        }
        
        # Keyword-Mappings
        self.keyword_mappings = {
            ImmissionsschutzCategory.LUFTQUALITAET: [
                "luftqualität", "luft", "schadstoff", "no2", "pm10", "pm2.5",
                "ozon", "feinstaub", "luftverschmutzung"
            ],
            ImmissionsschutzCategory.LAERMSCHUTZ: [
                "lärm", "lärmschutz", "geräusch", "schall", "dezibel", "db",
                "nachtruhe", "ruhezeiten"
            ],
            ImmissionsschutzCategory.TA_LUFT: [
                "ta luft", "technische anleitung luft", "emission", "schornstein",
                "ableitung"
            ],
            ImmissionsschutzCategory.TA_LAERM: [
                "ta lärm", "technische anleitung lärm", "lärmgrenzwert"
            ],
            ImmissionsschutzCategory.GRENZWERTE: [
                "grenzwert", "grenzwerte", "limit", "schwellenwert", "zielwert"
            ],
        }
        
        logger.info("✅ Wissensbasis initialisiert")
    
    def _detect_category(self, query_text: str) -> ImmissionsschutzCategory:
        """Erkenne Kategorie aus Query-Text"""
        query_lower = query_text.lower()
        
        scores = {}
        for category, keywords in self.keyword_mappings.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[category] = score
        
        best = max(scores.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0 else ImmissionsschutzCategory.UNBEKANNT
    
    def _search_luftqualitaet(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche Luftqualitäts-Grenzwerte"""
        results = []
        query_lower = query_text.lower()
        
        for schadstoff_key, info in self.luftqualitaet_grenzwerte.items():
            if (schadstoff_key.lower() in query_lower or
                any(word in query_lower for word in info["schadstoff"].lower().split())):
                
                results.append({
                    "schadstoff": info["schadstoff"],
                    "jahresgrenzwert": info.get("jahresgrenzwert", "N/A"),
                    "stundengrenzwert": info.get("stundengrenzwert", "N/A"),
                    "tagesgrenzwert": info.get("tagesgrenzwert", "N/A"),
                    "quelle": info["quelle"],
                    "gesundheit": info.get("gesundheit", "N/A"),
                    "kategorie": "luftqualitaet",
                    "relevanz": 0.9
                })
        
        return results
    
    def _search_laermschutz(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche Lärmschutz-Grenzwerte"""
        results = []
        query_lower = query_text.lower()
        
        for gebiet_key, info in self.laermschutz_grenzwerte.items():
            if (gebiet_key.lower() in query_lower or
                any(word in query_lower for word in info["gebietstyp"].lower().split())):
                
                results.append({
                    "gebietstyp": info["gebietstyp"],
                    "tag": info["tag"],
                    "nacht": info["nacht"],
                    "quelle": info["quelle"],
                    "beschreibung": info["beschreibung"],
                    "kategorie": "laermschutz",
                    "relevanz": 0.9
                })
        
        return results
    
    def _search_ta_luft(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche TA Luft Wissensbasis"""
        results = []
        query_lower = query_text.lower()
        
        for key, info in self.ta_luft_knowledge.items():
            if (key.lower() in query_lower or
                any(word in query_lower for word in info["titel"].lower().split()) or
                any(word in query_lower for word in info["beschreibung"].lower().split())):
                
                results.append({
                    "thema": info["titel"],
                    "beschreibung": info["beschreibung"],
                    "details": info.get("anforderungen", info.get("beispiele", [])),
                    "quelle": info["quelle"],
                    "kategorie": "ta_luft",
                    "relevanz": 0.85
                })
        
        return results
    
    def process_query(self, request: ImmissionsschutzQueryRequest) -> ImmissionsschutzQueryResponse:
        """Verarbeite Immissionsschutz-Anfrage"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Processing query: {request.query_text}")
            
            # Erkenne Kategorie
            category = request.category or self._detect_category(request.query_text)
            logger.info(f"📂 Detected category: {category.value}")
            
            # Sammle Ergebnisse
            results = []
            
            # Luftqualität
            if category in [ImmissionsschutzCategory.LUFTQUALITAET, ImmissionsschutzCategory.GRENZWERTE, ImmissionsschutzCategory.UNBEKANNT]:
                luft_results = self._search_luftqualitaet(request.query_text)
                results.extend(luft_results)
            
            # Lärmschutz
            if category in [ImmissionsschutzCategory.LAERMSCHUTZ, ImmissionsschutzCategory.TA_LAERM, ImmissionsschutzCategory.GRENZWERTE, ImmissionsschutzCategory.UNBEKANNT]:
                laerm_results = self._search_laermschutz(request.query_text)
                results.extend(laerm_results)
            
            # TA Luft
            if category in [ImmissionsschutzCategory.TA_LUFT, ImmissionsschutzCategory.UNBEKANNT]:
                ta_luft_results = self._search_ta_luft(request.query_text)
                results.extend(ta_luft_results)
            
            # Sortiere nach Relevanz
            results.sort(key=lambda x: x.get("relevanz", 0.5), reverse=True)
            results = results[:request.max_results]
            
            # Confidence
            confidence = 0.8 if results else 0.2
            
            # Processing-Zeit
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            response = ImmissionsschutzQueryResponse(
                query_id=request.query_id,
                results=results,
                metadata={
                    "agent_name": self.name,
                    "agent_version": self.version,
                    "category_detected": category.value,
                    "num_results": len(results),
                },
                confidence_score=confidence,
                processing_time_ms=processing_time,
                category=category,
                success=True
            )
            
            logger.info(f"✅ Query processed: {len(results)} results, {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            logger.error(traceback.format_exc())
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return ImmissionsschutzQueryResponse(
                query_id=request.query_id,
                results=[],
                metadata={"agent_name": self.name},
                confidence_score=0.0,
                processing_time_ms=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def query(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """Vereinfachte Query-Methode (Registry-kompatibel)"""
        request = ImmissionsschutzQueryRequest(
            query_id=str(uuid.uuid4()),
            query_text=query_text,
            context=kwargs.get("context", {}),
            max_results=kwargs.get("max_results", 10)
        )
        
        response = self.process_query(request)
        
        return {
            "success": response.success,
            "results": response.results,
            "metadata": response.metadata,
            "confidence": response.confidence_score,
            "processing_time_ms": response.processing_time_ms,
            "error": response.error_message
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Hole Agent-Informationen"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "domain": AGENT_DOMAIN,
            "capabilities": [cap.value if hasattr(cap, "value") else str(cap) for cap in AGENT_CAPABILITIES],
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "categories": [cat.value for cat in ImmissionsschutzCategory],
        }

# ==========================================
# EXAMPLE USAGE
# ==========================================

def main():
    """Beispiel-Verwendung"""
    print("=" * 80)
    print("VERITAS IMMISSIONSSCHUTZ AGENT - DEMO")
    print("=" * 80)
    
    agent = ImmissionsschutzAgent()
    print(f"\n✅ Agent initialisiert: {agent.name} v{agent.version}")
    
    test_queries = [
        "Welche Grenzwerte gelten für NO2?",
        "Lärmgrenzwerte für Wohngebiete",
        "Feinstaub PM10 Grenzwerte",
        "Was regelt die TA Luft?",
    ]
    
    print("\n" + "=" * 80)
    print("TEST QUERIES")
    print("=" * 80)
    
    for i, query_text in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query_text}")
        print(f"{'='*80}")
        
        result = agent.query(query_text)
        
        print(f"Success: {result['success']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Results: {len(result['results'])}")
        
        if result['results']:
            for j, res in enumerate(result['results'][:2], 1):
                print(f"\n  Result {j}:")
                for key, value in res.items():
                    print(f"    {key}: {value}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
