#!/usr/bin/env python3
"""
VERITAS AGENT: RECHTSRECHERCHE
================================

Spezialisierter Agent für Gesetzesrecherche und Rechtsprechung.

HAUPTFUNKTIONEN:
- Gesetzesrecherche (BGB, StGB, GG, etc.)
- Rechtsprechungsrecherche (BGH, BVerfG, BVerwG)
- Kommentarliteratur
- Gesetzesauslegung
- Rechtsgebiets-Identifikation

CAPABILITIES:
- Gesetzestexte abrufen
- Paragraphen erklären
- Rechtsprechung finden
- Gesetzesänderungen nachverfolgen
- Rechtsgebiete zuordnen

INTEGRATION:
- Registriert im AgentRegistry als "RechtsrecherchAgent"
- Domain: AgentDomain.LEGAL
- Capabilities: ["rechtsrecherche", "gesetze", "rechtsprechung", "bgb", "stgb", ...]

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
# RECHTSRECHERCHE CONFIGURATION
# ==========================================

AGENT_DOMAIN = "legal"
AGENT_NAME = "rechtsrecherche_agent"
AGENT_VERSION = "1.0"

AGENT_CAPABILITIES = [
    AgentCapability.QUERY_PROCESSING,
    AgentCapability.DATA_ANALYSIS,
    AgentCapability.DOCUMENT_RETRIEVAL,
]

# ==========================================
# DATA CLASSES & TYPES
# ==========================================

class Rechtsgebiet(Enum):
    """Rechtsgebiete"""
    ZIVILRECHT = "zivilrecht"               # BGB, HGB, etc.
    STRAFRECHT = "strafrecht"               # StGB, StPO, etc.
    OEFFENTLICHESRECHT = "oeffentlichesrecht"  # GG, VwVfG, etc.
    VERWALTUNGSRECHT = "verwaltungsrecht"   # VwGO, etc.
    SOZIALRECHT = "sozialrecht"             # SGB I-XII
    ARBEITSRECHT = "arbeitsrecht"           # ArbGG, KSchG, etc.
    UNBEKANNT = "unbekannt"

class Gesetzestyp(Enum):
    """Gesetzestypen"""
    GRUNDGESETZ = "GG"
    BGB = "BGB"
    STGB = "StGB"
    HGB = "HGB"
    VwVfG = "VwVfG"
    VwGO = "VwGO"
    SGB = "SGB"
    ArbGG = "ArbGG"
    KSCHG = "KSchG"
    BAURECHT = "BauGB"
    UMWELTRECHT = "BImSchG"

class Gerichtstyp(Enum):
    """Gerichtstypen"""
    BVERFG = "BVerfG"     # Bundesverfassungsgericht
    BGH = "BGH"           # Bundesgerichtshof
    BVERWG = "BVerwG"     # Bundesverwaltungsgericht
    BAG = "BAG"           # Bundesarbeitsgericht
    BSG = "BSG"           # Bundessozialgericht
    BFH = "BFH"           # Bundesfinanzhof

@dataclass
class RechtsrecherchAgentConfig:
    """Konfiguration für RechtsrecherchAgent"""
    enable_gesetzesrecherche: bool = True
    enable_rechtsprechung: bool = True
    enable_kommentare: bool = True
    enable_caching: bool = True
    enable_logging: bool = True
    
    min_confidence_threshold: float = 0.6
    max_retries: int = 2
    timeout_seconds: int = 30

@dataclass
class RechtsrecherchQueryRequest:
    """Query-Request für RechtsrecherchAgent"""
    query_id: str
    query_text: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Rechtsrecherche-spezifische Felder
    rechtsgebiet: Optional[Rechtsgebiet] = None
    gesetzestyp: Optional[Gesetzestyp] = None
    
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5
    max_results: int = 10

@dataclass
class RechtsrecherchQueryResponse:
    """Query-Response für RechtsrecherchAgent"""
    query_id: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    rechtsgebiet: Optional[Rechtsgebiet] = None
    gesetze: List[str] = field(default_factory=list)
    
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

# ==========================================
# RECHTSRECHERCH AGENT
# ==========================================

class RechtsrecherchAgent:
    """
    Spezialisierter Agent für Gesetzesrecherche und Rechtsprechung.
    
    Dieser Agent beantwortet Fragen zu:
    - Gesetzestexten (BGB, StGB, GG, VwVfG, etc.)
    - Rechtsprechung (BGH, BVerfG, BVerwG, etc.)
    - Kommentarliteratur
    - Gesetzesauslegung
    - Rechtsgebiets-Zuordnung
    
    Usage:
        >>> agent = RechtsrecherchAgent()
        >>> request = RechtsrecherchQueryRequest(
        ...     query_id="12345",
        ...     query_text="Was bedeutet § 433 BGB?"
        ... )
        >>> response = agent.process_query(request)
        >>> print(response.results)
    
    Example Queries:
        - "Was bedeutet § 433 BGB?"
        - "Welche Rechte hat ein Käufer nach BGB?"
        - "Was ist die Vertragsfreiheit?"
        - "Grundrechte aus dem Grundgesetz"
        - "Wann ist ein Vertrag sittenwidrig?"
    """
    
    def __init__(self, config: Optional[RechtsrecherchAgentConfig] = None):
        """Initialisiere RechtsrecherchAgent"""
        self.config = config or RechtsrecherchAgentConfig()
        self.agent_id = str(uuid.uuid4())
        self.name = AGENT_NAME
        self.version = AGENT_VERSION
        self.status = AgentStatus.IDLE if AGENT_SYSTEM_AVAILABLE else "IDLE"
        
        self._init_knowledge_base()
        
        logger.info(f"✅ {self.__class__.__name__} initialisiert (ID: {self.agent_id})")
    
    def _init_knowledge_base(self):
        """Initialisiere Wissensbasis mit Rechts-Wissen"""
        
        # BGB - Bürgerliches Gesetzbuch
        self.bgb_knowledge = {
            "§ 433 BGB": {
                "titel": "Vertragstypische Pflichten beim Kaufvertrag",
                "beschreibung": "Der Verkäufer verpflichtet sich, dem Käufer die Sache zu übergeben und das Eigentum zu verschaffen. Der Käufer ist verpflichtet, den vereinbarten Kaufpreis zu zahlen.",
                "rechtsgebiet": Rechtsgebiet.ZIVILRECHT,
                "gesetz": "BGB"
            },
            "§ 823 BGB": {
                "titel": "Schadensersatzpflicht",
                "beschreibung": "Wer vorsätzlich oder fahrlässig das Leben, den Körper, die Gesundheit, die Freiheit, das Eigentum oder ein sonstiges Recht eines anderen widerrechtlich verletzt, ist dem anderen zum Ersatz des daraus entstehenden Schadens verpflichtet.",
                "rechtsgebiet": Rechtsgebiet.ZIVILRECHT,
                "gesetz": "BGB"
            },
            "§ 138 BGB": {
                "titel": "Sittenwidriges Rechtsgeschäft; Wucher",
                "beschreibung": "Ein Rechtsgeschäft, das gegen die guten Sitten verstößt, ist nichtig.",
                "rechtsgebiet": Rechtsgebiet.ZIVILRECHT,
                "gesetz": "BGB"
            },
        }
        
        # StGB - Strafgesetzbuch
        self.stgb_knowledge = {
            "§ 212 StGB": {
                "titel": "Totschlag",
                "beschreibung": "Wer einen Menschen tötet, ohne Mörder zu sein, wird als Totschläger mit Freiheitsstrafe nicht unter fünf Jahren bestraft.",
                "rechtsgebiet": Rechtsgebiet.STRAFRECHT,
                "gesetz": "StGB"
            },
            "§ 223 StGB": {
                "titel": "Körperverletzung",
                "beschreibung": "Wer eine andere Person körperlich misshandelt oder an der Gesundheit schädigt, wird mit Freiheitsstrafe bis zu fünf Jahren oder mit Geldstrafe bestraft.",
                "rechtsgebiet": Rechtsgebiet.STRAFRECHT,
                "gesetz": "StGB"
            },
        }
        
        # GG - Grundgesetz
        self.gg_knowledge = {
            "Art. 1 GG": {
                "titel": "Menschenwürde",
                "beschreibung": "Die Würde des Menschen ist unantastbar. Sie zu achten und zu schützen ist Verpflichtung aller staatlichen Gewalt.",
                "rechtsgebiet": Rechtsgebiet.OEFFENTLICHESRECHT,
                "gesetz": "GG"
            },
            "Art. 2 GG": {
                "titel": "Persönliche Freiheitsrechte",
                "beschreibung": "Jeder hat das Recht auf die freie Entfaltung seiner Persönlichkeit, soweit er nicht die Rechte anderer verletzt.",
                "rechtsgebiet": Rechtsgebiet.OEFFENTLICHESRECHT,
                "gesetz": "GG"
            },
            "Art. 3 GG": {
                "titel": "Gleichheit vor dem Gesetz",
                "beschreibung": "Alle Menschen sind vor dem Gesetz gleich.",
                "rechtsgebiet": Rechtsgebiet.OEFFENTLICHESRECHT,
                "gesetz": "GG"
            },
        }
        
        # Rechtsprechung
        self.rechtsprechung_knowledge = {
            "BGH - Haustürgeschäfte": {
                "gericht": Gerichtstyp.BGH,
                "beschreibung": "Rechtsprechung zu Widerrufsrechten bei Haustürgeschäften nach BGB",
                "relevante_paragraphen": ["§ 312 BGB", "§ 355 BGB"],
                "rechtsgebiet": Rechtsgebiet.ZIVILRECHT
            },
            "BVerfG - Grundrechte": {
                "gericht": Gerichtstyp.BVERFG,
                "beschreibung": "Grundsatzentscheidungen zu Grundrechten aus dem Grundgesetz",
                "relevante_paragraphen": ["Art. 1 GG", "Art. 2 GG", "Art. 3 GG"],
                "rechtsgebiet": Rechtsgebiet.OEFFENTLICHESRECHT
            },
        }
        
        # Keyword-Mappings
        self.keyword_mappings = {
            Rechtsgebiet.ZIVILRECHT: [
                "bgb", "kaufvertrag", "vertrag", "schuldrecht", "eigentum",
                "schadensersatz", "vertragsrecht", "zivilrecht", "privatrecht"
            ],
            Rechtsgebiet.STRAFRECHT: [
                "stgb", "strafe", "straftat", "körperverletzung", "totschlag",
                "mord", "diebstahl", "strafrecht"
            ],
            Rechtsgebiet.OEFFENTLICHESRECHT: [
                "grundgesetz", "gg", "grundrechte", "menschenwürde", "freiheit",
                "gleichheit", "öffentliches recht", "verfassungsrecht"
            ],
            Rechtsgebiet.VERWALTUNGSRECHT: [
                "verwaltungsrecht", "verwaltungsakt", "vwvfg", "vwgo",
                "verwaltungsgericht"
            ],
            Rechtsgebiet.SOZIALRECHT: [
                "sozialrecht", "sgb", "sozialversicherung", "rente",
                "arbeitslosengeld", "sozialhilfe"
            ],
            Rechtsgebiet.ARBEITSRECHT: [
                "arbeitsrecht", "kündigung", "kündigungsschutz", "arbeitsgericht",
                "arbeitsvertrag", "betriebsrat"
            ],
        }
        
        logger.info("✅ Wissensbasis initialisiert")
    
    def _detect_rechtsgebiet(self, query_text: str) -> Rechtsgebiet:
        """Erkenne Rechtsgebiet aus Query-Text"""
        query_lower = query_text.lower()
        
        scores = {}
        for rechtsgebiet, keywords in self.keyword_mappings.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[rechtsgebiet] = score
        
        best = max(scores.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0 else Rechtsgebiet.UNBEKANNT
    
    def _search_bgb(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche BGB-Wissensbasis"""
        results = []
        query_lower = query_text.lower()
        
        for paragraph, info in self.bgb_knowledge.items():
            if (paragraph.lower() in query_lower or
                any(word in query_lower for word in info["titel"].lower().split()) or
                any(word in query_lower for word in info["beschreibung"].lower().split())):
                
                results.append({
                    "paragraph": paragraph,
                    "titel": info["titel"],
                    "beschreibung": info["beschreibung"],
                    "gesetz": info["gesetz"],
                    "rechtsgebiet": info["rechtsgebiet"].value,
                    "relevanz": 0.9
                })
        
        return results
    
    def _search_stgb(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche StGB-Wissensbasis"""
        results = []
        query_lower = query_text.lower()
        
        for paragraph, info in self.stgb_knowledge.items():
            if (paragraph.lower() in query_lower or
                any(word in query_lower for word in info["titel"].lower().split()) or
                any(word in query_lower for word in info["beschreibung"].lower().split())):
                
                results.append({
                    "paragraph": paragraph,
                    "titel": info["titel"],
                    "beschreibung": info["beschreibung"],
                    "gesetz": info["gesetz"],
                    "rechtsgebiet": info["rechtsgebiet"].value,
                    "relevanz": 0.9
                })
        
        return results
    
    def _search_gg(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche GG-Wissensbasis"""
        results = []
        query_lower = query_text.lower()
        
        for artikel, info in self.gg_knowledge.items():
            if (artikel.lower() in query_lower or
                any(word in query_lower for word in info["titel"].lower().split()) or
                any(word in query_lower for word in info["beschreibung"].lower().split())):
                
                results.append({
                    "artikel": artikel,
                    "titel": info["titel"],
                    "beschreibung": info["beschreibung"],
                    "gesetz": info["gesetz"],
                    "rechtsgebiet": info["rechtsgebiet"].value,
                    "relevanz": 0.9
                })
        
        return results
    
    def _search_rechtsprechung(self, query_text: str) -> List[Dict[str, Any]]:
        """Durchsuche Rechtsprechungs-Wissensbasis"""
        results = []
        query_lower = query_text.lower()
        
        for case_name, info in self.rechtsprechung_knowledge.items():
            if (case_name.lower() in query_lower or
                any(word in query_lower for word in info["beschreibung"].lower().split())):
                
                results.append({
                    "case": case_name,
                    "gericht": info["gericht"].value,
                    "beschreibung": info["beschreibung"],
                    "relevante_paragraphen": info["relevante_paragraphen"],
                    "rechtsgebiet": info["rechtsgebiet"].value,
                    "relevanz": 0.85
                })
        
        return results
    
    def process_query(self, request: RechtsrecherchQueryRequest) -> RechtsrecherchQueryResponse:
        """Verarbeite Rechtsrecherch-Anfrage"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Processing query: {request.query_text}")
            
            # Erkenne Rechtsgebiet
            rechtsgebiet = request.rechtsgebiet or self._detect_rechtsgebiet(request.query_text)
            logger.info(f"📂 Detected Rechtsgebiet: {rechtsgebiet.value}")
            
            # Sammle Ergebnisse
            results = []
            gesetze = []
            
            # BGB-Suche
            if rechtsgebiet in [Rechtsgebiet.ZIVILRECHT, Rechtsgebiet.UNBEKANNT]:
                bgb_results = self._search_bgb(request.query_text)
                results.extend(bgb_results)
                if bgb_results:
                    gesetze.append("BGB")
            
            # StGB-Suche
            if rechtsgebiet in [Rechtsgebiet.STRAFRECHT, Rechtsgebiet.UNBEKANNT]:
                stgb_results = self._search_stgb(request.query_text)
                results.extend(stgb_results)
                if stgb_results:
                    gesetze.append("StGB")
            
            # GG-Suche
            if rechtsgebiet in [Rechtsgebiet.OEFFENTLICHESRECHT, Rechtsgebiet.UNBEKANNT]:
                gg_results = self._search_gg(request.query_text)
                results.extend(gg_results)
                if gg_results:
                    gesetze.append("GG")
            
            # Rechtsprechungs-Suche
            rechtsprechung_results = self._search_rechtsprechung(request.query_text)
            results.extend(rechtsprechung_results)
            
            # Sortiere nach Relevanz
            results.sort(key=lambda x: x.get("relevanz", 0.5), reverse=True)
            results = results[:request.max_results]
            
            # Confidence
            confidence = 0.8 if results else 0.2
            
            # Processing-Zeit
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            response = RechtsrecherchQueryResponse(
                query_id=request.query_id,
                results=results,
                metadata={
                    "agent_name": self.name,
                    "agent_version": self.version,
                    "rechtsgebiet_detected": rechtsgebiet.value,
                    "num_results": len(results),
                },
                confidence_score=confidence,
                processing_time_ms=processing_time,
                rechtsgebiet=rechtsgebiet,
                gesetze=gesetze,
                success=True
            )
            
            logger.info(f"✅ Query processed: {len(results)} results, {processing_time}ms")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            logger.error(traceback.format_exc())
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return RechtsrecherchQueryResponse(
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
        request = RechtsrecherchQueryRequest(
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
            "rechtsgebiete": [rg.value for rg in Rechtsgebiet],
        }

# ==========================================
# EXAMPLE USAGE
# ==========================================

def main():
    """Beispiel-Verwendung"""
    print("=" * 80)
    print("VERITAS RECHTSRECHERCH AGENT - DEMO")
    print("=" * 80)
    
    agent = RechtsrecherchAgent()
    print(f"\n✅ Agent initialisiert: {agent.name} v{agent.version}")
    
    test_queries = [
        "Was bedeutet § 433 BGB?",
        "Grundrechte aus dem Grundgesetz",
        "Schadensersatz nach BGB",
        "Körperverletzung StGB",
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
