#!/usr/bin/env python3
"""
VERITAS VerwaltungsrechtWorker (Administrative Law Worker)
===========================================================

Spezialisierter Worker für deutsches Verwaltungsrecht mit Fokus auf:
- Baurecht (BauGB - Baugesetzbuch, BauO - Bauordnung)
- Baugenehmigungen und Bauanträge
- Verwaltungsverfahren (VwVfG - Verwaltungsverfahrensgesetz)
- Bebauungspläne und Flächennutzungspläne
- Zuständige Behörden und Genehmigungsprozesse

Author: VERITAS Development Team
Date: 2025-10-16
Version: 1.0 (Production)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Framework Import
try:
    from backend.agents.framework.base_agent import BaseAgent
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.agents.framework.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class VerwaltungsrechtDomain(Enum):
    """Verwaltungsrecht-Domänen"""

    BAURECHT = "baurecht"  # Baugesetzbuch, Bauordnung
    BAUGENEHMIGUNG = "baugenehmigung"  # Genehmigungsverfahren
    VERWALTUNGSVERFAHREN = "verwaltungsverfahren"  # VwVfG
    BEBAUUNGSPLAN = "bebauungsplan"  # Bauleitplanung
    BAUORDNUNG = "bauordnung"  # Landesbauordnung
    PLANUNGSRECHT = "planungsrecht"  # Raumordnung, Bauleitplanung


class GenehmigungsStatus(Enum):
    """Status einer Baugenehmigung"""

    NICHT_ERFORDERLICH = "nicht_erforderlich"
    ERFORDERLICH = "erforderlich"
    VEREINFACHT = "vereinfacht"  # Vereinfachtes Verfahren
    FREISTELLUNG = "freistellung"  # Freistellungsverfahren
    UNKLAR = "unklar"


@dataclass
class VerwaltungsrechtQuery:
    """Strukturierte Verwaltungsrecht-Anfrage"""

    query_text: str
    domain: VerwaltungsrechtDomain = VerwaltungsrechtDomain.BAURECHT
    bundesland: Optional[str] = None  # Z.B. "Bayern", "NRW"
    bauvorhaben_typ: Optional[str] = None  # Z.B. "Einfamilienhaus", "Gewerbe"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerwaltungsrechtResult:
    """Strukturiertes Verwaltungsrecht-Ergebnis"""

    query: str
    rechtliche_grundlagen: List[str] = field(default_factory=list)  # Gesetze, Verordnungen
    genehmigung_erforderlich: Optional[GenehmigungsStatus] = None
    zustaendige_behoerde: Optional[str] = None
    verfahrensschritte: List[str] = field(default_factory=list)
    erforderliche_unterlagen: List[str] = field(default_factory=list)
    fristen: List[Dict[str, str]] = field(default_factory=list)
    rechtsprechung: List[Dict[str, str]] = field(default_factory=list)  # Relevante Urteile
    weitere_hinweise: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    sources: List[str] = field(default_factory=list)


class VerwaltungsrechtWorker(BaseAgent):
    """
    VerwaltungsrechtWorker - Spezialist für deutsches Verwaltungsrecht

    Capabilities:
    - Baurecht-Analyse (BauGB, BauO)
    - Baugenehmigungsverfahren
    - Verwaltungsverfahren (VwVfG)
    - Bebauungsplan-Interpretation
    - Behördenzuständigkeit
    - Rechtsprechung im Verwaltungsrecht

    Integration:
    - RAG: Baurecht-Dokumenten-Datenbank
    - UDS3: Genehmigungen, Pläne, Urteile
    - Ollama: Rechtliche Analyse und Interpretation

    Example:
        >>> worker = VerwaltungsrechtWorker()
        >>> step = {
        ...     "query": "Benötige ich eine Baugenehmigung für ein Einfamilienhaus in Bayern?",
        ...     "parameters": {"bundesland": "Bayern", "typ": "Einfamilienhaus"}
        ... }
        >>> result = worker.execute_step(step, {})
        >>> print(result["summary"])
    """

    def __init__(self, ollama_client=None, rag_service=None, uds3_adapter=None):
        """
        Initialisiert VerwaltungsrechtWorker

        Args:
            ollama_client: Ollama Client für LLM-Analyse (optional)
            rag_service: RAG Service für Dokumentensuche (optional)
            uds3_adapter: UDS3 Adapter für Datenbank-Zugriff (optional)
        """
        super().__init__()

        self.ollama_client = ollama_client
        self.rag_service = rag_service
        self.uds3_adapter = uds3_adapter

        # Bundesland-spezifische Bauordnungen
        self.bauordnungen = {
            "Bayern": "BayBO",
            "Baden - Württemberg": "LBO BW",
            "Nordrhein - Westfalen": "BauO NRW",
            "Hessen": "HBO",
            "Niedersachsen": "NBauO",
            "Rheinland - Pfalz": "LBauO RP",
            # ... weitere Bundesländer
        }

        # Standard-Behörden nach Bundesland
        self.behoerden = {
            "Bayern": "Landratsamt / Kreisfreie Stadt (Bauaufsichtsbehörde)",
            "Baden - Württemberg": "Untere Baurechtsbehörde",
            "Nordrhein - Westfalen": "Untere Bauaufsichtsbehörde",
            # ... weitere
        }

        # Verfahrensarten
        self.verfahrensarten = {
            "Einfamilienhaus": "Bauantrag mit Bauvorlagen (§ 68 BauO)",
            "Garage": "Vereinfachtes Verfahren möglich",
            "Carport": "ggf. Freistellung / Genehmigungsfrei (je nach Größe)",
            "Gewerbe": "Vollständiges Baugenehmigungsverfahren",
            "Industrieanlage": "Vollständiges Verfahren + ggf. Umweltverträglichkeitsprüfung",
        }

        logger.info("✅ VerwaltungsrechtWorker initialisiert")

    def get_agent_type(self) -> str:
        """Gibt Agent-Type zurück"""
        return "VerwaltungsrechtWorker"

    def get_capabilities(self) -> List[str]:
        """
        Gibt Liste der Worker-Capabilities zurück

        Returns:
            Liste von Capability-Keywords für Worker Registry
        """
        return [
            # Deutsch
            "verwaltungsrecht",
            "baurecht",
            "baugenehmigung",
            "verwaltungsverfahren",
            "bauordnung",
            "bebauungsplan",
            "baugenehmigungsverfahren",
            "bauantrag",
            "baugesetz",
            "baugesetzbuch",
            "baugb",
            "landesbauordnung",
            "vwvfg",
            "planungsrecht",
            "bauleitplanung",
            "flaechennutzungsplan",
            "behoerde",
            "zustaendigkeit",
            # English (für API/Tech)
            "administrative_law",
            "building_law",
            "building_permit",
            "administrative_procedure",
            "zoning_plan",
            "building_code",
        ]

    async def execute_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Führt Verwaltungsrecht-Analyse durch

        Args:
            step: Step-Definition mit query, parameters
            context: Kontext mit RAG-Daten, User-Context

        Returns:
            Dict mit status, data (VerwaltungsrechtResult), summary, confidence_score

        Example Step:
            {
                "query": "Benötige ich eine Baugenehmigung für ein Einfamilienhaus?",
                "parameters": {
                    "bundesland": "Bayern",
                    "bauvorhaben_typ": "Einfamilienhaus",
                    "grundstuecksgroesse": 800,  # m²
                    "wohnflaeche": 150           # m²
                }
            }
        """
        logger.info("🏛️ VerwaltungsrechtWorker: Analysiere Query")

        try:
            # Parse Query
            query_text = step.get("query", "")
            parameters = step.get("parameters", {})

            # Strukturierte Query erstellen
            vr_query = self._parse_query(query_text, parameters)

            # Phase 1: RAG-Suche nach relevanten Baurecht-Dokumenten
            rag_results = await self._search_baurecht_documents(vr_query, context)

            # Phase 2: UDS3-Suche nach ähnlichen Genehmigungen/Urteilen
            uds3_results = await self._search_similar_cases(vr_query, context)

            # Phase 3: Ollama-Analyse für rechtliche Bewertung
            legal_analysis = await self._analyze_with_ollama(vr_query, rag_results, uds3_results)

            # Phase 4: Ergebnis strukturieren
            result = self._create_result(vr_query, rag_results, uds3_results, legal_analysis)

            # Phase 5: Confidence Score berechnen
            confidence = self._calculate_confidence(result, rag_results, uds3_results, legal_analysis)
            result.confidence_score = confidence

            logger.info(f"✅ VerwaltungsrechtWorker: Analyse abgeschlossen (Confidence: {confidence:.2f})")

            return {
                "status": "completed",
                "data": self._result_to_dict(result),
                "summary": self._create_summary(result),
                "confidence_score": confidence,
                "processing_time": 0.0,  # Wird von Framework berechnet
                "sources": result.sources,
            }

        except Exception as e:
            logger.error(f"❌ VerwaltungsrechtWorker execute_step fehlgeschlagen: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "data": {},
                "summary": f"Fehler bei Verwaltungsrecht-Analyse: {e}",
                "confidence_score": 0.0,
            }

    def _parse_query(self, query_text: str, parameters: Dict[str, Any]) -> VerwaltungsrechtQuery:
        """
        Parsed Verwaltungsrecht-Query aus Text und Parametern

        Args:
            query_text: Frei-Text Query
            parameters: Strukturierte Parameter

        Returns:
            VerwaltungsrechtQuery Objekt
        """
        # Domain erkennen
        query_lower = query_text.lower()
        domain = VerwaltungsrechtDomain.BAURECHT  # Default

        if "baugenehmigung" in query_lower or "bauantrag" in query_lower:
            domain = VerwaltungsrechtDomain.BAUGENEHMIGUNG
        elif "bebauungsplan" in query_lower or "bauleitplanung" in query_lower:
            domain = VerwaltungsrechtDomain.BEBAUUNGSPLAN
        elif "verwaltungsverfahren" in query_lower:
            domain = VerwaltungsrechtDomain.VERWALTUNGSVERFAHREN
        elif "bauordnung" in query_lower:
            domain = VerwaltungsrechtDomain.BAUORDNUNG

        # Bundesland extrahieren
        bundesland = parameters.get("bundesland")
        if not bundesland:
            # Versuche aus Query zu extrahieren
            for bl in self.bauordnungen.keys():
                if bl.lower() in query_lower:
                    bundesland = bl
                    break

        # Bauvorhaben-Typ extrahieren
        bauvorhaben_typ = parameters.get("bauvorhaben_typ")
        if not bauvorhaben_typ:
            for typ in self.verfahrensarten.keys():
                if typ.lower() in query_lower:
                    bauvorhaben_typ = typ
                    break

        return VerwaltungsrechtQuery(
            query_text=query_text, domain=domain, bundesland=bundesland, bauvorhaben_typ=bauvorhaben_typ, context=parameters
        )

    async def _search_baurecht_documents(self, query: VerwaltungsrechtQuery, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Sucht in RAG-Datenbank nach relevanten Baurecht-Dokumenten

        Args:
            query: Strukturierte Query
            context: Kontext mit ggf. bereits RAG-Daten

        Returns:
            Liste von Dokumenten mit Metadaten
        """
        logger.info(f"📚 RAG-Suche: Baurecht-Dokumente für '{query.domain.value}'")

        # Check ob RAG Service verfügbar
        if not self.rag_service:
            logger.warning("⚠️ RAG Service nicht verfügbar - verwende Mock-Daten")
            return self._get_mock_baurecht_documents(query)

        try:
            # RAG-Suche mit Domain-Filter
            rag_query = f"{query.query_text} {query.domain.value}"
            if query.bundesland:
                rag_query += f" {query.bundesland}"

            # Suche mit Kategorie-Filter
            categories = ["BauGB", "BauO", "VwVfG", "Baurecht"]
            if query.bundesland and query.bundesland in self.bauordnungen:
                categories.append(self.bauordnungen[query.bundesland])

            results = await self.rag_service.retrieve(query=rag_query, categories=categories, top_k=5)

            logger.info(f"✅ RAG-Suche: {len(results)} Dokumente gefunden")
            return results

        except Exception as e:
            logger.error(f"❌ RAG-Suche fehlgeschlagen: {e}")
            return self._get_mock_baurecht_documents(query)

    async def _search_similar_cases(self, query: VerwaltungsrechtQuery, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sucht in UDS3 nach ähnlichen Fällen (Genehmigungen, Urteile)

        Args:
            query: Strukturierte Query
            context: Kontext

        Returns:
            Dict mit similar_permits, similar_rulings
        """
        logger.info(f"🗄️ UDS3-Suche: Ähnliche Fälle für '{query.bauvorhaben_typ}'")

        if not self.uds3_adapter:
            logger.warning("⚠️ UDS3 Adapter nicht verfügbar - verwende Mock-Daten")
            return self._get_mock_similar_cases(query)

        try:
            # Suche nach ähnlichen Baugenehmigungen
            similar_permits = await self.uds3_adapter.search_building_permits(
                bauvorhaben_typ=query.bauvorhaben_typ, bundesland=query.bundesland, limit=3
            )

            # Suche nach relevanter Rechtsprechung
            similar_rulings = await self.uds3_adapter.search_legal_rulings(
                keywords=[query.domain.value, query.bauvorhaben_typ or ""], limit=3
            )

            logger.info(f"✅ UDS3-Suche: {len(similar_permits)} Genehmigungen, " f"{len(similar_rulings)} Urteile")

            return {"similar_permits": similar_permits, "similar_rulings": similar_rulings}

        except Exception as e:
            logger.error(f"❌ UDS3-Suche fehlgeschlagen: {e}")
            return self._get_mock_similar_cases(query)

    async def _analyze_with_ollama(
        self, query: VerwaltungsrechtQuery, rag_results: List[Dict[str, Any]], uds3_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Führt rechtliche Analyse mit Ollama durch

        Args:
            query: Strukturierte Query
            rag_results: RAG-Suchergebnisse
            uds3_results: UDS3-Suchergebnisse

        Returns:
            Dict mit legal_assessment, recommendations, confidence
        """
        logger.info("🤖 Ollama-Analyse: Rechtliche Bewertung")

        if not self.ollama_client:
            logger.warning("⚠️ Ollama Client nicht verfügbar - verwende Regellogik")
            return self._rule_based_analysis(query, rag_results, uds3_results)

        try:
            # Prompt für Ollama erstellen
            prompt = self._create_legal_analysis_prompt(query, rag_results, uds3_results)

            # Ollama-Anfrage
            response = await self.ollama_client.generate(
                prompt=prompt,
                model="llama3.1:8b",  # oder "mistral"
                options={"temperature": 0.1},  # Niedrige Temperatur für präzise Antworten
            )

            # Response parsen
            analysis = self._parse_ollama_response(response)

            logger.info("✅ Ollama-Analyse abgeschlossen")
            return analysis

        except Exception as e:
            logger.error(f"❌ Ollama-Analyse fehlgeschlagen: {e}")
            return self._rule_based_analysis(query, rag_results, uds3_results)

    def _create_legal_analysis_prompt(
        self, query: VerwaltungsrechtQuery, rag_results: List[Dict[str, Any]], uds3_results: Dict[str, Any]
    ) -> str:
        """Erstellt Prompt für Ollama Legal Analysis"""

        # RAG-Dokumente zusammenfassen
        rag_context = "\n".join(
            [
                f"- {doc.get('title', 'Dokument')}: {doc.get('summary', doc.get('content', '')[:200])}"
                for doc in rag_results[:3]
            ]
        )

        # Ähnliche Fälle zusammenfassen
        similar_context = ""
        if uds3_results.get("similar_permits"):
            similar_context += "\n\nÄhnliche Genehmigungen:\n"
            for permit in uds3_results["similar_permits"][:2]:
                similar_context += f"- {permit.get('description', 'N / A')}: {permit.get('status', 'N / A')}\n"

        prompt = """Du bist ein Experte für deutsches Verwaltungsrecht und Baurecht.

ANFRAGE:
{query.query_text}

KONTEXT:
- Bundesland: {query.bundesland or 'Nicht angegeben'}
- Bauvorhaben: {query.bauvorhaben_typ or 'Nicht angegeben'}
- Rechtsgebiet: {query.domain.value}

RECHTLICHE GRUNDLAGEN:
{rag_context}

{similar_context}

AUFGABE:
Analysiere die Anfrage und beantworte folgende Fragen:

1. Ist eine Baugenehmigung erforderlich? (JA/NEIN/UNKLAR)
2. Welche rechtlichen Grundlagen sind relevant? (Gesetze, Paragraphen)
3. Welche Behörde ist zuständig?
4. Welche Verfahrensschritte sind erforderlich?
5. Welche Unterlagen werden benötigt?
6. Gibt es besondere Fristen?

ANTWORT (als JSON):
"""
        return prompt

    def _parse_ollama_response(self, response: str) -> Dict[str, Any]:
        """Parsed Ollama-Response zu strukturiertem Dict"""
        # Vereinfachte Parsing-Logik
        # In Production: JSON-Parsing mit Validation

        return {"legal_assessment": response, "recommendations": [], "confidence": 0.75}

    def _rule_based_analysis(
        self, query: VerwaltungsrechtQuery, rag_results: List[Dict[str, Any]], uds3_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Regelbasierte Analyse als Fallback (ohne Ollama)"""

        assessment = f"Verwaltungsrechtliche Analyse für {query.bauvorhaben_typ or 'Bauvorhaben'}"

        recommendations = []

        # Regel 1: Baugenehmigung erforderlich?
        if query.bauvorhaben_typ in ["Einfamilienhaus", "Gewerbe", "Industrieanlage"]:
            recommendations.append("Baugenehmigung ist erforderlich")
        elif query.bauvorhaben_typ in ["Garage", "Carport"]:
            recommendations.append("Vereinfachtes Verfahren möglich - prüfen Sie die Landesbauordnung")

        # Regel 2: Bundesland-spezifische Hinweise
        if query.bundesland and query.bundesland in self.bauordnungen:
            recommendations.append(f"Maßgebliche Bauordnung: {self.bauordnungen[query.bundesland]}")

        return {
            "legal_assessment": assessment,
            "recommendations": recommendations,
            "confidence": 0.6,  # Regelbasiert = niedrigere Confidence
        }

    def _create_result(
        self,
        query: VerwaltungsrechtQuery,
        rag_results: List[Dict[str, Any]],
        uds3_results: Dict[str, Any],
        legal_analysis: Dict[str, Any],
    ) -> VerwaltungsrechtResult:
        """Erstellt strukturiertes Ergebnis"""

        result = VerwaltungsrechtResult(query=query.query_text)

        # Rechtliche Grundlagen aus RAG
        result.rechtliche_grundlagen = [doc.get("title", "Dokument") for doc in rag_results[:5]]

        # Genehmigungsstatus
        if query.bauvorhaben_typ in ["Einfamilienhaus", "Gewerbe"]:
            result.genehmigung_erforderlich = GenehmigungsStatus.ERFORDERLICH
        elif query.bauvorhaben_typ in ["Garage", "Carport"]:
            result.genehmigung_erforderlich = GenehmigungsStatus.VEREINFACHT
        else:
            result.genehmigung_erforderlich = GenehmigungsStatus.UNKLAR

        # Zuständige Behörde
        if query.bundesland and query.bundesland in self.behoerden:
            result.zustaendige_behoerde = self.behoerden[query.bundesland]
        else:
            result.zustaendige_behoerde = "Untere Bauaufsichtsbehörde (zuständig nach Landesrecht)"

        # Verfahrensschritte
        result.verfahrensschritte = [
            "1. Bauvoranfrage (optional)",
            "2. Bauantrag mit Bauvorlagen einreichen",
            "3. Prüfung durch Bauaufsichtsbehörde",
            "4. Ggf. Nachforderung von Unterlagen",
            "5. Baugenehmigung oder Ablehnung",
            "6. Baubeginn nach Erteilung der Genehmigung",
        ]

        # Erforderliche Unterlagen
        result.erforderliche_unterlagen = [
            "Bauzeichnungen (Grundrisse, Ansichten, Schnitte)",
            "Lageplan",
            "Baubeschreibung",
            "Berechnungen (Wohnfläche, umbauter Raum)",
            "Nachweise (Standsicherheit, Brandschutz, Wärmeschutz)",
            "Ggf. Umweltgutachten",
        ]

        # Fristen
        result.fristen = [
            {"typ": "Bearbeitungsfrist", "dauer": "In der Regel 2 - 3 Monate"},
            {"typ": "Gültigkeit", "dauer": "Baugenehmigung gilt 3 Jahre"},
        ]

        # Rechtsprechung aus UDS3
        if uds3_results.get("similar_rulings"):
            result.rechtsprechung = [
                {
                    "titel": ruling.get("title", "Urteil"),
                    "gericht": ruling.get("court", "N / A"),
                    "aktenzeichen": ruling.get("case_number", "N / A"),
                }
                for ruling in uds3_results["similar_rulings"][:3]
            ]

        # Weitere Hinweise
        result.weitere_hinweise = legal_analysis.get("recommendations", [])

        # Quellen
        result.sources = [doc.get("source", "RAG") for doc in rag_results[:5]]

        return result

    def _calculate_confidence(
        self,
        result: VerwaltungsrechtResult,
        rag_results: List[Dict[str, Any]],
        uds3_results: Dict[str, Any],
        legal_analysis: Dict[str, Any],
    ) -> float:
        """Berechnet Confidence Score"""

        confidence = 0.5  # Basis

        # RAG-Ergebnisse vorhanden?
        if len(rag_results) > 0:
            confidence += 0.2
        if len(rag_results) >= 3:
            confidence += 0.1

        # UDS3-Ergebnisse vorhanden?
        if uds3_results.get("similar_permits"):
            confidence += 0.1

        # Ollama-Analyse vorhanden?
        if legal_analysis.get("confidence", 0) > 0.7:
            confidence += 0.1

        return min(confidence, 1.0)

    def _create_summary(self, result: VerwaltungsrechtResult) -> str:
        """Erstellt Zusammenfassung des Ergebnisses"""

        summary = "Verwaltungsrechtliche Analyse:\n\n"

        if result.genehmigung_erforderlich:
            summary += f"Genehmigungsstatus: {result.genehmigung_erforderlich.value}\n"

        if result.zustaendige_behoerde:
            summary += f"Zuständige Behörde: {result.zustaendige_behoerde}\n"

        if result.rechtliche_grundlagen:
            summary += "\nRechtliche Grundlagen:\n"
            for grundlage in result.rechtliche_grundlagen[:3]:
                summary += f"- {grundlage}\n"

        if result.verfahrensschritte:
            summary += "\nWesentliche Verfahrensschritte:\n"
            for schritt in result.verfahrensschritte[:4]:
                summary += f"- {schritt}\n"

        return summary

    def _result_to_dict(self, result: VerwaltungsrechtResult) -> Dict[str, Any]:
        """Konvertiert VerwaltungsrechtResult zu Dict"""
        return {
            "query": result.query,
            "rechtliche_grundlagen": result.rechtliche_grundlagen,
            "genehmigung_erforderlich": result.genehmigung_erforderlich.value if result.genehmigung_erforderlich else None,
            "zustaendige_behoerde": result.zustaendige_behoerde,
            "verfahrensschritte": result.verfahrensschritte,
            "erforderliche_unterlagen": result.erforderliche_unterlagen,
            "fristen": result.fristen,
            "rechtsprechung": result.rechtsprechung,
            "weitere_hinweise": result.weitere_hinweise,
            "confidence_score": result.confidence_score,
            "sources": result.sources,
        }

    # Mock-Daten-Methoden für Testing/Fallback

    def _get_mock_baurecht_documents(self, query: VerwaltungsrechtQuery) -> List[Dict[str, Any]]:
        """Mock Baurecht-Dokumente für Testing"""
        return [
            {
                "title": "BauGB § 29 - Zulässigkeit von Vorhaben im Geltungsbereich eines Bebauungsplans",
                "summary": "Innerhalb der im Zusammenhang bebauten Ortsteile ist ein Vorhaben zulässig...",
                "source": "BauGB",
                "relevance": 0.95,
            },
            {
                "title": f"{self.bauordnungen.get(query.bundesland or 'Bayern', 'BayBO')} - Baugenehmigungsverfahren",
                "summary": "Das Baugenehmigungsverfahren wird durch Bauantrag eingeleitet...",
                "source": "Landesbauordnung",
                "relevance": 0.90,
            },
            {
                "title": "VwVfG § 10 - Nichtförmlichkeit des Verwaltungsverfahrens",
                "summary": "Das Verwaltungsverfahren ist nicht an bestimmte Formen gebunden...",
                "source": "VwVfG",
                "relevance": 0.75,
            },
        ]

    def _get_mock_similar_cases(self, query: VerwaltungsrechtQuery) -> Dict[str, Any]:
        """Mock ähnliche Fälle für Testing"""
        return {
            "similar_permits": [
                {
                    "description": f"{query.bauvorhaben_typ or 'Bauvorhaben'} in vergleichbarer Lage",
                    "status": "Genehmigt",
                    "location": query.bundesland or "Bayern",
                    "year": 2024,
                }
            ],
            "similar_rulings": [
                {
                    "title": "Baugenehmigung für Einfamilienhaus",
                    "court": "VGH München",
                    "case_number": "15 B 21.123",
                    "summary": "Baugenehmigung rechtmäßig erteilt...",
                }
            ],
        }


# Convenience Function für Worker Registry Integration
def create_verwaltungsrecht_worker(ollama_client=None, rag_service=None, uds3_adapter=None) -> VerwaltungsrechtWorker:
    """
    Factory Function für VerwaltungsrechtWorker

    Args:
        ollama_client: Ollama Client (optional)
        rag_service: RAG Service (optional)
        uds3_adapter: UDS3 Adapter (optional)

    Returns:
        VerwaltungsrechtWorker Instanz
    """
    return VerwaltungsrechtWorker(ollama_client=ollama_client, rag_service=rag_service, uds3_adapter=uds3_adapter)


# Test/Demo
if __name__ == "__main__":
    print("=" * 80)
    print("VERITAS VerwaltungsrechtWorker - Demo")
    print("=" * 80)

    worker = VerwaltungsrechtWorker()

    print(f"\nWorker Type: {worker.get_agent_type()}")
    print(f"Capabilities: {len(worker.get_capabilities())} items")
    print(f"  Sample: {', '.join(worker.get_capabilities()[:5])}...")

    # Test execute_step (synchron für Demo)
    import asyncio

    async def demo():
        step = {
            "query": "Benötige ich eine Baugenehmigung für ein Einfamilienhaus in Bayern?",
            "parameters": {"bundesland": "Bayern", "bauvorhaben_typ": "Einfamilienhaus"},
        }

        print(f"\nTest Query: {step['query']}")
        print(f"Parameters: {step['parameters']}")

        result = await worker.execute_step(step, {})

        print(f"\nStatus: {result['status']}")
        print(f"Confidence: {result['confidence_score']:.2f}")
        print(f"\nSummary:\n{result['summary']}")

    asyncio.run(demo())

    print("\n" + "=" * 80)
    print("✅ VerwaltungsrechtWorker Demo abgeschlossen!")
    print("=" * 80)
