# Intent Recognition Schemas

YAML/JSON-based intent recognition system for the VERITAS Orchestrator.

## Overview

This directory contains **intent recognition schemas** that define how the orchestrator recognizes user requests for different content types and routes them to appropriate agents.

### Supported Content Types

1. **Presentations** (`presentation_intent.yaml`)
   - PowerPoint slides
   - Diagrams, flowcharts, org charts
   - 8 template categories with 28 variations

2. **Word Documents** (`word_document_intent.yaml`)
   - Reports, letters, protocols, contracts
   - Formatted text documents
   - Template-based generation

3. **Tables** (`table_intent.yaml`)
   - Excel spreadsheets, CSV files
   - Data tables, comparisons, schedules
   - Structured data presentation

4. **Images** (`image_intent.yaml`)
   - AI-generated images
   - Technical diagrams, infographics
   - Photo-realistic renders

## Architecture

### 1. Schema Structure

Each intent schema YAML file contains:

```yaml
content_type: "presentation"
category: "visual_content"
priority: 0.85

intent_patterns:
  # Keyword patterns for detecting this content type
  
template_mappings:
  # Specific templates within this content type
  
llm_solution_steps:
  # Step-by-step instructions for LLM
  
agent_routing:
  # Which agents to use
```

### 2. Intent Recognition Flow

```
User Query
    ↓
Intent Recognition Manager
    ↓ (matches keywords)
Content Type Detection
    ↓
Template Selection
    ↓
LLM Solution Steps
    ↓
Agent Routing
    ↓
Content Generation
```

### 3. Master Configuration

`master_config.yaml` contains global settings:
- Content type priorities
- Confidence thresholds
- Fuzzy matching settings
- LLM integration config
- Quality assurance rules

## Usage

### Python API

```python
from backend.agents.orchestrator.intent_recognition_manager import get_intent_manager

# Initialize
manager = get_intent_manager()

# Recognize intent from user query
matches = manager.recognize_intent(
    "Erstelle eine Präsentation über BImSchG mit einem Flussdiagramm"
)

# Get best match
if matches:
    best_match = matches[0]
    print(f"Content Type: {best_match.content_type}")
    print(f"Template: {best_match.template_category}")
    print(f"Confidence: {best_match.confidence}")
    print(f"Agent: {best_match.agent_routing['primary_agent']}")
    
    # Get solution steps
    steps = best_match.llm_steps
    for step in steps:
        print(f"Step {step['step']}: {step['description']}")
```

### Orchestrator Integration

```python
class AgentOrchestrator:
    def __init__(self):
        self.intent_manager = get_intent_manager()
    
    async def process_query(self, query: str):
        # Recognize intent
        matches = self.intent_manager.recognize_intent(query)
        
        if not matches:
            return self._handle_no_match(query)
        
        best_match = matches[0]
        
        # Route to appropriate agent
        agent_name = best_match.agent_routing['primary_agent']
        
        # Execute solution steps
        for step in best_match.llm_steps:
            await self._execute_step(step, best_match)
        
        return result
```

## Schema Examples

### Presentation Intent

```yaml
template_mappings:
  process:
    keywords:
      - "prozess"
      - "workflow"
      - "ablauf"
      - "genehmigung"
    template_category: "process"
    variations:
      - "linear_process"
      - "decision_process"
    confidence: 0.9
```

When user says: "Erstelle einen Genehmigungsprozess"
- Matches keyword: "genehmigung"
- Selects template: "process"
- Variation: "linear_process"
- Routes to: PresentationCanvasAgent

### Word Document Intent

```yaml
template_mappings:
  report:
    keywords:
      - "bericht"
      - "report"
      - "analyse"
      - "gutachten"
    template_category: "report"
    variations:
      - "technical_report"
      - "executive_summary"
    confidence: 0.88
```

When user says: "Schreibe einen Bericht"
- Matches keyword: "bericht"
- Selects template: "report"
- Variation: "technical_report"
- Routes to: WordDocumentAgent

## LLM Solution Steps

Each schema defines step-by-step instructions for the LLM:

```yaml
llm_solution_steps:
  - step: 1
    action: "analyze_request"
    description: "Anforderung analysieren"
    outputs: ["keywords", "intent"]
    
  - step: 2
    action: "select_template"
    description: "Template auswählen"
    inputs: ["keywords"]
    outputs: ["template_category"]
    uses: "TemplateManager"
    
  - step: 3
    action: "generate_content"
    description: "Inhalt generieren"
    inputs: ["template", "data"]
    outputs: ["final_content"]
```

## Adding New Content Types

To add a new content type:

1. **Create Schema File**: `new_type_intent.yaml`

```yaml
content_type: "new_type"
category: "category_name"
priority: 0.80

intent_patterns:
  creation:
    keywords:
      - "keyword1"
      - "keyword2"
    confidence: 0.85

template_mappings:
  template1:
    keywords: [...]
    template_category: "template1"
    variations: [...]
    confidence: 0.80

llm_solution_steps:
  - step: 1
    action: "..."
    description: "..."

agent_routing:
  primary_agent: "NewTypeAgent"
  dependencies: [...]
```

2. **Update Master Config**: Add to `master_config.yaml`

```yaml
content_type_priorities:
  new_type: 0.80

extension_points:
  new_type:
    enabled: true
    schema_file: "new_type_intent.yaml"
```

3. **Test**: Run intent recognition manager

```bash
python backend/agents/orchestrator/intent_recognition_manager.py
```

## Configuration Options

### Global Settings

```yaml
global_config:
  min_confidence_threshold: 0.75
  max_intents_returned: 3
  fuzzy_matching: true
  supported_languages: ["de", "en"]
```

### Resolution Strategy

```yaml
resolution_strategy:
  multi_match_strategy: "highest_confidence"
  fallback_strategy: "ask_user"
  default_content_type: "text"
```

### Agent Routing

```yaml
agent_routing:
  dynamic_routing: true
  selection_strategy: "capability_based"
  enable_fallback: true
  max_fallback_depth: 2
```

## Quality Assurance

Built-in quality checks:

```yaml
quality_assurance:
  enable_checks: true
  checks:
    - "confidence_threshold"
    - "data_completeness"
    - "template_availability"
    - "agent_availability"
  failure_action: "retry_with_clarification"
```

## Monitoring

Track metrics and performance:

```yaml
monitoring:
  log_intent_recognition: true
  track_metrics: true
  metrics:
    - "intent_accuracy"
    - "resolution_time"
    - "agent_success_rate"
```

## Benefits

### 1. **Declarative Configuration**
- No code changes needed to add templates
- Easy to maintain and update
- Clear separation of concerns

### 2. **Multi-Content-Type Support**
- Handles presentations, documents, tables, images
- Extensible to new types (video, audio, code)
- Consistent approach across all types

### 3. **LLM-Friendly**
- Step-by-step instructions
- Clear inputs/outputs
- Reusable patterns

### 4. **Agent Agnostic**
- Routes to any agent
- Fallback chains
- Dynamic selection

### 5. **Quality Assured**
- Confidence thresholds
- Validation checks
- Error handling

## Testing

Run the demo:

```bash
python backend/agents/orchestrator/intent_recognition_manager.py
```

Expected output:
- List of content types
- Test queries with matches
- LLM solution steps
- Agent routing information

## Future Extensions

Planned content types:

- **Video** (`video_intent.yaml`)
- **Audio** (`audio_intent.yaml`)
- **3D Models** (`3d_model_intent.yaml`)
- **Code Generation** (`code_intent.yaml`)
- **Maps** (`map_intent.yaml`)
- **Charts** (`chart_intent.yaml`)

---

**Version:** 1.0.0  
**Created:** December 13, 2025  
**Author:** VERITAS Development Team
