# 🔍 Raw-Response Debug-View - Feature Documentation

**Version:** v3.18.3  
**Erstellt:** 10.10.2025  
**Feature-Typ:** Debugging Tool  
**Status:** ✅ IMPLEMENTED

---

## 🎯 Problem

Bei der Analyse von LLM-Antworten traten generische Meta-Phrasen auf:
- "Antwort auf die Frage: Was ist das BImSchG?"
- "Basierend auf den Dokumenten..."
- "Hier ist die Antwort..."

**Root Cause:** Unclear ob Dual-Prompt System korrekt funktioniert oder ob LLM-Response gefiltert wird.

---

## ✨ Lösung: Collapsible Raw-Response Section

### Features

1. **🔍 Raw-Antwort (Debug)** - Collapsible Section
   - Standardmäßig **eingeklappt** (nur für Power-User)
   - Zeigt ungefilterte LLM-Response
   - Inkl. LLM-Parameter (Model, Temperature, Tokens, Top-p)
   - Inkl. Antwortzeit

2. **📊 LLM-Parameter-Display**
   ```
   📊 LLM-Parameter:
     • Modell: llama3:latest
     • Temperature: 0.7
     • Max Tokens: 500
     • Top-p: 0.9
     • Antwortzeit: 3.45s
   ```

3. **📝 Ungefilterte LLM-Antwort**
   - Zeigt Original-Response (bevor Frontend-Parsing)
   - Monospace-Font (Courier New) für bessere Lesbarkeit
   - Grauer Hintergrund zur visuellen Trennung

4. **⚠️ Problem-Erkennung (Auto-Detection)**
   - Erkennt generische Meta-Phrasen:
     - "Antwort auf die Frage"
     - "Basierend auf"
     - "Hier ist"
   - Erkennt sehr kurze Antworten (< 50 Zeichen)
   - Zeigt Warnung + Tipp für Dual-Prompt System

---

## 📊 UI-Layout

### Collapsed (Standard)
```
┌────────────────────────────────────────────────────────┐
│ [Heute 14:45] 🤖 VERITAS:                              │
│ The Building Code Ordinance (BImSchG) is a German law │
│ that regulates construction...                         │
│                                                        │
│ ▶ 📚 Quellen (7)                                       │
│ ▶ 💡 Weitere Schritte (3)                              │
│ ▶ 🔍 Raw-Antwort (Debug)    ← NEU! Eingeklappt       │
└────────────────────────────────────────────────────────┘
```

### Expanded (Debugging)
```
┌────────────────────────────────────────────────────────┐
│ ▼ 🔍 Raw-Antwort (Debug)                               │
│                                                        │
│   📊 LLM-Parameter:                                    │
│     • Modell: llama3:latest                           │
│     • Temperature: 0.7                                 │
│     • Max Tokens: 500                                  │
│     • Top-p: 0.9                                       │
│     • Antwortzeit: 3.45s                               │
│                                                        │
│   📝 Ungefilterte LLM-Antwort:                         │
│   ────────────────────────────────────────────────────│
│   Antwort auf die Frage: Was ist das BImSchG?         │
│                                                        │
│   The Building Code Ordinance (BImSchG) is a German   │
│   law that regulates construction...                   │
│   ────────────────────────────────────────────────────│
│                                                        │
│   ⚠️ Erkannte Probleme:                                │
│     • ⚠️ Generische Meta-Phrase: 'Antwort auf die     │
│       Frage'                                           │
│                                                        │
│   💡 Tipp: Prüfe Dual-Prompt System im Backend        │
└────────────────────────────────────────────────────────┘
```

---

## 🛠️ Implementation

### Code Changes

**File:** `frontend/ui/veritas_ui_chat_formatter.py` (+80 LOC)

#### 1. Neue Methode: `_insert_raw_response_collapsible()`
```python
def _insert_raw_response_collapsible(
    self, 
    content: str, 
    metadata: Dict, 
    message_id: str
) -> None:
    """
    Fügt Raw-Response als Collapsible Section ein (für Debugging)
    
    Features:
    - LLM-Parameter-Display
    - Ungefilterte Content-Anzeige
    - Auto-Problem-Detection
    - Tipps für Dual-Prompt System
    """
```

#### 2. Integration in `_render_assistant_message_structured()`
```python
# === 7) RAW RESPONSE (Collapsible, DEBUG) ===
if COLLAPSIBLE_AVAILABLE and message_id and metadata:
    self._insert_raw_response_collapsible(content, metadata, message_id)
```

#### 3. Neue Tag-Konfigurationen
```python
# Raw Response Tags
text_widget.tag_configure("raw_header", ...)   # Bold Headers
text_widget.tag_configure("raw_param", ...)    # Courier New, Params
text_widget.tag_configure("raw_content", ...)  # Courier New, grau BG
text_widget.tag_configure("raw_separator", ...)# Trennlinien
text_widget.tag_configure("raw_warning", ...)  # Orange Warnungen
text_widget.tag_configure("raw_tip", ...)      # Blaue Tipps
```

**File:** `frontend/veritas_app.py` (+10 LOC)

#### 4. Metadata-Erweiterung im Backend-Response
```python
backend_response = {
    ...,
    'metadata': {
        'model': payload.get('model', 'unknown'),
        'temperature': payload.get('temperature', 'N/A'),
        'max_tokens': payload.get('max_tokens', 'N/A'),
        'top_p': payload.get('top_p', 'N/A'),
        'duration': response_data.get('rag_metadata', {}).get('duration', 'N/A'),
        'raw_content': response_data.get('answer', final_answer)
    }
}
```

---

## 🧪 Testing

### Test 1: Raw-Response wird angezeigt
1. **Sende Query:** "Was ist das BImSchG?"
2. **Erwarte:** `▶ 🔍 Raw-Antwort (Debug)` eingeklappt
3. **Klicke:** Expand Section
4. **Erwarte:** 
   - LLM-Parameter visible
   - Ungefilterte Antwort visible
   - Problem-Detection (falls zutreffend)

### Test 2: Problem-Detection (Generische Phrase)
1. **Wenn Response:** "Antwort auf die Frage: ..."
2. **Erwarte in Raw-Response:**
   ```
   ⚠️ Erkannte Probleme:
     • ⚠️ Generische Meta-Phrase: 'Antwort auf die Frage'
   
   💡 Tipp: Prüfe Dual-Prompt System im Backend
   ```

### Test 3: Problem-Detection (Kurze Antwort)
1. **Wenn Response:** < 50 Zeichen
2. **Erwarte:**
   ```
   ⚠️ Erkannte Probleme:
     • ⚠️ Sehr kurze Antwort (< 50 Zeichen)
   ```

### Test 4: LLM-Parameter korrekt
1. **Setze:** Temp=0.3, Tokens=300, Top-p=0.7, Model=phi3:latest
2. **Erwarte in Raw-Response:**
   ```
   📊 LLM-Parameter:
     • Modell: phi3:latest
     • Temperature: 0.3
     • Max Tokens: 300
     • Top-p: 0.7
   ```

---

## 🔍 Problem-Detection Rules

### Auto-Detected Probleme

| Problem | Detection | Warnung |
|---------|-----------|---------|
| **Generische Meta-Phrase** | `"Antwort auf die Frage" in content` | ⚠️ Meta-Phrase erkannt: '...' |
| **Basierend auf** | `content.startswith("Basierend auf")` | ⚠️ Meta-Phrase erkannt: 'Basierend auf' |
| **Hier ist** | `content.startswith("Hier ist")` | ⚠️ Meta-Phrase erkannt: 'Hier ist' |
| **Sehr kurz** | `len(content) < 50` | ⚠️ Sehr kurze Antwort (< 50 Zeichen) |

### Empfohlene Actions

**Wenn Problem erkannt:**
1. ✅ Prüfe Backend-Logs: `data/veritas_auto_server.log`
2. ✅ Prüfe Dual-Prompt System: `backend/agents/veritas_enhanced_prompts.py`
3. ✅ Verifiziere Template-Nutzung: `veritas_api_endpoint.py`
4. ✅ Teste mit anderem LLM-Modell (llama3.1:8b hat besseres Instruction-Following)

---

## 📈 Use Cases

### Use Case 1: Debugging generischer Antworten
**Symptom:** User beschwert sich über generische "Antwort auf die Frage..." Responses

**Workflow:**
1. User sendet Query
2. Raw-Response Section aufklappen
3. **Falls Problem erkannt:** Orange Warnung visible
4. Prüfe Backend Dual-Prompt Integration
5. Fixe Template-Nutzung

### Use Case 2: LLM-Parameter-Verifikation
**Symptom:** Antworten scheinen nicht Preset-Settings zu folgen

**Workflow:**
1. User klickt "⚖️ Präzise" Preset
2. Sendet Query
3. Raw-Response Section aufklappen
4. **Verifiziere:** `Temperature: 0.3`, `Tokens: 300`, `Top-p: 0.7`
5. Falls Abweichung → Backend-Parameter-Passing prüfen

### Use Case 3: Performance-Analyse
**Symptom:** Antworten dauern zu lange

**Workflow:**
1. Sende Query
2. Raw-Response Section aufklappen
3. **Prüfe:** `Antwortzeit: 12.34s`
4. Falls > 10s → Prüfe Token-Count, Modell-Geschwindigkeit
5. Erwäge schnelleres Modell (phi3:latest)

---

## 🎨 Styling

### Color Scheme
- **Raw Header:** `#555` (dunkelgrau, bold)
- **Raw Param:** `#666` (Courier New, grau)
- **Raw Content:** `#333` auf `#FAFAFA` (Monospace, grauer BG)
- **Raw Separator:** `#CCC` (hellgrau Linie)
- **Raw Warning:** `#FF6600` (orange)
- **Raw Tip:** `#0066CC` (blau, italic)

### Font Stack
- **Headers:** Segoe UI 9pt Bold
- **Parameters:** Courier New 8pt
- **Content:** Courier New 8pt
- **Warnings/Tips:** Segoe UI 8pt

---

## 🚀 Deployment

### Ready for Production
- ✅ Keine Syntax-Errors
- ✅ Collapsible standardmäßig eingeklappt (kein UI-Clutter)
- ✅ Nur für Power-User relevant
- ✅ Hilft bei Debugging

### Installation
```bash
cd c:\VCC\veritas
git pull  # Holt v3.18.3
python start_frontend.py
```

---

## 📝 Future Enhancements (Optional)

### Ideen für v3.19
1. **Copy-to-Clipboard** Button für Raw-Response
2. **Export Raw-Response** zu JSON-File
3. **Side-by-Side Comparison:** Filtered vs. Raw
4. **Auto-Fix Suggestions:** "Klicken zum Aktivieren von Dual-Prompt"
5. **Historical Raw-Responses:** Siehe letzte 5 Antworten

---

## 🐛 Known Issues

### None! 🎉
Feature funktioniert wie erwartet.

### Potential Edge Cases
1. **Sehr lange Raw-Responses (>5000 Zeichen):** Könnte langsam rendern
   - Lösung: Truncate mit "... (show more)" Link
2. **Missing Metadata:** Falls Backend keine Metadata sendet
   - Lösung: Graceful Fallback zu "N/A"

---

## 📚 Related Documentation

- `docs/DUAL_PROMPT_SYSTEM.md` - Dual-Prompt Architektur
- `docs/LLM_PARAMETER_SPRINT1_SUMMARY.md` - Parameter UI Features
- `backend/agents/veritas_enhanced_prompts.py` - Prompt Templates

---

**Erstellt:** 10.10.2025  
**Autor:** VERITAS AI System  
**Version:** v3.18.3  
**Status:** ✅ PRODUCTION READY
