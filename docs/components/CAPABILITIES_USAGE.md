# VERITAS Capabilities System - Nutzungsanleitung

## Übersicht

Das VERITAS Capabilities System ermöglicht dynamische Feature-Erkennung zwischen Frontend und Backend. Das Frontend fragt beim Start den `/capabilities` Endpoint ab und passt sich automatisch an verfügbare Features an.

## Backend Endpoint

### `/capabilities` (GET)

Gibt umfassende System-Informationen zurück:

```json
{
  "system": {
    "version": "1.0.0-production",
    "environment": "production",
    "timestamp": "2025-10-05T20:23:13.995819"
  },
  "endpoints": {
    "chat": {
      "path": "/v2/query",
      "available": true,
      "production_ready": true,
      "uses_intelligent_pipeline": true
    },
    "streaming_chat": {
      "path": "/v2/query/stream",
      "available": true,
      "production_ready": true
    },
    ...
  },
  "features": {
    "ollama": {
      "available": true,
      "models": ["llama3:latest", "mistral:latest", ...],
      "model_count": 10,
      "default_model": "llama3:latest",
      "offline_mode": false
    },
    "uds3": {
      "available": true,
      "multi_db_distribution": true,
      "databases": ["vector", "graph", "relational"]
    },
    "intelligent_pipeline": {
      "available": true,
      "initialized": true,
      "features": [
        "multi_agent_orchestration",
        "rag_based_agent_selection",
        "llm_commentary",
        ...
      ],
      "available_agents": [
        "geo_context",
        "legal_framework",
        ...
      ]
    },
    "streaming": {
      "available": true,
      "endpoints": ["/v2/query/stream", "/v2/intelligent/query"],
      "features": ["progress_updates", "intermediate_results", "llm_thinking"]
    }
  },
  "modes": {
    "veritas": {
      "available": true,
      "requires": ["intelligent_pipeline"],
      "optimal": true
    },
    "chat": {
      "available": true,
      "requires": ["ollama"],
      "optimal": true
    },
    "vpb": {
      "available": true,
      "requires": ["intelligent_pipeline", "uds3"],
      "optimal": true
    },
    "covina": {
      "available": true,
      "requires": ["uds3", "intelligent_pipeline"],
      "optimal": true,
      "status": "experimental"
    }
  },
  "recommendations": [
    {
      "type": "success",
      "message": "Alle Features verfügbar - System voll funktionsfähig",
      "action": "Keine Aktion erforderlich"
    }
  ]
}
```

## Frontend Integration

### 1. Capabilities laden (beim App-Start)

```python
class VeritasApp:
    def __init__(self):
        # Capabilities beim Start laden
        self.capabilities: Dict[str, Any] = {}
        self._load_backend_capabilities()

    def _load_backend_capabilities(self):
        """Lädt Backend-Capabilities vom /capabilities Endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/capabilities", timeout=10)
            if response.status_code == 200:
                self.capabilities = response.json()
                # Log wichtige Infos
                logger.info("✅ Backend Capabilities geladen")
                return True
        except Exception as e:
            logger.error(f"❌ Capabilities-Fehler: {e}")
            self.capabilities = self._get_fallback_capabilities()
            return False
```

### 2. Feature-Verfügbarkeit prüfen

```python
# Prüfe ob Feature verfügbar ist
if app.is_feature_available('features.ollama.available'):
    # Zeige LLM-Modell-Auswahl
    models = app.get_capability_value('features.ollama.models', [])

# Prüfe ob Streaming verfügbar ist
if app.is_feature_available('features.streaming.available'):
    # Aktiviere Streaming-UI
    streaming_endpoints = app.get_capability_value('features.streaming.endpoints', [])
```

### 3. Modes dynamisch laden

```python
def get_available_question_methods(self):
    """Lädt Modi aus Capabilities"""
    modes = self.get_capability_value('modes', {})

    available_modes = []
    for mode_key, mode_info in modes.items():
        if mode_info.get('available', False):
            optimal = mode_info.get('optimal', False)
            available_modes.append({
                'key': mode_key,
                'display': mode_key.upper(),
                'optimal': optimal
            })

    # Sortiere: Optimale Modi zuerst
    available_modes.sort(key=lambda m: (not m['optimal'], m['key']))
    return available_modes
```

### 4. LLM-Modelle aus Capabilities

```python
def get_available_llm_models(self):
    """Holt Modelle aus Capabilities"""
    # Primär: Capabilities
    models = self.get_capability_value('features.ollama.models', [])
    if models:
        return models

    # Fallback: API-Call
    response = requests.get(f"{API_BASE_URL}/get_models")
    # ...
```

### 5. UI-Anpassung basierend auf Features

```python
# Zeige nur verfügbare Features
if app.is_feature_available('features.uds3.available'):
    # Zeige UDS3-spezifische UI-Elemente
    databases = app.get_capability_value('features.uds3.databases', [])
    for db in databases:
        # Erstelle DB-Auswahl

if app.is_feature_available('features.intelligent_pipeline.available'):
    # Zeige Agent-Auswahl
    agents = app.get_capability_value('features.intelligent_pipeline.available_agents', [])
```

## Utility-Methoden

### `is_feature_available(path: str) -> bool`

Prüft ob ein Feature verfügbar ist.

```python
# Beispiele:
app.is_feature_available('features.ollama.available')
app.is_feature_available('features.streaming.available')
app.is_feature_available('modes.veritas.optimal')
```

### `get_capability_value(path: str, default: Any) -> Any`

Holt einen Wert aus den Capabilities.

```python
# Beispiele:
models = app.get_capability_value('features.ollama.models', [])
version = app.get_capability_value('system.version', 'unknown')
agents = app.get_capability_value('features.intelligent_pipeline.available_agents', [])
```

## Best Practices

### 1. Immer Fallback bereitstellen

```python
# ✅ RICHTIG
models = app.get_capability_value('features.ollama.models', [])
if not models:
    models = ["llama3:latest", "mistral:latest"]  # Fallback

# ❌ FALSCH
models = app.capabilities['features']['ollama']['models']  # Kann KeyError werfen
```

### 2. Graceful Degradation

```python
# Wenn Feature nicht verfügbar: UI-Element ausblenden
if not app.is_feature_available('features.streaming.available'):
    streaming_button.config(state='disabled')
    tooltip.set_text("Streaming nicht verfügbar - Backend-Update erforderlich")
```

### 3. User-Feedback bei fehlenden Features

```python
recommendations = app.get_capability_value('recommendations', [])
for rec in recommendations:
    if rec['type'] == 'warning':
        show_warning_banner(rec['message'], rec['action'])
```

### 4. Periodisches Neu-Laden (optional)

```python
# Bei langer Laufzeit: Capabilities aktualisieren
def refresh_capabilities(self):
    """Aktualisiert Capabilities (z.B. alle 5 Minuten)"""
    old_capabilities = self.capabilities.copy()
    self._load_backend_capabilities()

    # Prüfe auf Änderungen
    if old_capabilities != self.capabilities:
        logger.info("⚡ Capabilities haben sich geändert - UI aktualisieren")
        self._update_ui_based_on_capabilities()
```

## Recommendation Types

Das Backend gibt verschiedene Typen von Empfehlungen:

- **`success`**: Alles funktioniert optimal
- **`info`**: Informative Hinweise (z.B. optionale Features)
- **`warning`**: Nicht-kritische Probleme (z.B. Ollama offline)
- **`error`**: Kritische Probleme (z.B. Pipeline nicht initialisiert)

```python
for rec in app.get_capability_value('recommendations', []):
    rec_type = rec['type']
    message = rec['message']
    action = rec.get('action', '')

    if rec_type == 'error':
        messagebox.showerror("System-Fehler", f"{message}\n\n{action}")
    elif rec_type == 'warning':
        show_warning_banner(message, action)
```

## Vorteile

1. **Dynamische Feature-Erkennung**: Frontend passt sich automatisch an Backend-Capabilities an
2. **Verbesserte User Experience**: Nur verfügbare Features werden angezeigt
3. **Klare Fehlermeldungen**: Recommendations geben konkrete Handlungsanweisungen
4. **Versionskontrolle**: System-Version wird mitgeliefert
5. **Zukunftssicher**: Neue Features können ohne Frontend-Update genutzt werden
6. **Offline-Fähigkeit**: Fallback-Capabilities wenn Backend nicht erreichbar

## Implementierungsstatus

### ✅ Implementiert

- [x] Backend `/capabilities` Endpoint
- [x] Frontend Capabilities-Loader
- [x] LLM-Modell-Erkennung via Capabilities
- [x] Modes-Erkennung via Capabilities
- [x] Feature-Detection Utility-Methoden
- [x] Fallback-System
- [x] Logging und Status-Anzeige

### 🔄 Geplant

- [ ] UI-Anpassung basierend auf Recommendations
- [ ] Periodisches Capabilities-Refresh
- [ ] Capabilities-Cache im LocalStorage
- [ ] Visual Indicator für optimale/suboptimale Modi
- [ ] Feature-Changelog-Anzeige bei Capabilities-Änderung

## Beispiel: Vollständige Integration

```python
class VeritasApp:
    def __init__(self):
        # 1. Capabilities laden
        self.capabilities = {}
        self._load_backend_capabilities()

        # 2. UI basierend auf Capabilities konfigurieren
        self._configure_ui_from_capabilities()

    def _configure_ui_from_capabilities(self):
        """Konfiguriert UI basierend auf verfügbaren Features"""

        # LLM-Modelle
        if self.is_feature_available('features.ollama.available'):
            models = self.get_capability_value('features.ollama.models', [])
            self.llm_selector.configure(values=models)
        else:
            self.llm_selector.configure(state='disabled')

        # Modi
        modes = self.get_capability_value('modes', {})
        for mode_key, mode_info in modes.items():
            if mode_info.get('optimal'):
                self.mode_selector.add_option(mode_key, badge='✅')
            elif mode_info.get('available'):
                self.mode_selector.add_option(mode_key, badge='⚠️')

        # Recommendations anzeigen
        recommendations = self.get_capability_value('recommendations', [])
        for rec in recommendations:
            if rec['type'] in ['warning', 'error']:
                self.show_notification(rec['message'], rec['type'])
```

---

**Version:** 1.0.0
**Erstellt:** 05.10.2025
**Autor:** VERITAS Development Team
