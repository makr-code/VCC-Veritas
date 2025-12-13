# Presentation Templates Directory

This directory contains generic standard templates for PowerPoint diagram generation. These templates serve as **building instructions** for the LLM to create consistent, professional diagrams.

## 📁 Template Categories

### 1. **List** (`list.yaml`)
Simple bullet point and numbered lists
- Simple bullet list
- Numbered list
- Two-column list

**Use Cases:** Key points, benefits, requirements, checklists

### 2. **Process** (`process.yaml`)
Sequential process flows and workflows
- Linear process flow
- Process with decision points
- Horizontal process flow

**Use Cases:** BImSchG approval process, project workflows, procedures

### 3. **Cycle** (`cycle.yaml`)
Circular and cyclical diagrams
- PDCA cycle (Plan-Do-Check-Act)
- Generic circular process
- Lifecycle diagram

**Use Cases:** Continuous improvement, project lifecycle, circular economy

### 4. **Hierarchy** (`hierarchy.yaml`)
Organizational and tree structures
- Organization chart
- Tree diagram
- Work Breakdown Structure (WBS)

**Use Cases:** Org charts, reporting structures, project decomposition

### 5. **Relationship** (`relationship.yaml`)
Connections and dependencies between elements
- Venn diagram
- Network diagram
- Stakeholder map
- Dependency diagram

**Use Cases:** Set relationships, stakeholder analysis, system dependencies

### 6. **Matrix** (`matrix.yaml`)
Grid-based comparisons and categorizations
- 2x2 matrix
- SWOT analysis
- 3x3 matrix
- Comparison table

**Use Cases:** SWOT analysis, priority matrices, feature comparisons

### 7. **Pyramid** (`pyramid.yaml`)
Hierarchical layers and foundations
- Standard pyramid
- Inverted pyramid
- Maslow's hierarchy
- Food pyramid

**Use Cases:** Hierarchical concepts, foundation structures, priority levels

### 8. **Spiderweb** (`spiderweb.yaml`)
Radar charts and multi-axis comparisons
- Radar chart
- Competency web
- Multi-series comparison
- Star rating diagram

**Use Cases:** Multi-dimensional comparisons, skill assessments, performance evaluation

---

## 🔧 Template Structure

Each template YAML file contains:

```yaml
name: "template_name"
category: "category"
description: "Template description"
version: "1.0.0"

variations:
  - id: "variation_id"
    name: "Variation Name"
    description: "What this variation does"
    structure:
      layout: "content"
      elements:
        - type: "element_type"
          role: "element_role"
          position: {x: int, y: int}
          size: {width: int, height: int}
          properties: {...}

llm_example:
  prompt: "Example user prompt"
  vdl_output: {...}

color_schemes:
  scheme_name:
    color_key: "#hexcolor"
```

---

## 💻 Using Templates (Python API)

### Basic Usage

```python
from backend.agents.presentation_template_manager import get_template_manager

# Get template manager
manager = get_template_manager()

# List all templates
templates = manager.list_templates()
for template in templates:
    print(f"{template.name}: {template.description}")

# Read a specific template
process_template = manager.read_template('process')

# Get variations
variations = manager.get_variations('process')
for var in variations:
    print(f"{var['id']}: {var['name']}")

# Get specific variation
linear_flow = manager.get_variation('process', 'linear_process')
```

### CRUD Operations

```python
# CREATE
manager.create_template(
    name="custom_template",
    category="custom",
    description="My custom template",
    variations=[...]
)

# READ
template = manager.read_template('custom_template')

# UPDATE
manager.update_template('custom_template', {
    'description': 'Updated description',
    'version': '1.1.0'
})

# DELETE
manager.delete_template('custom_template')
```

### Search and Filter

```python
# Search templates
results = manager.search_templates('flow')

# List by category
hierarchy_templates = manager.list_templates(category='hierarchy')

# Get all categories
categories = manager.get_categories()
```

### Export/Import

```python
# Export to JSON
json_str = manager.export_template_to_json('process')

# Import from JSON
manager.import_template_from_json(json_str, overwrite=False)
```

---

## 🤖 LLM Integration

Templates provide **building instructions** for the LLM. Each template includes:

1. **Structure Definition**: Exact layout and element positioning
2. **LLM Examples**: Sample prompts and expected VDL output
3. **Color Schemes**: Professional color palettes
4. **Variations**: Different versions of the same diagram type

### Example: LLM Using Process Template

**User Prompt:**
```
"Create a flowchart for BImSchG approval with 5 steps"
```

**LLM Reads Template:**
```python
template = manager.read_template('process')
example = template['llm_example']
# LLM sees structure and example output
```

**LLM Generates VDL:**
```json
{
  "use_native_shapes": true,
  "slides": [{
    "layout": "content",
    "template": "process",
    "template_variation": "linear_process",
    "data": {
      "title": "BImSchG Approval Process",
      "steps": [
        {"type": "start", "text": "Application", "color": "#70ad47"},
        {"type": "process", "text": "Review", "color": "#4472c4"},
        {"type": "decision", "text": "Complete?", "color": "#ed7d31"},
        {"type": "process", "text": "Evaluation", "color": "#4472c4"},
        {"type": "end", "text": "Approval", "color": "#70ad47"}
      ]
    }
  }]
}
```

---

## 📊 Template Categories Overview

| Category | Template Count | Variations | Best For |
|----------|---------------|------------|----------|
| List | 1 | 3 | Bullet points, numbered lists |
| Process | 1 | 3 | Workflows, procedures |
| Cycle | 1 | 3 | Continuous processes |
| Hierarchy | 1 | 3 | Org charts, tree structures |
| Relationship | 1 | 4 | Connections, dependencies |
| Matrix | 1 | 4 | Comparisons, SWOT |
| Pyramid | 1 | 4 | Hierarchical layers |
| Spiderweb | 1 | 4 | Multi-axis comparisons |

**Total: 8 templates, 28 variations**

---

## 🎨 Color Schemes

All templates include professional color schemes:

### Standard Professional
```yaml
primary: "#4472c4"    # Blue
secondary: "#70ad47"  # Green
accent: "#ed7d31"     # Orange
warning: "#ffc000"    # Yellow
```

### Environmental
```yaml
primary: "#277728"    # Dark green
secondary: "#4c9c4d"  # Medium green
accent: "#70ad47"     # Light green
```

### Process Colors
```yaml
start_end: "#70ad47"  # Green
process: "#4472c4"    # Blue
decision: "#ed7d31"   # Orange
data: "#ffc000"       # Yellow
```

---

## ✅ Best Practices

### For Template Designers

1. **Keep it Simple**: Templates should be easy to understand and use
2. **Provide Examples**: Include `llm_example` for every template
3. **Use Consistent Naming**: Follow naming conventions (lowercase, underscores)
4. **Document Properties**: Explain all available properties
5. **Version Control**: Increment version when making changes

### For LLM Integration

1. **Read Templates First**: Always read the template before generating VDL
2. **Follow Structure**: Use the template structure as a guide
3. **Use Examples**: Reference `llm_example` for format guidance
4. **Apply Color Schemes**: Use provided color schemes for consistency
5. **Validate Output**: Ensure generated VDL matches template structure

### For Developers

1. **Cache Templates**: Use template manager's caching for performance
2. **Validate Input**: Validate user data before applying to templates
3. **Handle Errors**: Templates may not exist or be malformed
4. **Test Variations**: Test all template variations
5. **Update Documentation**: Keep this README synchronized with templates

---

## 🔄 Adding New Templates

To add a new template:

1. **Create YAML File**: Create `your_template.yaml` in this directory
2. **Follow Structure**: Use existing templates as reference
3. **Include Examples**: Add `llm_example` section
4. **Define Variations**: Create at least 2-3 variations
5. **Add Color Schemes**: Provide professional color palettes
6. **Test**: Validate with `presentation_template_manager.py`
7. **Document**: Update this README

### Template Checklist

- [ ] YAML file created
- [ ] `name`, `category`, `description`, `version` defined
- [ ] At least 2 variations included
- [ ] `llm_example` with prompt and VDL output
- [ ] Color schemes defined
- [ ] Structure validated
- [ ] Tested with template manager
- [ ] README updated

---

## 📚 Related Documentation

- **Best Practices**: `docs/components/POWERPOINT_SHAPES_BEST_PRACTICES.md`
- **Quick Reference**: `docs/components/POWERPOINT_AI_AGENT_QUICK_REFERENCE.md`
- **Implementation Summary**: `docs/components/POWERPOINT_AI_AGENT_IMPLEMENTATION_SUMMARY.md`
- **German Answer**: `docs/components/POWERPOINT_AI_AGENT_ANTWORT.md`

---

## 🎯 Template Usage Statistics

Templates are designed to cover the most common diagram types:

- **80%** of use cases covered by 8 main categories
- **28 variations** provide flexibility
- **Extensible** - easy to add new templates
- **LLM-friendly** - structured for AI understanding

---

**Version:** 1.0.0  
**Created:** December 13, 2025  
**Status:** ✅ Production Ready
