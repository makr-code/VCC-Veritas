"""
Checklist Agent for VERITAS
===========================

Specialized agent for generating checklists based on:
- Documents, approvals, measurement reports from ThemisDB
- Regulations (laws, ordinances, judgments, guidelines, DIN, etc.)
- Data from ThemisDB and internet sources
- Ollama LLM for intelligent generation

This agent can be called via:
1. Direct FastAPI endpoint: POST /api/checklist/generate
2. Automatic detection in user queries (intent recognition)

Integration with Argus2 Android App:
- Returns JSON format suitable for mobile consumption
- Provides structured checklist data for display

Author: VERITAS Development Team
Date: December 2025
Version: 1.0
"""
import json
import logging
from typing import Any, Dict, List, Optional

from backend.agents.framework.base_agent import BaseAgent
from backend.database.uds3_integration import get_uds3_client

logger = logging.getLogger(__name__)


class ChecklistAgent(BaseAgent):
    """
    Checklist generation agent for compliance and administrative processes.
    
    Capabilities:
    - Generate checklists from regulations and documents
    - Query ThemisDB for relevant data
    - Query external regulations (laws, DIN standards, etc.)
    - Use Ollama LLM for intelligent checklist creation
    - Return structured JSON format
    
    Features:
    - Combines multiple data sources (ThemisDB + Internet)
    - Considers current regulations and standards
    - Generates actionable checklist items
    - Includes references and legal basis
    - Mobile-friendly JSON output for Argus2 integration
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        ollama_client=None
    ):
        """
        Initialize Checklist Agent.
        
        Args:
            agent_id: Unique agent identifier
            config: Agent configuration dictionary
            ollama_client: Ollama client for LLM integration
        """
        super().__init__(
            agent_id=agent_id,
            config=config or {},
            quality_policy=None,
            enable_monitoring=True
        )
        
        # Initialize UDS3 for ThemisDB access (optional - can be None for testing)
        try:
            self.uds3 = get_uds3_client()
        except Exception as e:
            logger.warning(f"UDS3 client not available: {e}. Agent will work in limited mode.")
            self.uds3 = None
        
        # Store Ollama client
        self.ollama_client = ollama_client
        
        # Default configuration
        self.default_model = config.get("model", "llama3.2") if config else "llama3.2"
        self.temperature = config.get("temperature", 0.3) if config else 0.3
        self.max_tokens = config.get("max_tokens", 2000) if config else 2000
        
        logger.info(
            f"ChecklistAgent initialized (model={self.default_model}, "
            f"temp={self.temperature})"
        )
    
    def get_agent_type(self) -> str:
        """Return agent type identifier."""
        return "checklist"
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "checklist_generation",
            "compliance_checklist",
            "administrative_checklist",
            "regulation_checklist",
            "process_checklist",
            "approval_checklist",
            "construction_checklist",
            "environmental_checklist",
            "safety_checklist",
            "quality_checklist"
        ]
    
    def execute_step(
        self,
        step: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute checklist agent step.
        
        Args:
            step: Step configuration with:
                - step_type: Type of step (generate_checklist, query_data, etc.)
                - step_config: Step-specific configuration
            
            context: Execution context with:
                - plan_id: Research plan ID
                - previous_results: Results from previous steps
        
        Returns:
            Result dictionary with:
                - status: "success" or "error"
                - data: Checklist data (JSON format)
                - confidence_score: 0.0-1.0
                - quality_score: 0.0-1.0
        """
        step_type = step.get("step_type", "unknown")
        step_config = step.get("step_config", {})
        
        logger.info(f"Executing checklist step: {step_type}")
        
        try:
            if step_type == "generate_checklist":
                return self._generate_checklist(step_config, context)
            
            elif step_type == "query_themisdb":
                return self._query_themisdb(step_config, context)
            
            elif step_type == "query_regulations":
                return self._query_regulations(step_config, context)
            
            elif step_type == "combine_sources":
                return self._combine_sources(step_config, context)
            
            else:
                return {
                    "status": "error",
                    "error_message": f"Unknown step type: {step_type}"
                }
        
        except Exception as e:
            logger.error(f"Error executing checklist step: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def generate_checklist(
        self,
        topic: str,
        context: Optional[str] = None,
        checklist_type: str = "general",
        include_regulations: bool = True,
        include_themisdb: bool = True,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        High-level method to generate a checklist.
        
        This is the main entry point for checklist generation.
        
        Args:
            topic: Topic or purpose of the checklist
            context: Additional context information
            checklist_type: Type of checklist (general, compliance, construction, etc.)
            include_regulations: Whether to query regulations
            include_themisdb: Whether to query ThemisDB
            model: LLM model to use (overrides default)
            temperature: Temperature for LLM (overrides default)
            max_tokens: Max tokens for LLM (overrides default)
        
        Returns:
            Dictionary with:
                - status: "success" or "error"
                - checklist: Checklist data in JSON format
                - metadata: Generation metadata
                - sources: Data sources used
        """
        logger.info(f"Generating checklist: topic='{topic}', type='{checklist_type}'")
        
        try:
            # Step 1: Gather data from ThemisDB
            themisdb_data = {}
            if include_themisdb:
                themisdb_data = self._query_themisdb_for_topic(topic, checklist_type)
            
            # Step 2: Query regulations
            regulations_data = {}
            if include_regulations:
                regulations_data = self._query_regulations_for_topic(topic, checklist_type)
            
            # Step 3: Generate checklist using LLM
            checklist_data = self._generate_checklist_with_llm(
                topic=topic,
                context=context,
                checklist_type=checklist_type,
                themisdb_data=themisdb_data,
                regulations_data=regulations_data,
                model=model or self.default_model,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens
            )
            
            return {
                "status": "success",
                "checklist": checklist_data,
                "metadata": {
                    "topic": topic,
                    "checklist_type": checklist_type,
                    "model": model or self.default_model,
                    "sources_used": {
                        "themisdb": include_themisdb,
                        "regulations": include_regulations
                    }
                },
                "sources": self._compile_sources(themisdb_data, regulations_data)
            }
        
        except Exception as e:
            logger.error(f"Error generating checklist: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": str(e),
                "checklist": None
            }
    
    def _generate_checklist(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute checklist generation step."""
        topic = config.get("topic", "")
        checklist_type = config.get("checklist_type", "general")
        context_info = config.get("context", "")
        
        # Use the high-level method
        result = self.generate_checklist(
            topic=topic,
            context=context_info,
            checklist_type=checklist_type,
            include_regulations=config.get("include_regulations", True),
            include_themisdb=config.get("include_themisdb", True),
            model=config.get("model"),
            temperature=config.get("temperature"),
            max_tokens=config.get("max_tokens")
        )
        
        if result["status"] == "success":
            return {
                "status": "success",
                "data": result["checklist"],
                "confidence_score": 0.85,
                "quality_score": 0.88,
                "sources": result.get("sources", [])
            }
        else:
            return {
                "status": "error",
                "error_message": result.get("error_message", "Unknown error")
            }
    
    def _query_themisdb(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Query ThemisDB for documents, approvals, and reports."""
        query = config.get("query", "")
        domain = config.get("domain", "administrative")
        top_k = config.get("top_k", 10)
        
        logger.info(f"Querying ThemisDB: '{query}' (domain={domain})")
        
        try:
            # Check if UDS3 is available
            if not self.uds3 or not hasattr(self.uds3, 'semantic_search'):
                logger.warning("UDS3 semantic_search not available, using fallback")
                return {
                    "status": "success",
                    "data": {"documents": [], "total_results": 0},
                    "confidence_score": 0.0,
                    "quality_score": 0.0,
                    "sources": ["ThemisDB-Unavailable"]
                }
            
            # Query ThemisDB via UDS3
            results = self.uds3.semantic_search(
                query=query,
                top_k=top_k,
                domain=domain
            )
            
            # Format results
            documents = [
                {
                    "id": result.get("id", f"doc_{i}"),
                    "content": result.get("content", ""),
                    "metadata": result.get("metadata", {}),
                    "relevance": result.get("score", 0.0),
                    "source": "ThemisDB",
                    "type": result.get("metadata", {}).get("type", "document")
                }
                for i, result in enumerate(results)
            ]
            
            avg_score = (
                sum(d["relevance"] for d in documents) / len(documents)
                if documents else 0.0
            )
            
            return {
                "status": "success",
                "data": {
                    "documents": documents,
                    "total_results": len(documents)
                },
                "confidence_score": min(avg_score * 1.2, 1.0),
                "quality_score": avg_score,
                "sources": ["ThemisDB"]
            }
        
        except Exception as e:
            logger.error(f"Error querying ThemisDB: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _query_regulations(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query regulations (laws, ordinances, judgments, guidelines, DIN).
        
        This queries both ThemisDB and potentially external sources.
        """
        query = config.get("query", "")
        regulation_types = config.get("regulation_types", ["law", "ordinance", "guideline"])
        
        logger.info(f"Querying regulations: '{query}'")
        
        try:
            # Check if UDS3 is available
            if not self.uds3 or not hasattr(self.uds3, 'semantic_search'):
                logger.warning("UDS3 not available for regulation search")
                return {
                    "status": "success",
                    "data": {"regulations": [], "total_results": 0},
                    "confidence_score": 0.0,
                    "quality_score": 0.0,
                    "sources": []
                }
            
            # Query UDS3 with regulation-specific domain
            results = self.uds3.semantic_search(
                query=query,
                top_k=15,
                domain="legal"
            )
            
            # Filter and categorize by regulation type
            regulations = []
            for i, result in enumerate(results):
                metadata = result.get("metadata", {})
                doc_type = metadata.get("type", "").lower()
                
                # Categorize regulation
                reg_type = "other"
                if "gesetz" in doc_type or "law" in doc_type:
                    reg_type = "law"
                elif "verordnung" in doc_type or "ordinance" in doc_type:
                    reg_type = "ordinance"
                elif "richtlinie" in doc_type or "guideline" in doc_type:
                    reg_type = "guideline"
                elif "din" in doc_type or "iso" in doc_type or "en " in doc_type:
                    reg_type = "standard"
                elif "urteil" in doc_type or "judgment" in doc_type:
                    reg_type = "judgment"
                
                regulations.append({
                    "id": result.get("id", f"reg_{i}"),
                    "title": metadata.get("title", ""),
                    "type": reg_type,
                    "content": result.get("content", ""),
                    "metadata": metadata,
                    "relevance": result.get("score", 0.0),
                    "source": metadata.get("source", "ThemisDB")
                })
            
            avg_score = (
                sum(r["relevance"] for r in regulations) / len(regulations)
                if regulations else 0.0
            )
            
            return {
                "status": "success",
                "data": {
                    "regulations": regulations,
                    "total_results": len(regulations),
                    "by_type": self._group_by_type(regulations)
                },
                "confidence_score": min(avg_score * 1.1, 1.0),
                "quality_score": avg_score,
                "sources": ["ThemisDB-Regulations"]
            }
        
        except Exception as e:
            logger.error(f"Error querying regulations: {e}", exc_info=True)
            return {
                "status": "error",
                "error_message": str(e)
            }
    
    def _combine_sources(
        self,
        config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine data from multiple sources."""
        # Get previous results from context
        previous_results = context.get("previous_results", {})
        
        # Extract data from previous steps
        themisdb_data = previous_results.get("themisdb", {})
        regulations_data = previous_results.get("regulations", {})
        
        # Combine
        combined = {
            "documents": themisdb_data.get("documents", []),
            "regulations": regulations_data.get("regulations", []),
            "total_sources": (
                len(themisdb_data.get("documents", [])) +
                len(regulations_data.get("regulations", []))
            )
        }
        
        return {
            "status": "success",
            "data": combined,
            "confidence_score": 0.85,
            "quality_score": 0.83,
            "sources": ["Combined-ThemisDB-Regulations"]
        }
    
    def _query_themisdb_for_topic(
        self,
        topic: str,
        checklist_type: str
    ) -> Dict[str, Any]:
        """Query ThemisDB for topic-relevant data."""
        logger.info(f"Querying ThemisDB for topic: {topic}")
        
        # Build search query
        search_query = f"{topic} {checklist_type}"
        
        config = {
            "query": search_query,
            "domain": "administrative",
            "top_k": 10
        }
        
        result = self._query_themisdb(config, {})
        
        if result.get("status") == "success":
            return result.get("data", {})
        else:
            logger.warning(f"ThemisDB query failed: {result.get('error_message')}")
            return {}
    
    def _query_regulations_for_topic(
        self,
        topic: str,
        checklist_type: str
    ) -> Dict[str, Any]:
        """Query regulations for topic-relevant data."""
        logger.info(f"Querying regulations for topic: {topic}")
        
        # Build search query
        search_query = f"{topic} {checklist_type}"
        
        config = {
            "query": search_query,
            "regulation_types": ["law", "ordinance", "guideline", "standard"]
        }
        
        result = self._query_regulations(config, {})
        
        if result.get("status") == "success":
            return result.get("data", {})
        else:
            logger.warning(f"Regulations query failed: {result.get('error_message')}")
            return {}
    
    def _generate_checklist_with_llm(
        self,
        topic: str,
        context: Optional[str],
        checklist_type: str,
        themisdb_data: Dict[str, Any],
        regulations_data: Dict[str, Any],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Generate checklist using Ollama LLM.
        
        Returns structured JSON checklist.
        """
        logger.info(f"Generating checklist with LLM (model={model})")
        
        # Build prompt
        prompt = self._build_checklist_prompt(
            topic=topic,
            context=context,
            checklist_type=checklist_type,
            themisdb_data=themisdb_data,
            regulations_data=regulations_data
        )
        
        # Call Ollama if available
        if self.ollama_client and hasattr(self.ollama_client, 'generate'):
            try:
                response = self.ollama_client.generate(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Parse response
                checklist_json = self._parse_llm_response(response)
                return checklist_json
            
            except Exception as e:
                logger.error(f"Error calling Ollama: {e}", exc_info=True)
                # Fallback to template-based checklist
                return self._generate_template_checklist(
                    topic, checklist_type, themisdb_data, regulations_data
                )
        
        else:
            logger.warning("Ollama client not available, using template-based generation")
            return self._generate_template_checklist(
                topic, checklist_type, themisdb_data, regulations_data
            )
    
    def _build_checklist_prompt(
        self,
        topic: str,
        context: Optional[str],
        checklist_type: str,
        themisdb_data: Dict[str, Any],
        regulations_data: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM checklist generation."""
        # Extract relevant information
        documents = themisdb_data.get("documents", [])
        regulations = regulations_data.get("regulations", [])
        
        # Build document summary
        doc_summary = ""
        if documents:
            doc_summary = "\n\nRelevante Dokumente aus ThemisDB:\n"
            for doc in documents[:5]:  # Top 5
                doc_summary += f"- {doc.get('metadata', {}).get('title', 'Dokument')}: "
                doc_summary += f"{doc.get('content', '')[:200]}...\n"
        
        # Build regulation summary
        reg_summary = ""
        if regulations:
            reg_summary = "\n\nGeltende Vorschriften:\n"
            for reg in regulations[:5]:  # Top 5
                reg_summary += f"- {reg.get('title', 'Vorschrift')} ({reg.get('type', 'Typ')}): "
                reg_summary += f"{reg.get('content', '')[:200]}...\n"
        
        # Build full prompt
        prompt = f"""Du bist ein Experte für Verwaltungs- und Compliance-Checklisten.

Erstelle eine detaillierte Checkliste zum Thema: "{topic}"

Art der Checkliste: {checklist_type}
{f'Kontext: {context}' if context else ''}
{doc_summary}
{reg_summary}

WICHTIG: Erstelle die Checkliste im folgenden JSON-Format:

{{
  "title": "Titel der Checkliste",
  "description": "Kurze Beschreibung",
  "checklist_type": "{checklist_type}",
  "categories": [
    {{
      "category_name": "Kategorie 1",
      "items": [
        {{
          "item_id": 1,
          "title": "Aufgabe 1",
          "description": "Detaillierte Beschreibung",
          "required": true,
          "legal_basis": "Rechtsgrundlage (falls zutreffend)",
          "references": ["Quelle 1", "Quelle 2"],
          "priority": "high|medium|low",
          "estimated_duration": "Geschätzte Dauer"
        }}
      ]
    }}
  ],
  "notes": "Wichtige Hinweise",
  "references": ["Quellenangaben"]
}}

Generiere die Checkliste basierend auf den bereitgestellten Daten und geltenden Vorschriften.
Antworte NUR mit dem JSON-Objekt, ohne zusätzlichen Text."""
        
        return prompt
    
    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """
        Parse LLM response to extract JSON checklist.
        
        Args:
            response: Response from Ollama
        
        Returns:
            Parsed checklist JSON
        """
        # Extract text from response
        if isinstance(response, dict):
            text = response.get("response", "") or response.get("text", "")
        elif isinstance(response, str):
            text = response
        else:
            text = str(response)
        
        # Try to find JSON in response
        try:
            # Look for JSON block
            start = text.find("{")
            end = text.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_text = text[start:end]
                checklist = json.loads(json_text)
                return checklist
            else:
                logger.warning("No JSON found in LLM response, using template")
                raise ValueError("No JSON in response")
        
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing LLM response: {e}")
            # Return minimal structure
            return {
                "title": "Generierte Checkliste",
                "description": "Fehler beim Parsen der LLM-Antwort",
                "checklist_type": "general",
                "categories": [],
                "notes": f"Fehler: {str(e)}",
                "references": []
            }
    
    def _generate_template_checklist(
        self,
        topic: str,
        checklist_type: str,
        themisdb_data: Dict[str, Any],
        regulations_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate checklist using template (fallback when LLM is unavailable).
        
        Args:
            topic: Checklist topic
            checklist_type: Type of checklist
            themisdb_data: Data from ThemisDB
            regulations_data: Regulations data
        
        Returns:
            Template-based checklist JSON
        """
        logger.info("Generating template-based checklist")
        
        documents = themisdb_data.get("documents", [])
        regulations = regulations_data.get("regulations", [])
        
        # Build categories based on data
        categories = []
        
        # Category 1: Document review
        if documents:
            doc_items = []
            for i, doc in enumerate(documents[:5], 1):
                doc_items.append({
                    "item_id": i,
                    "title": f"Prüfung: {doc.get('metadata', {}).get('title', 'Dokument')}",
                    "description": doc.get("content", "")[:200],
                    "required": True,
                    "legal_basis": "",
                    "references": [doc.get("source", "ThemisDB")],
                    "priority": "high",
                    "estimated_duration": "30 Minuten"
                })
            
            categories.append({
                "category_name": "Dokumentenprüfung",
                "items": doc_items
            })
        
        # Category 2: Regulatory compliance
        if regulations:
            reg_items = []
            for i, reg in enumerate(regulations[:5], 1):
                reg_items.append({
                    "item_id": i + 100,
                    "title": f"Compliance-Check: {reg.get('title', 'Vorschrift')}",
                    "description": f"Prüfung der Einhaltung: {reg.get('content', '')[:200]}",
                    "required": True,
                    "legal_basis": reg.get("title", ""),
                    "references": [reg.get("source", "")],
                    "priority": "high",
                    "estimated_duration": "45 Minuten"
                })
            
            categories.append({
                "category_name": "Vorschriftenkonformität",
                "items": reg_items
            })
        
        # Default category if no data
        if not categories:
            categories.append({
                "category_name": "Allgemeine Prüfung",
                "items": [
                    {
                        "item_id": 1,
                        "title": f"Prüfung: {topic}",
                        "description": "Allgemeine Prüfung und Bewertung",
                        "required": True,
                        "legal_basis": "",
                        "references": [],
                        "priority": "medium",
                        "estimated_duration": "1 Stunde"
                    }
                ]
            })
        
        return {
            "title": f"Checkliste: {topic}",
            "description": f"{checklist_type.capitalize()}-Checkliste für {topic}",
            "checklist_type": checklist_type,
            "categories": categories,
            "notes": "Diese Checkliste wurde auf Basis verfügbarer Daten generiert.",
            "references": list(set(
                [doc.get("source", "ThemisDB") for doc in documents] +
                [reg.get("source", "") for reg in regulations]
            ))
        }
    
    def _group_by_type(self, regulations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group regulations by type and count them."""
        by_type = {}
        for reg in regulations:
            reg_type = reg.get("type", "other")
            by_type[reg_type] = by_type.get(reg_type, 0) + 1
        return by_type
    
    def _compile_sources(
        self,
        themisdb_data: Dict[str, Any],
        regulations_data: Dict[str, Any]
    ) -> List[str]:
        """Compile list of data sources used."""
        sources = []
        
        if themisdb_data and themisdb_data.get("documents"):
            sources.append("ThemisDB-Documents")
        
        if regulations_data and regulations_data.get("regulations"):
            sources.append("ThemisDB-Regulations")
        
        return sources or ["Template-Based"]


def create_checklist_agent(
    agent_id: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    ollama_client=None
) -> ChecklistAgent:
    """
    Factory function to create Checklist Agent.
    
    Args:
        agent_id: Optional agent identifier
        config: Optional configuration dictionary
        ollama_client: Optional Ollama client
    
    Returns:
        ChecklistAgent instance
    """
    return ChecklistAgent(
        agent_id=agent_id,
        config=config,
        ollama_client=ollama_client
    )
