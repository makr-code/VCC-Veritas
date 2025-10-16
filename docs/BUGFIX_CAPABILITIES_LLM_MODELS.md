# Bugfix: LLM-Modelle aus Capabilities laden

**Datum:** 05.10.2025, 20:36 Uhr  
**Problem:** Frontend lud LLM-Modelle vom alten `/get_models` Endpoint statt aus Capabilities

## Problem-Diagnose

### Symptom
```
✅ Backend Capabilities geladen:
   Ollama: 10 Modelle verfügbar
   
ABER:
✅ 4 LLM-Modelle vom API abgerufen  ❌ (sollten 10 aus Capabilities sein!)
```

### Root Cause

Die `ChatWindowBase._get_available_models()` Methode sollte Modelle von der Parent-App (VeritasApp) holen, aber:

1. **`MainChatWindow` übergab den Parent nicht an die Basis-Klasse:**
   ```python
   # VORHER (FALSCH):
   class MainChatWindow(ChatWindowBase):
       def __init__(self, thread_manager: ThreadManager, veritas_app=None):
           super().__init__("MainChat", thread_manager)  # ❌ parent fehlt!
           self.veritas_app = veritas_app
   ```

2. **`ChildChatWindow` hatte dasselbe Problem:**
   ```python
   # VORHER (FALSCH):
   class ChildChatWindow(ChatWindowBase):
       def __init__(self, window_id: str, thread_manager: ThreadManager, veritas_app=None):
           super().__init__(window_id, thread_manager)  # ❌ parent fehlt!
   ```

3. **Ergebnis:** `self.parent` war `None` in `ChatWindowBase`, daher Fallback auf alten API-Call

## Lösung

### 1. Capabilities-Methoden zu `ModernVeritasApp` hinzugefügt

```python
class ModernVeritasApp:
    def _init_gui_state(self):
        # ...
        self.capabilities: Dict[str, Any] = {}  # ✅ Hinzugefügt
    
    def _load_backend_capabilities(self):
        """Lädt /capabilities Endpoint"""
        # ...
    
    def is_feature_available(self, feature_path: str) -> bool:
        """Prüft Feature-Verfügbarkeit"""
        # ...
    
    def get_capability_value(self, path: str, default: Any = None) -> Any:
        """Holt Wert aus Capabilities"""
        # ...
```

### 2. Parent-Parameter in Chat-Fenstern korrigiert

**MainChatWindow:**
```python
# NACHHER (KORREKT):
class MainChatWindow(ChatWindowBase):
    def __init__(self, thread_manager: ThreadManager, veritas_app=None):
        super().__init__("MainChat", thread_manager, parent=veritas_app)  # ✅ parent übergeben
        self.veritas_app = veritas_app
```

**ChildChatWindow:**
```python
# NACHHER (KORREKT):
class ChildChatWindow(ChatWindowBase):
    def __init__(self, window_id: str, thread_manager: ThreadManager, veritas_app=None):
        super().__init__(window_id, thread_manager, parent=veritas_app)  # ✅ parent übergeben
        self.veritas_app = veritas_app
```

### 3. `_get_available_models()` um Parent-Zugriff erweitert

```python
def _get_available_models(self):
    """Ruft verfügbare LLM-Modelle vom API ab"""
    # ✅ Prüfe zuerst ob parent App Capabilities hat
    if self.parent and hasattr(self.parent, 'get_available_llm_models'):
        try:
            logger.info(f"🔍 Versuche LLM-Modelle von Parent-App zu laden...")
            models = self.parent.get_available_llm_models()
            if models:
                logger.info(f"✅ {len(models)} LLM-Modelle aus Parent-App Capabilities")
                return models
        except Exception as e:
            logger.error(f"❌ Parent-App Capabilities Fehler: {e}")
    
    # Fallback: Direkter API-Call
    # ...
```

### 4. `get_available_llm_models()` für beide App-Typen angepasst

**VeritasApp:**
```python
def get_available_llm_models(self):
    """Ruft verfügbare LLM-Modelle aus den Capabilities ab"""
    if self.capabilities:
        models = self.get_capability_value('features.ollama.models', [])
        if models:
            logger.info(f"✅ {len(models)} LLM-Modelle aus Capabilities geladen")
            return models
    # Fallback zu /get_models API...
```

**ModernVeritasApp:** (identisch angepasst)

## Test-Ergebnisse

### ✅ Vorher (Fehler):
```
2025-10-05 20:35:35 - INFO - ℹ️ Kein Parent verfügbar - verwende API-Fallback
2025-10-05 20:35:35 - INFO - ✅ 4 LLM-Modelle vom API abgerufen  ❌
```

### ✅ Nachher (Korrekt):
```
2025-10-05 20:36:12 - INFO - 🔍 Versuche LLM-Modelle von Parent-App zu laden...
2025-10-05 20:36:12 - INFO - ✅ 10 LLM-Modelle aus Capabilities geladen
2025-10-05 20:36:12 - INFO - ✅ 10 LLM-Modelle aus Parent-App Capabilities  ✅
```

**Alle 10 Modelle aus Capabilities!** 🎉

## Betroffene Dateien

### `frontend/veritas_app.py`

1. **Zeile 2587:** `ModernVeritasApp._init_gui_state()` - Capabilities-Attribut hinzugefügt
2. **Zeilen 3647-3727:** Neue Capabilities-Methoden für `ModernVeritasApp`
3. **Zeile 3735:** `check_api_status()` - Lädt Capabilities beim Start
4. **Zeilen 1117-1152:** `ChatWindowBase._get_available_models()` - Parent-Zugriff hinzugefügt
5. **Zeile 1353:** `MainChatWindow.__init__()` - Parent-Parameter hinzugefügt
6. **Zeile 1933:** `ChildChatWindow.__init__()` - Parent-Parameter hinzugefügt
7. **Zeilen 2230-2262:** `VeritasApp.get_available_llm_models()` - Capabilities-Integration
8. **Zeilen 3790-3826:** `ModernVeritasApp.get_available_llm_models()` - Capabilities-Integration

## Zusammenfassung

### Problem
Frontend lud nur 4 Modelle vom alten `/get_models` Endpoint statt 10 aus den Capabilities.

### Ursache
Parent-App wurde nicht an Chat-Fenster übergeben, daher kein Zugriff auf Capabilities.

### Lösung
1. Parent-Parameter in `MainChatWindow` und `ChildChatWindow` korrekt übergeben
2. `_get_available_models()` prüft zuerst Parent-Capabilities
3. Capabilities-Methoden zu `ModernVeritasApp` hinzugefügt
4. Beide App-Typen nutzen jetzt Capabilities primär, API als Fallback

### Ergebnis
✅ **10 Modelle aus Capabilities korrekt geladen**  
✅ Fallback-Mechanismus funktioniert  
✅ Beide App-Typen (`VeritasApp`, `ModernVeritasApp`) unterstützt  
✅ Logging zeigt klare Quelle der Modelle

---

**Status:** ✅ Behoben und getestet  
**Commit-Message:** `fix: Load LLM models from capabilities instead of /get_models endpoint. Pass parent to ChatWindowBase in MainChatWindow and ChildChatWindow.`
