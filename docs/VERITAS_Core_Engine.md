# VERITAS Core Engine - Technische Dokumentation

## Überblick

Die **VERITAS Core Engine** (`veritas_core.py`) bildet das technische Herzstück des VERITAS-Systems. Als GUI-unabhängige Backend-Komponente stellt sie alle kritischen Services für Thread-Management, asynchrone Kommunikation, Backend-Integration und Session-Management bereit.

## Architekturprinzipien

### Design Philosophy
- **Separation of Concerns** - Keine GUI-Abhängigkeiten
- **Thread Safety** - Vollständig thread-sichere Operationen
- **Modular Design** - Klar getrennte Verantwortlichkeiten
- **Standardized Messaging** - Einheitliche Nachrichtenkommunikation

### Kernkomponenten

```
┌─────────────────────────────────────────────────────────────┐
│                    VERITAS CORE ENGINE                      │
├─────────────────────────────────────────────────────────────┤
│  ThreadManager     │ Queue-basierte Thread-Orchestrierung   │
│  SessionManager    │ Benutzer- und Sitzungsverwaltung       │
│  BackendProcessor  │ API-Integration und Datenverarbeitung  │
│  VeritasCore       │ Zentraler Orchestrator                 │
│  MessageSystem     │ Typisierte Nachrichtenkommunikation    │
└─────────────────────────────────────────────────────────────┘
```

## Nachrichtensystem (Message System)

### MessageType Enumeration
Das System definiert standardisierte Nachrichtentypen für verschiedene Kommunikationsszenarien:

- **CHAT** - Chat-Nachrichten zwischen Benutzern und KI
- **STATUS** - Systemstatus und Statusupdates
- **ERROR** - Fehlermeldungen und Ausnahmebehandlung
- **TASK** - Task-bezogene Kommunikation
- **NOTIFICATION** - System-Benachrichtigungen
- **BACKEND_RESPONSE** - Backend-API-Antworten

### Nachrichtenstrukturen

#### QueueMessage
Basis-Nachrichtenstruktur für die Queue-Kommunikation:
- **Typisierte Nachrichten** - Eindeutige Klassifizierung
- **Metadata-Support** - Erweiterte Kontextinformationen
- **Timestamp-Integration** - Automatische Zeitstempel

#### ChatMessage
Spezialisiert für Chat-Kommunikation:
- **Role-based Messaging** - User/Assistant/System-Rollen
- **Content Management** - Rich-Content-Unterstützung
- **Conversation Threading** - Konversationszuordnung

#### BackendResponse
Strukturierte Backend-API-Antworten:
- **Success/Error Handling** - Eindeutige Statusbehandlung
- **Response Data Management** - Typisierte Antwortdaten
- **HTTP-Integration** - Standard-HTTP-Response-Mapping

## Thread Management System

### ThreadManager Klasse
Der **ThreadManager** implementiert ein hochmodernes Queue-basiertes Thread-Management:

#### Kernfunktionen
- **Queue Registration** - Dynamische Queue-Registrierung
- **Thread-safe Operations** - Vollständig thread-sichere Operationen
- **Message Broadcasting** - Nachrichten-Verteilung an mehrere Empfänger
- **Queue Cleanup** - Automatische Ressourcenverwaltung

#### Thread-Safety Mechanismen
- **Queue.Queue Verwendung** - Thread-sichere Python-Queues
- **Lock-free Design** - Vermeidung von Race-Conditions
- **Graceful Shutdown** - Sauberes Thread-Shutdown

### Messaging Patterns

#### Publisher-Subscriber Pattern
```python
# Beispiel-Workflow (konzeptionell)
thread_manager.register_queue("ui_updates", ui_queue)
thread_manager.register_queue("backend", backend_queue)
thread_manager.broadcast_message(chat_message)
```

#### Request-Response Pattern
```python
# Backend-Integration
response = backend_processor.process_message(request)
thread_manager.send_to_queue("ui_updates", response)
```

## Session Management

### SessionManager Klasse
Zentrale Verwaltung von Benutzersitzungen und Anwendungszustand:

#### Session-Lifecycle
1. **Session Creation** - Neue Benutzersitzung initialisieren
2. **State Management** - Sitzungszustand verwalten
3. **Persistence** - Sitzungsdaten persistieren
4. **Cleanup** - Ressourcen freigeben

#### Features
- **User Context** - Benutzerspezifische Kontextinformationen
- **Session Persistence** - Sitzungsübergreifende Datenspeicherung
- **Multi-User Support** - Mehrbenutzerunterstützung
- **Security Integration** - UDS3-Sicherheitsintegration

## Backend Integration Engine

### BackendProcessor Klasse
Zentrale Schnittstelle für alle Backend-API-Integrationen:

#### API-Management
- **HTTP Client Management** - Effiziente HTTP-Verbindungen
- **Request/Response Handling** - Strukturierte API-Kommunikation
- **Error Handling** - Robuste Fehlerbehandlung
- **Retry Logic** - Automatische Wiederholungsversuche

#### Datenverarbeitung
- **Request Transformation** - Anfragen-Aufbereitung
- **Response Processing** - Antworten-Verarbeitung
- **Data Validation** - Eingabe- und Ausgabe-Validierung
- **Content Filtering** - Inhaltsfilterung

#### Integration Points
- **FastAPI Backend** - Hauptbackend-Service
- **External APIs** - Externe Datenquellen
- **Database Services** - Datenbankintegration
- **File Processing** - Dokumentenverarbeitung

## Core Engine Orchestrator

### VeritasCore Klasse
Der zentrale Orchestrator koordiniert alle Core-Komponenten:

#### Orchestrierung
- **Component Initialization** - Komponenteninitialisierung
- **Service Coordination** - Service-Koordination
- **Event Handling** - Ereignisbehandlung
- **Resource Management** - Ressourcenverwaltung

#### Integration Layer
- **GUI Integration** - Schnittstelle zur Benutzeroberfläche
- **Pipeline Integration** - Anbindung an Verarbeitungspipelines
- **API Gateway** - Zentrale API-Schnittstelle

## UDS3 Security Integration

### Sicherheitsframework
Die Core Engine integriert das UDS3 v3.0 Sicherheitsframework:

#### Protection Mechanisms
- **Module Verification** - Modulintegritätsprüfung
- **License Validation** - Lizenzvalidierung
- **Access Control** - Zugriffskontrolle
- **Audit Logging** - Sicherheitsprotokollierung

#### Security Layers
1. **Authentication** - Benutzerauthentifizierung
2. **Authorization** - Berechtigungsvalidierung
3. **Encryption** - Datenübertragungsverschlüsselung
4. **Audit Trail** - Nachverfolgbarkeit

## Performance-Optimierungen

### Queue-basierte Architektur
- **Non-blocking Operations** - Asynchrone Verarbeitung
- **Message Buffering** - Nachrichtenpufferung
- **Load Balancing** - Lastverteilung
- **Resource Pooling** - Ressourcen-Pooling

### Memory Management
- **Garbage Collection** - Optimierte Speicherverwaltung
- **Object Pooling** - Objektwiederverwendung
- **Lazy Loading** - Bedarfsgerechtes Laden
- **Cache Management** - Intelligente Zwischenspeicherung

## Error Handling und Resilience

### Exception Management
- **Typed Exceptions** - Typisierte Ausnahmebehandlung
- **Error Propagation** - Kontrollierte Fehlerweiterleitung
- **Recovery Mechanisms** - Automatische Wiederherstellung
- **Graceful Degradation** - Elegante Funktionsreduktion

### Logging und Monitoring
- **Structured Logging** - Strukturierte Protokollierung
- **Performance Metrics** - Leistungsmetriken
- **Health Checks** - Systemgesundheitsprüfungen
- **Alert Systems** - Warnsysteme

## Integration in das VERITAS Ecosystem

### Covina Integration
- **Compliance Checks** - Automatische Compliance-Prüfungen
- **Risk Assessment** - Risikobewertung
- **Regulatory Updates** - Regulatorische Aktualisierungen

### Clara Integration
- **Client Context** - Mandantenspezifische Kontextinformationen
- **Case Management** - Fallverwaltungsintegration
- **Communication Hub** - Kommunikationszentrale

## Factory Pattern und Utilities

### Factory Functions
Das Modul stellt Factory-Funktionen für einfache Objekterstellung bereit:

- **create_veritas_core()** - Core Engine Instanziierung
- **create_chat_message()** - Chat-Nachrichtenerstellung
- **create_status_message()** - Status-Nachrichtenerstellung
- **validate_message_type()** - Nachrichten-Validierung

### Utility Functions
Hilfsfunktionen für alltägliche Operationen:
- **Message Validation** - Nachrichtenvalidierung
- **Type Checking** - Typprüfung
- **Configuration Management** - Konfigurationsverwaltung

## Testing und Qualitätssicherung

### Unit Testing
- **Component Testing** - Komponententests
- **Integration Testing** - Integrationstests
- **Performance Testing** - Leistungstests
- **Security Testing** - Sicherheitstests

### Quality Metrics
- **Code Coverage** - Testabdeckung
- **Performance Benchmarks** - Leistungskennzahlen
- **Security Audits** - Sicherheitsaudits
- **Documentation Coverage** - Dokumentationsabdeckung

## Entwicklungsrichtlinien

### Best Practices
- **Thread-Safety First** - Thread-Sicherheit als Priorität
- **Message-driven Design** - Nachrichtenorientierte Architektur
- **Separation of Concerns** - Klare Verantwortungstrennung
- **Error-first Development** - Fehlerbehandlung als Designprinzip

### Code Standards
- **Type Hints** - Vollständige Typisierung
- **Documentation** - Umfassende Dokumentation
- **Testing** - Test-driven Development
- **Security** - Security-by-Design

---

*Die VERITAS Core Engine bildet das solide Fundament für das gesamte VERITAS-System und gewährleistet durch ihre robuste, thread-sichere Architektur eine zuverlässige und skalierbare Basis für alle darauf aufbauenden Komponenten.*

## Behördeneinsatz und Compliance-Integration

Die Core Engine ist auf den Einsatz in behördlichen Hochrisiko-Kontexten (EU AI Act) ausgelegt:

- Audit-Logging by Design: Jede asynchrone Nachricht (MessageSystem) kann in einen revisionssicheren Audit-Stream gespiegelt werden (z. B. Hash-Ketten, Write-Ahead-Logs) für DSFA/AI-Act-Nachweise.
- Datenfluss-Transparenz: Standardisierte Payloads (Universal JSON Payload) erlauben Zweckbindung, Datenminimierung und Provenance-Tracking entlang der Pipeline.
- Erklärbarkeitshooks: Schnittstellen zu Knowledge Graph/Attributionen (z. B. Quellzitate, Evidenzgraph) sind im BackendProcessor und Message-Hooks anbindbar.
- Rollen-/Freigabepunkte: Core liefert die technischen Ankerpunkte für menschliche Aufsicht und Freigaben, orchestriert durch Clara.

Siehe Referenz: `veritas/docs/00 _ KI-RAG für Verwaltungsrecht planen_.md` und `veritas/docs/01 _ Ein umfassendes Strategiepapier für ein KI.docx.md`.

## Betrieb: On-Premise und Hybrid

- On-Prem: Keine Cloud-Abhängigkeit im Kern; externe Integrationen sind über klar begrenzte Adapter realisiert.
- Hybrid: Optionale Outbound-Integrationen über Proxy/Whitelists; Netzwerkgrenzen werden im API-Manager forciert.
- Resilienz: Queue-basiertes Threading, Backpressure, Retry-Policies und Circuit-Breaker-Patterns.

## Schnittstellen zu Covina und Clara

- Covina (Compliance): Policy-Checks, DSFA-Artefakte, Datenklassifizierung und Audit-Publishing können in die Message Hooks (Pre-/Post-Processing) injiziert werden.
- Clara (CRM/Case): Kontextanreicherung (Fall-ID, Rolle, Mandant) wird in SessionManager/MessageMetadata transportiert; Vier-Augen-Freigaben werden als Workflows abgebildet.

## Interoperabilität und Standards

- JSON-Schema-Validierung für Payloads; OpenAPI für Services; Exportformate für föderierten Austausch.
- Kompatibilität mit Verwaltungsstandards (XÖV, DCAT) über optionale Mapping-Layer.

Weiterführend: `veritas/docs/02 _ Navigierung der übersehenen Themenfelder der KI in der öffentlichen Verwaltung.docx.md`.
