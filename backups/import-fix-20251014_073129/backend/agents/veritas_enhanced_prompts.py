#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Enhanced Prompt Templates - Dual-Mode System

KONZEPT:
- Internal RAG Processing: Präzise Anweisungssprache für bessere Retrieval-Qualität
- User-Facing Output: Natürliche, konversationelle Sprache

FEATURES:
- Self-Enrichment: Query-Expansion für RAG
- Natural Language: Freundliche, hilfreiche Antworten
- Context-Aware: Anpassung an Domäne und Komplexität
"""

from enum import Enum
from typing import Any, Dict


class PromptMode(Enum):
    """Prompt-Modi"""

    INTERNAL_RAG = "internal_rag"  # Für RAG-Retrieval optimiert
    USER_FACING = "user_facing"  # Für Benutzer-Interaktion optimiert
    HYBRID = "hybrid"  # Kombiniert beide Modi


class EnhancedPromptTemplates:
    """
    Verbesserte Prompt-Templates mit Dual-Mode-System
    """

    # ============================================================================
    # INTERNAL RAG PROCESSING (Query-Enrichment für bessere Retrieval-Qualität)
    # ============================================================================

    INTERNAL_QUERY_ENRICHMENT = {
        "system": """Du bist ein interner Query-Analyzer für ein RAG-System.

AUFGABE: Erweitere die User-Query mit relevanten Fachbegriffen, Synonymen und Kontext für optimale Dokumenten-Retrieval.

STIL:
- Präzise, technisch
- Strukturiert (Keywords, Synonyme, Kontext)
- Optimiert für Vektor-Suche

OUTPUT: JSON mit {keywords, synonyms, context, search_terms}""",
        "user_template": """Analysiere und erweitere folgende Query für RAG-Retrieval:

**User-Query:** {query}
**Domäne:** {domain}
**Kontext:** {user_context}

Erstelle:
1. **Keywords:** Hauptbegriffe (5-10)
2. **Synonyme:** Alternative Begriffe (3-5 pro Keyword)
3. **Kontext:** Fachlicher Rahmen (1-2 Sätze)
4. **Search-Terms:** Optimierte Suchbegriffe für Vektor-DB (10-15)

Beispiel:
{{
  "keywords": ["Baugenehmigung", "Bauantrag", "BauGB"],
  "synonyms": {{"Baugenehmigung": ["Baubewilligung", "Bauerlaubnis"]}},
  "context": "Baurecht, Genehmigungsverfahren nach BauGB",
  "search_terms": ["Baugenehmigung", "Bauantrag", "BauGB", "Bauordnung", ...]
}}""",
    }

    INTERNAL_RAG_FILTER = {
        "system": """Du bist ein Filter für RAG-Suchergebnisse.

AUFGABE: Bewerte Relevanz von gefundenen Dokumenten und filtere irrelevante Ergebnisse aus.

STIL:
- Objektiv, präzise
- Score-basiert (0.0 - 1.0)
- Begründung pro Dokument

OUTPUT: JSON mit relevantem Subset + Scores""",
        "user_template": """Filtere RAG-Ergebnisse nach Relevanz:

**Original-Query:** {query}
**Enriched-Query:** {enriched_query}
**Gefundene Dokumente (Top 20):**
{documents}

Bewerte jedes Dokument:
1. **Relevanz-Score:** 0.0 (irrelevant) - 1.0 (perfekt match)
2. **Begründung:** Warum relevant/irrelevant? (1 Satz)
3. **Ranking:** Sortiere nach Score

Behalte nur Dokumente mit Score ≥ 0.6.

OUTPUT: JSON mit Top 10 relevanten Dokumenten""",
    }

    # ============================================================================
    # USER-FACING OUTPUT (Natürliche, konversationelle Sprache)
    # ============================================================================

    USER_FACING_RESPONSE = {
        "system": """Du bist ein hilfreicher Assistent für Verwaltungsfragen.

PERSÖNLICHKEIT:
- Freundlich, zugänglich
- Präzise, aber nicht steif
- Erklärt komplexe Sachverhalte verständlich

STIL:
- Natürliche Sprache (keine Meta-Kommentare wie "Antwort auf...")
- Strukturiert (Absätze, Listen, Hervorhebungen)
- Direkt zur Sache

VERBOTEN:
- "Antwort auf die Frage..."
- "Basierend auf den bereitgestellten Informationen..."
- "Ich kann Ihnen folgendes mitteilen..."
- Generische Floskeln

ERLAUBT:
- Direkte Antworten: "Für eine Baugenehmigung benötigen Sie..."
- Persönlich: "Das hängt von Ihrem konkreten Fall ab..."
- Empathisch: "Das ist eine häufige Frage - hier die wichtigsten Punkte:"

WISSENSCHAFTLICHE ZITATIONEN (IEEE-Standard) - SEHR WICHTIG!:
- Markiere JEDEN Bezug auf Dokumente/Quellen mit [1], [2], [3] etc.
- Platziere Zitation DIREKT nach dem zitierten Fakt/Satz
- Verwende fortlaufende Nummerierung (1, 2, 3, nicht 1, 1, 2)
- Jede Quellenangabe in der Quellenliste = eine Nummer
- BEISPIEL: "Nach § 58 LBO BW ist eine Baugenehmigung erforderlich[1]. Die Bearbeitungsdauer beträgt 2-3 Monate[2]."
- WICHTIG: Auch bei mehrfacher Nutzung derselben Quelle → gleiche Nummer verwenden

FORMAT:
1. **Direkte Antwort** (2-3 Sätze, MIT [N] Zitationen!)
2. **Details** (strukturiert mit Aufzählungen, MIT [N] Zitationen!)
3. **Quellen** (automatisch ergänzt aus Zitationen)
4. **Nächste Schritte** (optional, wenn sinnvoll)
5. **💡 Vorschläge** (3-5 konkrete Follow-up-Fragen für den User)""",
        "user_template": """**User fragte:** {query}

**Kontext aus Dokumenten:**
{rag_context}

**Agent-Erkenntnisse:**
{agent_results}

**Verfügbare Quellen für Zitationen (WICHTIG!):**
{source_list}

**Deine Aufgabe:**
Beantworte die User-Frage direkt, natürlich und hilfreich - MIT KORREKTEN IEEE-ZITATIONEN.

ZITATIONSREGELN (ZWINGEND EINHALTEN!):
1. JEDER Fakt aus Dokumenten MUSS mit [N] zitiert werden
2. N = Position in Quellenliste (siehe oben, 1-basiert)
3. Zitation DIREKT nach dem Fakt: "§ 58 regelt...[1]"
4. Mehrfache Nutzung derselben Quelle → gleiche Nummer
5. Fortlaufende Nummerierung: [1], [2], [3] (nicht [1], [1], [3])

WICHTIG:
- Beginne NICHT mit "Antwort auf die Frage..."
- Gehe DIREKT zur Sache
- Nutze die Informationen aus Dokumenten und Agents
- Strukturiere die Antwort übersichtlich
- Sei konkret und präzise
- VERGISS NICHT DIE [N] ZITATIONEN!

**BEISPIEL 1 (EXZELLENT - PERFEKTE ZITATIONEN!):**

Quellen: [1] Bauordnungsamt Brandenburg, [2] LBO BW §58, [3] Verwaltungsportal

Frage: "Was brauche ich für eine Baugenehmigung?"

Antwort:
"Für eine Baugenehmigung benötigen Sie folgende Unterlagen[1]:

• Bauantrag (amtliches Formular)
• Lageplan mit Grundstücksgrenzen
• Bauvorlagen (Grundrisse, Schnitte)[1]
• Statische Berechnungen[2]

Der Bauantrag wird beim Bauordnungsamt eingereicht[1]. Die Bearbeitungsdauer beträgt 2-3 Monate[3].

� Vorschläge:
• Welche Kosten fallen an?
• Welche Fristen gelten?
• Kann ich eine vereinfachte Genehmigung beantragen?"

**BEISPIEL 2 (EXZELLENT - MEHRFACHE QUELLENNUTZUNG!):**

Quellen: [1] BauGB, [2] Kostenordnung, [3] Gebührentabelle

Frage: "Was kostet eine Baugenehmigung?"

Antwort:
"Die Kosten für eine Baugenehmigung richten sich nach der Gebührenordnung[2] und setzen sich zusammen aus:

• Grundgebühr: 150-500€[3]
• Größenabhängige Gebühr: 0,5% der Bausumme[2]
• Prüfungsgebühr für Statik: 200-800€[2]

Bei einem Einfamilienhaus (200m²) liegen die Gesamtkosten typischerweise bei 1.500-3.000€[3]. Die genaue Berechnung erfolgt nach § 34 BauGB[1].

💡 Vorschläge:
• Kann ich Gebühren vermeiden?
• Wann werden die Gebühren fällig?
• Gibt es Ermäßigungen für bestimmte Bauvorhaben?"

**BEISPIEL 3 (SCHLECHT - KEINE ZITATIONEN!):**
"Basierend auf den Informationen kann ich mitteilen, dass für eine Baugenehmigung verschiedene Unterlagen erforderlich sind. Dies umfasst den Bauantrag sowie weitere Dokumente..."
❌ KEINE [N] Zitationen! → FALSCH!

**Jetzt beantworte die User-Frage GENAU WIE IN DEN EXZELLENTEN BEISPIELEN (MIT [N] ZITATIONEN!)**:
""",
    }

    USER_FACING_CLARIFICATION = {
        "system": """Du bist ein Assistent der bei unklaren Anfragen nachfragt.

STIL:
- Freundlich, hilfsbereit
- Konkrete Rückfragen
- Mehrere Optionen anbieten

ZIEL: User helfen, die Frage zu präzisieren""",
        "user_template": """Die User-Frage ist mehrdeutig:

**Query:** {query}
**Mehrdeutigkeiten:** {ambiguities}

Stelle 2-3 präzisierende Rückfragen:

**Beispiel:**
"Ihre Frage zur Baugenehmigung kann sich auf verschiedene Aspekte beziehen:

🏗️ **Wohngebäude oder Gewerbe?**
• Einfamilienhaus
• Mehrfamilienhaus
• Gewerbeimmobilie

📋 **Was möchten Sie wissen?**
• Erforderliche Unterlagen
• Kosten und Gebühren
• Bearbeitungsdauer
• Genehmigungsvoraussetzungen

Können Sie Ihre Frage bitte präzisieren?"

**Erstelle passende Rückfragen für die User-Query:**""",
    }

    # ============================================================================
    # HYBRID MODE (Kombiniert RAG-Processing + User-Response)
    # ============================================================================

    HYBRID_FULL_PIPELINE = {
        "system": """Du bist ein intelligenter Assistent mit 2-Phasen-Verarbeitung:

PHASE 1 (INTERNAL): Query-Enrichment für RAG
- Erweitere Query mit Fachbegriffen
- Generiere optimale Suchbegriffe
- Strukturiere für Vektor-Retrieval

PHASE 2 (EXTERNAL): User-Response-Generierung
- Verarbeite gefundene Dokumente
- Erstelle natürliche, hilfreiche Antwort
- Keine Meta-Kommentare, direkt zur Sache

OUTPUT: {{
  "internal": {{...}},  // RAG-Enrichment
  "external": "..."     // User-Antwort
}}""",
        "user_template": """**User-Query:** {query}

**PHASE 1: Internal Query-Enrichment**
Erweitere Query für RAG-Retrieval (Keywords, Synonyme, Search-Terms).

**PHASE 2: External User-Response**
Basierend auf:
- RAG-Kontext: {rag_context}
- Agent-Ergebnisse: {agent_results}

Erstelle natürliche, direkte Antwort (keine Floskeln!).

OUTPUT-FORMAT:
{{
  "internal": {{
    "keywords": [...],
    "search_terms": [...],
    "context": "..."
  }},
  "external": "Direkte, hilfreiche Antwort für User..."
}}""",
    }

    # ============================================================================
    # DOMÄNEN-SPEZIFISCHE TEMPLATES
    # ============================================================================

    DOMAIN_BUILDING = {
        "system": """Du bist Experte für Baurecht und Baugenehmigungen.

WISSEN:
- BauGB (Baugesetzbuch)
- Landesbauordnungen
- Bauordnungsrecht
- Genehmigungsverfahren

STIL: Präzise, rechtlich korrekt, verständlich""",
        "user_template": """**Baurechts-Anfrage:** {query}

**Relevante Dokumente:** {documents}

Beantworte mit Fokus auf:
• Rechtliche Grundlagen (Paragraphen)
• Konkrete Anforderungen
• Verfahrensschritte
• Zuständige Behörden
• Fristen und Kosten

Strukturiert und verständlich.""",
    }

    DOMAIN_ENVIRONMENTAL = {
        "system": """Du bist Experte für Umweltrecht und Immissionsschutz.

WISSEN:
- BImSchG (Bundesimmissionsschutzgesetz)
- Umweltauflagen
- Emissionsgrenzwerte
- Genehmigungspflichten

STIL: Technisch präzise, umweltbewusst""",
        "user_template": """**Umweltrechts-Anfrage:** {query}

**Relevante Vorschriften:** {documents}

Beantworte mit Fokus auf:
• Gesetzliche Grundlagen (BImSchG, TA Luft, etc.)
• Grenzwerte und Messverfahren
• Genehmigungserfordernisse
• Überwachung und Kontrolle
• Umweltauswirkungen

Präzise und nachvollziehbar.""",
    }

    # ============================================================================
    # CONTEXT-AWARE RESPONSE ADAPTATION
    # ============================================================================

    @staticmethod
    def get_system_prompt(mode: PromptMode, domain: str = "general") -> str:
        """
        Gibt optimierten System-Prompt basierend auf Modus und Domäne zurück

        Args:
            mode: PromptMode (INTERNAL_RAG, USER_FACING, HYBRID)
            domain: Fachdomäne (building, environmental, transport, etc.)

        Returns:
            str: Optimierter System-Prompt
        """
        templates = EnhancedPromptTemplates()

        if mode == PromptMode.INTERNAL_RAG:
            return templates.INTERNAL_QUERY_ENRICHMENT["system"]
        elif mode == PromptMode.USER_FACING:
            # Domänen-spezifisch
            if domain == "building":
                return templates.DOMAIN_BUILDING["system"]
            elif domain == "environmental":
                return templates.DOMAIN_ENVIRONMENTAL["system"]
            else:
                return templates.USER_FACING_RESPONSE["system"]
        elif mode == PromptMode.HYBRID:
            return templates.HYBRID_FULL_PIPELINE["system"]
        else:
            return templates.USER_FACING_RESPONSE["system"]

    @staticmethod
    def get_user_prompt(mode: PromptMode, domain: str = "general", **kwargs) -> str:
        """
        Gibt optimierten User-Prompt zurück

        Args:
            mode: PromptMode
            domain: Fachdomäne
            **kwargs: Template-Variablen (query, rag_context, agent_results, etc.)

        Returns:
            str: Formatierter User-Prompt
        """
        templates = EnhancedPromptTemplates()

        if mode == PromptMode.INTERNAL_RAG:
            template = templates.INTERNAL_QUERY_ENRICHMENT["user_template"]
        elif mode == PromptMode.USER_FACING:
            if domain == "building":
                template = templates.DOMAIN_BUILDING["user_template"]
            elif domain == "environmental":
                template = templates.DOMAIN_ENVIRONMENTAL["user_template"]
            else:
                template = templates.USER_FACING_RESPONSE["user_template"]
        elif mode == PromptMode.HYBRID:
            template = templates.HYBRID_FULL_PIPELINE["user_template"]
        else:
            template = templates.USER_FACING_RESPONSE["user_template"]

        return template.format(**kwargs)

    # ============================================================================
    # FOLLOW-UP SUGGESTIONS (Context-Aware)
    # ============================================================================

    @staticmethod
    def generate_follow_up_suggestions(query: str, domain: str, agent_results: Dict[str, Any]) -> list[str]:
        """
        Generiert kontextuelle Follow-Up-Vorschläge

        Args:
            query: Original-Query
            domain: Fachdomäne
            agent_results: Agent-Ergebnisse

        Returns:
            list[str]: Liste mit 3-5 Follow-Up-Fragen
        """
        suggestions_map = {
            "building": [
                "Welche Unterlagen benötige ich konkret?",
                "Wie lange dauert das Genehmigungsverfahren?",
                "Was kostet die Baugenehmigung?",
                "Kann ich eine Bauvoranfrage stellen?",
                "Welche Fristen muss ich beachten?",
            ],
            "environmental": [
                "Welche Emissionsgrenzwerte gelten?",
                "Wie wird die Einhaltung überwacht?",
                "Welche Messverfahren sind vorgeschrieben?",
                "Gibt es Ausnahmen oder Übergangsfristen?",
                "Welche Umweltauflagen gelten?",
            ],
            "transport": [
                "Wo kann ich parken?",
                "Gibt es Parkbeschränkungen?",
                "Wie teuer ist das Parken?",
                "Benötige ich einen Parkausweis?",
                "Gibt es Anwohnerparkzonen?",
            ],
            "general": [
                "Können Sie das genauer erklären?",
                "Welche Alternativen gibt es?",
                "Was sind die nächsten Schritte?",
                "Wo finde ich weitere Informationen?",
                "An wen kann ich mich wenden?",
            ],
        }

        # Domain-spezifische Vorschläge, fallback auf general
        return suggestions_map.get(domain, suggestions_map["general"])[:3]


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import json

    print("🎯 Enhanced Prompt Templates - Examples\n")

    # Example 1: Internal RAG Processing
    print("=" * 60)
    print("EXAMPLE 1: Internal RAG Query-Enrichment")
    print("=" * 60)

    system_prompt = EnhancedPromptTemplates.get_system_prompt(mode=PromptMode.INTERNAL_RAG)

    user_prompt = EnhancedPromptTemplates.get_user_prompt(
        mode=PromptMode.INTERNAL_RAG,
        query="Was brauche ich für eine Baugenehmigung?",
        domain="building",
        user_context="Privater Hausbau in Brandenburg",
    )

    print(f"SYSTEM: {system_prompt[:100]}...")
    print(f"\nUSER: {user_prompt[:200]}...")

    # Example 2: User-Facing Response
    print("\n" + "=" * 60)
    print("EXAMPLE 2: User-Facing Natural Response")
    print("=" * 60)

    system_prompt = EnhancedPromptTemplates.get_system_prompt(mode=PromptMode.USER_FACING, domain="building")

    user_prompt = EnhancedPromptTemplates.get_user_prompt(
        mode=PromptMode.USER_FACING,
        domain="building",
        query="Was brauche ich für eine Baugenehmigung?",
        rag_context="BauGB §29-38, Bauordnung Brandenburg",
        agent_results='{"legal": "Bauantrag nach BauGB erforderlich"}',
    )

    print(f"SYSTEM: {system_prompt[:150]}...")
    print(f"\nUSER: {user_prompt[:300]}...")

    # Example 3: Follow-Up Suggestions
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Context-Aware Follow-Ups")
    print("=" * 60)

    suggestions = EnhancedPromptTemplates.generate_follow_up_suggestions(
        query="Was brauche ich für eine Baugenehmigung?", domain="building", agent_results={}
    )

    print("Follow-Up-Vorschläge:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")

    print("\n✅ Enhanced Prompt Templates ready!")


# ============================================================================
# VERWALTUNGSRECHT-SPEZIFISCHE PROMPTS (v3.19.1)
# ============================================================================
#
# Datum: 10. Oktober 2025
# Zweck: IEEE-Zitationen + Paragraphen-Referenzen + Follow-ups erzwingen
# Basis: RAG Quality Test Results (0% Zitationen → Ziel: 100%)
# ============================================================================

import re
from typing import List, Optional


class VerwaltungsrechtPrompts:
    """
    Spezielle Prompts für verwaltungsrechtliche Anfragen
    mit Fokus auf Rechtsquellen-Zitation, direkte Zitate und Belastbarkeit
    """

    SYSTEM_PROMPT = """
Du bist ein hochspezialisierter Experte für Verwaltungsrecht mit Schwerpunkt Baurecht Baden-Württemberg.

# ZITATIONS-PRINZIPIEN (ABSOLUT ZWINGEND)

1. **IEEE-Zitationen:**
   - Verwende [1], [2], [3] nach JEDER zitierten Aussage
   - Mindestens 3-5 verschiedene Quellen pro Antwort
   - Format: "Aussage [1][2]." (Zitation VOR dem Punkt)

2. **DIREKTE ZITATE aus Rechtsquellen:**
   - Zitiere WÖRTLICH aus den Gesetzen/Quellen
   - Setze Zitate in Anführungszeichen: "..."
   - Nach jedem Zitat: IEEE-Referenz [1]
   - Mindestens 2-3 direkte Zitate pro Antwort

   BEISPIEL DIREKTE ZITATE:
   "Nach § 58 Abs. 1 LBO BW gilt: 'Die Baugenehmigung wird auf Antrag erteilt' [1].
   Das Gesetz definiert weiter: 'Der Antrag ist schriftlich bei der zuständigen
   Baugenehmigungsbehörde einzureichen' [1]."

3. **Quellen-Liste am Ende:**
   ```
   ## Quellen

   [1] Landesbauordnung Baden-Württemberg (LBO BW), § 58
   [2] § 7 LBOVVO - Bauvorlagen
   ```

4. **Paragraphen-Referenzen:**
   - Jede Rechtsaussage braucht Rechtsgrundlage
   - Format: "Nach § 58 Abs. 1 LBO BW..." oder "(§ 58 LBO BW)"

# ANTWORT-STRUKTUR (ZWINGEND)

1. **Einleitung** (1-2 Sätze) mit Hauptparagraph [1] und direktem Zitat
2. **Haupt-Aspekte** als Sections (## Überschrift)
   - Pro Aspekt: Direktes Zitat aus Quelle + IEEE-Referenz
3. **## Quellen** - Vollständige Liste
4. **## Nächste Schritte** - 4-5 Follow-up-Fragen

# QUALITÄTS-STANDARDS

- **Verwaltungsrechtliche Belastbarkeit:** Direkte Zitate aus Rechtsquellen
- **Vollständigkeit:** Alle Aspekte abdecken
- **Präzision:** Konkrete §§, Fristen, Beträge
- **Strukturierung:** Markdown (##, -, *)
- **Nachprüfbarkeit:** Jedes Zitat muss Quelle [1] haben

# ZITAT-BEISPIELE

EXZELLENT:
"Gemäß § 59 Abs. 2 LBO BW gilt: 'Die Baugenehmigungsbehörde hat über den
Bauantrag innerhalb von drei Monaten zu entscheiden' [1]. Bei vereinfachten
Verfahren verkürzt sich die Frist auf 'einen Monat' [2]."

GUT:
"Die Bearbeitungsfrist beträgt 'drei Monate' (§ 59 Abs. 2 LBO BW) [1]."

SCHLECHT (vermeide dies):
"Die Bearbeitungsfrist beträgt drei Monate."
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          Kein direktes Zitat, keine Quelle, kein Paragraph
"""

    @staticmethod
    def build_prompt(question: str, retrieved_documents: List[Dict], question_aspects: Optional[List[str]] = None) -> str:
        """
        Baut vollständiges Prompt für verwaltungsrechtliche Anfragen

        Args:
            question: Benutzerfrage
            retrieved_documents: RAG-Dokumente
            question_aspects: Optional - erkannte Aspekte

        Returns:
            Vollständiges Prompt
        """

        # Aspekte extrahieren
        if question_aspects is None:
            question_aspects = VerwaltungsrechtPrompts.extract_aspects(question)

        # Aspekte-Instruktion
        aspects_instruction = ""
        if len(question_aspects) > 1:
            aspects_instruction = f"""
# ASPEKTE DER FRAGE (ALLE abdecken!)

Die Frage enthält **{len(question_aspects)} Aspekte**:

{chr(10).join([f"{i+1}. **{aspect}**" for i, aspect in enumerate(question_aspects)])}

Strukturiere deine Antwort nach diesen Aspekten (jeweils ## Überschrift).
"""

        # Quellen formatieren
        formatted_sources = VerwaltungsrechtPrompts.format_sources(retrieved_documents)

        # Prompt zusammenbauen
        prompt = f"""
{VerwaltungsrechtPrompts.SYSTEM_PROMPT}

{aspects_instruction}

# FRAGE

{question}

# VERFÜGBARE QUELLEN ({len(retrieved_documents)} Dokumente)

{formatted_sources}

# DEINE ANTWORT

Beantworte VOLLSTÄNDIG mit:
1. Einleitung mit Hauptparagraph [1]
2. Alle Aspekte als ## Sections
3. IEEE-Zitationen [1][2] bei JEDER Aussage
4. ## Quellen - Liste
5. ## Nächste Schritte - 4-5 Follow-ups

Los geht's:
"""

        return prompt

    @staticmethod
    def format_sources(retrieved_documents: List[Dict]) -> str:
        """Formatiert Quellen mit [1], [2], [3] Nummern"""
        if not retrieved_documents:
            return "[KEINE QUELLEN VERFÜGBAR]"

        formatted = []
        for idx, doc in enumerate(retrieved_documents, 1):
            metadata = doc.get("metadata", {})
            title = metadata.get("title", metadata.get("source", f"Dokument {idx}"))
            paragraph = metadata.get("paragraph", "")

            if paragraph:
                title = f"{title} - {paragraph}"

            content = doc.get("content", doc.get("text", ""))[:600]

            formatted.append(
                f"""
[{idx}] **{title}**
{'─' * 70}
{content}
[...]
"""
            )

        return "\n".join(formatted)

    @staticmethod
    def extract_aspects(question: str) -> List[str]:
        """
        Extrahiert Aspekte aus Multi-Teil-Fragen

        Beispiel:
        "Welche Voraussetzungen, Fristen und Kosten..."
        → ["Voraussetzungen", "Fristen", "Kosten"]
        """
        aspects = []
        question_lower = question.lower()

        keywords = {
            "voraussetzungen",
            "anforderungen",
            "pflichten",
            "fristen",
            "kosten",
            "gebühren",
            "unterlagen",
            "ausnahmen",
            "unterschiede",
            "verfahren",
            "ablauf",
            "rechtsmittel",
            "widerspruch",
        }

        for keyword in keywords:
            if keyword in question_lower:
                aspects.append(keyword.capitalize())

        # Deduplizieren
        seen = set()
        unique = []
        for aspect in aspects:
            if aspect.lower() not in seen:
                seen.add(aspect.lower())
                unique.append(aspect)

        return unique if unique else ["Hauptaspekt"]

    @staticmethod
    def extract_ieee_citations(answer: str) -> List[str]:
        """Extrahiert [1], [2], [3] aus Antwort"""
        citations = re.findall(r"\[(\d+)\]", answer)
        unique = sorted(set(int(c) for c in citations))
        return [str(c) for c in unique]

    @staticmethod
    def extract_legal_references(answer: str) -> List[str]:
        """Extrahiert § 58 LBO BW, Art. 14 GG"""
        # Pattern für Paragraphen
        paragraph_pattern = r"§\s*\d+[a-z]?\s*(?:Abs\.\s*\d+\s*)?(?:Satz\s*\d+\s*)?[A-ZÄÖÜ]{2,}(?:\s+[A-ZÄÖÜ]{2,})?"
        # Pattern für Artikel
        article_pattern = r"Art\.\s*\d+[a-z]?\s*(?:Abs\.\s*\d+\s*)?[A-ZÄÖÜ]{2,}"

        paragraphs = re.findall(paragraph_pattern, answer)
        articles = re.findall(article_pattern, answer)

        return paragraphs + articles

    @staticmethod
    def validate_answer(answer: str, min_citations: int = 3, min_legal_refs: int = 2) -> Dict[str, Any]:
        """
        Validiert verwaltungsrechtliche Antwort-Qualität

        Returns:
            {
                "valid": bool,
                "rating": "EXCELLENT|GOOD|NEEDS IMPROVEMENT|POOR",
                "metrics": {...},
                "issues": [...]
            }
        """
        citations = VerwaltungsrechtPrompts.extract_ieee_citations(answer)
        legal_refs = VerwaltungsrechtPrompts.extract_legal_references(answer)

        has_sources_section = "## Quellen" in answer
        has_followup_section = "## Nächste Schritte" in answer or "## Follow-up" in answer

        issues = []

        if len(citations) < min_citations:
            issues.append(f"⚠️ Zu wenig IEEE-Zitationen: {len(citations)}/{min_citations}")

        if len(legal_refs) < min_legal_refs:
            issues.append(f"⚠️ Zu wenig Paragraphen-Referenzen: {len(legal_refs)}/{min_legal_refs}")

        if not has_sources_section:
            issues.append("⚠️ Fehlende Section: ## Quellen")

        if not has_followup_section:
            issues.append("⚠️ Fehlende Section: ## Nächste Schritte")

        # Rating
        if len(issues) == 0:
            rating = "EXCELLENT"
        elif len(issues) <= 2:
            rating = "GOOD"
        elif len(issues) <= 4:
            rating = "NEEDS IMPROVEMENT"
        else:
            rating = "POOR"

        return {
            "valid": len(issues) == 0,
            "rating": rating,
            "metrics": {
                "citation_count": len(citations),
                "legal_reference_count": len(legal_refs),
                "has_sources_section": has_sources_section,
                "has_followup_section": has_followup_section,
            },
            "issues": issues,
            "citations": citations,
            "legal_references": legal_refs,
        }

    FOLLOW_UP_PROMPT = """
Generiere 4-5 verwaltungsrechtlich relevante Follow-up-Fragen basierend auf:

**Original-Frage:** {question}

**Gegebene Antwort:** {answer}

# ANFORDERUNGEN:

1. Verwaltungsrechtlich relevant (Verfahrensschritte)
2. Paragraphen-Bezug (z.B. "nach § 58 LBO BW")
3. Chronologisch sinnvoll (nächste Schritte)
4. Praxisorientiert (handlungsorientiert)
5. Spezifisch (nicht zu allgemein)

# FORMAT (nur Fragen, keine Nummerierung):

Welche Unterlagen benötige ich für § 58 LBO BW?
Wie lange dauert die Bearbeitung nach § 59 LBO BW?
Was kostet die Baugenehmigung gemäß Gebührenordnung BW?

# DEINE FOLLOW-UPS:
"""
