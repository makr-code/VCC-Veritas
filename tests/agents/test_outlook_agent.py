"""
Tests for OutlookAgent

Tests email composition, calendar events, task management,
and contact management functionality.
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from backend.agents.outlook_agent import OutlookAgent
from backend.agents.outlook_template_manager import get_outlook_template_manager


class TestOutlookAgent:
    """Test suite for OutlookAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create OutlookAgent instance"""
        return OutlookAgent()
    
    @pytest.fixture
    def template_manager(self):
        """Create OutlookTemplateManager instance"""
        return get_outlook_template_manager()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'template_manager')
        assert hasattr(agent, 'compose_email')
        assert hasattr(agent, 'create_calendar_event')
        assert hasattr(agent, 'create_task')
        assert hasattr(agent, 'create_contact')
    
    def test_template_manager_initialization(self, template_manager):
        """Test template manager initializes correctly"""
        assert template_manager is not None
        templates = template_manager.list_templates()
        assert len(templates) > 0
        assert any(t['name'] == 'email_compose' for t in templates)
    
    def test_read_email_template(self, template_manager):
        """Test reading email_compose template"""
        template = template_manager.read_template('email_compose')
        assert template is not None
        assert template['name'] == 'email_compose'
        assert 'variations' in template
        assert len(template['variations']) > 0
    
    def test_read_calendar_template(self, template_manager):
        """Test reading calendar_event template"""
        template = template_manager.read_template('calendar_event')
        assert template is not None
        assert template['name'] == 'calendar_event'
        assert 'llm_example' in template
    
    @pytest.mark.asyncio
    async def test_compose_formal_email(self, agent):
        """Test composing formal business email"""
        result = await agent.compose_email({
            'template': 'email_compose',
            'variation': 'formal_email',
            'to': 'recipient@company.com',
            'subject': 'Project Update',
            'body': 'This is a formal email regarding the project status.',
            'send': False  # Don't actually send
        })
        
        assert result['status'] == 'success'
        assert 'content' in result
        assert result['type'] == 'email'
    
    @pytest.mark.asyncio
    async def test_compose_meeting_request(self, agent):
        """Test composing meeting request email"""
        result = await agent.compose_email({
            'template': 'email_compose',
            'variation': 'meeting_request',
            'to': 'team@company.com',
            'subject': 'Weekly Team Meeting',
            'body': 'Please join our weekly team meeting.',
            'meeting_time': (datetime.now() + timedelta(days=1)).isoformat(),
            'send': False
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'email'
    
    @pytest.mark.asyncio
    async def test_create_calendar_event(self, agent):
        """Test creating calendar event"""
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        
        result = await agent.create_calendar_event({
            'template': 'calendar_event',
            'variation': 'meeting',
            'title': 'Team Standup',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'location': 'Conference Room A',
            'attendees': ['alice@company.com', 'bob@company.com']
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'calendar_event'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_recurring_event(self, agent):
        """Test creating recurring calendar event"""
        start_time = datetime.now() + timedelta(days=1)
        
        result = await agent.create_calendar_event({
            'template': 'calendar_event',
            'variation': 'recurring_event',
            'title': 'Weekly Team Meeting',
            'start_time': start_time.isoformat(),
            'recurrence': 'weekly',
            'recurrence_pattern': 'Every Monday',
            'end_date': (start_time + timedelta(days=90)).isoformat()
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'calendar_event'
    
    @pytest.mark.asyncio
    async def test_create_task(self, agent):
        """Test creating task"""
        result = await agent.create_task({
            'template': 'task_management',
            'variation': 'simple_task',
            'title': 'Complete project documentation',
            'due_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'priority': 'high',
            'description': 'Write comprehensive documentation for the project'
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'task'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_contact(self, agent):
        """Test creating contact"""
        result = await agent.create_contact({
            'template': 'contact_management',
            'variation': 'business_contact',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@company.com',
            'company': 'ACME Corp',
            'phone': '+1-555-0123',
            'job_title': 'Senior Manager'
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'contact'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_email_with_attachments(self, agent):
        """Test composing email with attachments"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = os.path.join(tmpdir, 'test_document.txt')
            with open(test_file, 'w') as f:
                f.write('Test content')
            
            result = await agent.compose_email({
                'template': 'email_compose',
                'variation': 'formal_email',
                'to': 'recipient@company.com',
                'subject': 'Document Attached',
                'body': 'Please find the document attached.',
                'attachments': [test_file],
                'send': False
            })
            
            assert result['status'] == 'success'
    
    @pytest.mark.asyncio
    async def test_html_email_formatting(self, agent):
        """Test composing HTML formatted email"""
        html_body = """
        <html>
        <body>
        <h1>Project Update</h1>
        <p>This is an <strong>important</strong> update.</p>
        <ul>
        <li>Task 1 completed</li>
        <li>Task 2 in progress</li>
        </ul>
        </body>
        </html>
        """
        
        result = await agent.compose_email({
            'template': 'email_compose',
            'variation': 'newsletter',
            'to': 'team@company.com',
            'subject': 'Monthly Newsletter',
            'body': html_body,
            'format': 'html',
            'send': False
        })
        
        assert result['status'] == 'success'
    
    def test_template_search_by_category(self, template_manager):
        """Test searching templates by category"""
        templates = template_manager.search_templates(category='email_compose')
        assert len(templates) > 0
    
    def test_all_templates_readable(self, template_manager):
        """Test that all templates can be read"""
        templates = template_manager.list_templates()
        for template_info in templates:
            template = template_manager.read_template(template_info['name'])
            assert template is not None
            assert 'variations' in template
            assert len(template['variations']) > 0
    
    def test_template_validation(self, template_manager):
        """Test template validation"""
        template = template_manager.read_template('email_compose')
        assert 'name' in template
        assert 'category' in template
        assert 'variations' in template
        assert 'llm_example' in template
        assert isinstance(template['variations'], list)
    
    @pytest.mark.asyncio
    async def test_all_day_event(self, agent):
        """Test creating all-day event"""
        event_date = datetime.now() + timedelta(days=5)
        
        result = await agent.create_calendar_event({
            'template': 'calendar_event',
            'variation': 'all_day_event',
            'title': 'Company Holiday',
            'date': event_date.isoformat(),
            'all_day': True
        })
        
        assert result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
