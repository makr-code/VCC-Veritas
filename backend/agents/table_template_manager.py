"""
Table Template Manager - CRUD Operations for Table Templates

This module provides Create, Read, Update, Delete operations for 
table templates stored as YAML files.

Templates are organized by category:
- Data Table: Simple structured data
- Comparison: Feature/option comparisons
- Summary: Aggregated data with totals
- Schedule: Timelines and resource allocation
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableTemplateMetadata:
    """Table template metadata information"""
    name: str
    category: str
    description: str
    version: str
    file_path: str


class TableTemplateManager:
    """
    CRUD Manager for table templates
    
    Manages loading, saving, and querying of table template definitions
    stored in YAML format.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize table template manager
        
        Args:
            templates_dir: Directory containing template YAML files
                          Defaults to backend/agents/table_templates/
        """
        if templates_dir is None:
            current_file = Path(__file__)
            self.templates_dir = current_file.parent / "table_templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"TableTemplateManager initialized: {self.templates_dir}")
    
    # ==================== CREATE ====================
    
    def create_template(
        self,
        name: str,
        category: str,
        description: str,
        variations: List[Dict[str, Any]],
        version: str = "1.0.0",
        **kwargs
    ) -> bool:
        """Create a new template"""
        try:
            template_data = {
                "name": name,
                "category": category,
                "description": description,
                "version": version,
                "variations": variations,
                **kwargs
            }
            
            file_path = self.templates_dir / f"{name}.yaml"
            
            if file_path.exists():
                logger.warning(f"Template {name} already exists")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
            
            self._template_cache[name] = template_data
            logger.info(f"Template created: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create template {name}: {e}")
            return False
    
    # ==================== READ ====================
    
    def read_template(self, name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Read a template by name"""
        try:
            if use_cache and name in self._template_cache:
                return self._template_cache[name]
            
            file_path = self.templates_dir / f"{name}.yaml"
            
            if not file_path.exists():
                logger.warning(f"Template {name} not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            self._template_cache[name] = template_data
            return template_data
        
        except Exception as e:
            logger.error(f"Failed to read template {name}: {e}")
            return None
    
    def list_templates(self, category: Optional[str] = None) -> List[TableTemplateMetadata]:
        """List all available templates"""
        try:
            templates = []
            
            for file_path in self.templates_dir.glob("*.yaml"):
                template_data = self.read_template(file_path.stem)
                
                if template_data is None:
                    continue
                
                if category and template_data.get('category') != category:
                    continue
                
                metadata = TableTemplateMetadata(
                    name=template_data.get('name', file_path.stem),
                    category=template_data.get('category', 'unknown'),
                    description=template_data.get('description', ''),
                    version=template_data.get('version', '1.0.0'),
                    file_path=str(file_path)
                )
                templates.append(metadata)
            
            return templates
        
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return []
    
    def get_variations(self, template_name: str) -> List[Dict[str, Any]]:
        """Get all variations for a template"""
        template = self.read_template(template_name)
        if template is None:
            return []
        return template.get('variations', [])
    
    def get_variation(
        self,
        template_name: str,
        variation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific template variation"""
        variations = self.get_variations(template_name)
        
        for variation in variations:
            if variation.get('id') == variation_id:
                return variation
        
        return None
    
    # ==================== UPDATE ====================
    
    def update_template(self, name: str, updates: Dict[str, Any]) -> bool:
        """Update an existing template"""
        try:
            template_data = self.read_template(name, use_cache=False)
            
            if template_data is None:
                logger.warning(f"Template {name} not found")
                return False
            
            template_data.update(updates)
            
            file_path = self.templates_dir / f"{name}.yaml"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
            
            self._template_cache[name] = template_data
            logger.info(f"Template updated: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update template {name}: {e}")
            return False
    
    # ==================== DELETE ====================
    
    def delete_template(self, name: str) -> bool:
        """Delete a template"""
        try:
            file_path = self.templates_dir / f"{name}.yaml"
            
            if not file_path.exists():
                logger.warning(f"Template {name} not found")
                return False
            
            file_path.unlink()
            self._template_cache.pop(name, None)
            
            logger.info(f"Template deleted: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete template {name}: {e}")
            return False
    
    def clear_cache(self):
        """Clear template cache"""
        self._template_cache.clear()
        logger.info("Template cache cleared")


# Singleton instance
_table_template_manager: Optional[TableTemplateManager] = None


def get_table_template_manager() -> TableTemplateManager:
    """Get singleton instance of table template manager"""
    global _table_template_manager
    
    if _table_template_manager is None:
        _table_template_manager = TableTemplateManager()
    
    return _table_template_manager


# Test/demo
if __name__ == '__main__':
    manager = get_table_template_manager()
    
    print("="*60)
    print("Table Template Manager - Demo")
    print("="*60)
    
    print("\n📋 Available Templates:")
    templates = manager.list_templates()
    for template in templates:
        print(f"  - {template.name}: {template.description}")
    
    print("\n📖 Reading 'data_table' template:")
    data_table = manager.read_template('data_table')
    if data_table:
        print(f"  Variations: {len(data_table.get('variations', []))}")
        for var in data_table.get('variations', []):
            print(f"    - {var['id']}: {var['name']}")
    
    print("\n✅ Demo complete!")
