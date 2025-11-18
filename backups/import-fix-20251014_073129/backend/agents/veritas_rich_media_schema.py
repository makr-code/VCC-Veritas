"""
Rich Media JSON Schema für VERITAS Antworten
=============================================

Erweitert das JSON-Schema um Rich Media Support:
- 🖼️ Images (URLs, Base64, Captions)
- 🗺️ Maps (GeoJSON, Marker, Bounds)
- 📊 Charts (Plotly JSON, Chart.js config)
- 🎥 Videos (YouTube, Vimeo, Local)
- 📄 Documents (PDFs, Downloads)
- 📋 Tables (Structured Data)
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

# ============================================================================
# RICH MEDIA TYPES
# ============================================================================


@dataclass
class ImageMedia:
    """Image embedding"""

    url: str
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    source: Optional[str] = None  # Citation source


@dataclass
class GeoMapMedia:
    """Geographic map with markers"""

    center: tuple[float, float]  # (lat, lon)
    zoom: int = 12
    markers: List[Dict[str, Any]] = None  # [{"lat": 52.5, "lon": 13.4, "label": "Berlin"}]
    geojson: Optional[Dict] = None  # Full GeoJSON object
    bounds: Optional[List[List[float]]] = None  # [[lat_min, lon_min], [lat_max, lon_max]]


@dataclass
class ChartMedia:
    """Data visualization chart"""

    chart_type: Literal["bar", "line", "pie", "scatter", "heatmap"]
    data: Dict[str, Any]  # Chart.js or Plotly JSON format
    title: Optional[str] = None
    description: Optional[str] = None


@dataclass
class VideoMedia:
    """Video embedding"""

    url: str
    platform: Literal["youtube", "vimeo", "local"]
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None  # seconds


@dataclass
class DocumentMedia:
    """Document download/preview"""

    url: str
    filename: str
    file_type: Literal["pdf", "docx", "xlsx", "txt", "csv"]
    size: Optional[int] = None  # bytes
    description: Optional[str] = None


@dataclass
class TableMedia:
    """Structured data table"""

    headers: List[str]
    rows: List[List[Any]]
    caption: Optional[str] = None
    footer: Optional[str] = None


# ============================================================================
# ENHANCED JSON SCHEMA
# ============================================================================

RICH_MEDIA_SCHEMA = {
    "type": "object",
    "required": ["direct_answer", "details", "citations", "sources"],
    "properties": {
        "direct_answer": {"type": "string", "description": "Kurze, direkte Antwort (2-3 Sätze)"},
        "details": {"type": "array", "items": {"type": "string"}, "description": "Detail-Punkte mit Fakten"},
        "citations": {
            "type": "array",
            "items": {"type": "object", "properties": {"text": {"type": "string"}, "source_id": {"type": "integer"}}},
            "description": "Text-Fragment → Quellen-ID Zuordnung",
        },
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Verwendete Quellen (nummeriert)"},
        # Rich Media Extensions
        "images": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "caption": {"type": "string"},
                    "alt_text": {"type": "string"},
                    "source_id": {"type": "integer"},
                },
            },
            "description": "🖼️ Eingebettete Bilder",
        },
        "maps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "center": {"type": "array", "items": {"type": "number"}},
                    "zoom": {"type": "integer"},
                    "markers": {"type": "array"},
                    "geojson": {"type": "object"},
                },
            },
            "description": "🗺️ Geografische Karten",
        },
        "charts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "chart_type": {"type": "string", "enum": ["bar", "line", "pie", "scatter"]},
                    "data": {"type": "object"},
                    "title": {"type": "string"},
                },
            },
            "description": "📊 Datenvisualisierungen",
        },
        "videos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "platform": {"type": "string", "enum": ["youtube", "vimeo", "local"]},
                    "title": {"type": "string"},
                },
            },
            "description": "🎥 Video-Einbettungen",
        },
        "documents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"url": {"type": "string"}, "filename": {"type": "string"}, "file_type": {"type": "string"}},
            },
            "description": "📄 Dokumente zum Download",
        },
        "tables": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headers": {"type": "array", "items": {"type": "string"}},
                    "rows": {"type": "array"},
                    "caption": {"type": "string"},
                },
            },
            "description": "📋 Strukturierte Tabellen",
        },
        "next_steps": {"type": "string", "description": "Was sollte User als nächstes tun?"},
        "follow_ups": {"type": "array", "items": {"type": "string"}, "description": "3-5 Follow-up Fragen"},
    },
}


# ============================================================================
# RICH MEDIA PROMPT TEMPLATES
# ============================================================================


def get_rich_media_prompt() -> Dict[str, str]:
    """
    Returns enhanced JSON prompt with Rich Media support
    """
    return {
        "system": """Du bist ein intelligenter Assistent für Verwaltungsfragen mit Rich Media Support.

AUSGABEFORMAT: **NUR VALID JSON** (kein zusätzlicher Text!)

Deine Antwort MUSS diesem JSON-Schema folgen:

{
  "direct_answer": "Kurze direkte Antwort (2-3 Sätze)",
  "details": ["Detail 1", "Detail 2", "Detail 3"],
  "citations": [
    {"text": "Zu zitierender Fakt", "source_id": 1}
  ],
  "sources": ["Quelle 1", "Quelle 2"],

  // OPTIONAL: Rich Media
  "images": [
    {
      "url": "https://example.com/image.jpg",
      "caption": "Beschreibung",
      "alt_text": "Alt-Text",
      "source_id": 1
    }
  ],
  "maps": [
    {
      "center": [52.5200, 13.4050],
      "zoom": 12,
      "markers": [
        {"lat": 52.5200, "lon": 13.4050, "label": "Berlin", "popup": "Hauptstadt"}
      ]
    }
  ],
  "charts": [
    {
      "chart_type": "bar",
      "data": {
        "labels": ["Jan", "Feb", "Mär"],
        "datasets": [{
          "label": "Bauanträge",
          "data": [12, 19, 15]
        }]
      },
      "title": "Bauanträge 2024"
    }
  ],
  "tables": [
    {
      "headers": ["Kommune", "Gebühr", "Bearbeitungszeit"],
      "rows": [
        ["Berlin", "250€", "6 Wochen"],
        ["München", "300€", "8 Wochen"]
      ],
      "caption": "Vergleich Baugenehmigungsgebühren"
    }
  ],
  "videos": [...],  // Optional
  "documents": [...],  // Optional

  "next_steps": "Was sollte User als nächstes tun?",
  "follow_ups": ["Frage 1?", "Frage 2?", "Frage 3?"]
}

WICHTIG:
- JEDER Fakt muss in "citations" referenziert werden
- Rich Media NUR wenn sinnvoll (nicht erzwingen!)
- Antworte NUR mit valid JSON (keine Erklärungen davor/danach!)

WANN Rich Media nutzen:
🖼️ Images: Bei Gebäuden, Plänen, Formularen
🗺️ Maps: Bei Standorten, Zuständigkeitsgebieten, Verkehrsfragen
📊 Charts: Bei Statistiken, Vergleichen, Trends
📋 Tables: Bei Gebühren-Vergleichen, Fristen-Übersichten
🎥 Videos: Bei Tutorials, Erklärvideos
📄 Documents: Bei Formularen, Merkblättern, PDFs
""",
        "user_template": """**User fragte:** {query}

**Verfügbare Quellen:**
{source_list}

**Kontext aus Dokumenten:**
{rag_context}

**Agent-Erkenntnisse:**
{agent_results}

**BEISPIEL 1 (Baukosten mit Tabelle):**

Frage: "Welche Kosten entstehen bei einer Baugenehmigung?"

{{
  "direct_answer": "Die Kosten für eine Baugenehmigung variieren je nach Kommune und liegen zwischen 150€ und 500€ Grundgebühr plus 0,5% der Bausumme.",
  "details": [
    "Grundgebühr richtet sich nach Gemeinde und Bauvorhaben",
    "Größenabhängige Gebühr beträgt 0,5% der Bausumme",
    "Zusätzliche Prüfungsgebühren für Statik: 200-800€",
    "Beispiel: Einfamilienhaus (300.000€) = ca. 1.800€ Gesamtkosten"
  ],
  "citations": [
    {{"text": "Grundgebühr richtet sich nach Gemeinde", "source_id": 1}},
    {{"text": "0,5% der Bausumme", "source_id": 1}},
    {{"text": "Prüfungsgebühren für Statik: 200-800€", "source_id": 2}}
  ],
  "sources": [
    "Gebührenordnung BauO BW",
    "Kostenrechner Stadt Stuttgart"
  ],
  "tables": [
    {{
      "headers": ["Kommune", "Grundgebühr", "Größengebühr", "Beispiel (300k€)"],
      "rows": [
        ["Berlin", "250€", "0.5%", "1.750€"],
        ["München", "350€", "0.5%", "1.850€"],
        ["Stuttgart", "200€", "0.5%", "1.700€"]
      ],
      "caption": "Vergleich Baugenehmigungskosten (Stand 2024)"
    }}
  ],
  "next_steps": "Kontaktieren Sie Ihr zuständiges Bauordnungsamt für eine genaue Kostenschätzung.",
  "follow_ups": [
    "Wann werden die Gebühren fällig?",
    "Kann ich die Kosten steuerlich absetzen?",
    "Gibt es Ermäßigungen für Sanierungen?"
  ]
}}

**BEISPIEL 2 (Luftqualität mit Karte + Chart):**

Frage: "Wie ist die Luftqualität in Berlin?"

{{
  "direct_answer": "Die Luftqualität in Berlin ist aktuell gut. Die Messwerte liegen unter den EU-Grenzwerten.",
  "details": [
    "Feinstaub (PM10): 18 μg/m³ (Grenzwert: 40 μg/m³)",
    "Stickstoffdioxid (NO₂): 22 μg/m³ (Grenzwert: 40 μg/m³)",
    "Ozon (O₃): 45 μg/m³ (Zielwert: 120 μg/m³)",
    "Messungen vom Berliner Luftgütemessnetz"
  ],
  "citations": [
    {{"text": "Feinstaub (PM10): 18 μg/m³", "source_id": 1}},
    {{"text": "Stickstoffdioxid (NO₂): 22 μg/m³", "source_id": 1}},
    {{"text": "EU-Grenzwerte", "source_id": 2}}
  ],
  "sources": [
    "Berliner Luftgütemessnetz - Messdaten 10.10.2024",
    "EU-Luftqualitätsrichtlinie 2008/50/EG"
  ],
  "maps": [
    {{
      "center": [52.5200, 13.4050],
      "zoom": 11,
      "markers": [
        {{"lat": 52.5200, "lon": 13.4050, "label": "Alexanderplatz", "popup": "PM10: 18 μg/m³"}},
        {{"lat": 52.5065, "lon": 13.2846, "label": "Charlottenburg", "popup": "PM10: 15 μg/m³"}},
        {{"lat": 52.4545, "lon": 13.5265, "label": "Neukölln", "popup": "PM10: 22 μg/m³"}}
      ]
    }}
  ],
  "charts": [
    {{
      "chart_type": "bar",
      "data": {{
        "labels": ["PM10", "NO₂", "O₃"],
        "datasets": [
          {{
            "label": "Aktuell (μg/m³)",
            "data": [18, 22, 45],
            "backgroundColor": "rgba(75, 192, 192, 0.6)"
          }},
          {{
            "label": "Grenzwert (μg/m³)",
            "data": [40, 40, 120],
            "backgroundColor": "rgba(255, 99, 132, 0.6)"
          }}
        ]
      }},
      "title": "Luftqualität Berlin - Vergleich mit Grenzwerten"
    }}
  ],
  "follow_ups": [
    "Welche Messstationen gibt es in meiner Nähe?",
    "Wie hat sich die Luftqualität in den letzten Jahren entwickelt?",
    "Was kann ich persönlich für bessere Luft tun?"
  ]
}}

**BEISPIEL 3 (Bauantrag mit Image + Document):**

Frage: "Welche Unterlagen brauche ich für einen Bauantrag?"

{{
  "direct_answer": "Für einen Bauantrag benötigen Sie das amtliche Formular, Bauzeichnungen, Lageplan und statische Berechnungen.",
  "details": [
    "Amtlicher Bauantrag (Formular Ihrer Kommune)",
    "Lageplan mit Grundstücksgrenzen (M 1:500)",
    "Bauzeichnungen (Grundrisse, Schnitte, Ansichten)",
    "Statische Berechnungen von qualifiziertem Ingenieur",
    "Baubeschreibung mit Materialangaben"
  ],
  "citations": [
    {{"text": "Amtlicher Bauantrag", "source_id": 1}},
    {{"text": "Lageplan mit Grundstücksgrenzen", "source_id": 1}},
    {{"text": "Statische Berechnungen von qualifiziertem Ingenieur", "source_id": 2}}
  ],
  "sources": [
    "Bauordnungsamt Brandenburg - Checkliste Bauantrag",
    "LBO BW § 58 - Erforderliche Unterlagen"
  ],
  "images": [
    {{
      "url": "/media/bauantrag_beispiel_grundriss.png",
      "caption": "Beispiel: Grundriss für Bauantrag (Einfamilienhaus)",
      "alt_text": "Technische Zeichnung Grundriss Erdgeschoss",
      "source_id": 1
    }}
  ],
  "documents": [
    {{
      "url": "/downloads/bauantrag_formular_brandenburg.pdf",
      "filename": "Bauantrag-Formular-Brandenburg.pdf",
      "file_type": "pdf",
      "size": 245000,
      "description": "Amtliches Bauantragsformular Brandenburg (Stand 2024)"
    }},
    {{
      "url": "/downloads/checkliste_bauunterlagen.pdf",
      "filename": "Checkliste-Bauunterlagen.pdf",
      "file_type": "pdf",
      "description": "Vollständige Checkliste aller erforderlichen Unterlagen"
    }}
  ],
  "next_steps": "Laden Sie die Formulare herunter und wenden Sie sich für Beratung an Ihr zuständiges Bauordnungsamt.",
  "follow_ups": [
    "Wie lange dauert die Bearbeitung meines Bauantrags?",
    "Was kostet die Baugenehmigung?",
    "Kann ich den Bauantrag digital einreichen?"
  ]
}}

**Jetzt beantworte die User-Frage im GLEICHEN JSON-FORMAT (mit Rich Media wenn sinnvoll!):**
""",
    }


# ============================================================================
# FRONTEND RENDERER (Conceptual)
# ============================================================================


def render_rich_media_response(json_response: Dict[str, Any]) -> str:
    """
    Conceptual: Wie Frontend Rich Media rendern würde

    Returns:
        HTML/Markdown string with embedded rich media
    """
    output = []

    # Direct Answer
    output.append(f"**Direkte Antwort:**\n{json_response['direct_answer']}\n")

    # Details
    if json_response.get("details"):
        output.append("**Details:**\n")
        for detail in json_response["details"]:
            output.append(f"• {detail}")
        output.append("")

    # Images
    if json_response.get("images"):
        output.append("**📸 Bilder:**\n")
        for img in json_response["images"]:
            output.append(f"![{img.get('alt_text', 'Image')}]({img['url']})")
            if img.get("caption"):
                output.append(f"*{img['caption']}*")
        output.append("")

    # Maps
    if json_response.get("maps"):
        output.append("**🗺️ Karte:**\n")
        for map_data in json_response["maps"]:
            output.append(f"<div class='map' data-center='{map_data['center']}' data-zoom='{map_data['zoom']}'></div>")
        output.append("")

    # Charts
    if json_response.get("charts"):
        output.append("**📊 Diagramme:**\n")
        for chart in json_response["charts"]:
            output.append(
                f"<canvas id='chart-{chart.get('title', 'data')}' data-config='{json.dumps(chart['data'])}'></canvas>"
            )
        output.append("")

    # Tables
    if json_response.get("tables"):
        for table in json_response["tables"]:
            if table.get("caption"):
                output.append(f"**{table['caption']}**\n")

            # Markdown table
            output.append("| " + " | ".join(table["headers"]) + " |")
            output.append("| " + " | ".join(["---"] * len(table["headers"])) + " |")
            for row in table["rows"]:
                output.append("| " + " | ".join(str(cell) for cell in row) + " |")
            output.append("")

    # Sources
    if json_response.get("sources"):
        output.append("**Quellen:**")
        for i, source in enumerate(json_response["sources"], 1):
            output.append(f"[{i}] {source}")
        output.append("")

    # Follow-ups
    if json_response.get("follow_ups"):
        output.append("**💡 Vorschläge:**")
        for q in json_response["follow_ups"]:
            output.append(f"• {q}")

    return "\n".join(output)


if __name__ == "__main__":
    print("=" * 80)
    print("🎨 RICH MEDIA JSON SCHEMA")
    print("=" * 80)
    print("\nSchema Preview:")
    print(json.dumps(RICH_MEDIA_SCHEMA, indent=2))

    print("\n" + "=" * 80)
    print("📋 Supported Media Types:")
    print("=" * 80)
    print("🖼️  Images - URLs, Captions, Alt-Text")
    print("🗺️  Maps - GeoJSON, Markers, Interactive")
    print("📊 Charts - Bar, Line, Pie, Scatter")
    print("📋 Tables - Structured Data with Headers")
    print("🎥 Videos - YouTube, Vimeo, Local")
    print("📄 Documents - PDFs, Downloads, Previews")
