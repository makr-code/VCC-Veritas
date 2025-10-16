#!/usr/bin/env python3
"""
VERITAS Stage Reflection Service
=================================
LLM-gestütztes Meta-Reflection System für Pipeline-Stages

Dual-Prompt-System:
1. User Query Prompt → Primäre Verarbeitung
2. Meta-Reflection Prompt → Fortschritts-Analyse pro Stage

Features:
- Erfüllungsgrad-Analyse (0-100%)
- Gap-Identifikation (Was fehlt noch?)
- Konfidenz-Tracking
- Nächste Schritte Empfehlungen
- Strukturierte Progress-Messages

Created: 2025-10-15
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ReflectionStage(str, Enum):
    """Pipeline-Stages für Reflection"""
    HYPOTHESIS = "hypothesis"
    AGENT_SELECTION = "agent_selection"
    RETRIEVAL = "retrieval"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"


@dataclass
class StageReflection:
    """Strukturierte Stage-Reflection"""
    stage: ReflectionStage
    completion_percent: float  # 0-100
    fulfillment_status: str    # "incomplete", "partial", "complete"
    identified_gaps: List[str]  # Was fehlt noch?
    gathered_info: List[str]    # Was wurde gefunden?
    confidence: float           # 0-1
    next_actions: List[str]     # Empfohlene nächste Schritte
    llm_reasoning: str          # LLM Begründung
    timestamp: str


class StageReflectionService:
    """
    LLM-Service für Meta-Reflections zu Pipeline-Stages
    
    Generiert strukturierte Analysen zu:
    - Informations-Erfüllungsgrad
    - Identifizierte Lücken
    - Qualität der Zwischenergebnisse
    - Empfohlene nächste Schritte
    """
    
    def __init__(self, ollama_client=None):
        """
        Args:
            ollama_client: VeritasOllamaClient Instanz für LLM-Calls
        """
        self.ollama_client = ollama_client
        self.reflection_enabled = ollama_client is not None
        
        # Prompt-Templates für verschiedene Stages
        self.reflection_prompts = {
            ReflectionStage.HYPOTHESIS: self._build_hypothesis_reflection_prompt,
            ReflectionStage.AGENT_SELECTION: self._build_agent_selection_reflection_prompt,
            ReflectionStage.RETRIEVAL: self._build_retrieval_reflection_prompt,
            ReflectionStage.SYNTHESIS: self._build_synthesis_reflection_prompt,
            ReflectionStage.VALIDATION: self._build_validation_reflection_prompt,
        }
        
        logger.info(f"🔍 StageReflectionService initialized (LLM: {self.reflection_enabled})")
    
    async def reflect_on_stage(
        self,
        stage: ReflectionStage,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> StageReflection:
        """
        Führt LLM-gestützte Reflection für Stage aus
        
        Args:
            stage: Aktuelle Pipeline-Stage
            user_query: Original User-Query
            stage_data: Ergebnisse/Daten der aktuellen Stage
            context: Zusätzlicher Kontext (vorherige Stages etc.)
            
        Returns:
            StageReflection mit strukturierter Analyse
        """
        if not self.reflection_enabled:
            return self._create_fallback_reflection(stage, stage_data)
        
        try:
            # Baue Stage-spezifischen Reflection-Prompt
            prompt_builder = self.reflection_prompts.get(stage)
            if not prompt_builder:
                logger.warning(f"⚠️ Kein Reflection-Prompt für Stage: {stage}")
                return self._create_fallback_reflection(stage, stage_data)
            
            reflection_prompt = prompt_builder(user_query, stage_data, context or {})
            
            # LLM-Call für Meta-Reflection
            reflection_response = await self._call_llm_reflection(reflection_prompt, stage)
            
            # Parse LLM-Response zu strukturiertem Format
            reflection = self._parse_reflection_response(stage, reflection_response, stage_data)
            
            logger.info(f"✅ Stage Reflection: {stage} | Erfüllung: {reflection.completion_percent}%")
            return reflection
            
        except Exception as e:
            logger.error(f"❌ Reflection Error ({stage}): {e}")
            return self._create_fallback_reflection(stage, stage_data)
    
    def _build_hypothesis_reflection_prompt(
        self,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prompt für Hypothesen-Generierungs-Reflection"""
        hypotheses = stage_data.get('hypotheses', [])
        query_complexity = stage_data.get('complexity', 'unknown')
        
        return f"""
Du bist ein Meta-Analyst der die Qualität von generierten Hypothesen bewertet.

USER QUERY:
{user_query}

GENERIERTE HYPOTHESEN:
{chr(10).join(f"- {h}" for h in hypotheses) if hypotheses else "Keine Hypothesen generiert"}

QUERY KOMPLEXITÄT: {query_complexity}

DEINE AUFGABE:
Analysiere den Fortschritt der Hypothesen-Generierung:

1. ERFÜLLUNGSGRAD (0-100%):
   - Sind die Hypothesen relevant für die User-Query?
   - Decken sie verschiedene Aspekte ab?
   - Ist die Komplexität angemessen erfasst?

2. IDENTIFIZIERTE LÜCKEN:
   - Welche wichtigen Aspekte fehlen?
   - Welche Hypothesen sollten noch ergänzt werden?

3. GESAMMELTE INFORMATIONEN:
   - Was wurde bereits gut erfasst?
   - Welche Hypothesen sind besonders wertvoll?

4. NÄCHSTE SCHRITTE:
   - Welche Agents sollten basierend auf den Hypothesen aktiviert werden?
   - Welche Datenquellen sind relevant?

5. KONFIDENZ (0-1):
   - Wie sicher bist du, dass die Hypothesen zielführend sind?

Antworte in folgendem Format:
ERFÜLLUNG: <0-100>
STATUS: <incomplete|partial|complete>
LÜCKEN:
- <Lücke 1>
- <Lücke 2>
GESAMMELT:
- <Info 1>
- <Info 2>
NÄCHSTE_SCHRITTE:
- <Schritt 1>
- <Schritt 2>
KONFIDENZ: <0.0-1.0>
BEGRÜNDUNG: <Deine Reasoning>
"""
    
    def _build_agent_selection_reflection_prompt(
        self,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prompt für Agent-Auswahl-Reflection"""
        selected_agents = stage_data.get('selected_agents', [])
        available_agents = stage_data.get('available_agents', [])
        
        return f"""
Du bist ein Meta-Analyst der die Qualität der Agent-Auswahl bewertet.

USER QUERY:
{user_query}

AUSGEWÄHLTE AGENTS:
{chr(10).join(f"- {a}" for a in selected_agents)}

VERFÜGBARE AGENTS:
{chr(10).join(f"- {a}" for a in available_agents)}

DEINE AUFGABE:
Analysiere die Agent-Auswahl:

1. ERFÜLLUNGSGRAD (0-100%):
   - Sind die richtigen Agents für die Query ausgewählt?
   - Fehlen wichtige Agents?
   - Gibt es redundante Agents?

2. IDENTIFIZIERTE LÜCKEN:
   - Welche Informations-Domänen fehlen?
   - Welche zusätzlichen Agents könnten hilfreich sein?

3. GESAMMELTE INFORMATIONEN:
   - Welche Aspekte werden durch die Agents abgedeckt?
   - Welche Agent-Kombination ist besonders sinnvoll?

4. NÄCHSTE SCHRITTE:
   - Sollten weitere Agents hinzugefügt werden?
   - Welche Priorisierung ist sinnvoll?

5. KONFIDENZ (0-1):
   - Wie sicher bist du, dass die Agents die Query erfüllen können?

Antworte in folgendem Format:
ERFÜLLUNG: <0-100>
STATUS: <incomplete|partial|complete>
LÜCKEN:
- <Lücke 1>
GESAMMELT:
- <Info 1>
NÄCHSTE_SCHRITTE:
- <Schritt 1>
KONFIDENZ: <0.0-1.0>
BEGRÜNDUNG: <Deine Reasoning>
"""
    
    def _build_retrieval_reflection_prompt(
        self,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prompt für Retrieval-Reflection"""
        agent_results = stage_data.get('agent_results', {})
        total_sources = sum(len(r.get('sources', [])) for r in agent_results.values())
        
        return f"""
Du bist ein Meta-Analyst der die Qualität der Information-Retrieval bewertet.

USER QUERY:
{user_query}

AGENT ERGEBNISSE:
{chr(10).join(f"- {agent}: {len(result.get('sources', []))} Quellen, Konfidenz: {result.get('confidence', 0):.2f}" 
              for agent, result in agent_results.items())}

GESAMT: {total_sources} Quellen gefunden

DEINE AUFGABE:
Analysiere die Information-Retrieval:

1. ERFÜLLUNGSGRAD (0-100%):
   - Wurden ausreichend Informationen gefunden?
   - Ist die Qualität der Quellen hoch?
   - Decken die Informationen alle Aspekte der Query ab?

2. IDENTIFIZIERTE LÜCKEN:
   - Welche Informationen fehlen noch?
   - Welche Aspekte sind unterrepräsentiert?
   - Welche zusätzlichen Datenquellen könnten hilfreich sein?

3. GESAMMELTE INFORMATIONEN:
   - Was wurde bereits erfolgreich gefunden?
   - Welche Quellen sind besonders wertvoll?
   - Welche Agent-Ergebnisse sind am relevantesten?

4. NÄCHSTE SCHRITTE:
   - Sollte weiteres Retrieval durchgeführt werden?
   - Welche Informationen sollten priorisiert werden?
   - Ist genug für eine Synthese vorhanden?

5. KONFIDENZ (0-1):
   - Wie sicher bist du, dass die Informationen ausreichen?

Antworte in folgendem Format:
ERFÜLLUNG: <0-100>
STATUS: <incomplete|partial|complete>
LÜCKEN:
- <Lücke 1>
GESAMMELT:
- <Info 1>
NÄCHSTE_SCHRITTE:
- <Schritt 1>
KONFIDENZ: <0.0-1.0>
BEGRÜNDUNG: <Deine Reasoning>
"""
    
    def _build_synthesis_reflection_prompt(
        self,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prompt für Synthese-Reflection"""
        synthesis_result = stage_data.get('synthesis', {})
        response_text = synthesis_result.get('response_text', '')[:500]  # Erste 500 chars
        
        return f"""
Du bist ein Meta-Analyst der die Qualität der finalen Synthese bewertet.

USER QUERY:
{user_query}

GENERIERTE ANTWORT (Auszug):
{response_text}...

SYNTHESE METADATA:
- Konfidenz: {synthesis_result.get('confidence_score', 0):.2f}
- Quellen: {len(synthesis_result.get('sources', []))}
- Agent-Ergebnisse: {len(synthesis_result.get('agent_results', {}))}

DEINE AUFGABE:
Analysiere die finale Synthese:

1. ERFÜLLUNGSGRAD (0-100%):
   - Beantwortet die Synthese die User-Query vollständig?
   - Sind alle wichtigen Aspekte enthalten?
   - Ist die Antwort strukturiert und verständlich?

2. IDENTIFIZIERTE LÜCKEN:
   - Welche Informationen fehlen in der Antwort?
   - Welche Aspekte sollten ergänzt werden?
   - Gibt es offene Fragen?

3. GESAMMELTE INFORMATIONEN:
   - Was wurde gut synthetisiert?
   - Welche Stärken hat die Antwort?
   - Welche Informationen sind besonders wertvoll?

4. NÄCHSTE SCHRITTE:
   - Sollte die Synthese erweitert werden?
   - Welche Validierungen sind empfohlen?
   - Gibt es Follow-up-Fragen?

5. KONFIDENZ (0-1):
   - Wie sicher bist du, dass die Antwort den Nutzer zufriedenstellt?

Antworte in folgendem Format:
ERFÜLLUNG: <0-100>
STATUS: <incomplete|partial|complete>
LÜCKEN:
- <Lücke 1>
GESAMMELT:
- <Info 1>
NÄCHSTE_SCHRITTE:
- <Schritt 1>
KONFIDENZ: <0.0-1.0>
BEGRÜNDUNG: <Deine Reasoning>
"""
    
    def _build_validation_reflection_prompt(
        self,
        user_query: str,
        stage_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Prompt für Validierungs-Reflection"""
        validation_checks = stage_data.get('validation_checks', {})
        
        return f"""
Du bist ein Meta-Analyst der die Qualität der Validierung bewertet.

USER QUERY:
{user_query}

VALIDIERUNGS-CHECKS:
{chr(10).join(f"- {check}: {result}" for check, result in validation_checks.items())}

DEINE AUFGABE:
Analysiere die Validierung:

1. ERFÜLLUNGSGRAD (0-100%):
   - Sind alle wichtigen Checks durchgeführt?
   - Ist die Antwort qualitätsgesichert?

2. IDENTIFIZIERTE LÜCKEN:
   - Welche Validierungen fehlen?
   - Welche zusätzlichen Checks wären sinnvoll?

3. GESAMMELTE INFORMATIONEN:
   - Welche Validierungen waren erfolgreich?
   - Welche Qualitäts-Kriterien sind erfüllt?

4. NÄCHSTE SCHRITTE:
   - Sollten weitere Validierungen durchgeführt werden?
   - Ist die Antwort bereit für den Nutzer?

5. KONFIDENZ (0-1):
   - Wie sicher bist du, dass die Qualität ausreichend ist?

Antworte in folgendem Format:
ERFÜLLUNG: <0-100>
STATUS: <incomplete|partial|complete>
LÜCKEN:
- <Lücke 1>
GESAMMELT:
- <Info 1>
NÄCHSTE_SCHRITTE:
- <Schritt 1>
KONFIDENZ: <0.0-1.0>
BEGRÜNDUNG: <Deine Reasoning>
"""
    
    async def _call_llm_reflection(self, prompt: str, stage: ReflectionStage) -> str:
        """
        Ruft LLM mit Reflection-Prompt auf
        
        Args:
            prompt: Reflection-Prompt
            stage: Aktuelle Stage
            
        Returns:
            LLM Response-Text
        """
        try:
            if not self.ollama_client:
                logger.debug(f"⚠️ Kein Ollama-Client verfügbar für {stage}")
                return ""
            
            # Import OllamaRequest
            from backend.agents.veritas_ollama_client import OllamaRequest
            
            # Erstelle OllamaRequest
            request = OllamaRequest(
                model="llama3.2:latest",
                prompt=prompt,
                temperature=0.3,  # Niedrig für konsistente Analyse
                max_tokens=800,
                stream=False
            )
            
            # Async Call über Ollama-Client
            response = await self.ollama_client.generate_response(
                request=request,
                stream=False
            )
            
            # Response-Text extrahieren
            if hasattr(response, 'response'):
                return response.response
            elif isinstance(response, dict):
                return response.get('response', response.get('response_text', ''))
            else:
                logger.warning(f"⚠️ Unerwartetes Response-Format: {type(response)}")
                return str(response)
            
        except Exception as e:
            logger.error(f"❌ LLM Reflection Call Error ({stage}): {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _parse_reflection_response(
        self,
        stage: ReflectionStage,
        llm_response: str,
        stage_data: Dict[str, Any]
    ) -> StageReflection:
        """
        Parsed LLM-Response zu strukturiertem StageReflection
        
        Format erwartet:
        ERFÜLLUNG: 75
        STATUS: partial
        LÜCKEN:
        - Lücke 1
        ...
        """
        from datetime import datetime
        
        try:
            lines = llm_response.strip().split('\n')
            
            completion_percent = 50.0
            fulfillment_status = "partial"
            identified_gaps = []
            gathered_info = []
            next_actions = []
            confidence = 0.7
            llm_reasoning = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('ERFÜLLUNG:'):
                    try:
                        completion_percent = float(line.split(':')[1].strip())
                    except:
                        pass
                elif line.startswith('STATUS:'):
                    fulfillment_status = line.split(':')[1].strip().lower()
                elif line.startswith('KONFIDENZ:'):
                    try:
                        confidence = float(line.split(':')[1].strip())
                    except:
                        pass
                elif line.startswith('BEGRÜNDUNG:'):
                    llm_reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('LÜCKEN:'):
                    current_section = 'gaps'
                elif line.startswith('GESAMMELT:'):
                    current_section = 'gathered'
                elif line.startswith('NÄCHSTE_SCHRITTE:'):
                    current_section = 'actions'
                elif line.startswith('- ') and current_section:
                    item = line[2:].strip()
                    if current_section == 'gaps':
                        identified_gaps.append(item)
                    elif current_section == 'gathered':
                        gathered_info.append(item)
                    elif current_section == 'actions':
                        next_actions.append(item)
            
            return StageReflection(
                stage=stage,
                completion_percent=completion_percent,
                fulfillment_status=fulfillment_status,
                identified_gaps=identified_gaps,
                gathered_info=gathered_info,
                confidence=confidence,
                next_actions=next_actions,
                llm_reasoning=llm_reasoning,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"❌ Parse Reflection Error: {e}")
            return self._create_fallback_reflection(stage, stage_data)
    
    def _create_fallback_reflection(
        self,
        stage: ReflectionStage,
        stage_data: Dict[str, Any]
    ) -> StageReflection:
        """Erstellt Fallback-Reflection ohne LLM"""
        from datetime import datetime
        
        return StageReflection(
            stage=stage,
            completion_percent=70.0,
            fulfillment_status="partial",
            identified_gaps=["LLM-Reflection nicht verfügbar"],
            gathered_info=[f"Stage {stage} abgeschlossen"],
            confidence=0.6,
            next_actions=["Fortfahren mit nächster Stage"],
            llm_reasoning="Fallback ohne LLM-Analyse",
            timestamp=datetime.now().isoformat()
        )
    
    def format_reflection_for_display(self, reflection: StageReflection) -> str:
        """
        Formatiert Reflection für Frontend-Display
        
        Returns:
            Markdown-formatierte Reflection
        """
        status_emoji = {
            "incomplete": "🔴",
            "partial": "🟡",
            "complete": "🟢"
        }
        
        emoji = status_emoji.get(reflection.fulfillment_status, "⚪")
        
        output = f"""
### {emoji} Stage: {reflection.stage.value.title()}
**Erfüllungsgrad:** {reflection.completion_percent:.0f}% | **Status:** {reflection.fulfillment_status}  
**Konfidenz:** {reflection.confidence:.2f}

#### ✅ Gesammelte Informationen:
{chr(10).join(f"- {info}" for info in reflection.gathered_info) if reflection.gathered_info else "- Keine"}

#### ⚠️ Identifizierte Lücken:
{chr(10).join(f"- {gap}" for gap in reflection.identified_gaps) if reflection.identified_gaps else "- Keine"}

#### 🔜 Nächste Schritte:
{chr(10).join(f"- {action}" for action in reflection.next_actions) if reflection.next_actions else "- Keine"}

**LLM Reasoning:** {reflection.llm_reasoning}
"""
        return output.strip()


# Singleton-Instanz
_reflection_service: Optional[StageReflectionService] = None


def get_reflection_service(ollama_client=None) -> StageReflectionService:
    """
    Holt/erstellt Singleton StageReflectionService
    
    Args:
        ollama_client: Optional VeritasOllamaClient
        
    Returns:
        StageReflectionService Instanz
    """
    global _reflection_service
    
    if _reflection_service is None:
        _reflection_service = StageReflectionService(ollama_client)
    
    return _reflection_service
