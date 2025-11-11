#!/usr/bin/env python3
"""
VERITAS AGENT: VERWALTUNGSRECHT
================================

Spezialisierter Agent für Verwaltungsrecht, Baurecht und Genehmigungsverfahren.

HAUPTFUNKTIONEN:
- Baurecht und Baugenehmigungen
- Verwaltungsverfahrensrecht
- Immissionsschutzrecht (Verwaltungsaspekte)
- Planungsrecht und Raumordnung
- Umweltrecht (Verwaltungsverfahren)

CAPABILITIES:
- Verwaltungsrechtliche Einordnung von Anfragen
- Baurechts-Recherche (BauGB, BauNVO, LBO)
- Genehmigungsverfahren und Zuständigkeiten
- Verwaltungsakt-Prüfung
- Planungsrecht-Analyse

INTEGRATION:
- Registriert im AgentRegistry als "VerwaltungsrechtAgent"
- Domain: AgentDomain.LEGAL
- Capabilities: ["verwaltungsrecht", "baurecht", "baugenehmigung", "planungsrecht",
                 "immissionsschutzrecht", "verwaltungsverfahren", "umweltrecht"]

Author: VERITAS Development Team
Date: 2025-10-16
Version: 1.0 (Production)
"""

import asyncio
import json
import logging
import os
import sys
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

# VERITAS Core Imports
try:
    from backend.agents.veritas_api_agent_registry import AgentCapability, AgentStatus, get_agent_registry

    AGENT_SYSTEM_AVAILABLE = True
except ImportError as e:
    AGENT_SYSTEM_AVAILABLE = False
    logging.warning(f"⚠️ Agent System nicht verfügbar: {e}")

logger = logging.getLogger(__name__)

# ==========================================
# VERWALTUNGSRECHT CONFIGURATION
# ==========================================

AGENT_DOMAIN = "legal"
AGENT_NAME = "verwaltungsrecht_agent"
AGENT_VERSION = "1.0"

# Capabilities dieses Agents
AGENT_CAPABILITIES = [
    AgentCapability.QUERY_PROCESSING,
    AgentCapability.DATA_ANALYSIS,
    AgentCapability.DOCUMENT_RETRIEVAL,
]

# ==========================================
# DATA CLASSES & TYPES
# ==========================================


class VerwaltungsrechtCategory(Enum):
    """Kategorien des Verwaltungsrechts"""

    BAURECHT = "baurecht"  # Baurecht (BauGB, BauNVO, LBO)
    IMMISSIONSSCHUTZRECHT = "immissionsschutzrecht"  # Immissionsschutzrecht (BImSchG)
    PLANUNGSRECHT = "planungsrecht"  # Raumordnung und Bauleitplanung
    VERWALTUNGSVERFAHREN = "verwaltungsverfahren"  # VwVfG, Verwaltungsakte
    UMWELTRECHT = "umweltrecht"  # Umweltverwaltungsrecht
    GENEHMIGUNGSRECHT = "genehmigungsrecht"  # Genehmigungsverfahren
    GEWERBERECHT = "gewerberecht"  # Gewerberecht
    UNBEKANNT = "unbekannt"


class Rechtsquelle(Enum):
    """Verfügbare Rechtsquellen"""

    BAUGB = "BauGB"  # Baugesetzbuch
    BAUNVO = "BauNVO"  # Baunutzungsverordnung
    LBO = "LBO"  # Landesbauordnung
    BIMSCHG = "BImSchG"  # Bundes-Immissionsschutzgesetz
    VWVFG = "VwVfG"  # Verwaltungsverfahrensgesetz
    ROG = "ROG"  # Raumordnungsgesetz
    BNATSCHG = "BNatSchG"  # Bundesnaturschutzgesetz
    WHG = "WHG"  # Wasserhaushaltsgesetz
    KREISLAUFWIRTSCHAFTSG = "KrWG"  # Kreislaufwirtschaftsgesetz
    GEWO = "GewO"  # Gewerbeordnung


@dataclass
class VerwaltungsrechtAgentConfig:
    """Konfiguration für VerwaltungsrechtAgent"""

    enable_baurecht: bool = True
    enable_immissionsschutzrecht: bool = True
    enable_planungsrecht: bool = True
    enable_verwaltungsverfahren: bool = True
    enable_caching: bool = True
    enable_logging: bool = True

    # Quality & Performance Settings
    min_confidence_threshold: float = 0.6
    max_retries: int = 2
    timeout_seconds: int = 30


@dataclass
class VerwaltungsrechtQueryRequest:
    """Query-Request für VerwaltungsrechtAgent"""

    query_id: str
    query_text: str
    context: Dict[str, Any] = field(default_factory=dict)

    # Verwaltungsrecht-spezifische Felder
    category: Optional[VerwaltungsrechtCategory] = None
    rechtsquelle: Optional[Rechtsquelle] = None
    bundesland: Optional[str] = None  # Für landesspezifisches Recht (z.B. LBO Bayern)

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    priority: int = 5
    max_results: int = 10


@dataclass
class VerwaltungsrechtQueryResponse:
    """Query-Response für VerwaltungsrechtAgent"""

    query_id: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Qualitäts-Metriken
    confidence_score: float = 0.0
    processing_time_ms: int = 0
    category: Optional[VerwaltungsrechtCategory] = None
    rechtsquellen: List[Rechtsquelle] = field(default_factory=list)

    # Status
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# ==========================================
# VERWALTUNGSRECHT AGENT
# ==========================================


class VerwaltungsrechtAgent:
    """
    Spezialisierter Agent für Verwaltungsrecht, Baurecht und Genehmigungsverfahren.

    Dieser Agent beantwortet Fragen zu:
    - Baurecht (BauGB, BauNVO, Landesbauordnungen)
    - Immissionsschutzrecht (BImSchG, TA Luft, TA Lärm)
    - Planungsrecht (Bauleitplanung, Raumordnung)
    - Verwaltungsverfahrensrecht (VwVfG)
    - Genehmigungsverfahren (Baugenehmigung, immissionsschutzrechtliche Genehmigung)

    Usage:
        >>> agent = VerwaltungsrechtAgent()
        >>> request = VerwaltungsrechtQueryRequest(
        ...     query_id="12345",
        ...     query_text="Welche Unterlagen brauche ich für eine Baugenehmigung?"
        ... )
        >>> response = agent.process_query(request)
        >>> print(response.results)

    Example Queries:
        - "Welche Unterlagen brauche ich für eine Baugenehmigung?"
        - "Was bedeutet § 34 BauGB?"
        - "Welche Abstandsflächen gelten in Bayern?"
        - "Wie läuft ein Baugenehmigungsverfahren ab?"
        - "Was ist eine immissionsschutzrechtliche Genehmigung?"
    """

    def __init__(self, config: Optional[VerwaltungsrechtAgentConfig] = None):
        """
        Initialisiere VerwaltungsrechtAgent.

        Args:
            config: Agent-Konfiguration (optional)
        """
        self.config = config or VerwaltungsrechtAgentConfig()
        self.agent_id = str(uuid.uuid4())
        self.name = AGENT_NAME
        self.version = AGENT_VERSION
        self.status = AgentStatus.IDLE if AGENT_SYSTEM_AVAILABLE else "IDLE"

        # Wissensbasis initialisieren
        self._init_knowledge_base()

        logger.info(f"✅ {self.__class__.__name__} initialisiert (ID: {self.agent_id})")

    def _init_knowledge_base(self):
        """Initialisiere Wissensbasis mit Verwaltungsrecht-Wissen"""

        # Baurecht: Häufige Paragraphen
        self.baurecht_knowledge = {
            "§ 29 BauGB": {
                "titel": "Bauliche Nutzung",
                "beschreibung": "Begriff der baulichen Nutzung, Erfordernis der Baugenehmigung",
                "kategorie": VerwaltungsrechtCategory.BAURECHT,
                "rechtsquelle": Rechtsquelle.BAUGB,
            },
            "§ 30 BauGB": {
                "titel": "Zulässigkeit von Vorhaben im Bereich eines Bebauungsplans",
                "beschreibung": "Vorhaben sind im Geltungsbereich eines qualifizierten Bebauungsplans zulässig",
                "kategorie": VerwaltungsrechtCategory.BAURECHT,
                "rechtsquelle": Rechtsquelle.BAUGB,
            },
            "§ 34 BauGB": {
                "titel": "Zulässigkeit von Vorhaben innerhalb der im Zusammenhang bebauten Ortsteile",
                "beschreibung": "Einfügen in die Eigenart der näheren Umgebung (Art, Maß, Bauweise, überbaute Grundstücksfläche)",
                "kategorie": VerwaltungsrechtCategory.BAURECHT,
                "rechtsquelle": Rechtsquelle.BAUGB,
            },
            "§ 35 BauGB": {
                "titel": "Bauen im Außenbereich",
                "beschreibung": "Privilegierte und sonstige Vorhaben im Außenbereich",
                "kategorie": VerwaltungsrechtCategory.BAURECHT,
                "rechtsquelle": Rechtsquelle.BAUGB,
            },
        }

        # Immissionsschutzrecht
        self.immissionsschutzrecht_knowledge = {
            "§ 5 BImSchG": {
                "titel": "Pflichten der Betreiber genehmigungsbedürftiger Anlagen",
                "beschreibung": "Vorsorgepflicht, Schutz vor schädlichen Umwelteinwirkungen",
                "kategorie": VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT,
                "rechtsquelle": Rechtsquelle.BIMSCHG,
            },
            "§ 22 BImSchG": {
                "titel": "Pflichten nicht genehmigungsbedürftiger Anlagen",
                "beschreibung": "Vermeidung schädlicher Umwelteinwirkungen",
                "kategorie": VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT,
                "rechtsquelle": Rechtsquelle.BIMSCHG,
            },
        }

        # Genehmigungsverfahren
        self.genehmigungsverfahren_knowledge = {
            "Baugenehmigung": {
                "beschreibung": "Erforderliche Unterlagen: Bauantrag, Bauzeichnungen, Baubeschreibung, Berechnungen (Wohnfläche, umbauter Raum), Lageplan, Nachweise (Standsicherheit, Brandschutz, Wärmeschutz)",
                "kategorie": VerwaltungsrechtCategory.GENEHMIGUNGSRECHT,
                "zuständigkeit": "Bauaufsichtsbehörde (Landratsamt / Stadt)",
                "rechtsgrundlage": "Landesbauordnung (z.B. BayBO, LBO BW)",
            },
            "Immissionsschutzrechtliche Genehmigung": {
                "beschreibung": "Nach § 4 BImSchG für genehmigungsbedürftige Anlagen (4. BImSchV). Prüfung der Vorsorgepflicht nach § 5 BImSchG.",
                "kategorie": VerwaltungsrechtCategory.GENEHMIGUNGSRECHT,
                "zuständigkeit": "Immissionsschutzbehörde (je nach Bundesland)",
                "rechtsgrundlage": "BImSchG, 4. BImSchV",
            },
        }

        # Keyword-Mappings für schnelle Kategorisierung
        self.keyword_mappings = {
            VerwaltungsrechtCategory.BAURECHT: [
                "baurecht",
                "baugenehmigung",
                "bauantrag",
                "bebauungsplan",
                "abstandsflächen",
                "baugesetzbuch",
                "baugb",
                "baunvo",
                "lbo",
                "bauordnung",
                "bauvorhaben",
                "bauland",
                "außenbereich",
            ],
            VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT: [
                "immissionsschutz",
                "bimschg",
                "emissionen",
                "lärm",
                "luftqualität",
                "ta luft",
                "ta lärm",
                "anlagengenehmigung",
                "umwelteinwirkungen",
            ],
            VerwaltungsrechtCategory.PLANUNGSRECHT: [
                "bebauungsplan",
                "flächennutzungsplan",
                "bauleitplanung",
                "raumordnung",
                "regionalplan",
                "planfeststellung",
            ],
            VerwaltungsrechtCategory.VERWALTUNGSVERFAHREN: [
                "verwaltungsakt",
                "widerspruch",
                "anhörung",
                "verwaltungsverfahren",
                "vwvfg",
                "bescheid",
                "rechtsmittel",
            ],
            VerwaltungsrechtCategory.GENEHMIGUNGSRECHT: [
                "genehmigung",
                "genehmigungsverfahren",
                "erlaubnis",
                "zustimmung",
                "unterlagen",
                "antrag",
            ],
            VerwaltungsrechtCategory.UMWELTRECHT: [
                "umweltrecht",
                "naturschutz",
                "wasserschutz",
                "bodenschutz",
                "umweltverträglichkeit",
                "uvp",
            ],
        }

        logger.info("✅ Wissensbasis initialisiert")

    def _detect_category(self, query_text: str) -> VerwaltungsrechtCategory:
        """
        Erkenne die Kategorie der Anfrage basierend auf Keywords.

        Args:
            query_text: Anfrage-Text

        Returns:
            Erkannte Kategorie
        """
        query_lower = query_text.lower()

        # Score jede Kategorie
        scores = {}
        for category, keywords in self.keyword_mappings.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            scores[category] = score

        # Finde beste Kategorie
        best_category = max(scores.items(), key=lambda x: x[1])

        if best_category[1] > 0:
            return best_category[0]
        else:
            return VerwaltungsrechtCategory.UNBEKANNT

    def _search_baurecht(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Durchsuche Baurecht-Wissensbasis.

        Args:
            query_text: Suchtext

        Returns:
            Gefundene Ergebnisse
        """
        results = []
        query_lower = query_text.lower()

        for paragraph, info in self.baurecht_knowledge.items():
            # Suche nach Paragraph-Nummer oder Schlüsselwörtern im Titel/Beschreibung
            if (
                paragraph.lower() in query_lower
                or any(word in query_lower for word in info["titel"].lower().split())
                or any(word in query_lower for word in info["beschreibung"].lower().split())
            ):
                results.append(
                    {
                        "paragraph": paragraph,
                        "titel": info["titel"],
                        "beschreibung": info["beschreibung"],
                        "rechtsquelle": info["rechtsquelle"].value,
                        "kategorie": info["kategorie"].value,
                        "relevanz": 0.9,  # Hohe Relevanz für direkte Treffer
                    }
                )

        return results

    def _search_immissionsschutzrecht(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Durchsuche Immissionsschutzrecht-Wissensbasis.

        Args:
            query_text: Suchtext

        Returns:
            Gefundene Ergebnisse
        """
        results = []
        query_lower = query_text.lower()

        for paragraph, info in self.immissionsschutzrecht_knowledge.items():
            if (
                paragraph.lower() in query_lower
                or any(word in query_lower for word in info["titel"].lower().split())
                or any(word in query_lower for word in info["beschreibung"].lower().split())
            ):
                results.append(
                    {
                        "paragraph": paragraph,
                        "titel": info["titel"],
                        "beschreibung": info["beschreibung"],
                        "rechtsquelle": info["rechtsquelle"].value,
                        "kategorie": info["kategorie"].value,
                        "relevanz": 0.9,
                    }
                )

        return results

    def _search_genehmigungsverfahren(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Durchsuche Genehmigungsverfahren-Wissensbasis.

        Args:
            query_text: Suchtext

        Returns:
            Gefundene Ergebnisse
        """
        results = []
        query_lower = query_text.lower()

        for verfahren_name, info in self.genehmigungsverfahren_knowledge.items():
            if verfahren_name.lower() in query_lower or any(word in query_lower for word in verfahren_name.lower().split()):
                results.append(
                    {
                        "verfahren": verfahren_name,
                        "beschreibung": info["beschreibung"],
                        "zuständigkeit": info["zuständigkeit"],
                        "rechtsgrundlage": info["rechtsgrundlage"],
                        "kategorie": info["kategorie"].value,
                        "relevanz": 0.85,
                    }
                )

        return results

    def process_query(self, request: VerwaltungsrechtQueryRequest) -> VerwaltungsrechtQueryResponse:
        """
        Verarbeite eine Verwaltungsrecht-Anfrage.

        Args:
            request: Query-Request

        Returns:
            Query-Response mit Ergebnissen
        """
        start_time = datetime.now()

        try:
            logger.info(f"🔍 Processing query: {request.query_text}")

            # Erkenne Kategorie
            category = request.category or self._detect_category(request.query_text)
            logger.info(f"📂 Detected category: {category.value}")

            # Sammle Ergebnisse aus verschiedenen Quellen
            results = []
            rechtsquellen = []

            # Durchsuche Baurecht
            if category in [VerwaltungsrechtCategory.BAURECHT, VerwaltungsrechtCategory.UNBEKANNT]:
                baurecht_results = self._search_baurecht(request.query_text)
                results.extend(baurecht_results)
                if baurecht_results:
                    rechtsquellen.append(Rechtsquelle.BAUGB)

            # Durchsuche Immissionsschutzrecht
            if category in [VerwaltungsrechtCategory.IMMISSIONSSCHUTZRECHT, VerwaltungsrechtCategory.UNBEKANNT]:
                imsch_results = self._search_immissionsschutzrecht(request.query_text)
                results.extend(imsch_results)
                if imsch_results:
                    rechtsquellen.append(Rechtsquelle.BIMSCHG)

            # Durchsuche Genehmigungsverfahren
            if category in [VerwaltungsrechtCategory.GENEHMIGUNGSRECHT, VerwaltungsrechtCategory.UNBEKANNT]:
                genehmigung_results = self._search_genehmigungsverfahren(request.query_text)
                results.extend(genehmigung_results)

            # Sortiere nach Relevanz
            results.sort(key=lambda x: x.get("relevanz", 0.5), reverse=True)

            # Begrenze auf max_results
            results = results[: request.max_results]

            # Berechne Confidence Score
            confidence = 0.8 if results else 0.2

            # Processing-Zeit
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Erstelle Response
            response = VerwaltungsrechtQueryResponse(
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
                rechtsquellen=rechtsquellen,
                success=True,
            )

            logger.info(f"✅ Query processed successfully: {len(results)} results, {processing_time}ms")
            return response

        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            logger.error(traceback.format_exc())

            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            return VerwaltungsrechtQueryResponse(
                query_id=request.query_id,
                results=[],
                metadata={"agent_name": self.name},
                confidence_score=0.0,
                processing_time_ms=processing_time,
                success=False,
                error_message=str(e),
            )

    def query(self, query_text: str, **kwargs) -> Dict[str, Any]:
        """
        Vereinfachte Query-Methode (für Registry-Kompatibilität).

        Args:
            query_text: Anfrage-Text
            **kwargs: Zusätzliche Parameter

        Returns:
            Ergebnis-Dict
        """
        request = VerwaltungsrechtQueryRequest(
            query_id=str(uuid.uuid4()),
            query_text=query_text,
            context=kwargs.get("context", {}),
            max_results=kwargs.get("max_results", 10),
        )

        response = self.process_query(request)

        return {
            "success": response.success,
            "results": response.results,
            "metadata": response.metadata,
            "confidence": response.confidence_score,
            "processing_time_ms": response.processing_time_ms,
            "error": response.error_message,
        }

    def get_info(self) -> Dict[str, Any]:
        """
        Hole Agent-Informationen.

        Returns:
            Agent-Info-Dict
        """
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "domain": AGENT_DOMAIN,
            "capabilities": [cap.value if hasattr(cap, "value") else str(cap) for cap in AGENT_CAPABILITIES],
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "categories": [cat.value for cat in VerwaltungsrechtCategory],
            "rechtsquellen": [rq.value for rq in Rechtsquelle],
        }


# ==========================================
# EXAMPLE USAGE & TESTING
# ==========================================


def main():
    """Beispiel-Verwendung des VerwaltungsrechtAgent"""

    print("=" * 80)
    print("VERITAS VERWALTUNGSRECHT AGENT - DEMO")
    print("=" * 80)

    # Initialisiere Agent
    agent = VerwaltungsrechtAgent()
    print(f"\n✅ Agent initialisiert: {agent.name} v{agent.version}")

    # Test-Queries
    test_queries = [
        "Welche Unterlagen brauche ich für eine Baugenehmigung?",
        "Was bedeutet § 34 BauGB?",
        "Welche Pflichten hat ein Betreiber nach § 5 BImSchG?",
        "Was ist eine immissionsschutzrechtliche Genehmigung?",
    ]

    print("\n" + "=" * 80)
    print("TEST QUERIES")
    print("=" * 80)

    for i, query_text in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Query {i}: {query_text}")
        print(f"{'=' * 80}")

        request = VerwaltungsrechtQueryRequest(query_id=f"test_{i}", query_text=query_text)

        response = agent.process_query(request)

        print(f"Category: {response.category.value if response.category else 'N / A'}")
        print(f"Confidence: {response.confidence_score:.2f}")
        print(f"Processing Time: {response.processing_time_ms}ms")
        print(f"Results: {len(response.results)}")

        if response.results:
            print("\nTop Results:")
            for j, result in enumerate(response.results[:3], 1):
                print(f"\n  Result {j}:")
                for key, value in result.items():
                    print(f"    {key}: {value}")

    print("\n" + "=" * 80)
    print("AGENT INFO")
    print("=" * 80)
    info = agent.get_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    main()
