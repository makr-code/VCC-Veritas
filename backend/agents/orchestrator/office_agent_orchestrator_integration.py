"""
Office Agent Orchestrator Integration
=====================================

Integrates PowerPoint, Excel/Table, Outlook, and OneNote agents with the AgentOrchestrator.
Uses YAML-based intent recognition to route requests to appropriate agents.

Author: VERITAS System
Date: 2025-12-13
Version: 1.0
"""

import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from backend.agents.orchestrator.intent_recognition_manager import get_intent_manager
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
from backend.agents.excel_table_agent import ExcelTableAgent
from backend.agents.outlook_agent import OutlookAgent
from backend.agents.onenote_agent import OneNoteAgent

logger = logging.getLogger(__name__)


class OfficeAgentOrchestrator:
    """
    Orchestrates Office-related agent requests using intent recognition.
    
    Capabilities:
    - PowerPoint presentations with shapes and diagrams
    - Excel tables with multi-format export
    - Outlook email, calendar, tasks, contacts
    - OneNote meeting notes and knowledge management
    """
    
    def __init__(self):
        """Initialize the Office Agent Orchestrator"""
        self.intent_manager = get_intent_manager()
        
        # Initialize agents
        self.presentation_agent = PresentationCanvasAgent()
        self.table_agent = ExcelTableAgent()
        self.outlook_agent = OutlookAgent()
        self.onenote_agent = OneNoteAgent()
        
        logger.info("✅ Office Agent Orchestrator initialized")
    
    async def process_request(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user request and route to appropriate agent.
        
        Args:
            query: User query/request
            context: Optional context data
            
        Returns:
            Dict with result from the appropriate agent
        """
        try:
            # Step 1: Recognize intent
            matches = self.intent_manager.recognize_intent(query)
            
            if not matches:
                return {
                    "success": False,
                    "error": "Could not recognize intent from query",
                    "query": query
                }
            
            # Use highest confidence match
            best_match = matches[0]
            content_type = best_match.get("content_type")
            template_category = best_match.get("template_category")
            confidence = best_match.get("confidence", 0.0)
            llm_steps = best_match.get("llm_steps", [])
            
            logger.info(f"🎯 Intent recognized: {content_type}/{template_category} (confidence: {confidence:.2f})")
            
            # Step 2: Route to appropriate agent
            result = None
            
            if content_type == "presentation":
                result = await self._handle_presentation_request(
                    query, template_category, llm_steps, context
                )
            elif content_type == "table":
                result = await self._handle_table_request(
                    query, template_category, llm_steps, context
                )
            elif content_type == "outlook":
                result = await self._handle_outlook_request(
                    query, template_category, llm_steps, context
                )
            elif content_type == "onenote":
                result = await self._handle_onenote_request(
                    query, template_category, llm_steps, context
                )
            else:
                return {
                    "success": False,
                    "error": f"Unsupported content type: {content_type}",
                    "content_type": content_type
                }
            
            # Add metadata to result
            result["intent"] = {
                "content_type": content_type,
                "template_category": template_category,
                "confidence": confidence,
                "llm_steps": llm_steps
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing request: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def _handle_presentation_request(
        self,
        query: str,
        template_category: str,
        llm_steps: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle PowerPoint presentation requests"""
        try:
            logger.info(f"📊 Creating presentation: {template_category}")
            
            # Use template-based approach
            request_data = {
                "template": template_category,
                "query": query,
                "context": context or {}
            }
            
            result = await self.presentation_agent.generate_from_template(request_data)
            
            return {
                "success": True,
                "agent": "PowerPointAgent",
                "template_category": template_category,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Presentation generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "PowerPointAgent"
            }
    
    async def _handle_table_request(
        self,
        query: str,
        template_category: str,
        llm_steps: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle Excel/Table requests"""
        try:
            logger.info(f"📋 Creating table: {template_category}")
            
            # Extract output format from context or default to excel
            output_format = (context or {}).get("output_format", "excel")
            
            request_data = {
                "template": template_category,
                "query": query,
                "output_format": output_format,
                "context": context or {}
            }
            
            result = await self.table_agent.generate_table(request_data)
            
            return {
                "success": True,
                "agent": "ExcelTableAgent",
                "template_category": template_category,
                "output_format": output_format,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Table generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "ExcelTableAgent"
            }
    
    async def _handle_outlook_request(
        self,
        query: str,
        template_category: str,
        llm_steps: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle Outlook requests"""
        try:
            logger.info(f"📧 Creating Outlook item: {template_category}")
            
            request_data = {
                "template": template_category,
                "query": query,
                "context": context or {}
            }
            
            # Route to appropriate Outlook method
            if template_category == "email_compose":
                result = await self.outlook_agent.compose_email(request_data)
            elif template_category == "calendar_event":
                result = await self.outlook_agent.create_calendar_event(request_data)
            elif template_category == "task_management":
                result = await self.outlook_agent.create_task(request_data)
            elif template_category == "contact_management":
                result = await self.outlook_agent.create_contact(request_data)
            else:
                result = await self.outlook_agent.process_request(request_data)
            
            return {
                "success": True,
                "agent": "OutlookAgent",
                "template_category": template_category,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ Outlook processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "OutlookAgent"
            }
    
    async def _handle_onenote_request(
        self,
        query: str,
        template_category: str,
        llm_steps: List[str],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle OneNote requests"""
        try:
            logger.info(f"📝 Creating OneNote note: {template_category}")
            
            request_data = {
                "template": template_category,
                "query": query,
                "context": context or {}
            }
            
            # Route to appropriate OneNote method
            if template_category == "meeting_notes":
                result = await self.onenote_agent.create_meeting_notes(request_data)
            elif template_category == "project_notes":
                result = await self.onenote_agent.create_project_notes(request_data)
            elif template_category == "checklist":
                result = await self.onenote_agent.create_checklist(request_data)
            elif template_category == "knowledge_base":
                result = await self.onenote_agent.create_knowledge_article(request_data)
            elif template_category == "research_notes":
                result = await self.onenote_agent.create_research_notes(request_data)
            else:
                result = await self.onenote_agent.create_note(request_data)
            
            return {
                "success": True,
                "agent": "OneNoteAgent",
                "template_category": template_category,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"❌ OneNote processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "OneNoteAgent"
            }
    
    def get_supported_intents(self) -> List[Dict[str, Any]]:
        """Get list of supported intents/templates"""
        return self.intent_manager.list_all_templates()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            "presentation_agent": {
                "available": self.presentation_agent is not None,
                "capabilities": ["shapes", "diagrams", "flowcharts", "org_charts"]
            },
            "table_agent": {
                "available": self.table_agent is not None,
                "capabilities": ["excel", "csv", "word_tables", "powerpoint_tables"]
            },
            "outlook_agent": {
                "available": self.outlook_agent is not None,
                "capabilities": ["email", "calendar", "tasks", "contacts"]
            },
            "onenote_agent": {
                "available": self.onenote_agent is not None,
                "capabilities": ["meeting_notes", "project_notes", "checklists", "knowledge_base"]
            }
        }


# Singleton instance
_office_orchestrator_instance = None


def get_office_orchestrator() -> OfficeAgentOrchestrator:
    """Get singleton instance of OfficeAgentOrchestrator"""
    global _office_orchestrator_instance
    if _office_orchestrator_instance is None:
        _office_orchestrator_instance = OfficeAgentOrchestrator()
    return _office_orchestrator_instance
