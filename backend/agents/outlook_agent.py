"""
Outlook Agent - Email, Calendar, Task, and Contact Management

This agent handles Outlook operations including email composition,
calendar event creation, task management, and contact management.

Capabilities:
- Compose and send emails (formal, informal, meeting requests, status updates)
- Create calendar events (appointments, meetings, recurring events)
- Manage tasks (simple tasks, reminders, delegated tasks)
- Add and manage contacts (business and personal)
- Integration with Microsoft Graph API and Exchange Server
"""

import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email libraries
try:
    import smtplib
    from email import encoders
    from email.mime.base import MIMEBase
    SMTP_AVAILABLE = True
except ImportError:
    SMTP_AVAILABLE = False
    logging.warning("smtplib not available - email sending disabled")

# Microsoft Graph API (optional)
try:
    import msal
    import requests
    GRAPH_API_AVAILABLE = True
except ImportError:
    GRAPH_API_AVAILABLE = False
    logging.warning("msal/requests not available - Graph API disabled")

from backend.agents.outlook_template_manager import get_outlook_template_manager

logger = logging.getLogger(__name__)


class OutlookAgent:
    """
    Agent for Outlook Operations
    
    Handles email, calendar, tasks, and contacts.
    """
    
    def __init__(self, llm_service=None, output_dir: Optional[Path] = None):
        """
        Initialize Outlook Agent
        
        Args:
            llm_service: Optional LLM service for content generation
            output_dir: Directory for output files
        """
        self.llm_service = llm_service
        self.template_manager = get_outlook_template_manager()
        
        if output_dir is None:
            self.output_dir = Path("./output/outlook")
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration (should be loaded from config file in production)
        self.config = {
            'smtp_server': None,
            'smtp_port': 587,
            'smtp_user': None,
            'smtp_password': None,
            'graph_api_client_id': None,
            'graph_api_client_secret': None,
            'graph_api_tenant_id': None
        }
        
        logger.info("OutlookAgent initialized")
    
    async def compose_email(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compose an email
        
        Args:
            request: {
                'template': template name (e.g., 'email_compose'),
                'variation': variation ID (e.g., 'formal_email'),
                'to': recipient email(s) (string or list),
                'cc': optional CC recipients,
                'subject': email subject,
                'body': email body (or use LLM to generate),
                'attachments': optional list of file paths,
                'send': bool, whether to send immediately
            }
            
        Returns:
            Result dictionary with email details
        """
        try:
            template_id = request.get('template', 'email_compose')
            variation_id = request.get('variation', 'formal_email')
            
            # Load template
            template = self.template_manager.read_template(template_id)
            if not template:
                return {'success': False, 'error': f'Template {template_id} not found'}
            
            # Get variation details
            variation = self._get_template_variation(template, variation_id)
            if not variation:
                return {'success': False, 'error': f'Variation {variation_id} not found'}
            
            # Extract email details
            to_addr = request.get('to')
            cc_addr = request.get('cc', [])
            subject = request.get('subject', '')
            body = request.get('body', '')
            attachments = request.get('attachments', [])
            send_now = request.get('send', False)
            
            # Generate body with LLM if needed
            if not body and self.llm_service:
                body = await self._generate_email_body(variation, request)
            
            # Create email message
            email_data = {
                'to': to_addr,
                'cc': cc_addr,
                'subject': subject,
                'body': body,
                'attachments': attachments,
                'template': template_id,
                'variation': variation_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Save email as JSON
            output_file = self.output_dir / f"email_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(email_data, f, indent=2, ensure_ascii=False)
            
            # Send email if requested
            if send_now:
                send_result = await self._send_email(email_data)
                email_data['sent'] = send_result['success']
                email_data['send_error'] = send_result.get('error')
            
            logger.info(f"Email composed: {output_file}")
            
            return {
                'success': True,
                'email_data': email_data,
                'output_file': str(output_file),
                'sent': send_now
            }
            
        except Exception as e:
            logger.error(f"Error composing email: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_calendar_event(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a calendar event
        
        Args:
            request: {
                'template': template name (e.g., 'calendar_event'),
                'variation': variation ID (e.g., 'meeting_with_attendees'),
                'subject': event subject,
                'start_time': start datetime (ISO format or datetime object),
                'end_time': end datetime,
                'location': optional location,
                'attendees': optional list of attendee emails,
                'description': optional event description,
                'recurrence': optional recurrence pattern
            }
            
        Returns:
            Result dictionary with event details
        """
        try:
            template_id = request.get('template', 'calendar_event')
            variation_id = request.get('variation', 'simple_appointment')
            
            # Load template
            template = self.template_manager.read_template(template_id)
            if not template:
                return {'success': False, 'error': f'Template {template_id} not found'}
            
            # Extract event details
            subject = request.get('subject', 'Meeting')
            start_time = request.get('start_time')
            end_time = request.get('end_time')
            location = request.get('location', '')
            attendees = request.get('attendees', [])
            description = request.get('description', '')
            recurrence = request.get('recurrence')
            
            # Parse datetime if string
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time)
            
            # Create event data
            event_data = {
                'subject': subject,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'location': location,
                'attendees': attendees,
                'description': description,
                'recurrence': recurrence,
                'template': template_id,
                'variation': variation_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Save event as ICS file
            ics_content = self._generate_ics(event_data)
            output_file = self.output_dir / f"event_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(ics_content)
            
            # Also save as JSON
            json_file = output_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(event_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Calendar event created: {output_file}")
            
            return {
                'success': True,
                'event_data': event_data,
                'output_file': str(output_file),
                'ics_file': str(output_file),
                'json_file': str(json_file)
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_task(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a task
        
        Args:
            request: {
                'template': template name (e.g., 'task'),
                'variation': variation ID (e.g., 'simple_task'),
                'title': task title,
                'due_date': optional due date,
                'priority': optional priority (high, normal, low),
                'assignee': optional assignee email,
                'description': optional task description,
                'reminder': optional reminder datetime
            }
            
        Returns:
            Result dictionary with task details
        """
        try:
            template_id = request.get('template', 'task')
            variation_id = request.get('variation', 'simple_task')
            
            # Load template
            template = self.template_manager.read_template(template_id)
            if not template:
                return {'success': False, 'error': f'Template {template_id} not found'}
            
            # Extract task details
            title = request.get('title', 'New Task')
            due_date = request.get('due_date')
            priority = request.get('priority', 'normal')
            assignee = request.get('assignee')
            description = request.get('description', '')
            reminder = request.get('reminder')
            
            # Parse datetime if string
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date)
            if isinstance(reminder, str):
                reminder = datetime.fromisoformat(reminder)
            
            # Create task data
            task_data = {
                'title': title,
                'due_date': due_date.isoformat() if due_date else None,
                'priority': priority,
                'assignee': assignee,
                'description': description,
                'reminder': reminder.isoformat() if reminder else None,
                'status': 'not_started',
                'template': template_id,
                'variation': variation_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Save task as JSON
            output_file = self.output_dir / f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Task created: {output_file}")
            
            return {
                'success': True,
                'task_data': task_data,
                'output_file': str(output_file)
            }
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return {'success': False, 'error': str(e)}
    
    async def add_contact(
        self,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add a contact
        
        Args:
            request: {
                'template': template name (e.g., 'contact'),
                'variation': variation ID (e.g., 'business_contact'),
                'name': contact name,
                'email': email address,
                'phone': optional phone number,
                'company': optional company name,
                'job_title': optional job title,
                'address': optional address
            }
            
        Returns:
            Result dictionary with contact details
        """
        try:
            template_id = request.get('template', 'contact')
            variation_id = request.get('variation', 'business_contact')
            
            # Load template
            template = self.template_manager.read_template(template_id)
            if not template:
                return {'success': False, 'error': f'Template {template_id} not found'}
            
            # Extract contact details
            contact_data = {
                'name': request.get('name', ''),
                'email': request.get('email', ''),
                'phone': request.get('phone', ''),
                'company': request.get('company', ''),
                'job_title': request.get('job_title', ''),
                'address': request.get('address', ''),
                'template': template_id,
                'variation': variation_id,
                'created_at': datetime.now().isoformat()
            }
            
            # Generate VCF (vCard) format
            vcf_content = self._generate_vcf(contact_data)
            output_file = self.output_dir / f"contact_{datetime.now().strftime('%Y%m%d_%H%M%S')}.vcf"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(vcf_content)
            
            # Also save as JSON
            json_file = output_file.with_suffix('.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(contact_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Contact added: {output_file}")
            
            return {
                'success': True,
                'contact_data': contact_data,
                'output_file': str(output_file),
                'vcf_file': str(output_file),
                'json_file': str(json_file)
            }
            
        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_template_variation(self, template: Dict, variation_id: str) -> Optional[Dict]:
        """Get specific template variation"""
        for category in template.get('templates', []):
            for variation in category.get('variations', []):
                if variation.get('id') == variation_id:
                    return variation
        return None
    
    async def _generate_email_body(self, variation: Dict, request: Dict) -> str:
        """Generate email body using LLM"""
        # Placeholder - would use LLM service in production
        return f"Email body for {variation.get('name', 'email')}"
    
    async def _send_email(self, email_data: Dict) -> Dict[str, Any]:
        """Send email via SMTP or Graph API"""
        if not SMTP_AVAILABLE:
            return {'success': False, 'error': 'SMTP not available'}
        
        # Placeholder - would send actual email in production
        logger.info(f"Email sending simulated for: {email_data.get('to')}")
        return {'success': True, 'message': 'Email sent (simulated)'}
    
    def _generate_ics(self, event_data: Dict) -> str:
        """Generate ICS calendar file content"""
        ics = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Outlook Agent//EN",
            "BEGIN:VEVENT",
            f"SUMMARY:{event_data.get('subject', 'Event')}",
            f"DTSTART:{event_data.get('start_time', '').replace('-', '').replace(':', '')}",
            f"DTEND:{event_data.get('end_time', '').replace('-', '').replace(':', '')}",
            f"LOCATION:{event_data.get('location', '')}",
            f"DESCRIPTION:{event_data.get('description', '')}",
            "END:VEVENT",
            "END:VCALENDAR"
        ]
        return '\n'.join(ics)
    
    def _generate_vcf(self, contact_data: Dict) -> str:
        """Generate VCF (vCard) contact file content"""
        vcf = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"FN:{contact_data.get('name', '')}",
            f"EMAIL:{contact_data.get('email', '')}",
            f"TEL:{contact_data.get('phone', '')}",
            f"ORG:{contact_data.get('company', '')}",
            f"TITLE:{contact_data.get('job_title', '')}",
            f"ADR:{contact_data.get('address', '')}",
            "END:VCARD"
        ]
        return '\n'.join(vcf)
