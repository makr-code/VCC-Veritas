# 🎨 VERITAS Structured LLM Response System - Konzeptplan

**Version:** v4.1.0 (Rich Media + Streaming + Dynamic Tokens + Templates)  
**Created:** 12. Oktober 2025, 18:00 Uhr  
**Updated:** 12. Oktober 2025, 18:15 Uhr  
**Status:** 📋 KONZEPTPHASE - Ready for Implementation

---

## 📚 Dokumentations-Übersicht

**Dieses Dokument:** Vollständige technische Spezifikation (1,700+ Zeilen)

**Quick Access:**
- **Executive Summary:** `STRUCTURED_RESPONSE_EXECUTIVE_SUMMARY.md` (600 Zeilen, Business-Perspektive)
- **Quick Reference:** `STRUCTURED_RESPONSE_QUICKREF.md` (300 Zeilen, Cheat Sheet für Developer)

---

## 📑 Inhaltsverzeichnis

1. **[Zielsetzung](#-zielsetzung)** - Die 7 Hauptanforderungen
2. **[Kritische Architektur-Anforderungen](#-kritische-architektur-anforderungen)**
   - 2.1 Streaming Client ⚡ (BEREITS VORHANDEN)
   - 2.2 Dynamische Token-Size 📏 (NEU - Adaptive Token Manager)
   - 2.3 Template-System 📋 (NEU - 5 Verwaltungsrechtliche Templates)
3. **[Recherche: Bestehende VERITAS-Features](#-recherche-bestehende-veritas-features)**
   - Streaming-System (639 LOC) ✅
   - Markdown-Renderer (1,000 LOC) ✅
   - Chat-Formatter (2,100 LOC) ✅
   - Syntax-Highlighter (300 LOC) ✅
4. **[Vorgeschlagene Architektur](#-vorgeschlagene-architektur)**
   - Phase 1: Standardisiertes Response-Format (NDJSON)
   - Phase 2: Widget-Renderer-System
   - Phase 3: LLM-Prompt-Template
   - Phase 4: Integration in Chat-Formatter
5. **[Widget-Typen](#-widget-typen-vollständige-liste)** - Text, Media, Interactive, Visualisierungen, Custom
6. **[Implementierungs-Roadmap](#-implementierungs-roadmap-aktualisiert)** - 6 Phasen, 11-17 Tage
7. **[Beispiel-Use-Cases](#-beispiel-use-cases)** - Zuständigkeit, Code-Beispiel, Visualisierung
8. **[Technische Details](#-technische-details)** - Dependencies, Memory-Management, Performance
9. **[Moderne Referenz-Systeme](#-moderne-referenz-systeme)** - Discord, Telegram, VS Code, Jupyter
10. **[Empfehlung & Nächste Schritte](#-empfehlung--implementierungs-strategie)**

---

## 🎯 Zielsetzung

**Problem:** LLM-Antworten sind aktuell reiner Text/Markdown. Wir brauchen:
1. **Strukturierte Metadaten** (Quellen, Confidence, Vorschläge, etc.)
2. **Rich Media Support** (Buttons, Canvas, Images, Videos, Interactive Widgets)
3. **Standardisiertes Format** für LLM-Output (Markdown + JSON Mix)
4. **Tkinter-Native Rendering** aller Elemente
5. **Streaming Support** ⚡ (Sequenzielles Fortschreiben während LLM generiert) - **KRITISCH!**
6. **Dynamische Token-Size** 📏 (Flexible Context-Länge basierend auf Komplexität) - **KRITISCH!**
7. **Template-System** 📋 (Verwaltungsrechtliche Spezial-Prompts serverseitig) - **KRITISCH!**

**Hinweis:** Anforderungen 5-7 wurden vom User explizit als kritisch für das Konzept spezifiziert.

---

## ⚡ Kritische Architektur-Anforderungen

### 1. **Streaming Client** (BEREITS VORHANDEN ✅)

VERITAS hat bereits einen **voll funktionsfähigen Streaming-Client!**

**Bestehende Architektur:**
```
veritas_streaming_service.py (Backend)
    ├→ VeritasStreamingService (WebSocket + HTTP Streaming)
    ├→ StreamingUIMixin (Frontend Integration)
    ├→ ProgressStage/ProgressType (Progress-Updates)
    └→ ThreadManager Integration (Thread-Safe)

veritas_ollama_client.py (LLM Backend)
    └→ generate_response(stream=True) → AsyncGenerator
```

**Konsequenz für Structured Response:**
- ✅ **Sequenzielles Fortschreiben** ist bereits implementiert
- ⚠️ **JSON + Markdown Mix** muss **streaming-fähig** sein
- ⚠️ **Widget-Rendering** muss **inkrementell** erfolgen

**Neue Anforderung:**
```python
# STREAMING STRUCTURED RESPONSE FORMAT
# Statt 1x komplettes JSON am Ende → Mehrere JSON-Chunks während Streaming

# Chunk 1 (Header, sofort nach Start)
{
  "type": "response_start",
  "metadata": {
    "confidence": null,  # Wird später aktualisiert
    "template": "zustaendigkeit_behoerde",  # Welches Template wird genutzt
    "estimated_tokens": 2500  # Dynamisch geschätzt
  }
}

# Chunk 2-N (Text-Chunks, während LLM generiert)
{
  "type": "text_chunk",
  "content": "Gemäß **BauGB §35** ist für Ihr Vorhaben...",
  "position": "main"  # main | metadata | source | suggestion
}

# Chunk N+1 (Widget erscheint, wenn im Text erwähnt)
{
  "type": "widget",
  "widget": {
    "type": "table",
    "headers": ["Behörde", "Zuständigkeit"],
    "rows": [["Bauamt", "Baugenehmigung"], ...]
  }
}

# Letzter Chunk (Finalisierung)
{
  "type": "response_end",
  "metadata": {
    "confidence": 0.92,  # Finale Confidence
    "sources": [...],
    "suggestions": [...]
  }
}
```

**Implementation:**
```python
class StreamingStructuredResponseParser:
    """
    Parst Streaming-Response inkrementell
    Unterstützt Mix aus Text-Chunks und JSON-Widgets
    """
    
    def __init__(self, chat_formatter, widget_renderer):
        self.chat_formatter = chat_formatter
        self.widget_renderer = widget_renderer
        self.buffer = ""
        self.current_metadata = {}
        self.widgets_queue = []
    
    async def process_chunk(self, chunk: str) -> None:
        """
        Verarbeitet einzelnen Streaming-Chunk
        Kann Text ODER JSON sein
        """
        # Prüfe ob JSON-Chunk (startet mit '{')
        if chunk.strip().startswith('{'):
            try:
                data = json.loads(chunk)
                await self._handle_json_chunk(data)
            except json.JSONDecodeError:
                # Falls JSON unvollständig → in Buffer
                self.buffer += chunk
        else:
            # Text-Chunk → sofort rendern
            await self._handle_text_chunk(chunk)
    
    async def _handle_json_chunk(self, data: dict):
        chunk_type = data.get('type')
        
        if chunk_type == 'response_start':
            # Initialisiere Response (Template, Metadata)
            self.current_metadata = data.get('metadata', {})
            # UI: Zeige Template-Badge
            
        elif chunk_type == 'text_chunk':
            # Text inkrementell rendern
            content = data.get('content', '')
            position = data.get('position', 'main')
            
            if position == 'main':
                # Markdown rendern (incrementell!)
                self.chat_formatter.markdown_renderer.render_markdown(
                    content, append=True  # WICHTIG: append statt replace
                )
            
        elif chunk_type == 'widget':
            # Widget sofort rendern
            widget_spec = data.get('widget', {})
            self.widget_renderer.render_widget(widget_spec)
            
        elif chunk_type == 'response_end':
            # Finalisiere (Quellen, Vorschläge, Confidence)
            final_metadata = data.get('metadata', {})
            self.chat_formatter._insert_sources(final_metadata.get('sources', []))
            self.chat_formatter._insert_suggestions(final_metadata.get('suggestions', []))
            self.chat_formatter._insert_confidence_badge(final_metadata.get('confidence'))
    
    async def _handle_text_chunk(self, text: str):
        """Plain-Text-Chunk (kein JSON)"""
        # Sofort rendern (Streaming-Feeling!)
        self.chat_formatter.markdown_renderer.render_markdown(
            text, append=True
        )
```

---

### 2. **Dynamische Token-Size** 📏 (NEU)

**Problem:** 
Feste Token-Limits (z.B. 4096) sind bei komplexen verwaltungsrechtlichen Themen kontraproduktiv:
- Einfache Frage ("Wer ist zuständig?") → 500 Tokens reichen
- Komplexe Frage ("Vollständige Prüfung Bauantrag inkl. formell, rechtlich, sachlich") → 8000+ Tokens nötig

**Lösung: Adaptive Context Window**

```python
class AdaptiveTokenManager:
    """
    Dynamische Token-Size basierend auf:
    1. Frage-Komplexität (NLP-Analyse)
    2. Template-Requirements (jedes Template hat Min/Max)
    3. RAG-Kontext-Größe (wie viele Quellen gefunden)
    4. User-Historie (Follow-up vs. Neue Frage)
    """
    
    TOKEN_LIMITS = {
        'min': 1024,      # Minimales Context-Window
        'default': 4096,  # Standard für einfache Fragen
        'extended': 8192, # Erweitert für komplexe Themen
        'max': 16384      # Maximum (nur für sehr komplexe Analysen)
    }
    
    TEMPLATE_TOKEN_REQUIREMENTS = {
        'zustaendigkeit_behoerde': 2048,  # Einfache Zuständigkeits-Frage
        'formale_pruefung': 4096,         # Formale Prüfung (Antragsbestandteile)
        'rechtliche_pruefung': 6144,      # Rechtliche Prüfung (BauGB, BauNVO, LBO)
        'sachliche_pruefung': 8192,       # Sachliche Prüfung (technische Details)
        'vollstaendige_pruefung': 16384,  # Alle 3 Prüfungen kombiniert
    }
    
    def estimate_required_tokens(self, 
                                 user_query: str,
                                 template: str,
                                 rag_context_size: int,
                                 is_followup: bool = False) -> int:
        """
        Schätzt benötigte Token-Anzahl dynamisch
        
        Args:
            user_query: User-Frage
            template: Gewähltes Prompt-Template
            rag_context_size: Größe des RAG-Kontexts (Anzahl Tokens)
            is_followup: Ist es eine Follow-up-Frage?
        
        Returns:
            int: Empfohlene Token-Anzahl
        """
        # 1. Template-Basis
        base_tokens = self.TEMPLATE_TOKEN_REQUIREMENTS.get(template, self.TOKEN_LIMITS['default'])
        
        # 2. Frage-Komplexität analysieren
        query_complexity = self._analyze_query_complexity(user_query)
        complexity_factor = {
            'simple': 0.5,    # "Wer ist zuständig?" → 50% von base
            'medium': 1.0,    # Standard-Frage → 100% von base
            'complex': 1.5,   # Multi-Teil-Frage → 150% von base
            'very_complex': 2.0  # Vollständige Analyse → 200% von base
        }.get(query_complexity, 1.0)
        
        # 3. RAG-Kontext einberechnen
        rag_overhead = min(rag_context_size, 2048)  # Max 2048 Tokens für RAG
        
        # 4. Follow-up Reduktion (Context bereits geladen)
        followup_reduction = 0.7 if is_followup else 1.0
        
        # Finale Berechnung
        estimated_tokens = int(
            (base_tokens * complexity_factor + rag_overhead) * followup_reduction
        )
        
        # Clamp auf min/max
        return max(
            self.TOKEN_LIMITS['min'],
            min(estimated_tokens, self.TOKEN_LIMITS['max'])
        )
    
    def _analyze_query_complexity(self, query: str) -> str:
        """
        Analysiert Frage-Komplexität via NLP
        
        Indikatoren:
        - Wort-Anzahl
        - Anzahl Rechtsbegriffe
        - Anzahl Fragen (?, und, sowie)
        - Spezielle Keywords ("vollständig", "detailliert", "alle", "sämtliche")
        """
        words = query.split()
        word_count = len(words)
        
        # Rechtsbegriffe (vereinfacht)
        legal_terms = ['BauGB', 'BauNVO', 'LBO', 'Genehmigung', 'Zuständigkeit', 
                       'Prüfung', 'Verfahren', 'Antrag', 'Bebauungsplan']
        legal_term_count = sum(1 for term in legal_terms if term in query)
        
        # Komplexitäts-Keywords
        complex_keywords = ['vollständig', 'detailliert', 'alle', 'sämtliche', 
                            'komplett', 'umfassend', 'inklusiv']
        has_complex_keywords = any(kw in query.lower() for kw in complex_keywords)
        
        # Multi-Teil-Fragen
        question_parts = query.count('?') + query.count(' und ') + query.count(' sowie ')
        
        # Klassifizierung
        if word_count < 10 and legal_term_count <= 1:
            return 'simple'
        elif word_count > 50 or legal_term_count > 5 or has_complex_keywords:
            return 'very_complex'
        elif question_parts > 2 or legal_term_count > 3:
            return 'complex'
        else:
            return 'medium'
```

**Backend-Integration:**
```python
# In Ollama-Client
async def generate_response(self, request: OllamaRequest, template: str = None):
    # Dynamische Token-Schätzung
    token_manager = AdaptiveTokenManager()
    estimated_tokens = token_manager.estimate_required_tokens(
        user_query=request.prompt,
        template=template or 'default',
        rag_context_size=len(request.context or []),
        is_followup=request.context is not None
    )
    
    # Ollama Request mit dynamischer Token-Anzahl
    payload = {
        "model": request.model,
        "prompt": request.prompt,
        "stream": True,  # Streaming aktiviert
        "options": {
            "num_predict": estimated_tokens,  # Dynamisch!
            "temperature": request.temperature,
        }
    }
    
    logger.info(f"🎯 Estimated Tokens: {estimated_tokens} (Template: {template})")
```

---

### 3. **Template-System** 📋 (NEU - SERVERSEITIG)

**Problem:**
Verwaltungsrechtliche Aspekte erfordern **spezialisierte Prompts**:
- **Zuständigkeit der Behörde** → Andere Prompt-Struktur als
- **Formale Prüfung** → Andere Struktur als
- **Rechtliche Prüfung** → Andere Struktur als
- **Sachliche Prüfung**

Aktuell: 1 generischer System-Prompt für alles → Suboptimal!

**Lösung: Serverseitiges Template-System**

```python
# backend/templates/prompt_templates.py

from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    """Definition eines Prompt-Templates"""
    id: str
    name: str
    description: str
    system_prompt: str
    required_context: List[str]
    expected_tokens: int
    response_structure: Dict[str, Any]
    
class PromptTemplateLibrary:
    """
    Zentrale Template-Bibliothek für verwaltungsrechtliche Aspekte
    SERVERSEITIG - Templates werden NUR im Backend verwaltet
    """
    
    TEMPLATES = {
        'zustaendigkeit_behoerde': PromptTemplate(
            id='zustaendigkeit_behoerde',
            name='Zuständigkeit der Behörde',
            description='Ermittelt zuständige Behörde(n) für ein Vorhaben',
            system_prompt="""
Du bist VERITAS, ein Experte für deutsches Baurecht.

AUFGABE: Ermittle die zuständige(n) Behörde(n) für das beschriebene Vorhaben.

VORGEHEN:
1. Identifiziere Vorhaben-Typ (Hochbau, Tiefbau, Außenbereich, etc.)
2. Prüfe örtliche Zuständigkeit (Gemeinde, Landkreis, Bezirk)
3. Prüfe sachliche Zuständigkeit (Bauordnung, Naturschutz, Denkmalschutz, etc.)
4. Liste ALLE beteiligten Behörden auf

ANTWORT-FORMAT (Structured Response):
{
  "type": "text_chunk",
  "content": "Für Ihr Vorhaben sind folgende Behörden zuständig:\\n\\n**Hauptzuständigkeit:**\\n- [Behörde] ([Rechtsgrundlage])\\n\\n**Beteiligte Behörden:**\\n- [Behörde 1] ([Grund])\\n- [Behörde 2] ([Grund])"
}

{
  "type": "widget",
  "widget": {
    "type": "table",
    "headers": ["Behörde", "Zuständigkeit", "Rechtsgrundlage"],
    "rows": [
      ["Bauordnungsamt", "Baugenehmigung", "BauGB §29"],
      ["Untere Naturschutzbehörde", "Naturschutzprüfung", "BNatSchG §17"]
    ]
  }
}

WICHTIG:
- Nenne konkrete Rechtsgrundlagen (BauGB §X, LBO §Y)
- Unterscheide Hauptzuständigkeit vs. beteiligte Behörden
- Erwähne Verfahrensart (vereinfacht, normal, erweitert)

QUELLEN: Verwende RAG-Kontext für lokale Besonderheiten.
""",
            required_context=['bauvorhaben_typ', 'standort', 'nutzung'],
            expected_tokens=2048,
            response_structure={
                'main_text': 'markdown',
                'widgets': ['table'],
                'metadata': ['sources', 'confidence']
            }
        ),
        
        'formale_pruefung': PromptTemplate(
            id='formale_pruefung',
            name='Formale Prüfung Bauantrag',
            description='Prüft Vollständigkeit und Form des Bauantrags',
            system_prompt="""
Du bist VERITAS, Experte für formale Anforderungen im Baugenehmigungsverfahren.

AUFGABE: Formale Prüfung des Bauantrags (Vollständigkeit, Form, Fristen)

PRÜF-KATALOG:
1. **Antragsbestandteile** (BauPrüfVO):
   - Bauvorlagen vollständig? (Bauzeichnungen, Baubeschreibung, etc.)
   - Unterschriften vorhanden?
   - Bauvorlageberechtigung nachgewiesen?
   
2. **Formale Anforderungen**:
   - Richtiger Antragsweg?
   - Zuständigkeit gegeben?
   - Fristen eingehalten?
   
3. **Gebühren**:
   - Gebührentatbestand?
   - Betrag?

ANTWORT-FORMAT:
{
  "type": "text_chunk",
  "content": "## Formale Prüfung\\n\\n### ✅ Vollständig:\\n- [Punkt]\\n\\n### ⚠️ Fehlend/Unvollständig:\\n- [Punkt]"
}

{
  "type": "widget",
  "widget": {
    "type": "table",
    "headers": ["Bestandteil", "Status", "Rechtsgrundlage", "Handlungsbedarf"],
    "rows": [
      ["Bauzeichnungen", "✅ Vollständig", "BauPrüfVO §3", "Keine"],
      ["Standsicherheitsnachweis", "❌ Fehlt", "BauPrüfVO §5", "Nachreichen binnen 4 Wochen"]
    ]
  }
}

WICHTIG:
- Klare Unterscheidung: Vollständig ✅ vs. Fehlend ❌
- Rechtsgrundlagen für JEDEN Punkt
- Konkrete Handlungsempfehlungen
- Fristen nennen
""",
            required_context=['bauantrag_dokumente', 'antragsteller', 'bauvorhaben'],
            expected_tokens=4096,
            response_structure={
                'main_text': 'markdown_checklist',
                'widgets': ['table', 'checklist'],
                'metadata': ['sources', 'suggestions']
            }
        ),
        
        'rechtliche_pruefung': PromptTemplate(
            id='rechtliche_pruefung',
            name='Rechtliche Prüfung',
            description='Prüft Übereinstimmung mit öffentlich-rechtlichen Vorschriften',
            system_prompt="""
Du bist VERITAS, Experte für materielles Baurecht.

AUFGABE: Rechtliche Prüfung des Bauvorhabens (Vereinbarkeit mit öffentlich-rechtlichen Vorschriften)

PRÜF-EBENEN:
1. **Bauplanungsrecht** (BauGB, BauNVO):
   - Zulässigkeit im Plangebiet?
   - Art der baulichen Nutzung?
   - Maß der baulichen Nutzung?
   - Bauweise, überbaubare Grundstücksfläche?
   
2. **Bauordnungsrecht** (LBO):
   - Abstandsflächen?
   - Brandschutz?
   - Barrierefreiheit?
   
3. **Fachrecht**:
   - Naturschutz?
   - Denkmalschutz?
   - Immissionsschutz?

ANTWORT-FORMAT:
{
  "type": "text_chunk",
  "content": "## Rechtliche Prüfung\\n\\n### Bauplanungsrecht\\n\\n#### Zulässigkeit gem. BauGB §30\\n[Prüfung]..."
}

{
  "type": "widget",
  "widget": {
    "type": "canvas",
    "draw_commands": [
      {"cmd": "rect", "x": 50, "y": 50, "width": 100, "height": 80, "fill": "lightgray", "outline": "black"},
      {"cmd": "text", "x": 100, "y": 90, "text": "Gebäude", "font": ["Arial", 10]},
      {"cmd": "line", "x1": 150, "y1": 90, "x2": 200, "y2": 90, "color": "red", "width": 2},
      {"cmd": "text", "x": 210, "y": 85, "text": "3m Abstand", "font": ["Arial", 9], "color": "red"}
    ],
    "width": 400,
    "height": 300,
    "caption": "Abstandsflächen-Visualisierung"
  }
}

WICHTIG:
- Systematische Prüfung (Bauplanungsrecht → Bauordnungsrecht → Fachrecht)
- Jede Norm mit Fundstelle (BauGB §35 Abs. 2)
- Bei Konflikten: Ausnahme/Befreiung möglich?
- Visualisierungen für geometrische Anforderungen (Abstandsflächen, etc.)
""",
            required_context=['bauvorhaben', 'grundstueck', 'bebauungsplan', 'nutzung'],
            expected_tokens=6144,
            response_structure={
                'main_text': 'markdown_hierarchical',
                'widgets': ['canvas', 'table'],
                'metadata': ['sources', 'confidence', 'suggestions']
            }
        ),
        
        'sachliche_pruefung': PromptTemplate(
            id='sachliche_pruefung',
            name='Sachliche/Technische Prüfung',
            description='Prüft technische und sachliche Anforderungen',
            system_prompt="""
Du bist VERITAS, Experte für technische Bauvorschriften.

AUFGABE: Sachliche/Technische Prüfung des Bauvorhabens

PRÜF-ASPEKTE:
1. **Standsicherheit**:
   - Statik-Nachweis plausibel?
   - Gründung angemessen?
   
2. **Brandschutz**:
   - Gebäudeklasse?
   - Rettungswege?
   - Feuerwiderstandsklassen?
   
3. **Schall-/Wärmeschutz**:
   - EnEV/GEG Anforderungen?
   - Schallschutz nach DIN 4109?
   
4. **Erschließung**:
   - Zufahrt vorhanden?
   - Ver-/Entsorgung gesichert?

ANTWORT-FORMAT:
{
  "type": "text_chunk",
  "content": "## Sachliche Prüfung\\n\\n### Standsicherheit\\n[Prüfung]..."
}

{
  "type": "widget",
  "widget": {
    "type": "chart",
    "chart_type": "bar",
    "title": "Energieeffizienz-Anforderungen",
    "data": {
      "labels": ["IST-Wert", "SOLL (GEG)", "Grenzwert"],
      "values": [45, 55, 70]
    },
    "unit": "kWh/m²a"
  }
}

WICHTIG:
- Technische Normen referenzieren (DIN, VDE, EnEV/GEG)
- Bei Abweichungen: Kompensationsmaßnahmen?
- Visualisierung bei komplexen technischen Daten (Diagramme, Charts)
""",
            required_context=['bauvorhaben', 'technische_nachweise', 'gebaeudetyp'],
            expected_tokens=8192,
            response_structure={
                'main_text': 'markdown_technical',
                'widgets': ['chart', 'table', 'canvas'],
                'metadata': ['sources', 'confidence', 'suggestions']
            }
        ),
        
        'vollstaendige_pruefung': PromptTemplate(
            id='vollstaendige_pruefung',
            name='Vollständige Prüfung (Formell + Rechtlich + Sachlich)',
            description='Kombiniert alle 3 Prüfungsebenen',
            system_prompt="""
Du bist VERITAS, umfassender Experte für Baugenehmigungsverfahren.

AUFGABE: Vollständige Prüfung des Bauantrags (Formell, Rechtlich, Sachlich)

STRUKTUR:
1. **Executive Summary** (Ampel: ✅ Genehmigungsfähig / ⚠️ Mit Auflagen / ❌ Nicht genehmigungsfähig)
2. **Formale Prüfung** (siehe Template 'formale_pruefung')
3. **Rechtliche Prüfung** (siehe Template 'rechtliche_pruefung')
4. **Sachliche Prüfung** (siehe Template 'sachliche_pruefung')
5. **Gesamtfazit + Handlungsempfehlungen**

ANTWORT-FORMAT:
{
  "type": "text_chunk",
  "content": "# Vollständige Bauantrags-Prüfung\\n\\n## ✅ Executive Summary\\n\\nDer Bauantrag ist **genehmigungsfähig mit Auflagen**..."
}

{
  "type": "widget",
  "widget": {
    "type": "table",
    "headers": ["Prüfungsebene", "Status", "Kritische Punkte", "Handlungsbedarf"],
    "rows": [
      ["Formale Prüfung", "⚠️ Mit Mängeln", "Standsicherheitsnachweis fehlt", "Nachreichen binnen 4 Wo"],
      ["Rechtliche Prüfung", "✅ OK", "-", "-"],
      ["Sachliche Prüfung", "⚠️ Mit Auflagen", "Brandschutz Auflage", "Sprinkleranlage erforderlich"]
    ]
  }
}

WICHTIG:
- Executive Summary mit klarer Empfehlung (Ampel-System)
- Alle 3 Prüfungsebenen systematisch durchgehen
- Priorisierung: Was MUSS sofort behoben werden?
- Konkrete Handlungsschritte mit Fristen
""",
            required_context=['bauantrag_komplett', 'grundstueck', 'bebauungsplan', 'technische_nachweise'],
            expected_tokens=16384,  # SEHR GROSS!
            response_structure={
                'main_text': 'markdown_comprehensive',
                'widgets': ['table', 'chart', 'canvas', 'checklist'],
                'metadata': ['sources', 'confidence', 'suggestions', 'next_steps']
            }
        ),
    }
    
    @classmethod
    def get_template(cls, template_id: str) -> PromptTemplate:
        """Holt Template nach ID"""
        return cls.TEMPLATES.get(template_id)
    
    @classmethod
    def select_template_auto(cls, user_query: str, rag_context: Dict) -> str:
        """
        Wählt automatisch passendes Template basierend auf User-Frage
        
        Keyword-Matching:
        - "zuständig" → zustaendigkeit_behoerde
        - "vollständig" oder "Unterlagen" → formale_pruefung
        - "rechtlich" oder "zulässig" → rechtliche_pruefung
        - "technisch" oder "Statik" oder "Brandschutz" → sachliche_pruefung
        - "komplett" oder "umfassend" → vollstaendige_pruefung
        """
        query_lower = user_query.lower()
        
        # Keyword-Matching (vereinfacht, später via NLP/Classifier)
        if 'zuständig' in query_lower or 'behörde' in query_lower:
            return 'zustaendigkeit_behoerde'
        elif 'vollständig' in query_lower or 'unterlagen' in query_lower or 'formell' in query_lower:
            return 'formale_pruefung'
        elif 'rechtlich' in query_lower or 'zulässig' in query_lower or 'baurecht' in query_lower:
            return 'rechtliche_pruefung'
        elif 'technisch' in query_lower or 'statik' in query_lower or 'brandschutz' in query_lower:
            return 'sachliche_pruefung'
        elif any(kw in query_lower for kw in ['komplett', 'umfassend', 'alle prüfungen', 'vollständige prüfung']):
            return 'vollstaendige_pruefung'
        else:
            # Default: Kein spezielles Template
            return 'default'
```

**Backend-Integration:**
```python
# In Backend API (z.B. FastAPI Endpoint)
from backend.templates.prompt_templates import PromptTemplateLibrary, AdaptiveTokenManager

@app.post("/api/v1/chat/structured")
async def chat_structured(
    user_query: str,
    template_id: Optional[str] = None,  # Optional: User kann Template explizit wählen
    rag_context: Optional[Dict] = None
):
    """
    Structured Response Endpoint mit Template-System
    """
    # 1. Template auswählen (auto oder explizit)
    if template_id is None:
        template_id = PromptTemplateLibrary.select_template_auto(user_query, rag_context or {})
    
    template = PromptTemplateLibrary.get_template(template_id)
    
    if template is None:
        # Fallback auf Standard-Prompt
        system_prompt = "Du bist VERITAS, ein KI-Assistent für deutsches Baurecht."
        estimated_tokens = 4096
    else:
        system_prompt = template.system_prompt
        estimated_tokens = template.expected_tokens
    
    # 2. Dynamische Token-Anpassung
    token_manager = AdaptiveTokenManager()
    final_tokens = token_manager.estimate_required_tokens(
        user_query=user_query,
        template=template_id,
        rag_context_size=len(str(rag_context or {})),
        is_followup=False  # TODO: Session-History checken
    )
    
    logger.info(f"📋 Template: {template_id} | Tokens: {final_tokens}")
    
    # 3. Ollama Request mit Streaming
    ollama_request = OllamaRequest(
        model="llama3.2:latest",
        prompt=user_query,
        system=system_prompt,
        temperature=0.3,  # Niedrig für rechtliche Präzision
        max_tokens=final_tokens  # DYNAMISCH!
    )
    
    # 4. Streaming Response
    async def stream_structured_response():
        # Header-Chunk (sofort)
        yield json.dumps({
            "type": "response_start",
            "metadata": {
                "template": template_id,
                "estimated_tokens": final_tokens,
                "confidence": None  # Wird später aktualisiert
            }
        }) + "\n"
        
        # LLM Streaming
        async for chunk in ollama_client.generate_response(ollama_request, stream=True):
            # Text-Chunk
            yield json.dumps({
                "type": "text_chunk",
                "content": chunk.response,
                "position": "main"
            }) + "\n"
        
        # Finale Metadaten (am Ende)
        yield json.dumps({
            "type": "response_end",
            "metadata": {
                "confidence": 0.92,  # TODO: Aus Ollama Response
                "sources": [...],     # TODO: Aus RAG
                "suggestions": [...]  # TODO: Generieren
            }
        }) + "\n"
    
    return StreamingResponse(
        stream_structured_response(),
        media_type="application/x-ndjson"  # Newline-Delimited JSON
    )
```

---

## 🔍 Recherche: Bestehende VERITAS-Features

### ✅ Bereits vorhanden (SEHR GUT!)

VERITAS hat **bereits** ein fortgeschrittenes System:

#### 0. **Streaming-System** (`veritas_streaming_service.py`) ⚡ BEREITS VORHANDEN!
```python
class VeritasStreamingService:
    # Unterstützt:
    - WebSocket + HTTP Streaming
    - ProgressStage/ProgressType (RAG, Retrieval, Response, etc.)
    - Thread-Safe Integration (ThreadManager)
    - StreamingUIMixin (Frontend-Binding)
    - Cancel-Funktionalität
    
class StreamingUIMixin:
    # Frontend-Integration:
    - init_streaming_ui() - UI Setup
    - setup_streaming_integration() - Backend-Binding
    - _handle_streaming_message() - Message Processing
    
# Ollama-Client Streaming
async def generate_response(stream=True) -> AsyncGenerator:
    # Liefert inkrementelle Chunks
    async for chunk in response.aiter_lines():
        yield OllamaResponse(...)
```

**⚠️ WICHTIG FÜR STRUCTURED RESPONSE:**
- Streaming ist BEREITS implementiert ✅
- Structured Response MUSS streaming-fähig sein
- JSON + Markdown Mix MUSS inkrementell renderbar sein
- Widgets MÜSSEN während Streaming erscheinen können

---


#### 1. **Markdown-Renderer** (`veritas_ui_markdown.py`)
```python
class MarkdownRenderer:
    # Unterstützt:
    - Headings (#, ##, ###)
    - Bold (**text**), Italic (*text*)
    - Code-Blöcke (```python ... ```)
    - Syntax-Highlighting (Pygments)
  - Links [Text](URL) <!-- TODO: replace 'URL' with actual target -->
    - Listen (-, *, 1.)
    - Tabellen (Markdown Tables)
    - Blockquotes (> Text)
    - Copy-Button für Code
```

#### 2. **Chat-Display-Formatter** (`veritas_ui_chat_formatter.py`)
```python
class ChatDisplayFormatter:
    # Unterstützt:
    - RAG-Metadaten (Confidence, Sources, Agents)
    - Collapsible Sections (Details ausklappbar)
    - Quellen-Liste mit Icons
    - Klickbare Vorschläge
    - Feedback-Widgets (Thumbs Up/Down)
    - Relative Timestamps
    - Attachments-Liste
```

#### 3. **Syntax-Highlighter** (`veritas_ui_syntax.py`)
```python
class SyntaxHighlighter:
    # Unterstützt:
    - Pygments-Integration
    - 15+ Programmiersprachen
    - Custom Tag-Configuration
```

#### 4. **Icon-System** (`veritas_ui_icons.py`)
```python
class VeritasIcons:
    # Unterstützt:
    - Unicode Icons
    - Custom SVG Icons
    - Fallback-System
```

---

## 🆕 Was fehlt noch?

### ❌ Noch NICHT vorhanden:

1. **Standardisiertes LLM-Response-Format** (JSON Schema)
2. **Canvas-Widgets** (für Diagramme, Zeichnungen)
3. **Image/Video-Embedding** (direkt im Chat)
4. **Interactive Buttons** (außer Feedback-Buttons)
5. **Custom Tkinter Widgets** (z.B. Slider, Dropdown, etc.)
6. **LLM-Prompt-Template** für strukturierte Ausgabe

---

## 📐 Vorgeschlagene Architektur

### Phase 1: Standardisiertes Response-Format

**LLM Output Schema (JSON + Markdown Mix):**

```json
{
  "type": "structured_response",
  "version": "1.0",
  "content": {
    "text": "Dies ist die Hauptantwort in **Markdown**...",
    "metadata": {
      "confidence": 0.95,
      "sources": [
        {"url": "https://...", "title": "Quelle 1"},
        {"file": "doc.pdf", "page": 5}
      ],
      "timestamp": "2025-10-12T18:00:00Z",
      "agent": "VERITAS Legal RAG"
    },
    "suggestions": [
      "Weitere Frage 1?",
      "Weitere Frage 2?"
    ],
    "widgets": [
      {
        "type": "code_block",
        "language": "python",
        "code": "def hello():\n    print('Hello')",
        "caption": "Beispiel-Code"
      },
      {
        "type": "table",
        "headers": ["Spalte 1", "Spalte 2"],
        "rows": [["Wert 1", "Wert 2"]]
      },
      {
        "type": "image",
        "url": "https://example.com/image.png",
        "caption": "Beispiel-Bild",
        "width": 400
      },
      {
        "type": "button",
        "label": "Klick mich",
        "action": "show_details",
        "payload": {"detail_id": "123"}
      },
      {
        "type": "canvas",
        "draw_commands": [
          {"cmd": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100},
          {"cmd": "rect", "x": 50, "y": 50, "width": 100, "height": 50}
        ],
        "width": 400,
        "height": 300
      }
    ]
  }
}
```

---

### Phase 2: Widget-Renderer-System

**Neue Komponente:** `veritas_ui_widget_renderer.py`

```python
class WidgetRenderer:
    """
    Rendert strukturierte Widgets im Chat
    Erweitert MarkdownRenderer um Rich-Media-Support
    """
    
    def __init__(self, text_widget: tk.Text, parent_window: tk.Tk):
        self.text_widget = text_widget
        self.parent_window = parent_window
        self.embedded_widgets = []  # Referenzen für Cleanup
        
    def render_widget(self, widget_spec: dict) -> None:
        """Dispatcher für verschiedene Widget-Typen"""
        widget_type = widget_spec.get('type')
        
        if widget_type == 'code_block':
            self._render_code_block(widget_spec)
        elif widget_type == 'table':
            self._render_table(widget_spec)
        elif widget_type == 'image':
            self._render_image(widget_spec)
        elif widget_type == 'video':
            self._render_video(widget_spec)
        elif widget_type == 'button':
            self._render_button(widget_spec)
        elif widget_type == 'canvas':
            self._render_canvas(widget_spec)
        elif widget_type == 'chart':
            self._render_chart(widget_spec)
        # ... weitere Widget-Typen
    
    def _render_image(self, spec: dict) -> None:
        """Bindet Bild direkt im Chat ein"""
        from PIL import Image, ImageTk
        
        # Bild laden
        if 'url' in spec:
            # Von URL laden
            image = self._load_image_from_url(spec['url'])
        elif 'path' in spec:
            # Von lokalem Pfad laden
            image = Image.open(spec['path'])
        elif 'base64' in spec:
            # Von Base64 laden
            image = self._load_image_from_base64(spec['base64'])
        
        # Resize wenn nötig
        if 'width' in spec:
            image = self._resize_image(image, spec['width'])
        
        # In Tkinter-Format konvertieren
        photo = ImageTk.PhotoImage(image)
        
        # Im Text-Widget einbetten
        self.text_widget.image_create(tk.END, image=photo)
        
        # Referenz speichern (wichtig!)
        self.embedded_widgets.append(photo)
        
        # Caption hinzufügen
        if 'caption' in spec:
            self.text_widget.insert(tk.END, f"\n{spec['caption']}\n", "image_caption")
    
    def _render_button(self, spec: dict) -> None:
        """Bindet klickbaren Button im Chat ein"""
        # Button-Frame erstellen
        button = tk.Button(
            self.text_widget,
            text=spec['label'],
            command=lambda: self._handle_button_click(spec),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        
        # Button im Text-Widget einbetten
        self.text_widget.window_create(tk.END, window=button)
        self.text_widget.insert(tk.END, "\n")
        
        # Referenz speichern
        self.embedded_widgets.append(button)
    
    def _render_canvas(self, spec: dict) -> None:
        """Rendert Canvas mit Zeichnungen/Diagrammen"""
        # Canvas erstellen
        canvas = tk.Canvas(
            self.text_widget,
            width=spec.get('width', 400),
            height=spec.get('height', 300),
            bg='white',
            relief=tk.SOLID,
            borderwidth=1
        )
        
        # Zeichnungen ausführen
        for cmd in spec.get('draw_commands', []):
            if cmd['cmd'] == 'line':
                canvas.create_line(
                    cmd['x1'], cmd['y1'], cmd['x2'], cmd['y2'],
                    fill=cmd.get('color', 'black'),
                    width=cmd.get('width', 2)
                )
            elif cmd['cmd'] == 'rect':
                canvas.create_rectangle(
                    cmd['x'], cmd['y'],
                    cmd['x'] + cmd['width'], cmd['y'] + cmd['height'],
                    fill=cmd.get('fill', ''),
                    outline=cmd.get('outline', 'black')
                )
            elif cmd['cmd'] == 'text':
                canvas.create_text(
                    cmd['x'], cmd['y'],
                    text=cmd['text'],
                    font=cmd.get('font', ('Arial', 12)),
                    fill=cmd.get('color', 'black')
                )
            # ... weitere Zeichenbefehle
        
        # Canvas einbetten
        self.text_widget.window_create(tk.END, window=canvas)
        self.text_widget.insert(tk.END, "\n")
        
        # Referenz speichern
        self.embedded_widgets.append(canvas)
    
    def _render_chart(self, spec: dict) -> None:
        """Rendert Diagramm (z.B. mit matplotlib)"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        # Matplotlib-Figure erstellen
        fig, ax = plt.subplots(figsize=(6, 4))
        
        chart_type = spec.get('chart_type', 'bar')
        data = spec.get('data', {})
        
        if chart_type == 'bar':
            ax.bar(data['labels'], data['values'])
        elif chart_type == 'line':
            ax.plot(data['x'], data['y'])
        elif chart_type == 'pie':
            ax.pie(data['values'], labels=data['labels'])
        
        ax.set_title(spec.get('title', ''))
        
        # In Tkinter einbetten
        canvas = FigureCanvasTkAgg(fig, self.text_widget)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        
        self.text_widget.window_create(tk.END, window=canvas_widget)
        self.text_widget.insert(tk.END, "\n")
        
        # Referenz speichern
        self.embedded_widgets.append(canvas_widget)
        plt.close(fig)
    
    def cleanup(self) -> None:
        """Cleanup embedded widgets (wichtig für Memory-Management!)"""
        for widget in self.embedded_widgets:
            try:
                if isinstance(widget, tk.Widget):
                    widget.destroy()
            except:
                pass
        self.embedded_widgets.clear()
```

---

### Phase 3: LLM-Prompt-Template

**System-Prompt für strukturierte Ausgabe:**

```python
STRUCTURED_RESPONSE_PROMPT = """
Du bist VERITAS, ein KI-Assistent für deutsches Baurecht.

WICHTIG: Deine Antworten MÜSSEN folgendes JSON-Format haben:

{
  "type": "structured_response",
  "version": "1.0",
  "content": {
    "text": "Hauptantwort in **Markdown** mit allen Details...",
    "metadata": {
      "confidence": 0.95,
      "sources": [
        {"url": "https://...", "title": "BauGB §1"},
        {"file": "dokument.pdf", "page": 5}
      ],
      "agent": "VERITAS Legal RAG"
    },
    "suggestions": [
      "Welche Ausnahmen gibt es?",
      "Gilt das auch für Bestandsbauten?"
    ],
    "widgets": [
      // Optional: Code-Blöcke
      {
        "type": "code_block",
        "language": "python",
        "code": "...",
        "caption": "Beispiel"
      },
      // Optional: Tabellen
      {
        "type": "table",
        "headers": ["Spalte 1", "Spalte 2"],
        "rows": [["Wert 1", "Wert 2"]]
      }
    ]
  }
}

REGELN:
1. "text" enthält die HAUPTANTWORT in Markdown
2. "confidence" ist ein Wert zwischen 0.0 und 1.0
3. "sources" enthält ALLE verwendeten Quellen
4. "suggestions" enthält 2-3 Follow-up-Fragen
5. "widgets" ist OPTIONAL für Code, Tabellen, etc.

Beantworte folgende Frage:
"""
```

---

### Phase 4: Integration in Chat-Formatter

**Erweitere `ChatDisplayFormatter`:**

```python
class ChatDisplayFormatter:
    def __init__(self, ..., widget_renderer=None):
        # ... existing code ...
        self.widget_renderer = widget_renderer
    
    def _render_assistant_message(self, message: dict, ...):
        content = message.get('content', '')
        
        # Prüfe ob strukturierte Response
        if self._is_structured_response(content):
            response_data = json.loads(content)
            self._render_structured_response(response_data)
        else:
            # Fallback: Alte Markdown-Rendering
            self.markdown_renderer.render_markdown(content)
    
    def _render_structured_response(self, data: dict):
        """Rendert strukturierte LLM-Response"""
        content = data.get('content', {})
        
        # 1. Haupttext rendern
        main_text = content.get('text', '')
        self.markdown_renderer.render_markdown(main_text)
        
        # 2. Widgets rendern
        for widget_spec in content.get('widgets', []):
            self.widget_renderer.render_widget(widget_spec)
        
        # 3. Metadaten rendern
        metadata = content.get('metadata', {})
        if metadata:
            self._insert_metadata_section(metadata)
        
        # 4. Quellen rendern
        sources = metadata.get('sources', [])
        if sources:
            self._insert_sources(sources)
        
        # 5. Vorschläge rendern
        suggestions = content.get('suggestions', [])
        if suggestions:
            self._insert_suggestions(suggestions)
```

---

## 📊 Widget-Typen (Vollständige Liste)

### 1. **Text-basiert** (bereits vorhanden ✅)
- Markdown
- Code-Blöcke mit Syntax-Highlighting
- Tabellen

### 2. **Media** (neu ⭐)
- **Images** (PNG, JPG, GIF)
  - Von URL, lokalem Pfad, oder Base64
  - Auto-Resize
  - Caption-Support
- **Videos** (MP4, WebM) ⚠️ Eingeschränkt in Tkinter
  - Thumbnail + Externe Player-Link
  - Oder: Embedded mit `tkintervideo`

### 3. **Interactive Widgets** (neu ⭐)
- **Buttons**
  - Custom Actions
  - Payload-Support
  - Styled (Farben, Icons)
- **Links** (bereits vorhanden ✅)
- **Checkboxes**
- **Radio Buttons**
- **Sliders**
- **Dropdown-Menüs**

### 4. **Visualisierungen** (neu ⭐)
- **Canvas-Zeichnungen**
  - Linien, Rechtecke, Kreise, Text
  - Custom Draw-Commands
- **Charts/Diagramme** (matplotlib)
  - Bar Charts
  - Line Charts
  - Pie Charts
  - Scatter Plots
- **Mindmaps** (GraphViz oder Custom)
- **Timelines**

### 5. **Custom Widgets** (neu ⭐)
- **Collapsible Sections** (bereits vorhanden ✅)
- **Tabs**
- **Accordions**
- **Progress Bars**
- **Rating Stars**

---

## 🚀 Implementierungs-Roadmap

### **Phase 1: Foundation** (1-2 Tage)
- [x] ✅ Recherche bestehender VERITAS-Features (DONE)
- [ ] JSON Schema definieren
- [ ] `WidgetRenderer` Basisklasse erstellen
- [ ] Response-Parser implementieren

### **Phase 2: Basic Widgets** (2-3 Tage)
- [ ] Image-Rendering (PIL/Pillow)
- [ ] Button-Rendering
- [ ] Canvas-Rendering
- [ ] Chart-Rendering (matplotlib)

### **Phase 3: LLM Integration** (1-2 Tage)
- [ ] Structured Response Prompt
- [ ] Backend API-Änderungen
- [ ] Frontend Parser-Integration
- [ ] Fallback für alte Responses

### **Phase 4: Advanced Features** (2-3 Tage)
- [ ] Video-Support (Thumbnails + Links)
- [ ] Interactive Widgets (Sliders, Dropdowns)
- [ ] Custom Widget Templates
- [ ] Widget-Galerie (Dokumentation)

### **Phase 5: Testing & Optimization** (1-2 Tage)
- [ ] Memory-Management (Cleanup)
- [ ] Performance-Tests
- [ ] Error-Handling
- [ ] Dokumentation

**Total Estimate:** 7-12 Tage

---

## 💡 Beispiel-Use-Cases

### Use-Case 1: Rechtliche Frage mit Tabelle

**User:** "Welche Abstände gelten für Windkraftanlagen?"

**LLM Response:**
```json
{
  "content": {
    "text": "Gemäß **TA Lärm** gelten folgende Mindestabstände für Windkraftanlagen:",
    "widgets": [
      {
        "type": "table",
        "headers": ["Gebietstyp", "Mindestabstand", "Grenzwert Tag", "Grenzwert Nacht"],
        "rows": [
          ["Wohngebiet", "500m", "55 dB(A)", "40 dB(A)"],
          ["Mischgebiet", "300m", "60 dB(A)", "45 dB(A)"],
          ["Gewerbegebiet", "150m", "65 dB(A)", "50 dB(A)"]
        ]
      }
    ],
    "sources": [
      {"url": "https://...", "title": "TA Lärm §6"}
    ],
    "suggestions": [
      "Gibt es Ausnahmen für Bestandsanlagen?",
      "Wie werden die Abstände gemessen?"
    ]
  }
}
```

**Rendering:**
- Markdown-Text
- Schöne formatierte Tabelle (mit Rahmen)
- Klickbare Quellen
- Klickbare Vorschläge

---

### Use-Case 2: Code-Beispiel mit Diagramm

**User:** "Zeige mir wie ich BImSchG-Daten analysiere"

**LLM Response:**
```json
{
  "content": {
    "text": "Hier ist ein Python-Beispiel für BImSchG-Datenanalyse:",
    "widgets": [
      {
        "type": "code_block",
        "language": "python",
        "code": "import pandas as pd\n\ndf = pd.read_csv('bimschg_data.csv')\nprint(df.head())",
        "caption": "Daten einlesen"
      },
      {
        "type": "chart",
        "chart_type": "bar",
        "title": "Genehmigungen pro Jahr",
        "data": {
          "labels": ["2020", "2021", "2022", "2023"],
          "values": [150, 180, 220, 195]
        }
      }
    ]
  }
}
```

**Rendering:**
- Code-Block mit Syntax-Highlighting + Copy-Button
- Bar-Chart (matplotlib embedded)

---

### Use-Case 3: Interaktive Visualisierung

**User:** "Zeige mir die Lärmausbreitung"

**LLM Response:**
```json
{
  "content": {
    "text": "Hier ist eine schematische Darstellung der Lärmausbreitung:",
    "widgets": [
      {
        "type": "canvas",
        "width": 500,
        "height": 300,
        "draw_commands": [
          {"cmd": "rect", "x": 50, "y": 100, "width": 30, "height": 80, "fill": "gray", "outline": "black"},
          {"cmd": "text", "x": 65, "y": 140, "text": "Anlage", "font": ["Arial", 10]},
          {"cmd": "line", "x1": 80, "y1": 140, "x2": 200, "y2": 140, "color": "red", "width": 2},
          {"cmd": "text", "x": 140, "y": 130, "text": "55 dB(A)", "font": ["Arial", 10], "color": "red"},
          {"cmd": "line", "x1": 80, "y1": 140, "x2": 350, "y2": 140, "color": "orange", "width": 2},
          {"cmd": "text", "x": 230, "y": 130, "text": "45 dB(A)", "font": ["Arial", 10], "color": "orange"}
        ]
      },
      {
        "type": "button",
        "label": "Detaillierte Berechnung anzeigen",
        "action": "show_calculation",
        "payload": {"calc_id": "noise_calc_123"}
      }
    ]
  }
}
```

**Rendering:**
- Canvas mit Lärmausbreitungs-Diagramm
- Klickbarer Button für Details

---

## 🔧 Technische Details

### Dependencies

**Neue Dependencies:**
```python
# requirements.txt
Pillow>=10.0.0          # Image-Rendering
matplotlib>=3.7.0       # Charts/Diagramme
# Optional:
tkintervideo>=1.0.0    # Video-Support (experimental)
```

### Memory-Management

**Wichtig:** Embedded Widgets müssen sauber aufgeräumt werden!

```python
def clear_chat_display(self):
    """Cleanup vor dem Löschen"""
    # 1. Widget-Renderer cleanup
    if hasattr(self, 'widget_renderer'):
        self.widget_renderer.cleanup()
    
    # 2. Text löschen
    self.chat_text.delete('1.0', tk.END)
```

### Performance

**Optimierungen:**
- Images lazy-loaden (erst bei Sichtbarkeit)
- Charts cachen (nicht bei jedem Render neu zeichnen)
- Canvas-Objekte wiederverwenden
- Max Widget-Count pro Message (z.B. 10)

---

## 📚 Moderne Referenz-Systeme

### 1. **Discord** (Electron + React)
- Rich Embeds (Images, Videos, Links)
- Code-Blöcke mit Syntax-Highlighting
- Interactive Buttons
- **Limitation:** Web-basiert (nicht Tkinter)

### 2. **Telegram Desktop** (Qt/C++)
- Inline Bots mit Custom UIs
- Media-Rich Messages
- Buttons & Inline Keyboards
- **Lesson:** Qt hat besseres Widget-System als Tkinter

### 3. **VS Code Chat** (Electron)
- Code-Blöcke mit Actions
- Collapsible Sections
- File References
- **Lesson:** Markdown + Custom Widgets Mix

### 4. **Jupyter Notebooks** (Web)
- Rich Output (HTML, Images, Charts, Interactive Widgets)
- Matplotlib-Integration
- **Lesson:** Best Practice für Chart-Embedding

### 5. **Python Tkinter Chat Examples** (GitHub)
**Gefundene Projekte:**
- `tkinter-chat` (basic text only)
- `tkinter-messaging-app` (basic UI)
- **Finding:** Keine mit Rich-Media-Support wie gewünscht!

**Conclusion:** Wir entwickeln ein **eigenes System**, da es kein passendes Tkinter-Vorbild gibt!

---

## ✅ Empfehlung & Implementierungs-Strategie

**Beste Strategie (AKTUALISIERT mit Streaming/Templates):**

1. **Nutze bestehende VERITAS-Features** ✅
   - MarkdownRenderer (1,000 LOC)
   - ChatDisplayFormatter (2,100 LOC)
   - **StreamingService** ⚡ (639 LOC - BEREITS VORHANDEN!)
   
2. **Erweitere mit WidgetRenderer** (neue Komponente ~500 LOC)
   - Image/Video Support (PIL/Pillow)
   - Canvas-Widgets (tkinter.Canvas)
   - Chart-Widgets (matplotlib)
   - **Streaming-fähig** (inkrementelles Rendering)
   
3. **Implementiere Template-System** 📋 (Backend, ~400 LOC)
   - `PromptTemplateLibrary` (5 Templates: Zuständigkeit, Formell, Rechtlich, Sachlich, Vollständig)
   - Auto-Selection via Keyword-Matching
   - Template-spezifische System-Prompts
   
4. **Implementiere Adaptive Token-Manager** 📏 (~200 LOC)
   - Dynamische Token-Size basierend auf:
     - Frage-Komplexität (NLP-Analyse)
     - Template-Requirements
     - RAG-Kontext-Größe
     - Follow-up Detection
   
5. **Erweitere Streaming für Structured Response** ⚡ (~300 LOC)
   - `StreamingStructuredResponseParser`
   - Newline-Delimited JSON (NDJSON)
   - Inkrementelles Widget-Rendering

**Warum kein externes System?**
- ✅ VERITAS hat bereits 80% der Basis (inkl. Streaming!)
- ✅ Tkinter-Native (keine Web-Tech nötig)
- ✅ Volle Kontrolle über Rendering
- ✅ Bessere Performance
- ✅ Template-System ermöglicht verwaltungsrechtliche Spezialisierung
- ❌ Keine passenden Tkinter-Bibliotheken gefunden

---

## 🚀 Implementierungs-Roadmap (AKTUALISIERT)

### **Phase 1: Foundation + Streaming** (2-3 Tage)
- [x] ✅ Recherche bestehender VERITAS-Features (DONE)
- [ ] JSON Schema definieren (Streaming-fähig, NDJSON)
- [ ] `StreamingStructuredResponseParser` erstellen
- [ ] `WidgetRenderer` Basisklasse (mit incremental rendering)
- [ ] Response-Parser für Streaming-Chunks

### **Phase 2: Backend Template-System** (2-3 Tage)
- [ ] `PromptTemplateLibrary` erstellen (5 Templates)
- [ ] `AdaptiveTokenManager` implementieren
- [ ] Backend API Endpoint `/api/v1/chat/structured`
- [ ] Template Auto-Selection (Keyword-Matching)
- [ ] Ollama-Integration (dynamische Tokens + Streaming)

### **Phase 3: Basic Widgets (Streaming-fähig)** (2-3 Tage)
- [ ] Image-Rendering (PIL/Pillow, incremental)
- [ ] Button-Rendering (incremental)
- [ ] Canvas-Rendering (incremental)
- [ ] Chart-Rendering (matplotlib, incremental)
- [ ] Table-Rendering (bereits vorhanden, aber streaming-update nötig)

### **Phase 4: Frontend Integration** (1-2 Tage)
- [ ] Erweitere `ChatDisplayFormatter` für Streaming Structured Response
- [ ] Integration mit bestehendem `StreamingUIMixin`
- [ ] Progress-Updates während Widget-Rendering
- [ ] Error-Handling (unvollständige JSON-Chunks)

### **Phase 5: Advanced Features** (2-3 Tage)
- [ ] Video-Support (Thumbnails + Links)
- [ ] Interactive Widgets (Sliders, Dropdowns)
- [ ] Custom Widget Templates
- [ ] Widget-Galerie (Dokumentation)
- [ ] Template-Auswahl im UI (User kann explizit Template wählen)

### **Phase 6: Testing & Optimization** (2-3 Tage)
- [ ] Memory-Management (Cleanup, Streaming-Buffers)
- [ ] Performance-Tests (Streaming-Latency, Widget-Rendering)
- [ ] Template-Tests (alle 5 Templates mit Mock-Daten)
- [ ] Error-Handling (Streaming-Abbrüche, Netzwerkfehler)
- [ ] Dokumentation (Templates, Widget-Specs, Streaming-Format)

**Total Estimate:** 11-17 Tage (vorher 7-12 Tage, jetzt mit Streaming/Templates/Tokens)

---

## 🎯 Nächste Schritte (PRIORISIERT)

**Option 1: 🏗️ Streaming-Prototyp (EMPFOHLEN)** ⚡
→ Erstelle `StreamingStructuredResponseParser`  
→ Test-Skript für Mock-Streaming-Responses (NDJSON)  
→ Integration mit bestehendem `StreamingService`  
→ **Zeit:** 60-90 Min  
→ **Benefit:** Validiert Streaming-Architektur SOFORT

**Option 2: 📋 Template-System Backend** 
→ Erstelle `PromptTemplateLibrary` (5 Templates)  
→ `AdaptiveTokenManager` implementieren  
→ Backend API Endpoint  
→ **Zeit:** 90-120 Min  
→ **Benefit:** Validiert verwaltungsrechtliche Spezialisierung

**Option 3: 🖼️ Widget-Renderer Prototyp**
→ Erstelle `WidgetRenderer` mit Image + Button Support (streaming-fähig)  
→ Test-Skript für Mock-Responses  
→ **Zeit:** 60-90 Min  
→ **Benefit:** Validiert UI-Rendering

**Option 4: 📐 JSON-Schema finalisieren**
→ Finalisiere NDJSON Streaming-Format  
→ LLM-Prompt-Templates dokumentieren  
→ **Zeit:** 30-45 Min  
→ **Benefit:** Design-Dokumentation komplett

**Option 5: 📚 Alle Specs finalisieren**
→ Komplettes Design vor Implementation  
→ Widget-Galerie dokumentieren  
→ Template-Specs detaillieren  
→ **Zeit:** 90-120 Min  
→ **Benefit:** Vollständige Spezifikation

---

## 📊 Zusammenfassung der Anforderungen

| Anforderung | Status | Implementierung | Aufwand |
|-------------|--------|-----------------|---------|
| **Strukturierte Metadaten** | ⏳ Design | JSON Schema + Parser | 1-2 Tage |
| **Rich Media (Images, Videos)** | ⏳ Design | WidgetRenderer + PIL/Pillow | 2-3 Tage |
| **Standardisiertes Format** | ⏳ Design | NDJSON Streaming Format | 1 Tag |
| **Tkinter-Rendering** | ✅ Basis vorhanden | MarkdownRenderer erweitern | 1-2 Tage |
| **Streaming Support** ⚡ | ✅ VORHANDEN | StreamingStructuredResponseParser | 1-2 Tage |
| **Dynamische Token-Size** 📏 | ⏳ Design | AdaptiveTokenManager | 1 Tag |
| **Template-System** 📋 | ⏳ Design | PromptTemplateLibrary (5 Templates) | 2-3 Tage |

**Gesamt:** 11-17 Tage Development

---

## 💡 Kritische Design-Entscheidungen

### 1. **Streaming-Format: NDJSON (Newline-Delimited JSON)**
**Warum?**
- ✅ Jede Zeile = 1 vollständiges JSON-Objekt
- ✅ Parsing möglich ohne auf Ende zu warten
- ✅ Standard-Format für Streaming-APIs
- ✅ Kompatibel mit FastAPI `StreamingResponse`

**Beispiel:**
```ndjson
{"type":"response_start","metadata":{"template":"zustaendigkeit_behoerde"}}
{"type":"text_chunk","content":"Gemäß **BauGB §35**..."}
{"type":"widget","widget":{"type":"table","headers":[...]}}
{"type":"response_end","metadata":{"confidence":0.92}}
```

---

### 2. **Template-System: Serverseitig (Backend)**
**Warum?**
- ✅ Zentrale Verwaltung (keine Duplikation Frontend/Backend)
- ✅ Einfachere Updates (nur Backend deployen)
- ✅ Sicherheit (Prompts nicht im Frontend-Code)
- ✅ Bessere Testbarkeit

**Frontend bekommt nur:**
- Template-ID im Response-Header
- Template-Name für UI-Badge ("Formale Prüfung")

---

### 3. **Dynamische Tokens: Template-basiert + Complexity-Analysis**
**Warum?**
- ✅ Template gibt Basis-Tokens vor (z.B. "Vollständige Prüfung" = 16384)
- ✅ Complexity-Analysis passt an (einfache Frage → 50% Reduktion)
- ✅ RAG-Kontext wird einberechnet
- ✅ Follow-ups bekommen 30% Reduktion (Context-Reuse)

**Resultat:** Optimal zwischen Performance (kleine Tokens) und Qualität (große Tokens für komplexe Themen)

---

### 4. **Widget-Rendering: Incremental während Streaming**
**Warum?**
- ✅ Besseres UX (User sieht sofort was passiert)
- ✅ Keine "Freezing" während LLM generiert
- ✅ Widgets erscheinen "on-demand" wenn im Text erwähnt

**Herausforderung:**
- ⚠️ Widgets müssen **vor** finaler Markdown-Verarbeitung bekannt sein
- ⚠️ LLM muss Widgets **explizit ankündigen** via JSON-Chunk

**Lösung:**
```ndjson
{"type":"text_chunk","content":"Die Zuständigkeiten sind in folgender Tabelle:"}
{"type":"widget","widget":{"type":"table",...}}  ← Widget-Chunk BEVOR Referenz
{"type":"text_chunk","content":"Wie Sie sehen können..."}
```

---

## 🎉 Was macht dieses System BESONDERS?

1. **Streaming-Aware Structured Responses** ⚡
   - Kein Warten auf komplette Response
   - Widgets erscheinen während LLM generiert
   - Progress-Updates für jeden Widget-Typ

2. **Verwaltungsrechtliche Spezialisierung** 📋
   - 5 spezialisierte Templates (Zuständigkeit, Formell, Rechtlich, Sachlich, Vollständig)
   - Automatische Template-Selection via NLP
   - Template-spezifische Token-Limits

3. **Adaptive Context-Fenster** 📏
   - Keine festen 4096 Tokens mehr
   - Dynamisch 1024-16384 basierend auf Komplexität
   - Bis zu 70% Token-Einsparung bei einfachen Fragen
   - Bis zu 300% mehr Tokens bei komplexen Analysen

4. **Tkinter-Native Rich Media** 🎨
   - Images, Videos, Canvas, Charts DIREKT im Chat
   - Keine Browser-Dependency
   - Memory-effizientes Cleanup

5. **Production-Ready von Anfang an** ✅
   - Basiert auf bestehendem Streaming-System
   - Thread-Safe (ThreadManager-Integration)
   - Error-Handling für Streaming-Abbrüche
   - Graceful Degradation (Fallback auf Plain-Text)

---

**Möchtest du, dass ich mit der Implementation beginne?** 🚀

**Meine Empfehlung:**  
**Option 1: Streaming-Prototyp** (60-90 Min)  
→ Validiert Architektur SOFORT  
→ Kann HEUTE getestet werden  
→ Zeigt ob Streaming + Structured Response kompatibel sind

**Alternative:**  
**Option 2: Template-System** (90-120 Min)  
→ Validiert verwaltungsrechtliche Spezialisierung  
→ Kann sofort mit bestehendem Backend getestet werden

**Lass mich wissen, welche Option du bevorzugst!** 😊

---

**END OF KONZEPTPLAN (v4.1.0)**

