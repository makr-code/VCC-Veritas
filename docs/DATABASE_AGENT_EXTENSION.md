# DatabaseAgent TestServer Extension - Documentation

## 📋 Overview

Die `DatabaseAgentTestServerExtension` ist eine **generische, wiederverwendbare Template-Klasse** für die Integration von Datenbank-Agenten mit dem Immissionsschutz Test-Server. Sie bietet eine strukturierte, erweiterbare Basis für spezifische Agenten-Implementierungen.

## 🎯 Design-Prinzipien

### 1. **Generisch & Wiederverwendbar**
- Template-Pattern für Entity-Queries
- Keine hart-kodierten domänen-spezifischen Details
- Einfache Erweiterbarkeit durch Vererbung

### 2. **Type-Safe**
- Umfassende Type Hints
- Enums für Type Safety (`EntityType`, `QueryStrategy`, `ComplianceStatus`)
- Dataclasses für strukturierte Rückgabewerte

### 3. **Async-First**
- Alle Methoden async/await
- Non-blocking Operations
- Effiziente Parallelisierung möglich

### 4. **Robustes Error Handling**
- Strukturierte Result Objects (`QueryResult`, `ComplianceResult`)
- Keine Exceptions für normale Fehler (Success/Failure Pattern)
- Umfassendes Logging für Debugging

## 📦 Komponenten

### Core Classes

```python
class DatabaseAgentTestServerExtension:
    """Generische Extension für DatabaseAgent"""
    
    def __init__(self, config: Optional[TestServerConfig] = None)
    async def close(self)
```

### Enums

```python
class EntityType(str, Enum):
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
    SINGLE = "single"
    COLLECTION = "collection"
    AGGREGATION = "aggregation"
    RELATION = "relation"

class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    REQUIRES_ATTENTION = "requires_attention"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
```

### Result Objects

```python
@dataclass
class QueryResult:
    """Generisches Query-Ergebnis"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def has_data(self) -> bool

@dataclass
class ComplianceResult:
    """Compliance-Analyse Ergebnis"""
    bst_nr: str
    anl_nr: str
    status: ComplianceStatus
    score: float  # 0.0 - 1.0
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    details: Dict[str, Any]
    timestamp: str
    
    @property
    def is_compliant(self) -> bool
    
    @property
    def requires_action(self) -> bool
```

## 🔧 API Reference

### Generic Query Methods

#### `query_entity()`
```python
async def query_entity(
    self,
    entity_type: EntityType,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 50
) -> QueryResult
```

**Generische Entity-Query mit flexiblen Filtern.**

**Beispiel:**
```python
result = await agent.query_entity(
    EntityType.VERFAHREN,
    filters={"bst_nr": "10650200000", "status": "genehmigt"},
    limit=10
)

if result.success:
    verfahren = result.data
    count = result.metadata['count']
```

#### `get_entity_by_id()`
```python
async def get_entity_by_id(
    self,
    entity_type: EntityType,
    entity_id: str
) -> QueryResult
```

**Einzelne Entity per ID abrufen.**

**Beispiel:**
```python
result = await agent.get_entity_by_id(
    EntityType.DOKUMENT,
    "DOK-000123"
)
```

#### `get_complete_entity()`
```python
async def get_complete_entity(
    self,
    bst_nr: str,
    anl_nr: str,
    include_all_relations: bool = True
) -> QueryResult
```

**Vollständige Entity mit ALLEN Relationen abrufen.**

**Beispiel:**
```python
result = await agent.get_complete_entity("10650200000", "4001")

if result.success:
    anlage: AnlageExtended = result.data
    print(f"Verfahren: {len(anlage.verfahren)}")
    print(f"Dokumente: {len(anlage.dokumente)}")
    print(f"Wartungen: {len(anlage.wartungen)}")
```

#### `custom_query()`
```python
async def custom_query(
    self,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    method: str = "GET"
) -> QueryResult
```

**Flexible Custom Queries für spezielle Endpoints.**

**Beispiel:**
```python
result = await agent.custom_query(
    endpoint="/messreihen/kritische",
    params={"limit": 10}
)
```

### Convenience Methods

#### `query_verfahren()`
```python
async def query_verfahren(
    self,
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]
```

#### `query_messungen()`
```python
async def query_messungen(
    self,
    bst_nr: Optional[str] = None,
    anl_nr: Optional[str] = None,
    messart: Optional[str] = None,
    ueberschreitung: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]
```

#### `query_compliance_history()`
```python
async def query_compliance_history(
    self,
    bst_nr: str,
    anl_nr: str,
    limit: int = 10
) -> List[Dict[str, Any]]
```

### Analysis Methods

#### `analyze_compliance()`
```python
async def analyze_compliance(
    self,
    bst_nr: str,
    anl_nr: str
) -> ComplianceResult
```

**Umfassende Compliance-Analyse einer Anlage.**

**Analysiert:**
- ✅ Verfahrensstatus (genehmigt vs. in Bearbeitung)
- ✅ Grenzwertüberschreitungen (Messungen)
- ✅ Offene Mängel (kritisch, schwer, mittel, gering)
- ✅ Wartungsstatus (geplant vs. durchgeführt)
- ✅ Compliance-Historie (letzte Prüfungen)

**Scoring-System:**
- 90-100%: `COMPLIANT` ✅
- 70-89%: `REQUIRES_ATTENTION` ⚠️
- 50-69%: `NON_COMPLIANT` ❌
- 0-49%: `CRITICAL` 🔴

**Beispiel:**
```python
compliance = await agent.analyze_compliance("10650200000", "4001")

print(f"Status: {compliance.status.value}")
print(f"Score: {compliance.score:.1%}")
print(f"Is Compliant: {compliance.is_compliant}")

if compliance.requires_action:
    print("⚠️ Maßnahmen erforderlich!")
    for issue in compliance.issues:
        print(f"  - [{issue['severity']}] {issue['message']}")
    
    for rec in compliance.recommendations:
        print(f"  💡 {rec}")
```

**Rückgabe-Beispiel:**
```python
ComplianceResult(
    bst_nr="10650200000",
    anl_nr="4001",
    status=ComplianceStatus.COMPLIANT,
    score=0.95,
    issues=[
        {
            "type": "wartungsrueckstand",
            "severity": "low",
            "message": "2 Wartungen ausstehend"
        }
    ],
    recommendations=[
        "Wartungsplan überprüfen und Termine einhalten"
    ],
    details={
        "verfahren": {"total": 1, "genehmigt": 1},
        "messungen": {"total": 10, "ueberschreitungen": 0},
        "maengel": {"offen": 0, "kritisch": 0},
        "wartungen": {"total": 5, "geplant": 2}
    }
)
```

#### `check_auflagen_status()`
```python
async def check_auflagen_status(
    self,
    bst_nr: str,
    anl_nr: str
) -> Dict[str, Any]
```

**Status aller Auflagen prüfen.**

### Utility Methods

#### `get_server_health()`
```python
async def get_server_health(self) -> Dict[str, Any]
```

#### `get_server_statistics()`
```python
async def get_server_statistics(self) -> Dict[str, Any]
```

## 🔄 Erweiterung für spezifische Agenten

### Template für Spezialisierung

```python
class MySpecializedDatabaseAgent(DatabaseAgentTestServerExtension):
    """
    Spezialisierter Agent für XYZ-Domäne
    """
    
    def __init__(self, config: Optional[TestServerConfig] = None):
        super().__init__(config)
        # Zusätzliche Initialisierung
        self.domain_config = load_domain_config()
    
    async def my_domain_specific_query(
        self,
        param1: str,
        param2: int
    ) -> QueryResult:
        """
        Domänen-spezifische Query-Methode
        """
        # Nutze Basis-Methoden
        result = await self.query_entity(
            EntityType.VERFAHREN,
            filters={"custom_field": param1},
            limit=param2
        )
        
        # Füge spezifische Verarbeitung hinzu
        if result.success and result.data:
            processed_data = self._process_domain_data(result.data)
            result.data = processed_data
        
        return result
    
    def _process_domain_data(self, data: List[Dict]) -> List[Dict]:
        """Private Hilfsmethode für Domain-Logik"""
        # Custom processing...
        return data
    
    async def analyze_domain_compliance(
        self,
        entity_id: str
    ) -> ComplianceResult:
        """
        Erweiterte Compliance-Analyse mit domänen-spezifischen Regeln
        """
        # Basis-Analyse durchführen
        base_result = await self.analyze_compliance(entity_id)
        
        # Domänen-spezifische Regeln hinzufügen
        # ...
        
        return base_result
```

### Best Practices für Erweiterung

1. **Überschreiben von Template-Methoden:**
   ```python
   async def query_entity(self, entity_type, filters, limit):
       # Pre-processing
       filters = self._enhance_filters(filters)
       
       # Basis-Implementierung aufrufen
       result = await super().query_entity(entity_type, filters, limit)
       
       # Post-processing
       if result.success:
           result.data = self._transform_data(result.data)
       
       return result
   ```

2. **Neue Analyse-Methoden:**
   ```python
   async def calculate_risk_score(self, bst_nr, anl_nr) -> float:
       """Domänen-spezifische Risiko-Bewertung"""
       compliance = await self.analyze_compliance(bst_nr, anl_nr)
       # Custom risk calculation...
       return risk_score
   ```

3. **Domain-spezifische Enums:**
   ```python
   class MyDomainStatus(str, Enum):
       CUSTOM_STATUS_1 = "status1"
       CUSTOM_STATUS_2 = "status2"
   ```

## 📊 Usage Examples

### Beispiel 1: Basis-Nutzung

```python
from backend.agents.database_agent_testserver_extension import (
    DatabaseAgentTestServerExtension,
    EntityType
)

async def main():
    agent = DatabaseAgentTestServerExtension()
    
    try:
        # Generic Query
        result = await agent.query_entity(
            EntityType.VERFAHREN,
            filters={"status": "genehmigt"},
            limit=10
        )
        
        if result.success:
            print(f"Gefunden: {result.metadata['count']} Verfahren")
            for v in result.data:
                print(f"  - {v['verfahren_id']}: {v['verfahrensart']}")
    
    finally:
        await agent.close()
```

### Beispiel 2: Compliance-Analyse

```python
async def check_anlage_compliance():
    agent = DatabaseAgentTestServerExtension()
    
    try:
        compliance = await agent.analyze_compliance(
            "10650200000",
            "4001"
        )
        
        print(f"📊 Compliance-Report")
        print(f"Status: {compliance.status.value}")
        print(f"Score: {compliance.score:.1%}")
        
        if compliance.requires_action:
            print("\n⚠️ ACHTUNG: Maßnahmen erforderlich!")
            
            print("\n🔴 Issues:")
            for issue in compliance.issues:
                severity = issue['severity'].upper()
                message = issue['message']
                print(f"  [{severity}] {message}")
            
            print("\n💡 Empfehlungen:")
            for rec in compliance.recommendations:
                print(f"  - {rec}")
    
    finally:
        await agent.close()
```

### Beispiel 3: Multi-Entity Query

```python
async def get_comprehensive_data(bst_nr, anl_nr):
    agent = DatabaseAgentTestServerExtension()
    
    try:
        # Vollständige Entity-Daten
        result = await agent.get_complete_entity(bst_nr, anl_nr)
        
        if not result.success:
            print(f"Fehler: {result.error}")
            return
        
        anlage = result.data
        
        # Zugriff auf alle Relationen
        print(f"📍 Anlage: {anlage.anlage.bst_name}")
        print(f"\n📊 Daten:")
        print(f"  Verfahren: {len(anlage.verfahren)}")
        print(f"  Messungen: {len(anlage.messungen)}")
        print(f"  Dokumente: {len(anlage.dokumente)}")
        print(f"  Ansprechpartner: {len(anlage.ansprechpartner)}")
        print(f"  Wartungen: {len(anlage.wartungen)}")
        print(f"  Messreihen: {len(anlage.messreihen)}")
        print(f"  Compliance: {len(anlage.compliance_historie)}")
        
        # Statistik
        stats = anlage.statistik
        print(f"\n📈 Statistik:")
        print(f"  Überschreitungen: {stats['messungen_ueberschreitungen']}")
        print(f"  Offene Mängel: {stats['maengel_offen']}")
        print(f"  Geplante Wartungen: {stats['wartungen_geplant']}")
    
    finally:
        await agent.close()
```

### Beispiel 4: Custom Queries

```python
async def get_critical_data():
    agent = DatabaseAgentTestServerExtension()
    
    try:
        # Kritische Messreihen
        result = await agent.custom_query(
            "/messreihen/kritische",
            {"limit": 10}
        )
        
        if result.success:
            messreihen = result.data['messreihen']
            print(f"🔴 {len(messreihen)} kritische Messreihen:")
            
            for mr in messreihen:
                print(f"  - {mr['messart']}: {mr['ueberschreitungen_anzahl']} Überschreitungen")
                print(f"    Trend: {mr['trend']}, Bewertung: {mr['bewertung']}")
    
    finally:
        await agent.close()
```

## ✅ Testing

### Vollständiger Test

```bash
python test_database_agent_extension.py
```

### Erwartete Ausgabe

```
🧪 DatabaseAgent TestServer Extension - Comprehensive Tests
======================================================================

1️⃣ Server Health Check...
   Status: healthy
   Databases: bimschg, wka, immissionsschutz

2️⃣ Server Statistics...
   Verfahren: 800
   Messungen: 3000

3️⃣ Generic Entity Queries...
   ✅ Verfahren: 5 gefunden
   ✅ Messberichte: 5 gefunden
   ✅ Geplante Wartungen: 5 gefunden

...

✅ ALLE TESTS ERFOLGREICH!
```

## 📝 Zusammenfassung

### ✅ Features

- **Generisch**: Template-Pattern für Wiederverwendbarkeit
- **Type-Safe**: Enums, Type Hints, Dataclasses
- **Robust**: Success/Failure Pattern, umfassendes Logging
- **Async**: Non-blocking Operations
- **Erweiterbar**: Einfache Spezialisierung durch Vererbung
- **Getestet**: 10/10 Tests erfolgreich

### 📦 Komponenten

- **Core Class**: `DatabaseAgentTestServerExtension` (850 LOC)
- **Enums**: `EntityType`, `QueryStrategy`, `ComplianceStatus`
- **Result Objects**: `QueryResult`, `ComplianceResult`
- **Methods**: 15+ Generic + Convenience + Analysis Methods

### 🎯 Use Cases

1. **Basis-Queries**: Entity-Abfragen mit flexiblen Filtern
2. **Cross-Entity Relations**: Vollständige Daten mit allen Relationen
3. **Compliance-Analyse**: Automatische Bewertung mit Scoring
4. **Custom Queries**: Flexible Endpoint-Abfragen
5. **Spezialisierung**: Template für domänen-spezifische Agenten

---

**Status**: ✅ Production-Ready  
**Version**: 1.0  
**Autor**: VERITAS Team  
**Datum**: 18. Oktober 2025
