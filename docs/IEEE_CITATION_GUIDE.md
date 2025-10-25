# IEEE Citation System - Integration Guide

## 📚 Übersicht

VERITAS unterstützt wissenschaftliches Zitieren nach **IEEE-Standard** (Institute of Electrical and Electronics Engineers).

**Komponenten:**
1. **Inline-Citations** im Assistant-Text: `[1]`, `[2]`, `[3]`
2. **Quellenverzeichnis** in Metadaten-Wrapper (IEEE-formatiert)
3. **Klickbare Citations** mit Scroll-to-Reference
4. **Hover-Tooltips** mit Source-Details

---

## 🎯 IEEE Citation Standard

### Format-Übersicht

**Inline im Text:**
```
Deep Learning zeigt signifikante Erfolge [1] in der Verarbeitung
natürlicher Sprache [2], [3].
```

**Quellenverzeichnis:**
```
[1] J. Smith and A. Doe, "Deep Learning Advances," IEEE Trans. 
    Pattern Anal., vol. 42, no. 3, pp. 567-589, Mar. 2020.

[2] "VERITAS Documentation," https://veritas.example.com,
    accessed Oct. 17, 2025.

[3] A. Author, Document Title, Organization, 2024, pp. 1-50.
```

---

## 🔧 Backend-Integration

### 1. Citation-Marker im Response-Text

Das Backend muss Citations mit `{cite:source_id}` markieren:

```python
# Backend: Antwort-Generierung
response_text = """
Deep Learning zeigt Erfolge {cite:src_1} in der Verarbeitung
natürlicher Sprache {cite:src_2}.
"""

sources = [
    {
        'id': 'src_1',
        'file': 'deep_learning.pdf',
        'page': 42,
        'confidence': 0.87,
        'author': 'J. Smith',
        'title': 'Deep Learning Advances',
        'year': 2020
    },
    {
        'id': 'src_2',
        'url': 'https://veritas.example.com/docs',
        'title': 'VERITAS Documentation',
        'confidence': 0.85
    }
]

# Response an Frontend
return {
    'content': response_text,
    'sources': sources,
    'metadata': {...}
}
```

**Wichtig:**
- `{cite:source_id}` wird automatisch zu `[N]` konvertiert
- `source_id` muss mit `id` in Sources-Liste übereinstimmen
- Sources werden automatisch nummeriert (1, 2, 3, ...)

---

## 🎨 Frontend-Rendering

### Automatisches Rendering

Das `AssistantFullWidthLayout` rendert Citations automatisch:

```python
from frontend.ui.veritas_ui_chat_bubbles import AssistantFullWidthLayout

# Setup
assistant_layout = AssistantFullWidthLayout(
    text_widget=chat_text,
    markdown_renderer=markdown_renderer,
    metadata_handler=metadata_handler,
    enable_ieee_citations=True  # ✨ IEEE-Citations aktivieren
)

# Render Message mit Citations
assistant_layout.render_assistant_message(
    content="Text mit {cite:src_1} Citation.",
    metadata={...},
    sources=[
        {'id': 'src_1', 'file': 'doc.pdf', 'page': 10}
    ]
)
```

**Ergebnis:**
- Text: "Text mit [1] Citation."
- [1] ist klickbar (scroll to reference)
- [1] hat Hover-Tooltip mit Source-Details
- Metadaten-Wrapper zeigt: `[1] "doc.pdf", pp. 10.`

---

## 📋 Source-Metadaten für IEEE-Formatierung

### Unterstützte Felder

**Alle Source-Types:**
```python
{
    'id': 'src_1',           # Eindeutige ID (PFLICHT)
    'confidence': 0.87,      # Float 0-1
}
```

**PDF/Dokumente:**
```python
{
    'file': 'document.pdf',
    'author': 'J. Smith',         # Optional
    'title': 'Document Title',    # Optional
    'organization': 'IEEE',       # Optional
    'year': 2020,                 # Optional
    'page': 42,                   # Einzelne Seite
    'pages': '42-45',             # Seitenbereich
}
```

**Web-URLs:**
```python
{
    'url': 'https://example.com',
    'title': 'Page Title',        # Optional
    'website': 'Example Website', # Optional
    'access_date': 'Oct. 17, 2025' # Default: heute
}
```

**Bücher:**
```python
{
    'author': 'A. Author',
    'title': 'Book Title',
    'publisher': 'Publisher Name',
    'year': 2019,
    'edition': '2nd',             # Optional
    'isbn': '978-1234567890'      # Optional
}
```

**Datenbank-Einträge:**
```python
{
    'database': 'VERITAS DB',
    'entry_id': '12345',
    'title': 'Entry Title',
    'access_date': 'Oct. 17, 2025'
}
```

---

## 🎨 IEEE-Formatierungs-Regeln

### Journal-Artikel

**Format:**
```
[N] Author(s), "Article Title," Journal Name, vol. X, no. Y, 
    pp. ZZZ-ZZZ, Month Year.
```

**Beispiel:**
```
[1] J. Smith and A. Doe, "Deep Learning in NLP," IEEE Trans. 
    Pattern Anal., vol. 42, no. 3, pp. 567-589, Mar. 2020.
```

### Web-Quellen

**Format:**
```
[N] "Page Title," Website Name. URL (accessed Date).
```

**Beispiel:**
```
[2] "VERITAS Documentation," VERITAS Project. 
    https://veritas.example.com (accessed Oct. 17, 2025).
```

### PDF/Dokumente

**Format:**
```
[N] Author, "Document Title," Organization, Year, pp. Pages.
```

**Beispiel:**
```
[3] J. Smith, "Technical Report," IEEE, 2024, pp. 1-50.
```

### Bücher

**Format:**
```
[N] Author, Book Title, Edition. Publisher, Year.
```

**Beispiel:**
```
[4] A. Author, Machine Learning Basics, 2nd ed. MIT Press, 2019.
```

---

## 🖱️ Interaktive Features

### 1. Klickbare Citations

**Verhalten:**
- User klickt auf `[1]` im Text
- → Scrollt zu Quellenverzeichnis in Metadaten
- → Öffnet Metadaten-Wrapper (wenn collapsed)
- → Highlighted Reference [1]

**Implementierung:**
```python
# Automatisch durch IEEECitationRenderer
citation_renderer.render_text_with_citations(content)
```

### 2. Hover-Tooltips

**Anzeige bei Hover:**
```
📄 document.pdf
Page: 42
Confidence: 87%

"This is a snippet preview from the source..."
```

**Implementierung:**
```python
# Automatisch für alle Citations
# Tooltip zeigt Source-Details aus sources-Liste
```

### 3. Metadaten-Wrapper Expandieren

**Verhalten:**
- Metadaten initial collapsed: `▶ Metadata (3 Sources, ...)`
- Click auf Citation → Expand Metadaten
- Zeigt IEEE-Quellenverzeichnis

---

## 🔧 Konfiguration

### Citations aktivieren/deaktivieren

**Global:**
```python
assistant_layout = AssistantFullWidthLayout(
    ...,
    enable_ieee_citations=True  # Default
)
```

**Per Message:**
```python
assistant_layout.render_assistant_message(
    content="...",
    sources=[...],
    enable_citations=False  # Deaktiviere für diese Message
)
```

### Fallback ohne Citations

Wenn `enable_ieee_citations=False`:
- Standard Markdown-Rendering
- Metadaten zeigen einfache Bullet-Liste
- Keine klickbaren Citations

---

## 📊 Beispiel-Integration

### Vollständiges Beispiel

```python
# Backend-Response (simuliert)
backend_response = {
    'content': """
# Deep Learning in NLP

Aktuelle Studien zeigen signifikante Fortschritte {cite:src_1} 
in der maschinellen Verarbeitung natürlicher Sprache. 

Transformer-Architekturen {cite:src_2} haben die Genauigkeit 
um 15% verbessert.

## Weitere Forschung

Die VERITAS-Dokumentation {cite:src_3} bietet weitere Details.
""",
    'sources': [
        {
            'id': 'src_1',
            'file': 'nlp_advances.pdf',
            'author': 'J. Smith',
            'title': 'Deep Learning in NLP',
            'year': 2020,
            'page': 15,
            'confidence': 0.89
        },
        {
            'id': 'src_2',
            'file': 'transformers.pdf',
            'author': 'A. Vaswani et al.',
            'title': 'Attention is All You Need',
            'year': 2017,
            'pages': '5998-6008',
            'confidence': 0.92
        },
        {
            'id': 'src_3',
            'url': 'https://veritas.example.com/docs',
            'title': 'VERITAS Documentation',
            'confidence': 0.85
        }
    ],
    'metadata': {
        'complexity': 'Medium',
        'duration': 2.4,
        'model': 'llama3.2:latest'
    }
}

# Frontend-Rendering
assistant_layout.render_assistant_message(
    content=backend_response['content'],
    metadata=backend_response['metadata'],
    sources=backend_response['sources']
)
```

**Ergebnis im UI:**

```
# Deep Learning in NLP

Aktuelle Studien zeigen signifikante Fortschritte [1] 
in der maschinellen Verarbeitung natürlicher Sprache. 

Transformer-Architekturen [2] haben die Genauigkeit 
um 15% verbessert.

## Weitere Forschung

Die VERITAS-Dokumentation [3] bietet weitere Details.

▶ Metadata (3 Sources, Medium, 2.4s, llama3.2) 👍👎
```

**Bei Expand:**
```
▼ Metadata                                      👍👎
  📚 References (IEEE Standard):
     [1] J. Smith, "Deep Learning in NLP," 2020, pp. 15.
     [2] A. Vaswani et al., "Attention is All You Need," 
         2017, pp. 5998-6008.
     [3] "VERITAS Documentation," https://veritas.example.com, 
         accessed Oct. 17, 2025.
  ⚙️ Complexity: Medium
  ⏱️ Duration: 2.400s
  🤖 Model: llama3.2:latest
```

---

## 🧪 Testing

### Test-Cases

**1. Einfache Citation:**
```python
content = "Text with citation {cite:src_1}."
sources = [{'id': 'src_1', 'file': 'doc.pdf'}]
# Erwartet: "Text with citation [1]."
```

**2. Multiple Citations:**
```python
content = "Multiple {cite:src_1}, {cite:src_2} citations."
sources = [
    {'id': 'src_1', 'file': 'doc1.pdf'},
    {'id': 'src_2', 'file': 'doc2.pdf'}
]
# Erwartet: "Multiple [1], [2] citations."
```

**3. Unbekannte Source:**
```python
content = "Unknown {cite:unknown}."
sources = [{'id': 'src_1', 'file': 'doc.pdf'}]
# Erwartet: "Unknown [?]." (Fallback)
```

**4. Ohne Sources:**
```python
content = "No citations here."
sources = []
# Erwartet: Standard Markdown-Rendering
```

**5. Click-Handler:**
```python
# Click auf [1] → Scrollt zu Metadaten
# Metadaten expandieren (wenn collapsed)
# Highlight Reference [1]
```

---

## 📝 Backend-Checkliste

Für IEEE-Citations muss das Backend liefern:

- [ ] `{cite:source_id}` Marker im Response-Text
- [ ] `sources` Liste mit `id` Feld für jede Source
- [ ] Optional: `author`, `title`, `year` für bessere Formatierung
- [ ] Optional: `page` oder `pages` für Seitenangaben
- [ ] `confidence` Score für jede Source (0-1)

**Beispiel-Endpoint:**
```python
POST /chat/query

Response:
{
    "content": "Text {cite:src_1} mit Citation.",
    "sources": [
        {
            "id": "src_1",
            "file": "document.pdf",
            "page": 42,
            "confidence": 0.87,
            "author": "J. Smith",
            "title": "Document Title",
            "year": 2020
        }
    ],
    "metadata": {
        "complexity": "Medium",
        "duration": 1.5,
        "model": "llama3.2"
    }
}
```

---

## 🎯 Vorteile

### Wissenschaftliche Glaubwürdigkeit
- ✅ Standard IEEE-Format (weltweit anerkannt)
- ✅ Nachvollziehbare Quellenangaben
- ✅ Automatische Nummerierung

### User Experience
- ✅ Klickbare Citations (Scroll-to-Reference)
- ✅ Hover-Tooltips (Quick Preview)
- ✅ Kompakte Darstellung (collapsed by default)

### Entwickler-Freundlich
- ✅ Automatische Formatierung
- ✅ Flexible Source-Metadaten
- ✅ Fallback-Mechanismen
- ✅ Einfache Backend-Integration

---

## 🚀 Next Steps

### Phase 1: Backend-Anpassung
1. [ ] Backend liefert `{cite:source_id}` Marker
2. [ ] Source-IDs eindeutig vergeben
3. [ ] Metadaten erweitern (author, title, year)

### Phase 2: Frontend-Testing
4. [ ] Test mit verschiedenen Source-Types
5. [ ] Click-Handler testen
6. [ ] Hover-Tooltips validieren

### Phase 3: Advanced Features
7. [ ] BibTeX-Export aus Quellenverzeichnis
8. [ ] Copy Citation to Clipboard
9. [ ] Citation-Count pro Source (Analytics)

---

**Version:** 1.0  
**Datum:** 17. Oktober 2025  
**Status:** 🚀 Ready for Integration
