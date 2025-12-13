"""
OneNote Agent - Note Creation and Knowledge Management

This agent handles OneNote operations including creating structured notes,
organizing content in notebooks/sections/pages, and managing knowledge.

Capabilities:
- Create meeting notes with structured format
- Generate project notes and tracking pages
- Create research notes with citations
- Build personal knowledge bases
- Create interactive checklists
- Support for rich text, tables, images, and tags
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# HTML generation for OneNote
try:
    from html import escape as html_escape
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logging.warning("HTML not available - OneNote formatting disabled")

# Microsoft Graph API (optional)
try:
    import requests
    GRAPH_API_AVAILABLE = True
except ImportError:
    GRAPH_API_AVAILABLE = False
    logging.warning("requests not available - Graph API disabled")

from backend.agents.onenote_template_manager import get_onenote_template_manager

logger = logging.getLogger(__name__)


class OneNoteAgent:
    """
    Agent for OneNote Operations
    
    Creates and manages notes in OneNote format.
    """
    
    def __init__(self, llm_service=None, output_dir: Optional[Path] = None):
        """
        Initialize OneNote Agent
        
        Args:
            llm_service: Optional LLM service for content generation
            output_dir: Directory for output files
        """
        self.llm_service = llm_service
        self.template_manager = get_onenote_template_manager()
        
        if output_dir is None:
            self.output_dir = Path("./output/onenote")
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration
        self.config = {
            'graph_api_client_id': None,
            'graph_api_client_secret': None,
            'graph_api_tenant_id': None
        }
        
        logger.info("OneNoteAgent initialized")
    
    async def create_note(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a OneNote page
        
        Args:
            request: {
                'template': template name (e.g., 'meeting_notes'),
                'variation': variation ID (e.g., 'standup_notes'),
                'title': page title,
                'content': note content (or use template structure),
                'notebook': notebook name,
                'section': section name,
                'tags': optional list of tags,
                'metadata': optional metadata dict
            }
            
        Returns:
            Result dictionary with note details
        """
        try:
            template_id = request.get('template', 'meeting_notes')
            variation_id = request.get('variation', 'formal_meeting_minutes')
            
            # Load template
            template = self.template_manager.read_template(template_id)
            if not template:
                return {'success': False, 'error': f'Template {template_id} not found'}
            
            # Get variation details
            variation = self._get_template_variation(template, variation_id)
            if not variation:
                return {'success': False, 'error': f'Variation {variation_id} not found'}
            
            # Extract note details
            title = request.get('title', 'Untitled Note')
            content = request.get('content', {})
            notebook = request.get('notebook', 'My Notebook')
            section = request.get('section', 'General')
            tags = request.get('tags', [])
            metadata = request.get('metadata', {})
            
            # Generate note structure
            note_html = await self._generate_note_html(
                template_id, variation, title, content, metadata
            )
            
            # Create note data
            note_data = {
                'title': title,
                'notebook': notebook,
                'section': section,
                'tags': tags,
                'metadata': metadata,
                'template': template_id,
                'variation': variation_id,
                'created_at': datetime.now().isoformat(),
                'html_content': note_html
            }
            
            # Save note as HTML
            output_file = self.output_dir / f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(note_html)
            
            # Also save as JSON
            json_file = output_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"OneNote page created: {output_file}")
            
            return {
                'success': True,
                'note_data': note_data,
                'output_file': str(output_file),
                'html_file': str(output_file),
                'json_file': str(json_file)
            }
            
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_meeting_notes(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create structured meeting notes
        
        Args:
            request: {
                'meeting_title': title of meeting,
                'date': meeting date,
                'attendees': list of attendees,
                'agenda': list of agenda items,
                'discussion': discussion notes,
                'decisions': list of decisions,
                'action_items': list of action items with owners,
                'variation': template variation
            }
            
        Returns:
            Result dictionary with note details
        """
        content = {
            'meeting_title': request.get('meeting_title', ''),
            'date': request.get('date', datetime.now().strftime('%Y-%m-%d')),
            'attendees': request.get('attendees', []),
            'agenda': request.get('agenda', []),
            'discussion': request.get('discussion', ''),
            'decisions': request.get('decisions', []),
            'action_items': request.get('action_items', [])
        }
        
        request['template'] = 'meeting_notes'
        request['content'] = content
        
        return await self.create_note(request)
    
    async def create_project_notes(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create project documentation
        
        Args:
            request: {
                'project_name': name of project,
                'status': current status,
                'milestones': list of milestones,
                'tasks': list of tasks,
                'risks': list of risks,
                'notes': additional notes,
                'variation': template variation
            }
            
        Returns:
            Result dictionary with note details
        """
        content = {
            'project_name': request.get('project_name', ''),
            'status': request.get('status', 'Active'),
            'milestones': request.get('milestones', []),
            'tasks': request.get('tasks', []),
            'risks': request.get('risks', []),
            'notes': request.get('notes', '')
        }
        
        request['template'] = 'project_notes'
        request['content'] = content
        
        return await self.create_note(request)
    
    async def create_checklist(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create interactive checklist
        
        Args:
            request: {
                'title': checklist title,
                'items': list of checklist items,
                'variation': template variation
            }
            
        Returns:
            Result dictionary with note details
        """
        content = {
            'title': request.get('title', 'Checklist'),
            'items': request.get('items', [])
        }
        
        request['template'] = 'checklist'
        request['content'] = content
        
        return await self.create_note(request)
    
    def _get_template_variation(self, template: Dict, variation_id: str) -> Optional[Dict]:
        """Get specific template variation"""
        for category in template.get('templates', []):
            for variation in category.get('variations', []):
                if variation.get('id') == variation_id:
                    return variation
        return None
    
    async def _generate_note_html(
        self,
        template_id: str,
        variation: Dict,
        title: str,
        content: Dict,
        metadata: Dict
    ) -> str:
        """
        Generate HTML content for OneNote page
        
        Args:
            template_id: Template identifier
            variation: Template variation
            title: Page title
            content: Content dictionary
            metadata: Metadata dictionary
            
        Returns:
            HTML string
        """
        if not HTML_AVAILABLE:
            return "<html><body><h1>HTML generation not available</h1></body></html>"
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta charset="UTF-8">',
            f'<title>{html_escape(title)}</title>',
            '<style>',
            self._get_note_styles(),
            '</style>',
            '</head>',
            '<body>',
            f'<h1>{html_escape(title)}</h1>',
            f'<p class="metadata">Created: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>'
        ]
        
        # Generate content based on template type
        if template_id == 'meeting_notes':
            html_parts.extend(self._generate_meeting_notes_html(content))
        elif template_id == 'project_notes':
            html_parts.extend(self._generate_project_notes_html(content))
        elif template_id == 'checklist':
            html_parts.extend(self._generate_checklist_html(content))
        elif template_id == 'research_notes':
            html_parts.extend(self._generate_research_notes_html(content))
        else:
            html_parts.extend(self._generate_generic_html(content))
        
        html_parts.extend([
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def _get_note_styles(self) -> str:
        """Get CSS styles for note"""
        return """
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 20px auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 25px; }
            h3 { color: #7f8c8d; }
            .metadata { color: #95a5a6; font-size: 0.9em; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #f2f2f2; }
            ul, ol { margin: 10px 0; padding-left: 30px; }
            .checklist { list-style-type: none; }
            .checklist li:before { content: '☐ '; font-size: 1.2em; }
            .action-item { background-color: #fff3cd; padding: 10px; margin: 5px 0; border-left: 3px solid #ffc107; }
            .decision { background-color: #d4edda; padding: 10px; margin: 5px 0; border-left: 3px solid #28a745; }
            .risk { background-color: #f8d7da; padding: 10px; margin: 5px 0; border-left: 3px solid #dc3545; }
        """
    
    def _generate_meeting_notes_html(self, content: Dict) -> List[str]:
        """Generate HTML for meeting notes"""
        html = []
        
        if content.get('date'):
            html.append(f"<p><strong>Date:</strong> {html_escape(str(content['date']))}</p>")
        
        if content.get('attendees'):
            html.append("<h2>Attendees</h2><ul>")
            for attendee in content['attendees']:
                html.append(f"<li>{html_escape(str(attendee))}</li>")
            html.append("</ul>")
        
        if content.get('agenda'):
            html.append("<h2>Agenda</h2><ol>")
            for item in content['agenda']:
                html.append(f"<li>{html_escape(str(item))}</li>")
            html.append("</ol>")
        
        if content.get('discussion'):
            html.append(f"<h2>Discussion</h2><p>{html_escape(str(content['discussion']))}</p>")
        
        if content.get('decisions'):
            html.append("<h2>Decisions</h2>")
            for decision in content['decisions']:
                html.append(f'<div class="decision">{html_escape(str(decision))}</div>')
        
        if content.get('action_items'):
            html.append("<h2>Action Items</h2>")
            for action in content['action_items']:
                if isinstance(action, dict):
                    owner = action.get('owner', 'Unassigned')
                    task = action.get('task', '')
                    html.append(f'<div class="action-item"><strong>{html_escape(owner)}:</strong> {html_escape(task)}</div>')
                else:
                    html.append(f'<div class="action-item">{html_escape(str(action))}</div>')
        
        return html
    
    def _generate_project_notes_html(self, content: Dict) -> List[str]:
        """Generate HTML for project notes"""
        html = []
        
        if content.get('status'):
            html.append(f"<p><strong>Status:</strong> {html_escape(str(content['status']))}</p>")
        
        if content.get('milestones'):
            html.append("<h2>Milestones</h2><ul>")
            for milestone in content['milestones']:
                html.append(f"<li>{html_escape(str(milestone))}</li>")
            html.append("</ul>")
        
        if content.get('tasks'):
            html.append("<h2>Tasks</h2><ul>")
            for task in content['tasks']:
                html.append(f"<li>{html_escape(str(task))}</li>")
            html.append("</ul>")
        
        if content.get('risks'):
            html.append("<h2>Risks</h2>")
            for risk in content['risks']:
                html.append(f'<div class="risk">{html_escape(str(risk))}</div>')
        
        if content.get('notes'):
            html.append(f"<h2>Notes</h2><p>{html_escape(str(content['notes']))}</p>")
        
        return html
    
    def _generate_checklist_html(self, content: Dict) -> List[str]:
        """Generate HTML for checklist"""
        html = ["<ul class='checklist'>"]
        
        for item in content.get('items', []):
            html.append(f"<li>{html_escape(str(item))}</li>")
        
        html.append("</ul>")
        return html
    
    def _generate_research_notes_html(self, content: Dict) -> List[str]:
        """Generate HTML for research notes"""
        return self._generate_generic_html(content)
    
    def _generate_generic_html(self, content: Dict) -> List[str]:
        """Generate generic HTML for any content"""
        html = []
        
        for key, value in content.items():
            if isinstance(value, list):
                html.append(f"<h2>{html_escape(str(key).replace('_', ' ').title())}</h2><ul>")
                for item in value:
                    html.append(f"<li>{html_escape(str(item))}</li>")
                html.append("</ul>")
            elif isinstance(value, dict):
                html.append(f"<h2>{html_escape(str(key).replace('_', ' ').title())}</h2>")
                html.extend(self._generate_generic_html(value))
            else:
                html.append(f"<p><strong>{html_escape(str(key).replace('_', ' ').title())}:</strong> {html_escape(str(value))}</p>")
        
        return html
