# VERITAS API Manager - Technische Dokumentation

## Überblick

Der **VERITAS API Manager** (`veritas_api_manager.py`) fungiert als intelligenter Startup-Manager für das gesamte VERITAS API-System. Er implementiert fortschrittliche Port-Management-Technologien, automatische Dependency-Checks und intelligente Systemkonfiguration, um eine reibungslose und zuverlässige Inbetriebnahme aller VERITAS-Services zu gewährleisten.

## Systemarchitektur

### Design Philosophy
- **Intelligent Port Management** - Automatische Port-Erkennung und -Zuweisung
- **Dependency Validation** - Proaktive Systemvalidierung
- **Process Orchestration** - Intelligente Prozessverwaltung
- **Self-Healing Architecture** - Selbstreparatur-Mechanismen

### Kernkomponenten

```
┌─────────────────────────────────────────────────────────────┐
│                 VERITAS API MANAGER                         │
├─────────────────────────────────────────────────────────────┤
│  Port Management   │ Intelligente Port-Erkennung/-Zuweisung │
│  Dependency Check  │ Proaktive Systemvalidierung            │
│  Process Control   │ Service-Lifecycle-Management           │
│  Smart Startup     │ Automatisierte Initialisierung         │
│  Conflict Resolution │ Prozesskonflikt-Behandlung          │
└─────────────────────────────────────────────────────────────┘
```

## VeritasAPIManager Klasse

### Initialisierung und Konfiguration

#### Constructor Parameters
- **default_port**: Standard-Port (Default: 5000)
- **host**: Bind-Adresse (Default: "0.0.0.0")
- **project_root**: Projektverzeichnis (automatisch erkannt)

#### Instance Variables
- **current_port**: Aktuell verwendeter Port
- **process**: Referenz auf den laufenden API-Prozess
- **project_root**: Projektverzeichnis-Pfad

### Intelligentes Port-Management

#### Port-Verfügbarkeitsprüfung
**Funktionalität:** `check_port_availability(port: int) -> bool`

**Mechanismus:**
- **Socket-basierte Verfügbarkeitsprüfung** - Direkte Netzwerk-Socket-Prüfung
- **Exception-handling** - Robuste Fehlerbehandlung
- **Cross-platform Compatibility** - Plattformübergreifende Kompatibilität

**Technische Implementation:**
```python
# Konzeptioneller Ansatz
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.settimeout(1)
    result = sock.connect_ex((self.host, port))
    return result != 0  # Port verfügbar wenn Verbindung fehlschlägt
```

#### Dynamische Port-Suche
**Funktionalität:** `find_available_port(start_port: int, max_attempts: int) -> Optional[int]`

**Suchalgorithmus:**
- **Sequential Search** - Sequenzielle Portsuche ab Startport
- **Configurable Range** - Konfigurierbare Suchreichweite
- **Early Termination** - Frühzeitige Beendigung bei Fund
- **Fallback Mechanisms** - Fallback-Strategien

**Benefits:**
- **Automatic Port Assignment** - Automatische Port-Zuweisung
- **Conflict Avoidance** - Konfliktvermeidung
- **Resource Optimization** - Ressourcenoptimierung
- **Deployment Flexibility** - Deployment-Flexibilität

### Prozess-Management und Überwachung

#### VERITAS-Prozess-Erkennung
**Funktionalität:** `find_veritas_processes() -> List[Tuple[int, str]]`

**Erkennungsmechanismen:**
- **Process Name Matching** - Prozessname-Matching
- **Command Line Analysis** - Kommandozeilen-Analyse
- **Port Binding Detection** - Port-Binding-Erkennung
- **Resource Usage Monitoring** - Ressourcenverbrauchsüberwachung

**Erkannte Prozesse:**
- **VERITAS API Server** - Haupt-API-Server
- **Background Services** - Hintergrunddienste
- **Database Processes** - Datenbankprozesse
- **Worker Threads** - Worker-Threads

#### Konfligierende Prozesse verwalten
**Funktionalität:** `kill_conflicting_processes() -> bool`

**Conflict Resolution Strategy:**
1. **Process Identification** - Prozessidentifikation
2. **Impact Assessment** - Auswirkungsanalyse
3. **Graceful Shutdown** - Ordnungsgemäßes Herunterfahren
4. **Force Termination** - Zwangsbeendigung (falls nötig)
5. **Resource Cleanup** - Ressourcenbereinigung

### Dependency-Management

#### System-Dependency-Validation
**Funktionalität:** `check_dependencies() -> bool`

**Validierte Dependencies:**
- **Core Python Modules** - Kern-Python-Module
  - `fastapi` - Web-Framework
  - `uvicorn` - ASGI-Server
  - `pydantic` - Datenvalidierung
  - `requests` - HTTP-Client
- **System Dependencies** - Systemabhängigkeiten
- **Database Requirements** - Datenbankanforderungen
- **Network Dependencies** - Netzwerkabhängigkeiten

**Validation Process:**
```python
# Konzeptionelle Dependency-Prüfung
for module in required_modules:
    try:
        __import__(module)
        logger.info(f"✅ {module} verfügbar")
    except ImportError:
        missing_modules.append(module)
        logger.error(f"❌ {module} fehlt")
```

#### Automatic Dependency Resolution
- **Missing Module Detection** - Erkennung fehlender Module
- **Installation Recommendations** - Installationsempfehlungen
- **Version Compatibility Checks** - Versionskompatibilitätsprüfungen
- **Environment Validation** - Umgebungsvalidierung

### Smart Startup System

#### Intelligente Initialisierung
**Funktionalität:** `smart_startup() -> bool`

**Startup Workflow:**
1. **System Health Check** - Systemgesundheitsprüfung
2. **Dependency Validation** - Abhängigkeitsvalidierung
3. **Port Assignment** - Port-Zuweisung
4. **Process Cleanup** - Prozessbereinigung
5. **Service Launch** - Service-Start
6. **Health Verification** - Gesundheitsverifikation

**Decision Tree:**
```
Dependencies OK? → Port Available? → Conflicts Resolved? → Start Service
     ↓ No              ↓ No              ↓ No               ↓
Install Deps → Find Alternative → Resolve Conflicts → Verify Health
```

#### API-Server-Management
**Funktionalität:** `start_api_server(port: int) -> bool`

**Server Launch Process:**
- **Process Spawning** - Prozesserstellung
- **Environment Setup** - Umgebungseinrichtung
- **Configuration Management** - Konfigurationsverwaltung
- **Health Monitoring** - Gesundheitsüberwachung

**Server Monitoring:**
- **Process Health Checks** - Prozessgesundheitsprüfungen
- **Response Time Monitoring** - Antwortzeit-Überwachung
- **Error Rate Tracking** - Fehlerrate-Verfolgung
- **Resource Usage Monitoring** - Ressourcenverbrauch-Überwachung

### Interaktive Management-Features

#### Interactive Mode
**Funktionalität:** `interactive_mode()`

**Benutzerinteraktion:**
- **Real-time Status Display** - Echtzeit-Statusanzeige
- **Command Interface** - Befehlsschnittstelle
- **Configuration Options** - Konfigurationsoptionen
- **Diagnostic Tools** - Diagnosewerkzeuge

**Verfügbare Befehle:**
- **Status Check** - Statusprüfung
- **Service Restart** - Service-Neustart
- **Port Change** - Port-Änderung
- **Debug Mode** - Debug-Modus

#### Server Information Display
**Funktionalität:** `show_server_info()`

**Angezeigte Informationen:**
- **Service Status** - Service-Status
- **Port Configuration** - Port-Konfiguration
- **Process Information** - Prozessinformationen
- **Performance Metrics** - Leistungsmetriken

### Error Handling und Resilience

#### Exception Management
**Robuste Fehlerbehandlung:**

- **Typed Exceptions** - Typisierte Ausnahmen
- **Graceful Degradation** - Elegante Funktionsreduktion
- **Recovery Mechanisms** - Wiederherstellungsmechanismen
- **User-friendly Error Messages** - Benutzerfreundliche Fehlermeldungen

#### Logging und Monitoring
**Umfassendes Monitoring:**

- **Structured Logging** - Strukturierte Protokollierung
- **Performance Metrics** - Leistungsmetriken
- **Health Dashboards** - Gesundheits-Dashboards
- **Alert Systems** - Warnsysteme

### CLI Interface

#### Command-Line Arguments
**Flexible Kommandozeilensteuerung:**

- **Start Scheduler** - Scheduler starten
- **Manual Update** - Manuelle Updates
- **Interactive Mode** - Interaktiver Modus
- **Configuration Override** - Konfigurationsüberschreibung

#### Automation Support
**DevOps-Integration:**

- **Scriptable Interface** - Skriptfähige Schnittstelle
- **Exit Codes** - Standard-Exit-Codes
- **JSON Output** - JSON-Ausgabeformat
- **Silent Mode** - Stiller Modus

### Integration in das VERITAS Ecosystem

#### Core Engine Integration
**Nahtlose Backend-Integration:**

- **Service Discovery** - Service-Erkennung
- **Health Monitoring** - Gesundheitsüberwachung
- **Configuration Sync** - Konfigurationssynchronisation
- **Performance Optimization** - Leistungsoptimierung

#### Security Framework Integration
**UDS3-Sicherheitsintegration:**

- **Service Authentication** - Service-Authentifizierung
- **Encrypted Communication** - Verschlüsselte Kommunikation
- **Access Control** - Zugriffskontrolle
- **Audit Logging** - Auditprotokollierung

### Performance-Optimierungen

#### Startup Performance
**Optimierte Startzeiten:**

- **Parallel Initialization** - Parallele Initialisierung
- **Lazy Loading** - Bedarfsgerechtes Laden
- **Cache Utilization** - Cache-Nutzung
- **Resource Preallocation** - Ressourcenvorab-Allokation

#### Runtime Performance
**Laufzeit-Optimierungen:**

- **Process Pooling** - Prozess-Pooling
- **Connection Reuse** - Verbindungswiederverwendung
- **Memory Management** - Speicherverwaltung
- **Garbage Collection Optimization** - Garbage Collection-Optimierung

### Testing und Qualitätssicherung

#### Automated Testing
**Umfassendes Test-Framework:**

- **Unit Tests** - Komponententests
- **Integration Tests** - Integrationstests
- **Performance Tests** - Leistungstests
- **Security Tests** - Sicherheitstests

#### Quality Metrics
**Qualitätskennzahlen:**

- **Code Coverage** - Code-Abdeckung
- **Performance Benchmarks** - Leistungsbenchmarks
- **Reliability Metrics** - Zuverlässigkeitsmetriken
- **Security Audit Results** - Sicherheitsaudit-Ergebnisse

### Entwicklungsrichtlinien

#### Best Practices
- **Idempotent Operations** - Idempotente Operationen
- **Graceful Error Handling** - Elegante Fehlerbehandlung
- **Resource Cleanup** - Ressourcenbereinigung
- **Security-First Design** - Sicherheitsorientiertes Design

#### Maintenance Guidelines
- **Regular Health Checks** - Regelmäßige Gesundheitsprüfungen
- **Performance Monitoring** - Leistungsüberwachung
- **Security Updates** - Sicherheitsupdates
- **Documentation Maintenance** - Dokumentationspflege

---

*Der VERITAS API Manager stellt sicher, dass das gesamte VERITAS-System zuverlässig, effizient und sicher gestartet und betrieben wird, und bildet damit die operative Grundlage für alle nachgelagerten Services und Funktionalitäten.*

## Öffentlicher Sektor: Sicherheits- und Compliance-Aspekte

- Netzwerk-Härtung: Strikte Port-Zuordnung, Kollisionserkennung, Least-Privilege-Bindings, optional mTLS und IP-Whitelisting.
- Policy-Compliance: Konfigurationsprofile pro Behörde/Netzsegment; Start verweigern bei Policy-Verstößen (z. B. verbotene Ports/Bindings).
- DSFA-konforme Protokollierung: Start-/Stop-Ereignisse, Portnutzung, Abhängigkeiten und Fehlerpfade werden nachvollziehbar geloggt.
- Betriebsfreigabe: Vordefinierte Checklisten (Abhängigkeiten, Schemas, Zertifikate, Healthchecks) für wiederholbare Go-Lives.

Verweise: `veritas/docs/00 _ KI-Integration in Behördenprozesse.md`, `veritas/docs/02 _ Navigierung der übersehenen Themenfelder der KI in der öffentlichen Verwaltung.docx.md`.