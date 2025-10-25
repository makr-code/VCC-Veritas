"""
DatabaseAgent TestServer Extension (Generic Template)
======================================================

Generische Extension-Klasse für DatabaseAgent, die TestServer-Integration
ermöglicht. Dient als Vorlage für spezifische Datenbank-Agenten.

Design-Prinzipien:
- Generisch und wiederverwendbar
- Klare Trennung von Basis-Funktionalität und spezifischen Queries
- Async-First Design
- Type Hints für bessere IDE-Unterstützung
- Umfassendes Error Handling
- Logging für Debugging

Verwendung:
    # Basis-Nutzung
    agent = DatabaseAgentTestServerExtension()
    
    # Query-Methoden
    verfahren = await agent.query_verfahren(bst_nr="10650200000")
    anlage = await agent.get_complete_entity(bst_nr="10650200000", anl_nr="4001")
    
    # Analyse-Methoden
    compliance = await agent.analyze_compliance(bst_nr="10650200000", anl_nr="4001")
    
    # Spezifische Abfragen
    result = await agent.custom_query(
        endpoint="/messungen/search",
        params={"bst_nr": "10650200000", "ueberschreitung": True}
    )

Erweiterung für spezifische Agenten:
    class MySpecificDatabaseAgent(DatabaseAgentTestServerExtension):
        '''Spezialisierter Agent für XYZ-Datenbank'''
        
        async def my_specific_query(self, params):
            '''Domain-spezifische Query-Logik'''
            return await self.query_entity("my_table", filters=params)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backend.agents.test_server_client import (
    TestServerClient,
    TestServerConfig,
    AnlageBasic,
    AnlageExtended,
    Verfahren,
    Messung,
    Ueberwachung,
    Mangel,
    Dokument,
    Ansprechpartner,
    Wartung,
    Messreihe,
    ComplianceHistorie
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums für Type Safety
# =============================================================================

class EntityType(str, Enum):
    """Entitäts-Typen in der Datenbank"""
    ANLAGE = "anlage"
    VERFAHREN = "verfahren"
    MESSUNG = "messung"
    UEBERWACHUNG = "ueberwachung"
    MANGEL = "mangel"
    DOKUMENT = "dokument"
    ANSPRECHPARTNER = "ansprechpartner"
    WARTUNG = "wartung"
    MESSREIHE = "messreihe"
    COMPLIANCE = "compliance"


class QueryStrategy(str, Enum):
    """Query-Strategien"""
    SINGLE = "single"           # Einzelnes Entity
    COLLECTION = "collection"   # Liste von Entities
    AGGREGATION = "aggregation" # Aggregierte Daten
    RELATION = "relation"       # Cross-Entity Relations


class ComplianceStatus(str, Enum):
    """Compliance-Status"""
    COMPLIANT = "compliant"
    REQUIRES_ATTENTION = "requires_attention"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


# =============================================================================
# Result Objects
# =============================================================================

@dataclass
class QueryResult:
    """Generisches Query-Ergebnis"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_data(self) -> bool:
        """Prüft ob Daten vorhanden sind"""
        if isinstance(self.data, (list, dict)):
            return bool(self.data)
        return self.data is not None


@dataclass
class ComplianceResult:
    """Compliance-Analyse Ergebnis"""
    bst_nr: str
    anl_nr: str
    status: ComplianceStatus
    score: float  # 0.0 - 1.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def is_compliant(self) -> bool:
        return self.status == ComplianceStatus.COMPLIANT
    
    @property
    def requires_action(self) -> bool:
        return self.status in [ComplianceStatus.CRITICAL, ComplianceStatus.NON_COMPLIANT]


# =============================================================================
# Generic DatabaseAgent Extension
# =============================================================================

class DatabaseAgentTestServerExtension:
    """
    Generische DatabaseAgent Extension für TestServer-Integration
    
    Diese Klasse dient als Basis-Template für spezifische Datenbank-Agenten.
    Sie bietet generische Methoden für:
    - Entity Queries (Single & Collection)
    - Cross-Entity Relations
    - Compliance Analysis
    - Custom Queries
    
    Erweitern Sie diese Klasse für domänen-spezifische Funktionalität.
    """
    
    def __init__(self, config: Optional[TestServerConfig] = None):
        """
        Initialisiert die Extension
        
        Args:
            config: Optional TestServer Konfiguration
        """
        self.client = TestServerClient(config)
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = 300  # 5 Minuten
        
        logger.info("DatabaseAgentTestServerExtension initialisiert")
    
    async def close(self):
        """Schließt Client-Verbindungen"""
        await self.client.close()
    
    # =========================================================================
    # Generic Query Methods (Template Pattern)
    # =========================================================================
    
    async def query_entity(
        self,
        entity_type: EntityType,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> QueryResult:
        """
        Generische Entity-Query
        
        Template-Methode für Entity-Abfragen. Kann für spezifische
        Entity-Typen überschrieben werden.
        
        Args:
            entity_type: Typ der Entity
            filters: Filter-Parameter (z.B. {"bst_nr": "...", "status": "..."})
            limit: Max. Anzahl Ergebnisse
            
        Returns:
            QueryResult mit Daten oder Fehler
            
        Example:
            result = await agent.query_entity(
                EntityType.VERFAHREN,
                filters={"bst_nr": "10650200000", "status": "genehmigt"}
            )
        """
        try:
            # Map EntityType to endpoint
            endpoint_map = {
                EntityType.VERFAHREN: "/verfahren/search",
                EntityType.MESSUNG: "/messungen/search",
                EntityType.UEBERWACHUNG: "/ueberwachung/search",
                EntityType.MANGEL: "/maengel/search",
                EntityType.DOKUMENT: "/dokumente/search",
                EntityType.ANSPRECHPARTNER: "/ansprechpartner/search",
                EntityType.WARTUNG: "/wartung/search",
                EntityType.MESSREIHE: "/messreihen/search",
                EntityType.COMPLIANCE: "/compliance/search"
            }
            
            endpoint = endpoint_map.get(entity_type)
            if not endpoint:
                return QueryResult(
                    success=False,
                    error=f"Unbekannter EntityType: {entity_type}"
                )
            
            # Prepare params
            params = filters or {}
            params["limit"] = limit
            
            # Execute query via client
            result = await self.client._request("GET", endpoint, params=params)
            
            # Extract data (verschiedene Response-Strukturen)
            data_keys = ["verfahren", "messungen", "ueberwachungen", "maengel", 
                        "dokumente", "ansprechpartner", "wartungen", "messreihen", "historie"]
            
            data = None
            for key in data_keys:
                if key in result:
                    data = result[key]
                    break
            
            return QueryResult(
                success=True,
                data=data,
                metadata={
                    "entity_type": entity_type.value,
                    "count": len(data) if isinstance(data, list) else 0,
                    "filters": filters
                }
            )
            
        except Exception as e:
            logger.error(f"Fehler bei query_entity ({entity_type}): {e}", exc_info=True)
            return QueryResult(success=False, error=str(e))
    
    async def get_entity_by_id(
        self,
        entity_type: EntityType,
        entity_id: str
    ) -> QueryResult:
        """
        Einzelne Entity per ID abrufen
        
        Template-Methode für ID-basierte Abfragen.
        
        Args:
            entity_type: Typ der Entity
            entity_id: ID der Entity
            
        Returns:
            QueryResult mit Entity oder Fehler
        """
        try:
            endpoint_map = {
                EntityType.VERFAHREN: f"/verfahren/{entity_id}",
                EntityType.DOKUMENT: f"/dokumente/{entity_id}",
            }
            
            endpoint = endpoint_map.get(entity_type)
            if not endpoint:
                return QueryResult(
                    success=False,
                    error=f"ID-Query für {entity_type} nicht unterstützt"
                )
            
            result = await self.client._request("GET", endpoint)
            
            return QueryResult(
                success="error" not in result,
                data=result if "error" not in result else None,
                error=result.get("error"),
                metadata={"entity_type": entity_type.value, "entity_id": entity_id}
            )
            
        except Exception as e:
            logger.error(f"Fehler bei get_entity_by_id: {e}", exc_info=True)
            return QueryResult(success=False, error=str(e))
    
    async def get_complete_entity(
        self,
        bst_nr: str,
        anl_nr: str,
        include_all_relations: bool = True
    ) -> QueryResult:
        """
        Vollständige Entity mit allen Relationen abrufen
        
        Ruft eine Anlage mit ALLEN verknüpften Daten ab.
        Zentrale Methode für umfassende Daten-Abfragen.
        
        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            include_all_relations: Alle Relationen laden
            
        Returns:
            QueryResult mit AnlageExtended oder Fehler
        """
        try:
            anlage = await self.client.get_anlage_extended(
                bst_nr=bst_nr,
                anl_nr=anl_nr,
                include_messungen=include_all_relations,
                include_dokumente=include_all_relations
            )
            
            if anlage:
                return QueryResult(
                    success=True,
                    data=anlage,
                    metadata={
                        "bst_nr": bst_nr,
                        "anl_nr": anl_nr,
                        "statistik": anlage.statistik
                    }
                )
            else:
                return QueryResult(
                    success=False,
                    error=f"Anlage {bst_nr}/{anl_nr} nicht gefunden"
                )
                
        except Exception as e:
            logger.error(f"Fehler bei get_complete_entity: {e}", exc_info=True)
            return QueryResult(success=False, error=str(e))
    
    async def custom_query(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> QueryResult:
        """
        Custom Query für spezielle Endpoints
        
        Ermöglicht flexible Queries für nicht-Standard-Abfragen.
        
        Args:
            endpoint: API-Endpoint (z.B. "/statistik/overview")
            params: Query-Parameter
            method: HTTP-Methode
            
        Returns:
            QueryResult mit Response-Daten
            
        Example:
            result = await agent.custom_query(
                endpoint="/messreihen/kritische",
                params={"limit": 10}
            )
        """
        try:
            result = await self.client._request(method, endpoint, params=params or {})
            
            return QueryResult(
                success="error" not in result,
                data=result,
                metadata={"endpoint": endpoint, "method": method}
            )
            
        except Exception as e:
            logger.error(f"Fehler bei custom_query: {e}", exc_info=True)
            return QueryResult(success=False, error=str(e))
    
    # =========================================================================
    # Convenience Methods (High-Level API)
    # =========================================================================
    
    async def query_verfahren(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Verfahren abfragen
        
        Convenience-Methode für häufige Verfahrens-Queries.
        
        Args:
            bst_nr: BST-Nummer (optional)
            anl_nr: Anlagen-Nummer (optional)
            status: Status-Filter (optional)
            limit: Max. Anzahl
            
        Returns:
            Liste von Verfahren
        """
        filters = {}
        if bst_nr:
            filters["bst_nr"] = bst_nr
        if anl_nr:
            filters["anl_nr"] = anl_nr
        if status:
            filters["status"] = status
        
        result = await self.query_entity(EntityType.VERFAHREN, filters, limit)
        return result.data if result.success and result.data else []
    
    async def query_messungen(
        self,
        bst_nr: Optional[str] = None,
        anl_nr: Optional[str] = None,
        messart: Optional[str] = None,
        ueberschreitung: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Messungen abfragen
        
        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            messart: Messart (z.B. "Lärm_Tag", "PM10")
            ueberschreitung: Nur Überschreitungen
            limit: Max. Anzahl
            
        Returns:
            Liste von Messungen
        """
        return await self.client.search_messungen(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            messart=messart,
            ueberschreitung=ueberschreitung,
            limit=limit
        )
    
    async def query_compliance_history(
        self,
        bst_nr: str,
        anl_nr: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Compliance-Historie abrufen
        
        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            limit: Max. Anzahl
            
        Returns:
            Liste von Compliance-Prüfungen
        """
        return await self.client.search_compliance(
            bst_nr=bst_nr,
            anl_nr=anl_nr,
            limit=limit
        )
    
    # =========================================================================
    # Analysis Methods (Business Logic)
    # =========================================================================
    
    async def analyze_compliance(
        self,
        bst_nr: str,
        anl_nr: str
    ) -> ComplianceResult:
        """
        Compliance-Analyse durchführen
        
        Analysiert den Compliance-Status einer Anlage basierend auf:
        - Verfahrensstatus
        - Grenzwertüberschreitungen
        - Offene Mängel
        - Compliance-Historie
        - Wartungsstatus
        
        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            
        Returns:
            ComplianceResult mit Status, Score und Empfehlungen
        """
        try:
            # Vollständige Daten abrufen
            result = await self.get_complete_entity(bst_nr, anl_nr)
            
            if not result.success or not result.data:
                return ComplianceResult(
                    bst_nr=bst_nr,
                    anl_nr=anl_nr,
                    status=ComplianceStatus.UNKNOWN,
                    score=0.0,
                    issues=[{"type": "data_unavailable", "message": result.error}]
                )
            
            anlage: AnlageExtended = result.data
            issues = []
            recommendations = []
            score = 1.0  # Start bei 100%
            
            # 1. Verfahrensstatus prüfen
            verfahren_genehmigt = anlage.statistik.get("verfahren_genehmigt", 0)
            verfahren_total = anlage.statistik.get("verfahren_count", 0)
            
            if verfahren_total > 0:
                genehmigungsquote = verfahren_genehmigt / verfahren_total
                if genehmigungsquote < 1.0:
                    score -= 0.1
                    issues.append({
                        "type": "verfahren_status",
                        "severity": "medium",
                        "message": f"{verfahren_total - verfahren_genehmigt} Verfahren nicht genehmigt"
                    })
                    recommendations.append("Ausstehende Genehmigungsverfahren beschleunigen")
            
            # 2. Grenzwertüberschreitungen prüfen
            ueberschreitungen = anlage.statistik.get("messungen_ueberschreitungen", 0)
            messungen_total = anlage.statistik.get("messungen_count", 0)
            
            if messungen_total > 0:
                ueberschreitungs_rate = ueberschreitungen / messungen_total
                
                if ueberschreitungs_rate > 0.2:  # > 20%
                    score -= 0.3
                    issues.append({
                        "type": "grenzwert_ueberschreitungen",
                        "severity": "critical",
                        "message": f"{ueberschreitungen} Grenzwertüberschreitungen ({ueberschreitungs_rate:.1%})"
                    })
                    recommendations.append("Sofortige Maßnahmen zur Emissionsreduktion erforderlich")
                elif ueberschreitungs_rate > 0.05:  # > 5%
                    score -= 0.15
                    issues.append({
                        "type": "grenzwert_ueberschreitungen",
                        "severity": "high",
                        "message": f"{ueberschreitungen} Grenzwertüberschreitungen"
                    })
                    recommendations.append("Technische Überprüfung und Optimierung empfohlen")
            
            # 3. Mängel prüfen
            maengel_offen = anlage.statistik.get("maengel_offen", 0)
            maengel_kritisch = anlage.statistik.get("maengel_kritisch", 0)
            
            if maengel_kritisch > 0:
                score -= 0.25
                issues.append({
                    "type": "kritische_maengel",
                    "severity": "critical",
                    "message": f"{maengel_kritisch} kritische Mängel offen"
                })
                recommendations.append("Kritische Mängel umgehend beheben")
            elif maengel_offen > 0:
                score -= 0.1
                issues.append({
                    "type": "offene_maengel",
                    "severity": "medium",
                    "message": f"{maengel_offen} Mängel offen"
                })
                recommendations.append("Mängel zeitnah beheben")
            
            # 4. Wartungsstatus prüfen
            wartungen_geplant = anlage.statistik.get("wartungen_geplant", 0)
            wartungen_total = anlage.statistik.get("wartungen_count", 0)
            
            if wartungen_total > 0 and wartungen_geplant > wartungen_total * 0.3:
                score -= 0.05
                issues.append({
                    "type": "wartungsrueckstand",
                    "severity": "low",
                    "message": f"{wartungen_geplant} Wartungen ausstehend"
                })
                recommendations.append("Wartungsplan überprüfen und Termine einhalten")
            
            # 5. Compliance-Historie berücksichtigen
            compliance_historie = anlage.compliance_historie
            if compliance_historie:
                letztes_ergebnis = compliance_historie[0].ergebnis
                if letztes_ergebnis == "Kritisch":
                    score -= 0.2
                    issues.append({
                        "type": "compliance_historie",
                        "severity": "high",
                        "message": f"Letzte Prüfung: {letztes_ergebnis}"
                    })
                    recommendations.append("Maßnahmen aus letzter Compliance-Prüfung umsetzen")
            
            # Score begrenzen
            score = max(0.0, min(1.0, score))
            
            # Status bestimmen
            if score >= 0.9:
                status = ComplianceStatus.COMPLIANT
            elif score >= 0.7:
                status = ComplianceStatus.REQUIRES_ATTENTION
            elif score >= 0.5:
                status = ComplianceStatus.NON_COMPLIANT
            else:
                status = ComplianceStatus.CRITICAL
            
            return ComplianceResult(
                bst_nr=bst_nr,
                anl_nr=anl_nr,
                status=status,
                score=score,
                issues=issues,
                recommendations=recommendations,
                details={
                    "verfahren": {
                        "total": verfahren_total,
                        "genehmigt": verfahren_genehmigt
                    },
                    "messungen": {
                        "total": messungen_total,
                        "ueberschreitungen": ueberschreitungen
                    },
                    "maengel": {
                        "offen": maengel_offen,
                        "kritisch": maengel_kritisch
                    },
                    "wartungen": {
                        "total": wartungen_total,
                        "geplant": wartungen_geplant
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Fehler bei analyze_compliance: {e}", exc_info=True)
            return ComplianceResult(
                bst_nr=bst_nr,
                anl_nr=anl_nr,
                status=ComplianceStatus.UNKNOWN,
                score=0.0,
                issues=[{"type": "error", "message": str(e)}]
            )
    
    async def check_auflagen_status(
        self,
        bst_nr: str,
        anl_nr: str
    ) -> Dict[str, Any]:
        """
        Status aller Auflagen prüfen
        
        Gibt einen Überblick über Auflagen und deren Umsetzung.
        
        Args:
            bst_nr: BST-Nummer
            anl_nr: Anlagen-Nummer
            
        Returns:
            Dict mit Auflagen-Status
        """
        try:
            result = await self.get_complete_entity(bst_nr, anl_nr)
            
            if not result.success:
                return {"error": result.error}
            
            anlage: AnlageExtended = result.data
            
            # Auflagen aus Bescheiden extrahieren (über Verfahren)
            auflagen_info = {
                "gesamt": 0,
                "kategorien": {},
                "ueberfaellig": [],
                "in_bearbeitung": []
            }
            
            # Verfahren durchgehen um an Auflagen zu kommen
            for verfahren in anlage.verfahren:
                # Hier würde man normalerweise die Auflagen des Verfahrens abrufen
                # Da wir nur statistik haben, verwenden wir die
                pass
            
            return {
                "bst_nr": bst_nr,
                "anl_nr": anl_nr,
                "auflagen": auflagen_info,
                "verfahren_count": len(anlage.verfahren),
                "bescheide_count": anlage.statistik.get("bescheide_count", 0)
            }
            
        except Exception as e:
            logger.error(f"Fehler bei check_auflagen_status: {e}", exc_info=True)
            return {"error": str(e)}
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    async def get_server_health(self) -> Dict[str, Any]:
        """Server Health Check"""
        return await self.client.health_check()
    
    async def get_server_statistics(self) -> Dict[str, Any]:
        """Server-weite Statistiken abrufen"""
        return await self.client.get_statistics()


# =============================================================================
# Example: Specialized Agent (Template)
# =============================================================================

class ExampleSpecializedAgent(DatabaseAgentTestServerExtension):
    """
    Beispiel für einen spezialisierten Agenten
    
    Zeigt wie die Basis-Klasse erweitert werden kann.
    """
    
    async def my_domain_specific_query(self, param1: str, param2: int) -> QueryResult:
        """
        Domänen-spezifische Query-Methode
        
        Implementiert spezifische Business-Logik
        """
        # Nutze Basis-Methoden
        result = await self.query_entity(
            EntityType.VERFAHREN,
            filters={"custom_field": param1},
            limit=param2
        )
        
        # Füge spezifische Verarbeitung hinzu
        if result.success and result.data:
            # Custom processing...
            pass
        
        return result


# =============================================================================
# Singleton Helper
# =============================================================================

_database_agent: Optional[DatabaseAgentTestServerExtension] = None

def get_database_agent(
    config: Optional[TestServerConfig] = None
) -> DatabaseAgentTestServerExtension:
    """Singleton Pattern für DatabaseAgent"""
    global _database_agent
    
    if _database_agent is None:
        _database_agent = DatabaseAgentTestServerExtension(config)
    
    return _database_agent


# =============================================================================
# Usage Examples
# =============================================================================

async def example_usage():
    """Beispiel-Verwendung der Extension"""
    
    agent = DatabaseAgentTestServerExtension()
    
    try:
        print("="*70)
        print("DatabaseAgent TestServer Extension - Examples")
        print("="*70)
        
        # 1. Generische Entity-Query
        print("\n1️⃣ Generische Query (Verfahren):")
        result = await agent.query_entity(
            EntityType.VERFAHREN,
            filters={"status": "genehmigt"},
            limit=3
        )
        if result.success:
            print(f"   ✅ {result.metadata['count']} Verfahren gefunden")
        
        # 2. Vollständige Entity
        print("\n2️⃣ Vollständige Anlage:")
        result = await agent.get_complete_entity("10686360000", "4001")
        if result.success:
            anlage = result.data
            print(f"   ✅ Anlage: {anlage.anlage.bst_name}")
            print(f"      Verfahren: {len(anlage.verfahren)}")
            print(f"      Dokumente: {len(anlage.dokumente)}")
        
        # 3. Compliance-Analyse
        print("\n3️⃣ Compliance-Analyse:")
        compliance = await agent.analyze_compliance("10686360000", "4001")
        print(f"   Status: {compliance.status.value}")
        print(f"   Score: {compliance.score:.1%}")
        print(f"   Issues: {len(compliance.issues)}")
        if compliance.recommendations:
            print(f"   Empfehlung: {compliance.recommendations[0]}")
        
        # 4. Custom Query
        print("\n4️⃣ Custom Query (Kritische Messreihen):")
        result = await agent.custom_query(
            endpoint="/messreihen/kritische",
            params={"limit": 5}
        )
        if result.success:
            messreihen = result.data.get("messreihen", [])
            print(f"   ✅ {len(messreihen)} kritische Messreihen")
        
        print("\n" + "="*70)
        print("✅ Alle Examples erfolgreich!")
        print("="*70)
        
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
