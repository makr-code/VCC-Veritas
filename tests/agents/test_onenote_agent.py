"""
Tests for OneNoteAgent

Tests meeting notes, project documentation, checklists,
knowledge base, and research notes functionality.
"""

import pytest
import os
import tempfile
from datetime import datetime
from backend.agents.onenote_agent import OneNoteAgent
from backend.agents.onenote_template_manager import get_onenote_template_manager


class TestOneNoteAgent:
    """Test suite for OneNoteAgent"""
    
    @pytest.fixture
    def agent(self):
        """Create OneNoteAgent instance"""
        return OneNoteAgent()
    
    @pytest.fixture
    def template_manager(self):
        """Create OneNoteTemplateManager instance"""
        return get_onenote_template_manager()
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert hasattr(agent, 'template_manager')
        assert hasattr(agent, 'create_meeting_notes')
        assert hasattr(agent, 'create_project_notes')
        assert hasattr(agent, 'create_checklist')
        assert hasattr(agent, 'create_knowledge_base_article')
        assert hasattr(agent, 'create_research_notes')
    
    def test_template_manager_initialization(self, template_manager):
        """Test template manager initializes correctly"""
        assert template_manager is not None
        templates = template_manager.list_templates()
        assert len(templates) > 0
        assert any(t['name'] == 'meeting_notes' for t in templates)
    
    def test_read_meeting_notes_template(self, template_manager):
        """Test reading meeting_notes template"""
        template = template_manager.read_template('meeting_notes')
        assert template is not None
        assert template['name'] == 'meeting_notes'
        assert 'variations' in template
        assert len(template['variations']) > 0
    
    def test_read_checklist_template(self, template_manager):
        """Test reading checklist template"""
        template = template_manager.read_template('checklist')
        assert template is not None
        assert template['name'] == 'checklist'
        assert 'llm_example' in template
    
    @pytest.mark.asyncio
    async def test_create_standard_meeting_notes(self, agent):
        """Test creating standard meeting notes"""
        result = await agent.create_meeting_notes({
            'template': 'meeting_notes',
            'variation': 'standard_meeting',
            'meeting_title': 'Q4 Planning Session',
            'date': datetime.now().isoformat(),
            'attendees': ['Alice Johnson', 'Bob Smith', 'Carol Davis'],
            'agenda': [
                'Review Q3 results',
                'Set Q4 objectives',
                'Resource allocation'
            ],
            'notes': 'Discussed key objectives for next quarter.',
            'decisions': [
                'Approve budget increase',
                'Hire 2 new developers'
            ],
            'action_items': [
                {'owner': 'Alice', 'task': 'Prepare budget proposal', 'due': '2025-12-20'},
                {'owner': 'Bob', 'task': 'Draft job descriptions', 'due': '2025-12-18'}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'meeting_notes'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_daily_standup_notes(self, agent):
        """Test creating daily standup notes"""
        result = await agent.create_meeting_notes({
            'template': 'meeting_notes',
            'variation': 'daily_standup',
            'date': datetime.now().isoformat(),
            'attendees': ['Dev Team'],
            'updates': [
                {'person': 'Alice', 'yesterday': 'Fixed bug #123', 'today': 'Working on feature X', 'blockers': 'None'},
                {'person': 'Bob', 'yesterday': 'Code review', 'today': 'Deploy to staging', 'blockers': 'Waiting for approval'}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'meeting_notes'
    
    @pytest.mark.asyncio
    async def test_create_project_overview(self, agent):
        """Test creating project overview notes"""
        result = await agent.create_project_notes({
            'template': 'project_notes',
            'variation': 'project_overview',
            'project_name': 'VCC-Veritas Enhancement',
            'project_manager': 'Alice Johnson',
            'start_date': '2025-01-01',
            'end_date': '2025-06-30',
            'objectives': [
                'Improve agent capabilities',
                'Add new templates',
                'Enhance documentation'
            ],
            'stakeholders': ['Product Team', 'Development Team', 'Users'],
            'risks': [
                {'risk': 'Scope creep', 'mitigation': 'Weekly reviews'},
                {'risk': 'Resource constraints', 'mitigation': 'Prioritize features'}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'project_notes'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_simple_checklist(self, agent):
        """Test creating simple checklist"""
        result = await agent.create_checklist({
            'template': 'checklist',
            'variation': 'simple_checklist',
            'title': 'Weekly Tasks',
            'items': [
                {'task': 'Review pull requests', 'completed': True},
                {'task': 'Update documentation', 'completed': False},
                {'task': 'Team meeting', 'completed': True},
                {'task': 'Code deployment', 'completed': False}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'checklist'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_onboarding_checklist(self, agent):
        """Test creating onboarding checklist"""
        result = await agent.create_checklist({
            'template': 'checklist',
            'variation': 'onboarding_checklist',
            'employee_name': 'New Developer',
            'start_date': '2025-12-15',
            'items': [
                {'category': 'Day 1', 'task': 'Setup workstation', 'completed': False},
                {'category': 'Day 1', 'task': 'Meet the team', 'completed': False},
                {'category': 'Week 1', 'task': 'Complete training', 'completed': False},
                {'category': 'Week 2', 'task': 'First project assignment', 'completed': False}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'checklist'
    
    @pytest.mark.asyncio
    async def test_create_knowledge_base_article(self, agent):
        """Test creating knowledge base article"""
        result = await agent.create_knowledge_base_article({
            'template': 'knowledge_base',
            'variation': 'how_to_guide',
            'title': 'How to Deploy to Production',
            'category': 'DevOps',
            'summary': 'Step-by-step guide for production deployment',
            'prerequisites': [
                'Access to production server',
                'Approved change request',
                'Tested code in staging'
            ],
            'steps': [
                {'step': 1, 'title': 'Create backup', 'description': 'Backup current production database'},
                {'step': 2, 'title': 'Deploy code', 'description': 'Push code to production server'},
                {'step': 3, 'title': 'Run migrations', 'description': 'Execute database migrations'},
                {'step': 4, 'title': 'Verify', 'description': 'Test critical functionality'}
            ],
            'troubleshooting': [
                {'issue': 'Deployment fails', 'solution': 'Check server logs and rollback if needed'}
            ]
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'knowledge_base'
        assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_create_research_notes(self, agent):
        """Test creating research notes"""
        result = await agent.create_research_notes({
            'template': 'research_notes',
            'variation': 'literature_review',
            'topic': 'AI Agent Architectures',
            'date': datetime.now().isoformat(),
            'sources': [
                {'title': 'Paper 1', 'authors': 'Smith et al.', 'year': 2024, 'key_findings': 'Multi-agent systems improve performance'},
                {'title': 'Paper 2', 'authors': 'Jones et al.', 'year': 2024, 'key_findings': 'Template-based approaches reduce complexity'}
            ],
            'synthesis': 'Current research shows template-based multi-agent systems are effective.',
            'gaps': ['Limited research on YAML-based configurations'],
            'next_steps': ['Investigate configuration management best practices']
        })
        
        assert result['status'] == 'success'
        assert result['type'] == 'research_notes'
    
    def test_template_search_by_category(self, template_manager):
        """Test searching templates by category"""
        templates = template_manager.search_templates(category='meeting_notes')
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
        template = template_manager.read_template('meeting_notes')
        assert 'name' in template
        assert 'category' in template
        assert 'variations' in template
        assert 'llm_example' in template
        assert isinstance(template['variations'], list)
    
    @pytest.mark.asyncio
    async def test_retrospective_notes(self, agent):
        """Test creating retrospective meeting notes"""
        result = await agent.create_meeting_notes({
            'template': 'meeting_notes',
            'variation': 'retrospective',
            'sprint': 'Sprint 23',
            'date': datetime.now().isoformat(),
            'what_went_well': [
                'Good team collaboration',
                'Met all sprint goals'
            ],
            'what_to_improve': [
                'Better testing coverage',
                'More frequent code reviews'
            ],
            'action_items': [
                {'action': 'Implement automated testing', 'owner': 'Team'},
                {'action': 'Daily code review sessions', 'owner': 'Tech Lead'}
            ]
        })
        
        assert result['status'] == 'success'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
