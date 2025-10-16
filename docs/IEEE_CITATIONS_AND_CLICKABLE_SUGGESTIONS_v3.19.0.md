# IEEE-Zitationen & Klickbare Vorschläge - v3.19.0 Implementierungsplan

**Status:** 📋 PLANUNG (10.10.2025)  
**Priorität:** HOCH - UX-Verbesserung für wissenschaftliches Arbeiten  
**Geschätzter Aufwand:** 6-8 Stunden (Backend 3h, Frontend 4h, Testing 1h)  

---

## 🎯 User-Anforderungen

### Feature #1: IEEE-konforme Inline-Zitationen
> "Zitierte Quellen müssen zwingend in der Antwort mit hochgestellter Nummerierung [¹] (IEEE-Standard) gekennzeichnet werden. Diese soll als Link eingebunden werden und auf die Quelle verweisen. Die Quellen haben grundsätzlich das IEEE Format"

**Ziel:** 
- In-Text-Zitationen mit hochgestellten Nummern `[¹]`, `[²]`, `[³]`
- Klickbar → scrollt zur Quellenangabe unten
- IEEE-Format für Quellenangaben

**Beispiel:**
```
Nach § 58 LBO BW ist eine Baugenehmigung erforderlich[¹]. Die Bearbeitungsdauer 
beträgt laut Verwaltungsvorschrift in der Regel 2-3 Monate[²].

📚 Quellen:
[1] Landesbauordnung Baden-Württemberg (LBO BW), § 58 "Baugenehmigung", 
    Stand: 2023, https://www.landesrecht-bw.de/...
[2] Verwaltungsvorschrift des Wirtschaftsministeriums zur LBO, 
    Abschnitt 3.2 "Bearbeitungsfristen", 2022
```

### Feature #2: Klickbare Vorschläge als neue Queries
> "Vorschläge der LLM sollen als 'Links' angezeigt werden und bei Klicken als neue Eingabe ans Backend gesendet werden."

**Ziel:**
- Follow-up-Vorschläge als klickbare Buttons/Links
- Bei Klick → automatisch als neue Query gesendet
- Kein manuelles Copy-Paste nötig

**Beispiel:**
```
💡 Vorschläge:
  🔗 Welche Unterlagen benötige ich für die Baugenehmigung?
  🔗 Wie hoch sind die Gebühren für eine Baugenehmigung?
  🔗 Kann ich eine Bauvoranfrage stellen?
```

---

## 📊 Architektur-Übersicht

### Datenfluss: IEEE-Zitationen

```
Backend (LLM Prompt)
  ↓ Instruiert LLM: "Füge [1], [2] ein bei Zitaten"
LLM generiert Text
  ↓ "§ 58 LBO BW[1]... 2-3 Monate[2]"
Backend extrahiert Sources
  ↓ sources = [{id: 1, title: "LBO BW", ...}, {id: 2, ...}]
Frontend empfängt
  ↓ content = "§ 58 LBO BW[1]... 2-3 Monate[2]"
  ↓ sources = [...]
Markdown Renderer
  ↓ Parst [1], [2] → erstellt superscript Links
  ↓ <a href="#source-1"><sup>1</sup></a>
Text Widget
  ↓ Rendert mit tkinter Tags (superscript, link)
  ↓ Bindet Click-Event → scroll to source
```

### Datenfluss: Klickbare Vorschläge

```
Backend (LLM Prompt)
  ↓ "Generiere 3-5 Follow-up-Fragen"
LLM generiert
  ↓ suggestions = ["Welche Unterlagen?", "Wie hoch sind Gebühren?", ...]
Backend Response
  ↓ {answer: "...", suggestions: ["...", "..."]}
Frontend empfängt
  ↓ suggestions = ["...", "..."]
Chat Formatter
  ↓ _insert_suggestions_collapsible()
  ↓ Rendert als Buttons mit Click-Handler
Button Click
  ↓ Callback: send_query(suggestion_text)
Backend empfängt
  ↓ Neue Query-Verarbeitung
```

---

## 🔧 Implementierung: Feature #1 (IEEE-Zitationen)

### Phase 1: Backend-Anpassung (Prompt Engineering)

**Datei:** `backend/agents/veritas_enhanced_prompts.py`  
**Funktion:** `USER_FACING_RESPONSE` Template erweitern  

**Änderungen:**

```python
USER_FACING_RESPONSE = {
    "system": """Du bist ein hilfreicher Verwaltungsassistent.

WISSENSCHAFTLICHE ZITATIONEN (WICHTIG!):
- Nutze IEEE-Standard für Quellenangaben
- Markiere JEDEN Bezug auf Dokumente mit [1], [2], [3] etc.
- Platziere Zitation DIREKT nach dem zitierten Satz/Fakt
- Verwende fortlaufende Nummerierung

BEISPIEL (GUT):
"Nach § 58 LBO BW ist eine Baugenehmigung erforderlich[1]. Die Bearbeitungsdauer 
beträgt in der Regel 2-3 Monate[2]. Bei Naturschutzgebieten gelten Sonderregelungen[3]."

BEISPIEL (SCHLECHT):
"Nach § 58 LBO BW ist eine Baugenehmigung erforderlich. Die Bearbeitungsdauer 
beträgt in der Regel 2-3 Monate."  ← Keine Zitationen!

STIL:
- Direkt, natürlich, hilfreich
- Strukturiert mit Aufzählungen
- Konkrete Handlungsempfehlungen
- Quellenbasiert (IMMER mit [N] zitieren)""",
    
    "user_template": """**User fragte:** {query}

**Kontext aus Dokumenten:**
{rag_context}

**Verfügbare Quellen für Zitationen:**
{source_list}

**Deine Aufgabe:**
Beantworte die User-Frage präzise und zitiere JEDE Aussage mit [N].

ZITATIONSREGELN:
1. Jeder Fakt aus Dokumenten → [N] Referenz
2. N = Position in Quellenliste (1-basiert)
3. Mehrere Fakten aus gleicher Quelle → mehrfach [N] nutzen
4. Chronologische Nummerierung beibehalten

**Jetzt beantworte die User-Frage mit korrekten IEEE-Zitationen:**"""
}
```

**Source-List-Format:**
```python
# In RAG Chain: Quellen-Liste für Prompt formatieren
source_list = "\n".join([
    f"[{i+1}] {source['title']} ({source.get('type', 'Dokument')})"
    for i, source in enumerate(sources)
])
```

**Geschätzter Aufwand:** 1-2 Stunden (Prompt-Tuning, Testing)

---

### Phase 2: Frontend-Anpassung (Markdown Rendering)

**Datei:** `frontend/ui/veritas_markdown_renderer.py`  
**Neue Funktion:** `_parse_ieee_citations()`  

**Implementierung:**

```python
def _parse_ieee_citations(self, text: str) -> str:
    """
    Parst IEEE-Zitationen [1], [2] und erstellt superscript Links
    
    Args:
        text: Eingabe-Text mit [1], [2] Annotationen
    
    Returns:
        Text mit ersetzten Zitationen (Marker für Rendering)
    
    Beispiel:
        Input:  "§ 58 LBO BW[1] regelt..."
        Output: "§ 58 LBO BW<CITE id=1> regelt..."
    """
    # Regex: [1], [2], [3] etc.
    citation_pattern = r'\[(\d+)\]'
    
    def replace_citation(match):
        cite_num = match.group(1)
        # Marker für späteren Rendering-Schritt
        return f'<CITE id={cite_num}>'
    
    return re.sub(citation_pattern, replace_citation, text)

def render_markdown(self, markdown_text: str, default_tag: str = "assistant_main"):
    """Rendert Markdown mit IEEE-Zitationen"""
    
    # 1. Parse IEEE-Zitationen ZUERST
    text_with_cite_markers = self._parse_ieee_citations(markdown_text)
    
    # 2. Standard Markdown-Parsing
    # ... (bestehende Logik)
    
    # 3. Rendere Zitations-Marker
    for match in re.finditer(r'<CITE id=(\d+)>', text_with_cite_markers):
        cite_num = match.group(1)
        cite_start = self.text_widget.index(tk.END)
        
        # Hochgestellte Zahl
        self.text_widget.insert(tk.END, f"[{cite_num}]", "citation_superscript")
        cite_end = self.text_widget.index(tk.END)
        
        # Einzigartiger Tag für Click-Handler
        cite_tag = f"citation_link_{cite_num}"
        self.text_widget.tag_add(cite_tag, cite_start, cite_end)
        
        # Click-Handler: Scroll zu Source
        self.text_widget.tag_bind(
            cite_tag, 
            "<Button-1>", 
            lambda e, num=cite_num: self._scroll_to_source(num)
        )
        
        # Styling
        self.text_widget.tag_config(cite_tag, foreground='#0066CC', underline=1)
        self.text_widget.tag_bind(cite_tag, "<Enter>", 
            lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind(cite_tag, "<Leave>", 
            lambda e: self.text_widget.config(cursor=""))

def _scroll_to_source(self, source_num: str):
    """Scrollt zur Quellenangabe mit gegebener Nummer"""
    # Suche nach Tag "source_entry_{source_num}"
    source_tag = f"source_entry_{source_num}"
    
    # Finde Tag-Range
    ranges = self.text_widget.tag_ranges(source_tag)
    if ranges:
        # Scroll zu erster Position
        self.text_widget.see(ranges[0])
        
        # Optional: Highlight-Animation
        self.text_widget.tag_config(source_tag, background='#FFFFCC')
        self.text_widget.after(2000, lambda: 
            self.text_widget.tag_config(source_tag, background=''))
```

**Tag-Konfiguration:**

```python
# In _configure_tags()
text_widget.tag_configure(
    "citation_superscript",
    font=('Segoe UI', 7),  # Kleinere Schrift
    offset=4,  # Hochgestellt (tkinter offset in Pixel)
    foreground='#0066CC',
    underline=1
)
```

**Geschätzter Aufwand:** 2-3 Stunden (Parsing, Rendering, Click-Handler)

---

### Phase 3: IEEE-Formatierung der Quellen

**Datei:** `frontend/ui/veritas_ui_chat_formatter.py`  
**Funktion:** `_insert_sources_collapsible()` erweitern  

**IEEE-Format-Konvention:**

```
[N] Autor(en), "Titel", Typ, Herausgeber, Jahr, [Online]. Verfügbar: URL
```

**Beispiele:**
```
[1] Landesbauordnung Baden-Württemberg (LBO BW), § 58 "Baugenehmigung", 
    Landesrecht BW, 2023, [Online]. Verfügbar: https://www.landesrecht-bw.de/...

[2] Bundesimmissionsschutzgesetz (BImSchG), § 4 "Genehmigungsbedürftige Anlagen",
    Bundesrecht, 2022

[3] Verwaltungsvorschrift Technische Baubestimmungen, Abschnitt 3.2, 
    Wirtschaftsministerium BW, 2021
```

**Implementierung:**

```python
def _format_source_ieee(self, source: str, index: int, metadata: Dict) -> str:
    """
    Formatiert Quelle im IEEE-Standard
    
    Args:
        source: Source-String (kann bereits formatiert sein)
        index: 1-basierter Index
        metadata: Metadaten (type, year, url, author)
    
    Returns:
        IEEE-formatierter String
    """
    # Extrahiere Komponenten
    title = source
    doc_type = metadata.get('type', 'Dokument')
    year = metadata.get('year', '')
    url = metadata.get('url', '')
    author = metadata.get('author', '')
    
    # Baue IEEE-Format
    parts = [f"[{index}]"]
    
    if author:
        parts.append(f"{author},")
    
    parts.append(f'"{title}",')
    
    if doc_type:
        parts.append(f"{doc_type},")
    
    if year:
        parts.append(f"{year}")
    
    if url:
        parts.append(f"[Online]. Verfügbar: {url}")
    
    return " ".join(parts)

def _insert_sources_collapsible(self, sources: List[str], message_id: str):
    """Fügt Quellen mit IEEE-Formatierung ein"""
    
    # ... (bestehende CollapsibleSection-Logik)
    
    for i, source in enumerate(sources, 1):
        # Extrahiere Metadaten
        metadata = self._extract_source_metadata(source)
        
        # IEEE-Formatierung
        ieee_formatted = self._format_source_ieee(source, i, metadata)
        
        # Rendere mit eindeutigem Tag (für Citation-Links!)
        source_tag = f"source_entry_{i}"
        source_start = self.text_widget.index(tk.END)
        
        self.text_widget.insert(tk.END, f"  {ieee_formatted}\n", "source")
        
        source_end = self.text_widget.index(tk.END)
        self.text_widget.tag_add(source_tag, source_start, source_end)
```

**Geschätzter Aufwand:** 1 Stunde (Formatierung)

---

## 🔧 Implementierung: Feature #2 (Klickbare Vorschläge)

### Phase 1: Backend - Follow-up-Generierung

**Datei:** `backend/agents/veritas_enhanced_prompts.py`  
**Erweiterung:** Follow-up-Generierung im Prompt  

**Änderungen:**

```python
USER_FACING_RESPONSE = {
    "system": """Du bist ein hilfreicher Verwaltungsassistent.

... (bestehende Instruktionen) ...

FOLLOW-UP-VORSCHLÄGE:
- Generiere am Ende 3-5 sinnvolle Folgefragen
- Formuliere als vollständige Fragen (nicht Stichworte)
- Basiere auf User-Query und gegebener Antwort
- Format: Einfache Liste, eine Frage pro Zeile

BEISPIEL:
"💡 Vorschläge:
- Welche Unterlagen benötige ich für eine Baugenehmigung?
- Wie hoch sind die Gebühren für eine Baugenehmigung in Baden-Württemberg?
- Kann ich eine Bauvoranfrage stellen?"
""",
    
    "user_template": """**User fragte:** {query}

... (bestehende Instruktionen) ...

**Struktur deiner Antwort:**
1. Hauptantwort (mit [N] Zitationen)
2. 📋 Nächste Schritte (optional)
3. 💡 Vorschläge (3-5 Folgefragen)

**Jetzt beantworte die User-Frage:**"""
}
```

**Backend-Parsing:**

```python
# In RAG Chain: Parse Follow-ups aus LLM-Antwort
def _extract_suggestions(llm_response: str) -> List[str]:
    """Extrahiert Follow-up-Vorschläge aus LLM-Antwort"""
    suggestions = []
    
    # Suche nach "💡 Vorschläge:" Section
    match = re.search(r'💡 Vorschläge?:(.+?)(?:\n\n|$)', llm_response, re.DOTALL | re.IGNORECASE)
    if match:
        section = match.group(1)
        
        # Parse Bullet-Points
        for line in section.strip().split('\n'):
            line = line.strip()
            # Entferne Bullet-Point-Marker
            line = re.sub(r'^[•\-\*]\s*', '', line)
            if line:
                suggestions.append(line)
    
    return suggestions[:5]  # Max 5 Vorschläge

# In Response-Datenstruktur
response = {
    'answer': cleaned_answer,
    'sources': sources,
    'suggestions': _extract_suggestions(llm_response)  # NEU
}
```

**Geschätzter Aufwand:** 1 Stunde (Prompt-Erweiterung, Parsing)

---

### Phase 2: Frontend - Klickbare Suggestion-Buttons

**Datei:** `frontend/ui/veritas_ui_chat_formatter.py`  
**Funktion:** `_insert_suggestions_collapsible()` erweitern  

**Implementierung:**

```python
def _insert_suggestions_collapsible(self, suggestions: List[str], message_id: str):
    """
    Fügt Vorschläge als klickbare Buttons/Links ein
    
    Args:
        suggestions: Liste von Follow-up-Fragen
        message_id: Eindeutige Message-ID
    """
    if not suggestions:
        return
    
    # CollapsibleSection
    self.text_widget.insert(tk.END, "\n")
    
    if COLLAPSIBLE_AVAILABLE:
        section = CollapsibleSection(
            self.text_widget,
            header_text="💡 Vorschläge",
            start_collapsed=False,  # Default: ausgeklappt
            section_id=f"suggestions_{message_id}"
        )
        section.insert_header()
    else:
        self.text_widget.insert(tk.END, "💡 Vorschläge:\n", "header")
    
    # Rendere jeden Vorschlag als klickbarer Link
    for i, suggestion in enumerate(suggestions, 1):
        self._insert_suggestion_link(suggestion, i, message_id)
    
    if COLLAPSIBLE_AVAILABLE:
        section.finalize()

def _insert_suggestion_link(self, suggestion_text: str, index: int, message_id: str):
    """
    Rendert einzelnen Vorschlag als klickbaren Link
    
    Args:
        suggestion_text: Text des Vorschlags (Frage)
        index: Nummer des Vorschlags
        message_id: Message-ID (für eindeutige Tags)
    """
    # Link-Icon
    link_icon = "🔗" if not ICONS_AVAILABLE else VeritasIcons.action('link')
    
    # Eindeutiger Tag
    suggestion_tag = f"suggestion_link_{message_id}_{index}"
    
    # Rendere als klickbarer Text
    link_start = self.text_widget.index(tk.END)
    self.text_widget.insert(tk.END, f"  {link_icon} ", "suggestion_icon")
    self.text_widget.insert(tk.END, suggestion_text, suggestion_tag)
    self.text_widget.insert(tk.END, "\n")
    link_end = self.text_widget.index(tk.END)
    
    # Click-Handler: Sende als neue Query
    if self.suggestion_click_handler:
        self.text_widget.tag_bind(
            suggestion_tag,
            "<Button-1>",
            lambda e, text=suggestion_text: self.suggestion_click_handler(text)
        )
    
    # Styling: Hover-Effekt
    self.text_widget.tag_config(
        suggestion_tag,
        foreground='#0066CC',
        underline=0,  # Nur bei Hover
        font=('Segoe UI', 9)
    )
    
    self.text_widget.tag_bind(suggestion_tag, "<Enter>", 
        lambda e, tag=suggestion_tag: self._on_suggestion_hover(tag, True))
    self.text_widget.tag_bind(suggestion_tag, "<Leave>", 
        lambda e, tag=suggestion_tag: self._on_suggestion_hover(tag, False))

def _on_suggestion_hover(self, tag: str, is_hovering: bool):
    """Hover-Effekt für Suggestion-Links"""
    if is_hovering:
        self.text_widget.tag_config(tag, underline=1, background='#F0F8FF')
        self.text_widget.config(cursor="hand2")
    else:
        self.text_widget.tag_config(tag, underline=0, background='')
        self.text_widget.config(cursor="")
```

**Tag-Konfiguration:**

```python
# In _configure_tags()
text_widget.tag_configure(
    "suggestion_icon",
    font=('Segoe UI', 9),
    foreground='#0066CC'
)
```

**Geschätzter Aufwand:** 2 Stunden (UI-Rendering, Click-Handler)

---

### Phase 3: Frontend - Click-Handler Integration

**Datei:** `frontend/veritas_app.py`  
**Funktion:** Suggestion-Click-Callback  

**Implementierung:**

```python
def __init__(self, ...):
    # ... (bestehende Initialisierung)
    
    # Registriere Suggestion-Click-Handler
    if hasattr(self, 'chat_formatter'):
        self.chat_formatter.suggestion_click_handler = self._on_suggestion_clicked

def _on_suggestion_clicked(self, suggestion_text: str):
    """
    Callback wenn User auf Vorschlag klickt
    
    Args:
        suggestion_text: Text des geklickten Vorschlags
    """
    logging.info(f"[SUGGESTION-CLICK] User klickte auf: '{suggestion_text}'")
    
    # 1. Setze Query-Input
    self.user_input.delete("1.0", tk.END)
    self.user_input.insert("1.0", suggestion_text)
    
    # 2. Zeige System-Message
    self.add_system_message(f"🔗 Follow-up-Frage: {suggestion_text[:60]}...")
    
    # 3. Sende automatisch (optional: User muss bestätigen)
    # Option A: Automatisch senden
    self._send_message()
    
    # Option B: User muss Enter drücken (nur vorausfüllen)
    # self.user_input.focus_set()
```

**User-Präferenz (Optional):**

```python
# Config-Option für Auto-Send
self.auto_send_suggestions = tk.BooleanVar(value=True)

# UI-Toggle in Settings
auto_send_checkbox = ttk.Checkbutton(
    settings_frame,
    text="Auto-Send bei Vorschlägen",
    variable=self.auto_send_suggestions
)

# In _on_suggestion_clicked()
if self.auto_send_suggestions.get():
    self._send_message()
else:
    self.user_input.focus_set()
```

**Geschätzter Aufwand:** 1 Stunde (Integration, Testing)

---

## 🧪 Testing-Plan

### Test-Suite: IEEE-Zitationen

**Test 1: Inline-Zitationen generiert**
```python
Query: "Wie beantrage ich eine Baugenehmigung in Baden-Württemberg?"

Erwartete Antwort (LLM):
"Nach § 58 LBO BW ist eine Baugenehmigung beim zuständigen Bauordnungsamt zu 
beantragen[1]. Die erforderlichen Unterlagen sind in der Verwaltungsvorschrift 
geregelt[2]. Die Bearbeitungsdauer beträgt in der Regel 2-3 Monate[1]."

Validierung:
✅ [1], [2] im Text enthalten
✅ Korrekte Nummerierung (fortlaufend)
✅ Zitationen nach relevantem Satz
```

**Test 2: Citation-Links klickbar**
```python
User-Aktion: Klick auf [1] im Text

Erwartung:
✅ Scroll zu "📚 Quellen" Section
✅ [1] Eintrag wird gehighlighted (gelber Hintergrund)
✅ Highlight verschwindet nach 2 Sekunden
✅ Cursor ändert sich zu "hand2" bei Hover
```

**Test 3: IEEE-Formatierung korrekt**
```python
Erwartete Quellen-Section:
"📚 Quellen:
[1] Landesbauordnung Baden-Württemberg (LBO BW), § 58 "Baugenehmigung", 
    Landesrecht BW, 2023, [Online]. Verfügbar: https://www.landesrecht-bw.de/...
[2] Verwaltungsvorschrift Technische Baubestimmungen, Abschnitt 3.2, 
    Wirtschaftsministerium BW, 2021"

Validierung:
✅ [N] Nummerierung
✅ Titel in Anführungszeichen
✅ Typ angegeben (Gesetz, Verordnung, etc.)
✅ Jahr enthalten
✅ URL als "Verfügbar: ..."
```

---

### Test-Suite: Klickbare Vorschläge

**Test 1: Follow-ups generiert**
```python
Query: "Was ist das BImSchG?"

Erwartete Antwort-Struktur:
"Das Bundesimmissionsschutzgesetz (BImSchG)...[1]

💡 Vorschläge:
🔗 Welche Anlagen sind nach BImSchG genehmigungspflichtig?
🔗 Was sind die Unterschiede zwischen BImSchG und TA Luft?
🔗 Wie beantrage ich eine BImSchG-Genehmigung?"

Validierung:
✅ 3-5 Vorschläge generiert
✅ Vollständige Fragen (keine Stichworte)
✅ Thematisch passend zur Original-Query
```

**Test 2: Suggestion-Click funktioniert**
```python
User-Aktion: Klick auf "Welche Anlagen sind nach BImSchG genehmigungspflichtig?"

Erwartung:
✅ Query-Input wird gefüllt mit Vorschlagstext
✅ System-Message: "🔗 Follow-up-Frage: Welche Anlagen sind..."
✅ Query wird automatisch gesendet (falls Auto-Send aktiv)
✅ Neue Antwort erscheint im Chat

Backend-Log:
[SUGGESTION-CLICK] User klickte auf: 'Welche Anlagen sind...'
[RAG] Query-Verarbeitung: 'Welche Anlagen sind nach BImSchG genehmigungspflichtig?'
```

**Test 3: Hover-Effekt**
```python
User-Aktion: Maus über Vorschlag bewegen

Erwartung:
✅ Cursor ändert sich zu "hand2"
✅ Text wird unterstrichen
✅ Hintergrund wird hellblau (#F0F8FF)
✅ Effekt verschwindet bei Mouse-Leave
```

---

## 📊 Datenstruktur-Änderungen

### Backend Response Schema (Erweiterung)

**Datei:** `backend/api/veritas_api_endpoint.py`  

**VORHER:**
```python
class RAGResponse(BaseModel):
    answer: str
    sources: List[str] = []
    turn_id: str
    confidence: Optional[float] = None
    duration: Optional[float] = None
```

**NACHHER:**
```python
class SourceMetadata(BaseModel):
    """Erweiterte Source-Metadaten für IEEE-Formatierung"""
    id: int  # 1-basierte Nummerierung
    title: str
    type: Optional[str] = "Dokument"  # Gesetz, Verordnung, Urteil, etc.
    author: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None
    page: Optional[int] = None
    confidence: Optional[float] = None

class RAGResponse(BaseModel):
    answer: str  # Enthält jetzt [1], [2] Inline-Zitationen
    sources: List[str] = []  # DEPRECATED (Kompatibilität)
    sources_metadata: List[SourceMetadata] = []  # NEU: Strukturierte Metadaten
    suggestions: List[str] = []  # NEU: Follow-up-Fragen
    turn_id: str
    confidence: Optional[float] = None
    duration: Optional[float] = None
```

---

## 🎨 UI-Mockups

### IEEE-Zitationen Beispiel

```
┌─────────────────────────────────────────────────────────────┐
│ 📝 Antwort:                                                 │
│                                                             │
│ Nach § 58 LBO BW ist eine Baugenehmigung beim zuständigen   │
│ Bauordnungsamt zu beantragen[¹]. Die erforderlichen         │
│ Unterlagen sind in der Verwaltungsvorschrift geregelt[²].   │
│ Die Bearbeitungsdauer beträgt in der Regel 2-3 Monate[¹].   │
│                                                             │
│ 📊 Confidence: 85% HOCH  📚 2 Quellen  ⚡ 3.2s             │
│                                                             │
│ ▼ 📚 Quellen                                                │
│   [1] Landesbauordnung Baden-Württemberg (LBO BW),         │
│       § 58 "Baugenehmigung", Landesrecht BW, 2023,         │
│       [Online]. Verfügbar: https://www.landesrecht-bw.de... │
│   [2] Verwaltungsvorschrift Technische Baubestimmungen,    │
│       Abschnitt 3.2, Wirtschaftsministerium BW, 2021       │
│                                                             │
│ ▼ 💡 Vorschläge                                             │
│   🔗 Welche Unterlagen benötige ich für die Baugenehmigung?│
│   🔗 Wie hoch sind die Gebühren in Baden-Württemberg?      │
│   🔗 Kann ich eine Bauvoranfrage stellen?                  │
└─────────────────────────────────────────────────────────────┘

Interaktionen:
- Klick auf [¹] → Scrollt zu [1] in Quellen, highlighted 2s
- Hover über [¹] → Cursor: hand2, Underline
- Klick auf 🔗 Vorschlag → Sendet als neue Query
- Hover über Vorschlag → Underline, hellblauer Hintergrund
```

---

## 📋 Implementierungs-Reihenfolge

### Sprint 1: IEEE-Zitationen (3-4h)

**Tag 1 (2h):**
1. ✅ Backend: Prompt-Erweiterung (`veritas_enhanced_prompts.py`)
2. ✅ Backend: Source-List-Formatierung für Prompt
3. ✅ Testing: LLM generiert [1], [2] korrekt

**Tag 2 (2h):**
4. ✅ Frontend: Citation-Parsing (`_parse_ieee_citations()`)
5. ✅ Frontend: Superscript-Rendering mit Links
6. ✅ Frontend: Scroll-to-Source Funktionalität
7. ✅ Testing: Click-Handler funktioniert

**Tag 3 (1h):**
8. ✅ Frontend: IEEE-Formatierung der Quellen
9. ✅ Frontend: Source-Entry-Tags für Citation-Links
10. ✅ Testing: End-to-End (Query → Zitation → Click → Scroll)

---

### Sprint 2: Klickbare Vorschläge (2-3h)

**Tag 4 (1h):**
1. ✅ Backend: Follow-up-Generierung im Prompt
2. ✅ Backend: Suggestion-Parsing aus LLM-Response
3. ✅ Testing: 3-5 Vorschläge werden generiert

**Tag 5 (1.5h):**
4. ✅ Frontend: Suggestion-Link-Rendering
5. ✅ Frontend: Click-Handler mit Auto-Send
6. ✅ Frontend: Hover-Effekt
7. ✅ Testing: Click → Query-Input → Send

**Tag 6 (0.5h):**
8. ✅ Optional: Auto-Send Toggle in Settings
9. ✅ Testing: End-to-End (Query → Vorschlag → Click → Neue Query)

---

## 🔍 Potential Issues & Lösungen

### Issue #1: LLM vergisst Zitationen
**Problem:** LLM generiert Text ohne [1], [2] Marker  
**Lösung:**
- Prompt-Engineering: Mehrfache Betonung + Beispiele
- Post-Processing: Regex-basierte Zitations-Injection (Fallback)
- Few-Shot-Learning: Gute Beispiele im Prompt zeigen

### Issue #2: Falsche Zitations-Nummerierung
**Problem:** LLM nutzt [1], [3], [1] statt [1], [2], [3]  
**Lösung:**
- Source-List im Prompt mit [N] Präfix versehen
- Post-Processing: Normalisierung der Nummern
- Validation: Check ob alle Nummern in Sources existieren

### Issue #3: Suggestion-Text zu lang für Input
**Problem:** Vorschlag hat 200+ Zeichen, Query-Input zu klein  
**Lösung:**
- Prompt-Constraint: "Max. 80 Zeichen pro Vorschlag"
- UI: Multi-Line Input (bereits vorhanden)
- Truncate: Kürze Vorschlag auf 150 Zeichen mit "..."

### Issue #4: IEEE-Format nicht korrekt
**Problem:** Metadaten fehlen (Jahr, Autor, URL)  
**Lösung:**
- Backend: Metadaten-Extraktion aus ChromaDB verbessern
- Fallback: Minimales IEEE-Format ohne optionale Felder
- Dokumentation: Erwartetes Format für neue Dokumente

---

## 📝 TODO-Liste

### Backend (veritas_enhanced_prompts.py, veritas_api_endpoint.py)
- [ ] Prompt erweitern: IEEE-Zitationen Instruktionen
- [ ] Prompt erweitern: Follow-up-Generierung
- [ ] Source-List-Formatierung für Prompt
- [ ] Suggestion-Parsing aus LLM-Response
- [ ] Response-Schema: `sources_metadata`, `suggestions` Felder
- [ ] Testing: Prompt-Qualität mit echten Queries

### Frontend (veritas_markdown_renderer.py, veritas_ui_chat_formatter.py)
- [ ] Citation-Parsing: `_parse_ieee_citations()`
- [ ] Superscript-Rendering mit Click-Handler
- [ ] Scroll-to-Source Funktion: `_scroll_to_source()`
- [ ] IEEE-Source-Formatierung: `_format_source_ieee()`
- [ ] Source-Entry-Tags für Citation-Links
- [ ] Suggestion-Link-Rendering: `_insert_suggestion_link()`
- [ ] Suggestion-Click-Handler Integration
- [ ] Hover-Effekte (Citation + Suggestion)
- [ ] Tag-Konfigurationen: `citation_superscript`, `suggestion_icon`

### Frontend (veritas_app.py)
- [ ] Suggestion-Click-Callback: `_on_suggestion_clicked()`
- [ ] Auto-Send Toggle (optional)
- [ ] System-Message bei Suggestion-Click

### Testing
- [ ] LLM generiert [1], [2] korrekt
- [ ] Citation-Links scrollbar
- [ ] IEEE-Format korrekt
- [ ] Follow-ups generiert (3-5)
- [ ] Suggestion-Click funktioniert
- [ ] End-to-End: Query → Zitation → Click → Scroll
- [ ] End-to-End: Query → Vorschlag → Click → Neue Query

### Dokumentation
- [ ] User-Guide: IEEE-Zitationen nutzen
- [ ] User-Guide: Follow-up-Vorschläge klicken
- [ ] Developer-Docs: Citation-System Architektur
- [ ] README: v3.19.0 Features

---

## 🎓 Technische Entscheidungen

### Warum IEEE-Standard?
- ✅ Wissenschaftlicher Standard (etabliert)
- ✅ Nummerierte Zitationen (platzsparend)
- ✅ Eindeutige Zuordnung (1:1 Mapping)
- ✅ Machine-readable (strukturiert)

### Warum Inline-Zitationen statt Footer?
- ✅ Bessere Nachvollziehbarkeit (direkt am Fakt)
- ✅ Vertrauenswürdigkeit (transparente Quellen)
- ✅ Wissenschaftliches Arbeiten (Standard-Konvention)
- ✅ Klickbar (direkte Navigation zu Quelle)

### Warum Auto-Send bei Suggestion-Click?
- ✅ Weniger Klicks (1 statt 3: Click → Text einfügen → Enter)
- ✅ Besserer Flow (nahtlose Konversation)
- ✅ User-Erwartung (bei klickbaren Vorschlägen)
- ⚠️ Optional: Toggle für User-Kontrolle

### Warum Superscript statt [1] Bracket?
- ✅ Professioneller (wie Fachpublikationen)
- ✅ Platzsparend (kleinere Schrift)
- ✅ Erkennbar (standardisierte Notation)
- ⚠️ Limitierung: tkinter `offset` nur in Pixeln (nicht percentage)

---

## 📊 Erfolgsmetriken

### Quantitativ:
- **Zitationsrate:** ≥80% der Fakten mit [N] zitiert
- **Citation-Click-Rate:** ≥30% der User klicken auf Zitationen
- **Suggestion-Click-Rate:** ≥50% der User klicken auf Vorschläge
- **Follow-up-Rate:** ≥40% der Sessions haben Follow-ups

### Qualitativ:
- **IEEE-Konformität:** 100% der Quellen im IEEE-Format
- **User-Feedback:** "Quellen transparent und nachvollziehbar"
- **Wissenschaftlichkeit:** "Veritas als vertrauenswürdige Quelle nutzbar"

---

## 🚀 Nächste Schritte

**Sofort (heute):**
1. Dokumentation reviewed → User-Feedback einholen
2. Implementierungs-Reihenfolge bestätigen
3. Sprint 1 starten: Backend-Prompt-Erweiterung

**Kurzfristig (nächste 2 Tage):**
4. Sprint 1 abschließen: IEEE-Zitationen End-to-End
5. Sprint 2 starten: Klickbare Vorschläge

**Mittelfristig (nächste Woche):**
6. User-Testing mit echten Verwaltungsrecht-Queries
7. Prompt-Tuning basierend auf Zitationsqualität
8. Optional: Advanced Features (Zitations-Export, BibTeX, etc.)

---

**Version:** v3.19.0 Planung  
**Datum:** 10. Oktober 2025  
**Autor:** GitHub Copilot  
**Review:** ⏳ Pending User Approval
