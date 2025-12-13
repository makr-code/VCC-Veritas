"""
Intent Recognition Manager - YAML/JSON-based Intent Classification

This module provides a flexible, schema-driven approach to recognizing user intents
for different content types (presentations, Word documents, tables, images, etc.)

The system uses YAML configuration files to define:
- Keywords and patterns for each content type
- Template mappings
- LLM solution steps
- Agent routing configuration
"""

import yaml
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class IntentMatch:
    """Represents a matched intent"""
    content_type: str
    template_category: Optional[str]
    template_variation: Optional[str]
    confidence: float
    matched_keywords: List[str]
    llm_steps: List[Dict[str, Any]] = field(default_factory=list)
    agent_routing: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntentRecognitionManager:
    """
    YAML/JSON-based Intent Recognition System
    
    Loads intent schemas from YAML files and matches user queries
    to appropriate content types and templates.
    """
    
    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize Intent Recognition Manager
        
        Args:
            schema_dir: Directory containing intent schema YAML files
        """
        if schema_dir is None:
            current_file = Path(__file__)
            self.schema_dir = current_file.parent / "intent_schemas"
        else:
            self.schema_dir = Path(schema_dir)
        
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.master_config: Dict[str, Any] = {}
        
        # Load schemas
        self._load_schemas()
        
        logger.info(f"IntentRecognitionManager initialized with {len(self.schemas)} schemas")
    
    def _load_schemas(self):
        """Load all intent schemas from YAML files"""
        if not self.schema_dir.exists():
            logger.warning(f"Schema directory not found: {self.schema_dir}")
            return
        
        # Load master configuration first
        master_config_path = self.schema_dir / "master_config.yaml"
        if master_config_path.exists():
            with open(master_config_path, 'r', encoding='utf-8') as f:
                self.master_config = yaml.safe_load(f)
        
        # Load all intent schemas
        schema_pattern = self.master_config.get('schema_config', {}).get('schema_pattern', '*_intent.yaml')
        
        for schema_file in self.schema_dir.glob(schema_pattern):
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = yaml.safe_load(f)
                    content_type = schema.get('content_type')
                    if content_type:
                        self.schemas[content_type] = schema
                        logger.debug(f"Loaded schema: {content_type} from {schema_file.name}")
            except Exception as e:
                logger.error(f"Failed to load schema {schema_file}: {e}")
    
    def recognize_intent(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[IntentMatch]:
        """
        Recognize intent from user query
        
        Args:
            query: User query string
            context: Optional context information
            
        Returns:
            List of IntentMatch objects, sorted by confidence
        """
        matches = []
        query_lower = query.lower()
        
        # Check each content type schema
        for content_type, schema in self.schemas.items():
            # Check intent patterns first
            for pattern_name, pattern_config in schema.get('intent_patterns', {}).items():
                keywords = pattern_config.get('keywords', [])
                base_confidence = pattern_config.get('confidence', 0.5)
                
                matched_keywords = [kw for kw in keywords if kw.lower() in query_lower]
                
                if matched_keywords:
                    # Now check template mappings for more specific match
                    template_match = self._match_template(query_lower, schema)
                    
                    if template_match:
                        template_category, template_variation, template_confidence, template_keywords = template_match
                        
                        # Combine confidences
                        combined_confidence = (base_confidence + template_confidence) / 2
                        all_keywords = list(set(matched_keywords + template_keywords))
                        
                        match = IntentMatch(
                            content_type=content_type,
                            template_category=template_category,
                            template_variation=template_variation,
                            confidence=combined_confidence,
                            matched_keywords=all_keywords,
                            llm_steps=schema.get('llm_solution_steps', []),
                            agent_routing=schema.get('agent_routing', {}),
                            metadata={
                                'priority': schema.get('priority', 0.5),
                                'category': schema.get('category', 'unknown')
                            }
                        )
                        matches.append(match)
                    else:
                        # General content type match without specific template
                        match = IntentMatch(
                            content_type=content_type,
                            template_category=None,
                            template_variation=None,
                            confidence=base_confidence * 0.8,  # Lower confidence without template match
                            matched_keywords=matched_keywords,
                            llm_steps=schema.get('llm_solution_steps', []),
                            agent_routing=schema.get('agent_routing', {}),
                            metadata={
                                'priority': schema.get('priority', 0.5),
                                'category': schema.get('category', 'unknown')
                            }
                        )
                        matches.append(match)
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        # Apply minimum confidence threshold
        min_threshold = self.master_config.get('global_config', {}).get('min_confidence_threshold', 0.75)
        matches = [m for m in matches if m.confidence >= min_threshold]
        
        # Limit number of results
        max_results = self.master_config.get('global_config', {}).get('max_intents_returned', 3)
        matches = matches[:max_results]
        
        return matches
    
    def _match_template(
        self,
        query_lower: str,
        schema: Dict[str, Any]
    ) -> Optional[Tuple[str, Optional[str], float, List[str]]]:
        """
        Match query to specific template within a content type
        
        Returns:
            (template_category, template_variation, confidence, matched_keywords) or None
        """
        best_match = None
        best_confidence = 0.0
        
        for template_name, template_config in schema.get('template_mappings', {}).items():
            keywords = template_config.get('keywords', [])
            confidence = template_config.get('confidence', 0.5)
            
            matched_keywords = [kw for kw in keywords if kw.lower() in query_lower]
            
            if matched_keywords:
                # Calculate match strength
                match_strength = len(matched_keywords) / len(keywords) if keywords else 0
                adjusted_confidence = confidence * (0.7 + 0.3 * match_strength)
                
                if adjusted_confidence > best_confidence:
                    best_confidence = adjusted_confidence
                    template_category = template_config.get('template_category', template_name)
                    variations = template_config.get('variations', [])
                    template_variation = variations[0] if variations else None
                    best_match = (template_category, template_variation, adjusted_confidence, matched_keywords)
        
        return best_match
    
    def get_llm_solution_steps(
        self,
        content_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get LLM solution steps for a content type
        
        Args:
            content_type: Content type (e.g., 'presentation', 'word_document')
            
        Returns:
            List of solution step dictionaries
        """
        schema = self.schemas.get(content_type)
        if schema:
            return schema.get('llm_solution_steps', [])
        return []
    
    def get_agent_routing(
        self,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Get agent routing configuration for a content type
        
        Args:
            content_type: Content type
            
        Returns:
            Agent routing configuration
        """
        schema = self.schemas.get(content_type)
        if schema:
            return schema.get('agent_routing', {})
        return {}
    
    def get_template_info(
        self,
        content_type: str,
        template_category: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get template information
        
        Args:
            content_type: Content type
            template_category: Template category name
            
        Returns:
            Template configuration or None
        """
        schema = self.schemas.get(content_type)
        if schema:
            templates = schema.get('template_mappings', {})
            for template_name, template_config in templates.items():
                if template_config.get('template_category') == template_category:
                    return template_config
        return None
    
    def reload_schemas(self):
        """Reload all schemas from disk"""
        self.schemas.clear()
        self._load_schemas()
        logger.info("Schemas reloaded")
    
    def export_schema(
        self,
        content_type: str,
        format: str = 'yaml'
    ) -> Optional[str]:
        """
        Export a schema as YAML or JSON
        
        Args:
            content_type: Content type to export
            format: 'yaml' or 'json'
            
        Returns:
            Serialized schema or None
        """
        schema = self.schemas.get(content_type)
        if not schema:
            return None
        
        if format == 'json':
            return json.dumps(schema, indent=2)
        else:
            return yaml.dump(schema, default_flow_style=False, allow_unicode=True)
    
    def list_content_types(self) -> List[str]:
        """Get list of all supported content types"""
        return list(self.schemas.keys())
    
    def get_schema_info(self, content_type: str) -> Optional[Dict[str, Any]]:
        """Get complete schema information for a content type"""
        return self.schemas.get(content_type)


# Singleton instance
_intent_manager: Optional[IntentRecognitionManager] = None


def get_intent_manager() -> IntentRecognitionManager:
    """Get singleton instance of Intent Recognition Manager"""
    global _intent_manager
    
    if _intent_manager is None:
        _intent_manager = IntentRecognitionManager()
    
    return _intent_manager


# Standalone test/demo
if __name__ == '__main__':
    import sys
    
    # Initialize manager
    manager = get_intent_manager()
    
    print("="*60)
    print("Intent Recognition Manager - Demo")
    print("="*60)
    
    # List content types
    print("\n📋 Supported Content Types:")
    for content_type in manager.list_content_types():
        schema = manager.get_schema_info(content_type)
        priority = schema.get('priority', 0)
        category = schema.get('category', 'unknown')
        print(f"  - {content_type} (priority: {priority}, category: {category})")
    
    # Test queries
    test_queries = [
        "Erstelle eine Präsentation über BImSchG mit einem Flussdiagramm",
        "Ich brauche ein SWOT-Analyse-Diagramm",
        "Schreibe einen Bericht über Umweltgenehmigungen",
        "Generiere eine Tabelle mit allen Anlagen",
        "Erstelle ein fotorealistisches Bild von einer Windkraftanlage"
    ]
    
    print("\n🔍 Testing Intent Recognition:")
    for query in test_queries:
        print(f"\n  Query: \"{query}\"")
        matches = manager.recognize_intent(query)
        
        if matches:
            for i, match in enumerate(matches, 1):
                print(f"    Match {i}:")
                print(f"      Content Type: {match.content_type}")
                print(f"      Template: {match.template_category} ({match.template_variation})")
                print(f"      Confidence: {match.confidence:.2f}")
                print(f"      Keywords: {', '.join(match.matched_keywords[:3])}")
                print(f"      Agent: {match.agent_routing.get('primary_agent', 'N/A')}")
        else:
            print("    No matches found")
    
    # Show LLM steps for presentation
    print("\n📝 LLM Solution Steps for 'presentation':")
    steps = manager.get_llm_solution_steps('presentation')
    for step in steps:
        print(f"  Step {step.get('step')}: {step.get('description')}")
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
