"""
JSON Citation Formatter
=======================

Strategie: LLM generiert strukturiertes JSON, wir formatieren zu IEEE-Standard.

Flow:
1. LLM Output: {"answer": "...", "citations": [...], "sources": [...]}
2. Post-Process: Füge [1],[2],[3] ein
3. Final Output: IEEE-formatierte Antwort
"""

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Einzelne Zitation"""

    text: str  # Der zu zitierende Text-Abschnitt
    source_id: int  # Welche Quelle (1-basiert)


@dataclass
class StructuredAnswer:
    """Strukturierte Antwort vom LLM"""

    direct_answer: str  # Kurze direkte Antwort
    details: List[str]  # Detail-Punkte
    citations: List[Citation]  # Zitationen
    sources: List[str]  # Quellen-Liste
    next_steps: str = ""  # Optional
    follow_ups: List[str] = None  # Optional


class JSONCitationFormatter:
    """
    Formatiert LLM JSON-Output zu IEEE-Standard
    """

    JSON_SCHEMA = {
        "type": "object",
        "required": ["direct_answer", "details", "citations", "sources"],
        "properties": {
            "direct_answer": {"type": "string", "description": "Kurze, direkte Antwort (2-3 Sätze)"},
            "details": {"type": "array", "items": {"type": "string"}, "description": "Liste von Detail-Punkten"},
            "citations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Zu zitierender Text"},
                        "source_id": {"type": "integer", "description": "Quellen-ID (1-basiert)"},
                    },
                },
                "description": "Zitationen mit Zuordnung zu Quellen",
            },
            "sources": {"type": "array", "items": {"type": "string"}, "description": "Verwendete Quellen (in Reihenfolge)"},
            "next_steps": {"type": "string", "description": "Optional: Nächste Schritte"},
            "follow_ups": {"type": "array", "items": {"type": "string"}, "description": "Optional: 3-5 Follow-up Fragen"},
        },
    }

    @staticmethod
    def get_json_prompt_template(enable_rich_media: bool = False) -> Dict[str, str]:
        """
        Returns prompt template for JSON-structured output

        Args:
            enable_rich_media: If True, includes rich media support (maps, charts, images)
        """
        if enable_rich_media:
            # Import rich media prompts
            try:
                from backend.agents.veritas_rich_media_schema import get_rich_media_prompt

                return get_rich_media_prompt()
            except ImportError:
                logger.warning("Rich media schema not available, falling back to basic JSON")

        return {
            "system": """Du bist ein hilfreicher Assistent für Verwaltungsfragen.

AUSGABEFORMAT: **NUR VALID JSON** (kein zusätzlicher Text!)

Deine Antwort MUSS diesem JSON-Schema folgen:

{
  "direct_answer": "Kurze direkte Antwort (2-3 Sätze)",
  "details": [
    "Detail-Punkt 1",
    "Detail-Punkt 2",
    "Detail-Punkt 3"
  ],
  "citations": [
    {"text": "Zu zitierender Fakt", "source_id": 1},
    {"text": "Weiterer Fakt", "source_id": 2}
  ],
  "sources": [
    "Quelle 1 Name",
    "Quelle 2 Name"
  ],
  "next_steps": "Optional: Was sollte User als nächstes tun?",
  "follow_ups": [
    "Follow-up Frage 1?",
    "Follow-up Frage 2?",
    "Follow-up Frage 3?"
  ]
}

WICHTIG:
- JEDER Fakt in "details" sollte eine Citation in "citations" haben
- source_id referenziert Position in "sources" (1-basiert)
- Antworte NUR mit valid JSON (keine Erklärungen davor/danach!)
""",
            "user_template": """**User fragte:** {query}

**Verfügbare Quellen:**
{source_list}

**Kontext aus Dokumenten:**
{rag_context}

**Agent-Erkenntnisse:**
{agent_results}

**BEISPIEL (GOOD JSON OUTPUT):**

Frage: "Was kostet eine Baugenehmigung?"

Verfügbare Quellen:
[1] Gebührenordnung BauO BW
[2] Kostenrechner Stadt Stuttgart

Antwort:
{{
  "direct_answer": "Die Kosten für eine Baugenehmigung richten sich nach der Gebührenordnung und liegen bei ca. 0,5% der Bausumme plus Grundgebühr.",
  "details": [
    "Grundgebühr: 150-500€ je nach Gemeinde",
    "Größenabhängige Gebühr: 0,5% der Bausumme",
    "Prüfungsgebühr für Statik: 200-800€",
    "Beispiel Einfamilienhaus (200m², 300.000€): ca. 1.500-2.000€ Gesamtkosten"
  ],
  "citations": [
    {{"text": "Grundgebühr: 150-500€ je nach Gemeinde", "source_id": 1}},
    {{"text": "Größenabhängige Gebühr: 0,5% der Bausumme", "source_id": 1}},
    {{"text": "Prüfungsgebühr für Statik: 200-800€", "source_id": 1}},
    {{"text": "Beispiel Einfamilienhaus (200m², 300.000€): ca. 1.500-2.000€", "source_id": 2}}
  ],
  "sources": [
    "Gebührenordnung BauO BW",
    "Kostenrechner Stadt Stuttgart"
  ],
  "next_steps": "Kontaktieren Sie Ihr zuständiges Bauordnungsamt für eine genaue Kostenschätzung.",
  "follow_ups": [
    "Wann werden die Gebühren fällig?",
    "Kann ich die Kosten steuerlich absetzen?",
    "Gibt es Ermäßigungen für bestimmte Bauvorhaben?"
  ]
}}

**Jetzt beantworte die User-Frage im GLEICHEN JSON-FORMAT (NUR JSON, nichts anderes!):**
""",
        }

    @staticmethod
    def parse_json_response(llm_output: str) -> Dict[str, Any]:
        """
        Parst LLM JSON-Output

        Args:
            llm_output: Raw LLM output (hoffentlich JSON)

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If not valid JSON
        """
        # Try to extract JSON if LLM added text before/after
        llm_output = llm_output.strip()

        # Fix common JSON escape issues from LLMs
        # LLMs often use \_ or \  incorrectly
        llm_output = llm_output.replace("\\_", "_")  # NO\_2 → NO_2
        llm_output = llm_output.replace("\\  ", " ")  # Extra spaces

        # Find JSON object boundaries
        json_start = llm_output.find("{")
        json_end = llm_output.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in LLM output")

        json_str = llm_output[json_start:json_end]

        try:
            data = json.loads(json_str)
            logger.info(f"✅ Successfully parsed JSON ({len(json_str)} chars)")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            logger.error(f"Raw output: {llm_output[:200]}...")
            raise ValueError(f"Invalid JSON from LLM: {e}")

    @staticmethod
    def format_to_ieee(structured_data: Dict[str, Any]) -> str:
        """
        Formatiert strukturiertes JSON zu IEEE-Standard mit [N] Citations

        Args:
            structured_data: Parsed JSON from LLM

        Returns:
            IEEE-formatierte Antwort
        """
        # Build citation map: text -> source_id
        citation_map = {}
        for citation in structured_data.get("citations", []):
            text = citation.get("text", "").strip()
            source_id = citation.get("source_id", 0)
            if text and source_id > 0:
                citation_map[text] = source_id

        logger.info(f"📚 Citation Map: {len(citation_map)} citations")

        # Format output
        output = []

        # 1. Direkte Antwort
        direct_answer = structured_data.get("direct_answer", "")
        if direct_answer:
            output.append("**Direkte Antwort:**")
            # Try to add citations to direct answer
            direct_answer_cited = JSONCitationFormatter._inject_citations(direct_answer, citation_map)
            output.append(direct_answer_cited)
            output.append("")

        # 2. Details mit Citations
        details = structured_data.get("details", [])
        if details:
            output.append("**Details:**")
            output.append("")
            for detail in details:
                # Inject citations
                detail_cited = JSONCitationFormatter._inject_citations(detail, citation_map)
                output.append(f"• {detail_cited}")
            output.append("")

        # 3. Quellen
        sources = structured_data.get("sources", [])
        if sources:
            output.append("**Quellen:**")
            for i, source in enumerate(sources, 1):
                output.append(f"[{i}] {source}")
            output.append("")

        # 4. Nächste Schritte (optional)
        next_steps = structured_data.get("next_steps", "")
        if next_steps:
            output.append("**Nächste Schritte:**")
            output.append(next_steps)
            output.append("")

        # 5. Follow-ups (optional)
        follow_ups = structured_data.get("follow_ups", [])
        if follow_ups:
            output.append("**💡 Vorschläge:**")
            for question in follow_ups:
                output.append(f"• {question}")

        # 6. Rich Media (optional)
        # Images
        images = structured_data.get("images", [])
        if images:
            output.append("")
            output.append("**📸 Bilder:**")
            for img in images:
                url = img.get("url", "")
                caption = img.get("caption", "")
                alt_text = img.get("alt_text", "Bild")
                source_id = img.get("source_id")

                img_tag = f"![{alt_text}]({url})"
                if source_id:
                    img_tag += f"[{source_id}]"
                output.append(img_tag)

                if caption:
                    output.append(f"*{caption}*")

        # Maps
        maps = structured_data.get("maps", [])
        if maps:
            output.append("")
            output.append("**🗺️ Karte:**")
            for map_data in maps:
                center = map_data.get("center", [0, 0])
                zoom = map_data.get("zoom", 12)
                markers = map_data.get("markers", [])

                output.append(f"<!-- MAP: center={center}, zoom={zoom} -->")
                output.append(f"Zentrum: {center[0]:.4f}, {center[1]:.4f} (Zoom: {zoom})")

                if markers:
                    output.append("Marker:")
                    for marker in markers:
                        label = marker.get("label", "Punkt")
                        popup = marker.get("popup", "")
                        lat = marker.get("lat", 0)
                        lon = marker.get("lon", 0)
                        output.append(f"  • {label} ({lat:.4f}, {lon:.4f}): {popup}")

        # Charts
        charts = structured_data.get("charts", [])
        if charts:
            output.append("")
            output.append("**📊 Diagramme:**")
            for chart in charts:
                chart_type = chart.get("chart_type", "bar")
                title = chart.get("title", "Diagramm")
                output.append(f"<!-- CHART: type={chart_type} -->")
                output.append(f"{title} ({chart_type.upper()})")

        # Tables
        tables = structured_data.get("tables", [])
        if tables:
            output.append("")
            for table in tables:
                if table.get("caption"):
                    output.append(f"**{table['caption']}**")
                    output.append("")

                headers = table.get("headers", [])
                rows = table.get("rows", [])

                if headers and rows:
                    # Markdown table
                    output.append("| " + " | ".join(headers) + " |")
                    output.append("| " + " | ".join(["---"] * len(headers)) + " |")
                    for row in rows:
                        output.append("| " + " | ".join(str(cell) for cell in row) + " |")
                    output.append("")

        # Documents
        documents = structured_data.get("documents", [])
        if documents:
            output.append("")
            output.append("**📄 Dokumente:**")
            for doc in documents:
                filename = doc.get("filename", "Dokument")
                url = doc.get("url", "")
                file_type = doc.get("file_type", "pdf").upper()
                description = doc.get("description", "")

                output.append(f"📎 [{filename}]({url}) ({file_type})")
                if description:
                    output.append(f"   {description}")

        # Videos
        videos = structured_data.get("videos", [])
        if videos:
            output.append("")
            output.append("**🎥 Videos:**")
            for video in videos:
                title = video.get("title", "Video")
                url = video.get("url", "")
                platform = video.get("platform", "youtube")

                output.append(f"▶️ [{title}]({url}) ({platform.title()})")

        return "\n".join(output)

    @staticmethod
    def _inject_citations(text: str, citation_map: Dict[str, int]) -> str:
        """
        Fügt [N] Citations in Text ein basierend auf Citation Map

        Args:
            text: Original text
            citation_map: {text_fragment: source_id}

        Returns:
            Text mit [N] citations
        """
        # Exakte Matches first
        for cited_text, source_id in citation_map.items():
            if cited_text in text:
                # Füge Citation nach dem Text ein (wenn nicht schon vorhanden)
                if f"[{source_id}]" not in text:
                    text = text.replace(cited_text, f"{cited_text}[{source_id}]")
                    logger.debug(f"✅ Injected [{source_id}] after '{cited_text[:30]}...'")

        return text

    @staticmethod
    def format_with_fallback(llm_output: str) -> tuple[str, bool]:
        """
        Versucht JSON zu parsen und zu formatieren, Fallback zu Raw Output

        Args:
            llm_output: Raw LLM output

        Returns:
            (formatted_output, success)
        """
        try:
            structured_data = JSONCitationFormatter.parse_json_response(llm_output)
            formatted = JSONCitationFormatter.format_to_ieee(structured_data)
            return formatted, True
        except Exception as e:
            logger.warning(f"⚠️ JSON formatting failed: {e}, using raw output")
            return llm_output, False


# Quick Test
if __name__ == "__main__":
    # Test Example
    test_json = """
    {
      "direct_answer": "§ 58 LBO BW regelt die Genehmigung von Bauvorhaben.",
      "details": [
        "Bauantrag muss beim Bauordnungsamt eingereicht werden",
        "Erforderliche Unterlagen: Lageplan, Bauzeichnungen, Statik",
        "Bearbeitungsdauer: in der Regel 2-3 Monate"
      ],
      "citations": [
        {"text": "Bauantrag muss beim Bauordnungsamt eingereicht werden", "source_id": 1},
        {"text": "Erforderliche Unterlagen: Lageplan, Bauzeichnungen, Statik", "source_id": 1},
        {"text": "Bearbeitungsdauer: in der Regel 2-3 Monate", "source_id": 2}
      ],
      "sources": [
        "LBO BW § 58 - Landesbauordnung Baden-Württemberg",
        "Bauordnungsamt Leitfaden 2024"
      ],
      "follow_ups": [
        "Welche Kosten fallen für die Baugenehmigung an?",
        "Kann ich eine vereinfachte Genehmigung beantragen?",
        "Welche Fristen muss ich beachten?"
      ]
    }
    """

    formatter = JSONCitationFormatter()

    print("=" * 80)
    print("🧪 TEST: JSON Citation Formatter")
    print("=" * 80)

    print("\n📥 INPUT (JSON):")
    print(test_json)

    print("\n📤 OUTPUT (IEEE-formatted):")
    formatted, success = formatter.format_with_fallback(test_json)
    print(formatted)

    print("\n📊 RESULT:")
    print(f"  Success: {success}")
    print(f"  Citations present: {'[1]' in formatted and '[2]' in formatted}")
