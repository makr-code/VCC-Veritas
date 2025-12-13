# Microsoft Office Agent Suite - Complete Documentation

## Overview

This document provides comprehensive documentation for the complete Microsoft Office Agent Suite implementation in VCC-Veritas. The suite includes agents for PowerPoint, Excel/Tables, Outlook, and OneNote, along with a unified YAML-based intent recognition system.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent Capabilities](#agent-capabilities)
3. [Intent Recognition System](#intent-recognition-system)
4. [Template System](#template-system)
5. [Usage Examples](#usage-examples)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### System Components

```
VCC-Veritas Agent Suite
├── PowerPoint Agent (PresentationCanvasAgent)
│   ├── Shape rendering (182+ shapes)
│   ├── Diagram templates (8 categories, 28 variations)
│   └── Template Manager (CRUD operations)
├── Excel/Table Agent (ExcelTableAgent)
│   ├── Multi-format generation (Excel, CSV, Word, PowerPoint)
│   ├── Table templates (4 categories)
│   └── Template Manager (CRUD operations)
├── Outlook Agent (OutlookAgent)
│   ├── Email composition
│   ├── Calendar management
│   ├── Task management
│   ├── Contact management
│   └── Template Manager (4 categories, 14 variations)
├── OneNote Agent (OneNoteAgent)
│   ├── Meeting notes
│   ├── Project documentation
│   ├── Checklists
│   ├── Knowledge base
│   ├── Research notes
│   └── Template Manager (5 categories, 19 variations)
└── Intent Recognition Manager
    ├── YAML-based schemas (6 content types)
    ├── Keyword matching
    ├── LLM solution steps
    └── Agent routing configuration
```

### Design Principles

1. **Template-Driven**: All agents use YAML templates for consistency and LLM guidance
2. **CRUD Operations**: Unified template management across all agents
3. **Declarative Configuration**: Intent schemas define behavior without code changes
4. **Extensibility**: Easy to add new templates, content types, and agents
5. **Multilingual**: Supports German and English keywords

---

## Agent Capabilities

### 1. PowerPoint Agent (PresentationCanvasAgent)

**File**: `backend/agents/presentation_canvas_agent.py`

**Capabilities**:
- 182+ native PowerPoint shapes (rectangles, circles, arrows, flowcharts, stars, callouts)
- 29 arrow types, 29 flowchart shapes
- Connectors: straight, elbow, curve
- Template-based diagrams with automatic layout
- Native PPTX output (editable objects, not images)

**Template Categories** (8):
- **List**: Bullet points, numbered lists, icon lists
- **Process**: Workflows, decision flows, approval processes
- **Cycle**: PDCA, circular processes, continuous improvement
- **Hierarchy**: Org charts, tree diagrams, company structures
- **Relationship**: Venn diagrams, network maps, stakeholder maps
- **Matrix**: SWOT, 2x2, 3x3 grids, comparison matrices
- **Pyramid**: Hierarchical layers, Maslow's hierarchy
- **Spiderweb**: Radar charts, competency assessments

**Usage**:
```python
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent

agent = PresentationCanvasAgent()
result = await agent.create_presentation({
    'template': 'process',
    'variation': 'workflow',
    'use_native_shapes': True,
    'data': {
        'steps': [
            {'shape': 'flowchart_process', 'text': 'Step 1', 'color': '#4472C4'},
            {'shape': 'flowchart_decision', 'text': 'Decision?', 'color': '#ED7D31'},
            {'shape': 'flowchart_terminator', 'text': 'End', 'color': '#70AD47'}
        ]
    }
})
```

### 2. Excel/Table Agent (ExcelTableAgent)

**File**: `backend/agents/excel_table_agent.py`

**Capabilities**:
- Generate Excel spreadsheets (.xlsx) with formatting
- Generate CSV files
- Embed tables in Word documents (.docx)
- Embed tables in PowerPoint presentations (.pptx)
- Automatic styling (headers, alternate rows, colors)
- Support for formulas and aggregations

**Template Categories** (4):
- **data_table**: Simple data tables, formatted tables
- **comparison**: Feature comparisons, option comparisons, product comparisons
- **summary**: Quarterly summaries, aggregated data, totals and statistics
- **schedule**: Project schedules, resource allocation, timelines

**Usage**:
```python
from backend.agents.excel_table_agent import ExcelTableAgent

agent = ExcelTableAgent()

# Generate Excel file
result = await agent.generate_table({
    'template': 'data_table',
    'variation': 'formatted_data_table',
    'data': {
        'headers': ['Product', 'Q1', 'Q2', 'Q3', 'Q4'],
        'rows': [
            ['Widget A', 100, 120, 115, 130],
            ['Widget B', 85, 90, 95, 100]
        ]
    },
    'output_format': 'excel',
    'output_path': 'output.xlsx'
})

# Embed in Word document
agent.embed_in_existing_word(dataframe, 'document.docx')

# Embed in PowerPoint
agent.embed_in_existing_powerpoint(dataframe, 'presentation.pptx', slide_index=2)
```

### 3. Outlook Agent (OutlookAgent)

**File**: `backend/agents/outlook_agent.py`

**Capabilities**:
- Email composition (formal, informal, meeting requests, newsletters)
- Calendar event creation (appointments, meetings, recurring events)
- Task management (simple tasks, project tasks, reminders)
- Contact management (business contacts, personal contacts, distribution lists)
- HTML formatting support
- Attachment handling
- Microsoft Graph API integration

**Template Categories** (4):
- **email_compose**: Formal emails, informal emails, meeting requests, status updates
- **calendar_event**: Meetings, appointments, recurring events, all-day events
- **task_management**: Simple tasks, project tasks, recurring tasks, delegated tasks
- **contact_management**: Business contacts, personal contacts, distribution lists

**Usage**:
```python
from backend.agents.outlook_agent import OutlookAgent

agent = OutlookAgent()

# Compose email
result = await agent.compose_email({
    'template': 'email_compose',
    'variation': 'formal_email',
    'to': 'recipient@company.com',
    'subject': 'Project Update',
    'body': 'Please find attached the latest project update.',
    'attachments': ['report.pdf'],
    'send': False  # Set to True to actually send
})

# Create calendar event
result = await agent.create_calendar_event({
    'template': 'calendar_event',
    'variation': 'meeting',
    'title': 'Team Standup',
    'start_time': '2025-12-14T09:00:00',
    'end_time': '2025-12-14T09:30:00',
    'location': 'Conference Room A',
    'attendees': ['team@company.com']
})

# Create task
result = await agent.create_task({
    'template': 'task_management',
    'variation': 'project_task',
    'title': 'Complete documentation',
    'due_date': '2025-12-20',
    'priority': 'high',
    'assigned_to': 'developer@company.com'
})
```

### 4. OneNote Agent (OneNoteAgent)

**File**: `backend/agents/onenote_agent.py`

**Capabilities**:
- Structured meeting notes (standard, standup, retrospective, decision logs)
- Project documentation (overview, sprint planning, requirements, post-mortem)
- Interactive checklists (simple, onboarding, QA, process)
- Knowledge base articles (how-to guides, FAQs, best practices, troubleshooting)
- Research notes (literature reviews, study notes, experiment logs, interviews)

**Template Categories** (5):
- **meeting_notes**: Standard meetings, daily standups, retrospectives, decision logs
- **project_notes**: Project overview, sprint planning, requirements, post-mortem
- **checklist**: Simple checklists, onboarding, QA checklists, process checklists
- **knowledge_base**: How-to guides, FAQs, best practices, troubleshooting
- **research_notes**: Literature reviews, study notes, experiment logs, interview notes

**Usage**:
```python
from backend.agents.onenote_agent import OneNoteAgent

agent = OneNoteAgent()

# Create meeting notes
result = await agent.create_meeting_notes({
    'template': 'meeting_notes',
    'variation': 'standard_meeting',
    'meeting_title': 'Q4 Planning',
    'date': '2025-12-13',
    'attendees': ['Alice', 'Bob', 'Carol'],
    'agenda': ['Review Q3 results', 'Set Q4 objectives'],
    'decisions': ['Approve budget increase'],
    'action_items': [
        {'owner': 'Alice', 'task': 'Prepare proposal', 'due': '2025-12-20'}
    ]
})

# Create project documentation
result = await agent.create_project_notes({
    'template': 'project_notes',
    'variation': 'project_overview',
    'project_name': 'VCC-Veritas Enhancement',
    'objectives': ['Improve capabilities', 'Add templates'],
    'stakeholders': ['Product Team', 'Dev Team'],
    'timeline': {'start': '2025-01-01', 'end': '2025-06-30'}
})

# Create checklist
result = await agent.create_checklist({
    'template': 'checklist',
    'variation': 'onboarding_checklist',
    'employee_name': 'New Developer',
    'items': [
        {'category': 'Day 1', 'task': 'Setup workstation'},
        {'category': 'Week 1', 'task': 'Complete training'}
    ]
})
```

---

## Intent Recognition System

**File**: `backend/agents/orchestrator/intent_recognition_manager.py`

### Overview

The Intent Recognition Manager uses YAML-based schemas to classify user requests and route them to the appropriate agent with LLM solution steps.

### Content Types Supported

1. **presentation** - PowerPoint presentations
2. **table** - Excel/tables in Word/PowerPoint
3. **word_document** - Word documents
4. **image** - AI-generated images
5. **outlook** - Email, calendar, tasks, contacts
6. **onenote** - Notes and knowledge management

### Schema Structure

Each intent schema (YAML file) contains:
- **content_type**: Type identifier
- **keywords**: German and English trigger words
- **template_categories**: Available template types
- **llm_steps**: Step-by-step instructions for LLM
- **agent_routing**: Primary and fallback agents
- **quality_assurance**: Validation rules

### Usage

```python
from backend.agents.orchestrator.intent_recognition_manager import get_intent_manager

manager = get_intent_manager()

# Recognize intent from user query
result = manager.recognize_intent("Erstelle eine Präsentation mit Flowchart")

# Result contains:
# - content_type: 'presentation'
# - template_category: 'process'
# - confidence: 0.85
# - llm_steps: ['1. Analyze requirements', '2. Select template', ...]
# - agent_routing: {'primary_agent': 'PresentationCanvasAgent', ...}

# List all content types
content_types = manager.list_content_types()

# Search by specific criteria
results = manager.search_intents(content_type='presentation', min_confidence=0.7)
```

### Keyword Examples

**Presentation**:
- German: präsentation, folie, diagramm, flowchart, organigramm, matrix, swot
- English: presentation, slide, diagram, flowchart, org chart, matrix, swot

**Table**:
- German: tabelle, excel, daten, vergleich, zeitplan, übersicht
- English: table, excel, data, comparison, schedule, overview

**Outlook**:
- German: email, e-mail, termin, kalender, aufgabe, kontakt
- English: email, appointment, calendar, task, contact

**OneNote**:
- German: notizen, meeting, protokoll, checkliste, wissensdatenbank
- English: notes, meeting, minutes, checklist, knowledge base

---

## Template System

### Template Management

All agents use a unified CRUD template manager pattern:

```python
from backend.agents.presentation_template_manager import get_template_manager
from backend.agents.table_template_manager import get_table_template_manager
from backend.agents.outlook_template_manager import get_outlook_template_manager
from backend.agents.onenote_template_manager import get_onenote_template_manager

# List templates
manager = get_template_manager()
templates = manager.list_templates()

# Read specific template
template = manager.read_template('process')

# Search templates
results = manager.search_templates(category='flowchart')

# Export templates to JSON
manager.export_templates('templates_backup.json')

# Import templates from JSON
manager.import_templates('templates_backup.json')
```

### Template Structure (YAML)

```yaml
name: process
category: processes
description: Process flow and workflow diagrams
variations:
  - name: workflow
    description: Standard workflow process
    structure:
      - start: flowchart_terminator
      - steps: flowchart_process (array)
      - decisions: flowchart_decision (optional)
      - end: flowchart_terminator
  - name: approval_process
    description: Multi-stage approval workflow
    structure:
      - request: flowchart_data
      - approval_steps: flowchart_decision (array)
      - actions: flowchart_process (array)
llm_example: |
  To create a workflow process:
  1. Identify process steps
  2. Map to flowchart shapes
  3. Connect with arrows
  4. Add decision points
```

---

## Usage Examples

### Example 1: Creating a SWOT Analysis Presentation

```python
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent

agent = PresentationCanvasAgent()
result = await agent.create_presentation({
    'template': 'matrix',
    'variation': 'swot_analysis',
    'use_native_shapes': True,
    'data': {
        'strengths': ['Strong team', 'Good technology'],
        'weaknesses': ['Limited budget', 'Time constraints'],
        'opportunities': ['Market growth', 'New features'],
        'threats': ['Competition', 'Regulations']
    }
})
```

### Example 2: Generating Quarterly Sales Report Table

```python
from backend.agents.excel_table_agent import ExcelTableAgent

agent = ExcelTableAgent()
result = await agent.generate_table({
    'template': 'summary',
    'variation': 'quarterly_summary',
    'data': {
        'headers': ['Product', 'Q1', 'Q2', 'Q3', 'Q4', 'Total'],
        'rows': [
            ['Product A', 10000, 12000, 11000, 13000, 46000],
            ['Product B', 8000, 8500, 9000, 9500, 35000]
        ],
        'totals': True
    },
    'output_format': 'excel',
    'styling': {
        'header_color': '#4472C4',
        'alternate_rows': True,
        'bold_totals': True
    }
})
```

### Example 3: Sending Team Meeting Invitation

```python
from backend.agents.outlook_agent import OutlookAgent

agent = OutlookAgent()
result = await agent.compose_email({
    'template': 'email_compose',
    'variation': 'meeting_request',
    'to': 'team@company.com',
    'subject': 'Weekly Team Meeting - Monday 9 AM',
    'body': '''
    Hi Team,
    
    Please join our weekly team meeting on Monday at 9 AM.
    
    Agenda:
    - Sprint review
    - Planning for next week
    - Q&A
    
    Best regards
    ''',
    'send': True
})

# Also create calendar event
event_result = await agent.create_calendar_event({
    'template': 'calendar_event',
    'variation': 'recurring_event',
    'title': 'Weekly Team Meeting',
    'start_time': '2025-12-16T09:00:00',
    'end_time': '2025-12-16T10:00:00',
    'recurrence': 'weekly',
    'attendees': ['team@company.com']
})
```

### Example 4: Creating Project Meeting Notes

```python
from backend.agents.onenote_agent import OneNoteAgent

agent = OneNoteAgent()
result = await agent.create_meeting_notes({
    'template': 'meeting_notes',
    'variation': 'standard_meeting',
    'meeting_title': 'Project Kickoff - VCC Enhancement',
    'date': '2025-12-13',
    'attendees': ['Alice (PM)', 'Bob (Dev)', 'Carol (Design)'],
    'agenda': [
        'Project overview and objectives',
        'Timeline and milestones',
        'Roles and responsibilities',
        'Next steps'
    ],
    'notes': '''
    Project goals:
    - Add new agent capabilities
    - Implement template system
    - Improve documentation
    
    Timeline: 6 months (Jan - Jun 2025)
    ''',
    'decisions': [
        'Use YAML for templates',
        'Implement 4 main agents',
        'Weekly status meetings'
    ],
    'action_items': [
        {'owner': 'Alice', 'task': 'Create project plan', 'due': '2025-12-20'},
        {'owner': 'Bob', 'task': 'Setup development environment', 'due': '2025-12-15'},
        {'owner': 'Carol', 'task': 'Design UI mockups', 'due': '2025-12-22'}
    ]
})
```

---

## Testing

### Running Tests

```bash
# Run all agent tests
pytest tests/agents/ -v

# Run specific agent tests
pytest tests/agents/test_excel_table_agent.py -v
pytest tests/agents/test_outlook_agent.py -v
pytest tests/agents/test_onenote_agent.py -v
pytest tests/agents/test_intent_recognition_manager.py -v

# Run with coverage
pytest tests/agents/ --cov=backend/agents --cov-report=html
```

### Test Coverage

The test suite includes:
- **360+ test cases** across all agents
- Unit tests for each agent
- Template validation tests
- Intent recognition tests
- Integration tests
- Error handling tests

**Test Files**:
- `test_presentation_canvas_agent.py` - PowerPoint agent tests
- `test_presentation_shapes_diagrams.py` - Shape and diagram tests
- `test_presentation_template_manager.py` - Template manager tests
- `test_excel_table_agent.py` - Excel/Table agent tests
- `test_outlook_agent.py` - Outlook agent tests
- `test_onenote_agent.py` - OneNote agent tests
- `test_intent_recognition_manager.py` - Intent recognition tests

---

## Deployment

### Dependencies

Add to `requirements.txt`:
```
openpyxl>=3.1.2
pandas>=2.0.0
python-pptx>=0.6.21
python-docx>=1.1.0
PyYAML>=6.0
```

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Update `master_config.yaml` with priorities:
```yaml
content_type_priorities:
  presentation: 0.80
  table: 0.82
  outlook: 0.78
  onenote: 0.76
  word_document: 0.75
  image: 0.70
```

### Orchestrator Integration

```python
from backend.agents.orchestrator.intent_recognition_manager import get_intent_manager
from backend.agents.presentation_canvas_agent import PresentationCanvasAgent
from backend.agents.excel_table_agent import ExcelTableAgent
from backend.agents.outlook_agent import OutlookAgent
from backend.agents.onenote_agent import OneNoteAgent

# In orchestrator
intent_manager = get_intent_manager()
agents = {
    'presentation': PresentationCanvasAgent(),
    'table': ExcelTableAgent(),
    'outlook': OutlookAgent(),
    'onenote': OneNoteAgent()
}

# Recognize intent and route
intent = intent_manager.recognize_intent(user_query)
agent = agents[intent['content_type']]
result = await agent.execute(intent)
```

---

## Troubleshooting

### Common Issues

**1. Template Not Found**
```python
# Solution: Check template name and category
manager = get_template_manager()
templates = manager.list_templates()
print([t['name'] for t in templates])
```

**2. Low Confidence Score**
```python
# Solution: Add more specific keywords to intent schema
# Edit intent_schemas/*.yaml and add keywords
```

**3. Import Errors**
```python
# Solution: Ensure all dependencies are installed
pip install openpyxl pandas python-pptx python-docx PyYAML
```

**4. File Permission Errors**
```python
# Solution: Check write permissions for output directory
import os
os.access('/path/to/output', os.W_OK)
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('agents')
```

---

## Summary Statistics

### Implementation Metrics

- **4 Complete Agents**: PowerPoint, Excel/Table, Outlook, OneNote
- **8 Template Managers**: With full CRUD operations
- **6 Intent Schemas**: Covering all content types
- **28+ Sample Templates**: Across all categories
- **182+ PowerPoint Shapes**: Native PPTX support
- **60+ Template Variations**: Covering common use cases
- **360+ Test Cases**: Comprehensive coverage
- **6 Documentation Files**: Complete user guides

### Template Breakdown

| Agent | Categories | Variations | Total Templates |
|-------|------------|------------|-----------------|
| PowerPoint | 8 | 28 | 28 |
| Excel/Table | 4 | 8 | 8 |
| Outlook | 4 | 14 | 14 |
| OneNote | 5 | 19 | 19 |
| **Total** | **21** | **69** | **69** |

---

## Next Steps

1. **Orchestrator Integration**: Integrate intent recognition into main orchestrator
2. **API Endpoints**: Create REST API endpoints for each agent
3. **Frontend Integration**: Add UI components for template selection
4. **Performance Optimization**: Implement caching and async processing
5. **Extended Templates**: Add more domain-specific templates
6. **Video/Audio Support**: Extend to multimedia content types
7. **Analytics**: Add usage tracking and analytics

---

## Support

For questions or issues:
- Check this documentation first
- Review test files for usage examples
- Check template YAML files for structure
- Review agent source code for implementation details

---

**Last Updated**: 2025-12-13  
**Version**: 1.0  
**Authors**: VCC-Veritas Development Team
