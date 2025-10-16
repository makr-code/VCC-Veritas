# VERITAS Chat Persistence & Session Management

**Version:** v3.20.0  
**Priorität:** ⭐⭐⭐ HIGH  
**Geschätzter Aufwand:** 4-6 Stunden  
**Status:** 🔄 TODO

---

## 🎯 Ziel

**Automatisches Speichern und Wiederherstellen von Chat-Konversationen:**
1. ✅ Chat-Logs als JSON speichern (Auto-Save)
2. ✅ Letzte Session bei Neustart wiederherstellen
3. ✅ Chat-History in LLM-Kontext einbeziehen (Context Window)
4. ✅ Multi-Session Management (mehrere Chats parallel)

---

## 📋 Task List

### Phase 1: Chat-Log Persistierung (1-2h)

#### Task 1.1: JSON-Schema für Chat-Logs ⏱️ 30min

**Ziel:** Standardisiertes Format für Chat-Speicherung

**Schema:**
```json
{
  "session_id": "uuid-v4",
  "created_at": "2025-10-12T10:00:00Z",
  "updated_at": "2025-10-12T12:30:00Z",
  "title": "BImSchG Anfrage vom 12.10.2025",
  "llm_model": "llama3.1:8b",
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "Was ist das BImSchG?",
      "timestamp": "2025-10-12T10:01:00Z",
      "attachments": []
    },
    {
      "id": "msg_2",
      "role": "assistant",
      "content": "Das Bundes-Immissionsschutzgesetz...",
      "timestamp": "2025-10-12T10:01:36Z",
      "metadata": {
        "confidence": 0.887,
        "duration_seconds": 36.88,
        "sources_count": 8,
        "agents_used": ["EnvironmentalAgent", "BuildingAgent"],
        "sources": [
          {
            "id": "doc_123",
            "title": "BImSchG Gesetzestext",
            "relevance": 0.95,
            "snippet": "..."
          }
        ]
      }
    }
  ],
  "metadata": {
    "total_messages": 2,
    "total_tokens": 1234,
    "avg_confidence": 0.887,
    "tags": ["umweltrecht", "bimschg"],
    "starred": false
  }
}
```

**Deliverables:**
- [ ] `shared/chat_schema.py` - Pydantic Models für Chat-Schema
- [ ] JSON-Schema Validation
- [ ] Unit Tests für Schema

**Code-Beispiel:**
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attachments: List[str] = []
    metadata: Optional[dict] = None

class ChatSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    title: str = "Neue Konversation"
    llm_model: str = "llama3.1:8b"
    messages: List[ChatMessage] = []
    metadata: dict = {}
```

---

#### Task 1.2: Auto-Save Service ⏱️ 45min

**Ziel:** Automatisches Speichern nach jeder Nachricht

**Features:**
- ✅ Auto-Save nach jeder User/Assistant Message
- ✅ Speicherort: `data/chat_sessions/{session_id}.json`
- ✅ Backup-Strategie: Tägliche Backups in `data/chat_backups/`
- ✅ Max. Chat-Größe: 10 MB (Warning bei Überschreitung)

**Deliverables:**
- [ ] `backend/services/chat_persistence_service.py` (200 LOC)
  - `save_chat_session(session: ChatSession)` - Speichert Session
  - `load_chat_session(session_id: str)` - Lädt Session
  - `list_chat_sessions()` - Liste aller Sessions
  - `delete_chat_session(session_id: str)` - Löscht Session
  - `create_backup()` - Erstellt tägliches Backup

**Code-Beispiel:**
```python
import json
import os
from pathlib import Path
from datetime import datetime
import shutil

class ChatPersistenceService:
    def __init__(self, base_path: str = "data/chat_sessions"):
        self.base_path = Path(base_path)
        self.backup_path = Path("data/chat_backups")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    def save_chat_session(self, session: ChatSession) -> bool:
        """Speichert Chat-Session als JSON"""
        try:
            session.updated_at = datetime.utcnow()
            file_path = self.base_path / f"{session.session_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session.dict(), f, indent=2, default=str)
            
            # Auto-Backup wenn Session größer als 5 MB
            if file_path.stat().st_size > 5 * 1024 * 1024:
                self.create_backup(session.session_id)
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Session: {e}")
            return False
    
    def load_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Lädt Chat-Session aus JSON"""
        try:
            file_path = self.base_path / f"{session_id}.json"
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return ChatSession(**data)
        except Exception as e:
            logger.error(f"Fehler beim Laden der Session: {e}")
            return None
    
    def list_chat_sessions(self, limit: int = 50) -> List[dict]:
        """Liste aller Chat-Sessions (sortiert nach updated_at)"""
        sessions = []
        for file_path in self.base_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append({
                    'session_id': data['session_id'],
                    'title': data.get('title', 'Unbenannt'),
                    'updated_at': data['updated_at'],
                    'message_count': len(data.get('messages', []))
                })
            except Exception as e:
                logger.warning(f"Fehler beim Lesen von {file_path}: {e}")
        
        # Sortiere nach updated_at (neueste zuerst)
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        return sessions[:limit]
```

---

#### Task 1.3: Frontend Integration ⏱️ 30min

**Ziel:** Auto-Save in `ModernVeritasApp` integrieren

**Änderungen:**
- [ ] `frontend/veritas_app.py`: Auto-Save nach `_handle_response()`
- [ ] `frontend/veritas_app.py`: Session-ID beim Start generieren
- [ ] `frontend/veritas_app.py`: "Speichern als..." Dialog für Custom Title

**Code-Beispiel:**
```python
class ModernVeritasApp:
    def __init__(self):
        # ... existing code ...
        self.session_id = str(uuid.uuid4())
        self.persistence_service = ChatPersistenceService()
        self.auto_save_enabled = True
    
    def _handle_response(self, response_text, sources, ...):
        # ... existing code ...
        
        # Auto-Save nach Assistant-Antwort
        if self.auto_save_enabled:
            self._auto_save_chat()
    
    def _auto_save_chat(self):
        """Speichert aktuellen Chat automatisch"""
        try:
            session = ChatSession(
                session_id=self.session_id,
                title=self._generate_title(),
                llm_model=self.selected_llm,
                messages=[ChatMessage(**msg) for msg in self.chat_messages]
            )
            self.persistence_service.save_chat_session(session)
        except Exception as e:
            logger.error(f"Auto-Save Fehler: {e}")
    
    def _generate_title(self) -> str:
        """Generiert Titel aus erster User-Frage"""
        if self.chat_messages:
            first_user_msg = next((m for m in self.chat_messages if m['role'] == 'user'), None)
            if first_user_msg:
                content = first_user_msg['content']
                # Kürze auf 50 Zeichen
                return content[:47] + "..." if len(content) > 50 else content
        return f"Chat vom {datetime.now().strftime('%d.%m.%Y %H:%M')}"
```

---

### Phase 2: Session Wiederherstellung (1-2h)

#### Task 2.1: "Letzte Session wiederherstellen" beim Start ⏱️ 30min

**Ziel:** Automatisches Laden der letzten Chat-Session

**Features:**
- ✅ Beim Start: Dialog "Letzte Session wiederherstellen?"
- ✅ Falls "Ja": Lade letzte Session (neueste `updated_at`)
- ✅ Falls "Nein": Neue Session starten
- ✅ Settings: "Immer letzte Session laden" Checkbox

**Deliverables:**
- [ ] `frontend/ui/veritas_ui_session_dialog.py` (150 LOC)
- [ ] `frontend/veritas_app.py`: Integration in `__init__()`

**Code-Beispiel:**
```python
class SessionRestoreDialog:
    def __init__(self, parent, persistence_service):
        self.parent = parent
        self.persistence_service = persistence_service
        self.result = None
    
    def show(self) -> Optional[str]:
        """Zeigt Dialog und gibt session_id zurück (oder None)"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Session wiederherstellen")
        dialog.geometry("500x300")
        
        # Letzte Sessions auflisten
        sessions = self.persistence_service.list_chat_sessions(limit=10)
        
        if not sessions:
            messagebox.showinfo("Keine Sessions", "Keine gespeicherten Sessions gefunden.")
            return None
        
        # Liste der letzten 10 Sessions
        tk.Label(dialog, text="Letzte Chat-Sessions:", font=("Arial", 12, "bold")).pack(pady=10)
        
        listbox = tk.Listbox(dialog, height=10)
        for session in sessions:
            display = f"{session['title']} ({session['message_count']} Nachrichten) - {session['updated_at']}"
            listbox.insert(tk.END, display)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def on_restore():
            selection = listbox.curselection()
            if selection:
                self.result = sessions[selection[0]]['session_id']
                dialog.destroy()
        
        tk.Button(button_frame, text="Wiederherstellen", command=on_restore).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Neu starten", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        dialog.transient(self.parent)
        dialog.grab_set()
        self.parent.wait_window(dialog)
        
        return self.result
```

---

#### Task 2.2: Session-Verwaltung UI ⏱️ 45min

**Ziel:** GUI für Session-Management

**Features:**
- ✅ "Sessions verwalten" im Hamburger-Menü
- ✅ Dialog mit Liste aller Sessions
- ✅ Aktionen: Öffnen, Umbenennen, Löschen, Exportieren
- ✅ Suche/Filter nach Titel, Datum, Tags

**Deliverables:**
- [ ] `frontend/ui/veritas_ui_session_manager.py` (300 LOC)

**UI-Mockup:**
```
┌─────────────────────────────────────────────────────────────┐
│  Session-Verwaltung                                    [X]  │
├─────────────────────────────────────────────────────────────┤
│  Suche: [____________________]  🔍                         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ☑ BImSchG Anfrage (12.10.2025 10:00)               │  │
│  │   8 Nachrichten | Confidence: 88.7%                 │  │
│  │                                                      │  │
│  │ ☐ Baurecht Frage (11.10.2025 14:30)                │  │
│  │   12 Nachrichten | Confidence: 92.1%                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [Öffnen] [Umbenennen] [Löschen] [Exportieren] [Schließen]│
└─────────────────────────────────────────────────────────────┘
```

---

### Phase 3: LLM Context Integration (1-2h)

#### Task 3.1: Chat-History in LLM-Kontext ⏱️ 45min

**Ziel:** Vergangene Nachrichten in LLM-Prompt einbeziehen

**Features:**
- ✅ Letzte N Nachrichten als Kontext
- ✅ Token-Limit beachten (z.B. max 2000 Tokens für History)
- ✅ Sliding Window: Neueste Nachrichten priorisieren
- ✅ Relevanz-basierte Auswahl (ähnliche Fragen bevorzugen)

**Deliverables:**
- [ ] `backend/agents/context_manager.py` (250 LOC)
  - `build_conversation_context(messages, max_tokens)`
  - `select_relevant_messages(current_query, history)`
  - `estimate_tokens(text)` - Token-Schätzung

**Code-Beispiel:**
```python
class ConversationContextManager:
    def __init__(self, max_context_tokens: int = 2000):
        self.max_context_tokens = max_context_tokens
    
    def build_conversation_context(
        self, 
        current_query: str,
        messages: List[ChatMessage],
        strategy: str = "sliding_window"  # "sliding_window" | "relevance" | "all"
    ) -> str:
        """Erstellt Kontext aus Chat-History"""
        
        if strategy == "sliding_window":
            return self._sliding_window_context(messages)
        elif strategy == "relevance":
            return self._relevance_based_context(current_query, messages)
        else:
            return self._all_messages_context(messages)
    
    def _sliding_window_context(self, messages: List[ChatMessage]) -> str:
        """Neueste N Nachrichten (bis Token-Limit)"""
        context_parts = []
        current_tokens = 0
        
        # Reverse iteration (neueste zuerst)
        for msg in reversed(messages):
            msg_text = f"{msg.role}: {msg.content}"
            msg_tokens = self.estimate_tokens(msg_text)
            
            if current_tokens + msg_tokens > self.max_context_tokens:
                break
            
            context_parts.insert(0, msg_text)
            current_tokens += msg_tokens
        
        return "\n\n".join(context_parts)
    
    def _relevance_based_context(
        self, 
        current_query: str, 
        messages: List[ChatMessage]
    ) -> str:
        """Wählt relevanteste Nachrichten basierend auf Similarity"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        # TF-IDF Similarity
        vectorizer = TfidfVectorizer()
        texts = [msg.content for msg in messages if msg.role == 'user']
        texts.append(current_query)
        
        if len(texts) < 2:
            return ""
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
        
        # Top-K relevanteste Nachrichten
        top_k_indices = similarities.argsort()[-5:][::-1]
        
        context_parts = []
        current_tokens = 0
        
        for idx in top_k_indices:
            msg = messages[idx]
            # Füge auch die zugehörige Antwort hinzu
            msg_text = f"User: {msg.content}"
            if idx + 1 < len(messages) and messages[idx + 1].role == 'assistant':
                msg_text += f"\nAssistant: {messages[idx + 1].content}"
            
            msg_tokens = self.estimate_tokens(msg_text)
            if current_tokens + msg_tokens > self.max_context_tokens:
                break
            
            context_parts.append(msg_text)
            current_tokens += msg_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def estimate_tokens(self, text: str) -> int:
        """Grobe Token-Schätzung (1 Token ≈ 4 Zeichen)"""
        return len(text) // 4
```

---

#### Task 3.2: Ollama Integration ⏱️ 30min

**Ziel:** Chat-History in Ollama-Requests integrieren

**Änderungen:**
- [ ] `backend/agents/veritas_ollama_client.py`: Context in System-Prompt
- [ ] Format: "Bisherige Konversation:\n{context}\n\nAktuelle Frage:\n{query}"

**Code-Beispiel:**
```python
class VeritasOllamaClient:
    def __init__(self):
        # ... existing code ...
        self.context_manager = ConversationContextManager(max_context_tokens=2000)
    
    async def query_with_context(
        self, 
        query: str, 
        chat_history: List[ChatMessage],
        context_strategy: str = "sliding_window"
    ):
        """Query mit Chat-History Kontext"""
        
        # Erstelle Kontext aus History
        conversation_context = self.context_manager.build_conversation_context(
            current_query=query,
            messages=chat_history,
            strategy=context_strategy
        )
        
        # Erweitere System-Prompt
        system_prompt = self.prompt_templates.get_system_prompt(mode=PromptMode.USER_FACING)
        
        if conversation_context:
            system_prompt += f"\n\n## Bisherige Konversation:\n{conversation_context}"
        
        # Ollama Query
        response = await self.ollama.generate(
            model=self.model,
            prompt=query,
            system=system_prompt,
            options=self.options
        )
        
        return response
```

---

### Phase 4: Testing & Validation (1h)

#### Task 4.1: Unit Tests ⏱️ 30min

**Test-Dateien:**
- [ ] `tests/backend/test_chat_persistence.py` (200 LOC)
  - Test: save_chat_session()
  - Test: load_chat_session()
  - Test: list_chat_sessions()
  - Test: delete_chat_session()
  - Test: create_backup()

- [ ] `tests/backend/test_context_manager.py` (150 LOC)
  - Test: sliding_window_context()
  - Test: relevance_based_context()
  - Test: estimate_tokens()
  - Test: max_token_limit

**Test-Beispiel:**
```python
def test_save_and_load_chat_session():
    service = ChatPersistenceService(base_path="tests/temp_sessions")
    
    # Erstelle Test-Session
    session = ChatSession(
        session_id="test_123",
        title="Test Chat",
        messages=[
            ChatMessage(role="user", content="Hallo"),
            ChatMessage(role="assistant", content="Guten Tag!")
        ]
    )
    
    # Speichern
    assert service.save_chat_session(session) == True
    
    # Laden
    loaded = service.load_chat_session("test_123")
    assert loaded is not None
    assert loaded.title == "Test Chat"
    assert len(loaded.messages) == 2
    assert loaded.messages[0].content == "Hallo"
```

---

#### Task 4.2: Integration Tests ⏱️ 30min

**Test-Szenarios:**
- [ ] **Szenario 1:** Neuer Chat → Auto-Save → Neustart → Wiederherstellen
- [ ] **Szenario 2:** Multi-Message Chat → Context in LLM → Relevante Antwort
- [ ] **Szenario 3:** 100+ Nachrichten → Token-Limit → Sliding Window
- [ ] **Szenario 4:** Session löschen → Bestätigung → Datei entfernt

**Test-Script:**
```python
# tests/integration/test_chat_persistence_e2e.py

def test_chat_persistence_full_workflow():
    """E2E Test: Chat erstellen, speichern, laden, verwenden"""
    
    # 1. Erstelle neuen Chat
    app = ModernVeritasApp()
    app.session_id = "test_e2e_session"
    
    # 2. Sende erste Nachricht
    app.chat_messages.append({
        'role': 'user',
        'content': 'Was ist das BImSchG?'
    })
    app._auto_save_chat()
    
    # 3. Simuliere Assistant-Antwort
    app.chat_messages.append({
        'role': 'assistant',
        'content': 'Das Bundes-Immissionsschutzgesetz...'
    })
    app._auto_save_chat()
    
    # 4. Prüfe gespeicherte Datei
    file_path = Path("data/chat_sessions/test_e2e_session.json")
    assert file_path.exists()
    
    # 5. Lade Session
    persistence = ChatPersistenceService()
    loaded_session = persistence.load_chat_session("test_e2e_session")
    assert loaded_session is not None
    assert len(loaded_session.messages) == 2
    
    # 6. Verwende Context Manager
    context_mgr = ConversationContextManager()
    context = context_mgr.build_conversation_context(
        current_query="Gibt es Ausnahmen?",
        messages=loaded_session.messages
    )
    assert "BImSchG" in context
    assert "Bundes-Immissionsschutz" in context
```

---

## 📊 Success Criteria

### Functional Requirements

- [x] **Auto-Save:** Chat wird automatisch nach jeder Nachricht gespeichert
- [x] **Session Restore:** Letzte Session kann bei Neustart wiederhergestellt werden
- [x] **LLM Context:** Chat-History wird in LLM-Kontext einbezogen
- [x] **Session Management:** UI zum Verwalten aller Sessions
- [x] **Backup:** Tägliche Backups werden erstellt

### Non-Functional Requirements

- [x] **Performance:** Auto-Save <100ms
- [x] **Storage:** Max 10 MB pro Session (Warning)
- [x] **Context Size:** Max 2000 Tokens für History
- [x] **UI Response:** Session-Dialog <500ms
- [x] **Reliability:** 99.9% Save-Success-Rate

---

## 📝 Implementation Checklist

### Phase 1: Persistierung ✅
- [ ] Task 1.1: JSON-Schema erstellt
- [ ] Task 1.2: ChatPersistenceService implementiert
- [ ] Task 1.3: Frontend Auto-Save integriert

### Phase 2: Session Management ✅
- [ ] Task 2.1: Session-Restore-Dialog
- [ ] Task 2.2: Session-Manager UI

### Phase 3: LLM Context ✅
- [ ] Task 3.1: ConversationContextManager
- [ ] Task 3.2: Ollama Integration

### Phase 4: Testing ✅
- [ ] Task 4.1: Unit Tests (15 Tests)
- [ ] Task 4.2: Integration Tests (4 Szenarien)

---

## 🚀 Deployment

### Files Created
```
shared/
  chat_schema.py                          (100 LOC)

backend/services/
  chat_persistence_service.py             (200 LOC)

backend/agents/
  context_manager.py                      (250 LOC)

frontend/ui/
  veritas_ui_session_dialog.py            (150 LOC)
  veritas_ui_session_manager.py           (300 LOC)

tests/backend/
  test_chat_persistence.py                (200 LOC)
  test_context_manager.py                 (150 LOC)

tests/integration/
  test_chat_persistence_e2e.py            (150 LOC)

data/
  chat_sessions/                          (Auto-created)
  chat_backups/                           (Auto-created)
```

**Total:** ~1,500 LOC

---

## 📖 Documentation

- [ ] `docs/CHAT_PERSISTENCE.md` (500 LOC)
  - Architecture Overview
  - JSON Schema Documentation
  - API Reference
  - User Guide (Session-Management)
  - Troubleshooting

---

**Geschätzter Gesamt-Aufwand:** 4-6 Stunden  
**Priorität:** ⭐⭐⭐ HIGH (vor Performance-Optimierung)  
**Status:** 🔄 Ready to Start

**Next:** Nach Completion → `TODO_PERFORMANCE_TESTING.md`
