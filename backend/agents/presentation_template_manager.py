"""
Presentation Template Manager - CRUD Operations for Diagram Templates

This module provides Create, Read, Update, Delete operations for 
presentation diagram templates stored as YAML files.

Templates are organized by category:
- List: Bullet points, numbered lists
- Processes: Process flows, workflows
- Cycle: Circular diagrams, PDCA
- Hierarchy: Org charts, tree diagrams
- Relationship: Venn diagrams, network diagrams
- Matrix: SWOT, 2x2, 3x3 grids
- Pyramid: Hierarchical layers
- Spiderweb: Radar charts, competency webs
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TemplateMetadata:
    """Template metadata information"""
    name: str
    category: str
    description: str
    version: str
    file_path: str


class PresentationTemplateManager:
    """
    CRUD Manager for presentation diagram templates
    
    Manages loading, saving, and querying of template definitions
    stored in YAML format.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager
        
        Args:
            templates_dir: Directory containing template YAML files
                          Defaults to backend/agents/presentation_templates/
        """
        if templates_dir is None:
            current_file = Path(__file__)
            self.templates_dir = current_file.parent / "presentation_templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._template_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"PresentationTemplateManager initialized: {self.templates_dir}")
    
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
        """
        Create a new template
        
        Args:
            name: Template name (e.g., "list", "process")
            category: Template category
            description: Template description
            variations: List of template variations
            version: Template version
            **kwargs: Additional template properties
            
        Returns:
            True if created successfully, False otherwise
        """
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
                logger.warning(f"Template {name} already exists, use update() instead")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
            
            # Update cache
            self._template_cache[name] = template_data
            
            logger.info(f"Template created: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to create template {name}: {e}", exc_info=True)
            return False
    
    # ==================== READ ====================
    
    def read_template(self, name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Read a template by name
        
        Args:
            name: Template name
            use_cache: Use cached version if available
            
        Returns:
            Template data or None if not found
        """
        try:
            # Check cache first
            if use_cache and name in self._template_cache:
                return self._template_cache[name]
            
            file_path = self.templates_dir / f"{name}.yaml"
            
            if not file_path.exists():
                logger.warning(f"Template {name} not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # Update cache
            self._template_cache[name] = template_data
            
            return template_data
        
        except Exception as e:
            logger.error(f"Failed to read template {name}: {e}", exc_info=True)
            return None
    
    def list_templates(self, category: Optional[str] = None) -> List[TemplateMetadata]:
        """
        List all available templates
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of template metadata
        """
        try:
            templates = []
            
            for file_path in self.templates_dir.glob("*.yaml"):
                template_data = self.read_template(file_path.stem)
                
                if template_data is None:
                    continue
                
                # Filter by category if specified
                if category and template_data.get('category') != category:
                    continue
                
                metadata = TemplateMetadata(
                    name=template_data.get('name', file_path.stem),
                    category=template_data.get('category', 'unknown'),
                    description=template_data.get('description', ''),
                    version=template_data.get('version', '1.0.0'),
                    file_path=str(file_path)
                )
                templates.append(metadata)
            
            return templates
        
        except Exception as e:
            logger.error(f"Failed to list templates: {e}", exc_info=True)
            return []
    
    def get_categories(self) -> List[str]:
        """
        Get list of all template categories
        
        Returns:
            List of unique categories
        """
        try:
            categories = set()
            
            for template in self.list_templates():
                categories.add(template.category)
            
            return sorted(list(categories))
        
        except Exception as e:
            logger.error(f"Failed to get categories: {e}", exc_info=True)
            return []
    
    def get_variations(self, template_name: str) -> List[Dict[str, Any]]:
        """
        Get all variations for a template
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of template variations
        """
        template = self.read_template(template_name)
        
        if template is None:
            return []
        
        return template.get('variations', [])
    
    def get_variation(
        self,
        template_name: str,
        variation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific template variation
        
        Args:
            template_name: Name of the template
            variation_id: ID of the variation
            
        Returns:
            Variation data or None if not found
        """
        variations = self.get_variations(template_name)
        
        for variation in variations:
            if variation.get('id') == variation_id:
                return variation
        
        return None
    
    # ==================== UPDATE ====================
    
    def update_template(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update an existing template
        
        Args:
            name: Template name
            updates: Dictionary of updates to apply
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            template_data = self.read_template(name, use_cache=False)
            
            if template_data is None:
                logger.warning(f"Template {name} not found, use create() instead")
                return False
            
            # Apply updates
            template_data.update(updates)
            
            # Save updated template
            file_path = self.templates_dir / f"{name}.yaml"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
            
            # Update cache
            self._template_cache[name] = template_data
            
            logger.info(f"Template updated: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to update template {name}: {e}", exc_info=True)
            return False
    
    # ==================== DELETE ====================
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template
        
        Args:
            name: Template name
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.templates_dir / f"{name}.yaml"
            
            if not file_path.exists():
                logger.warning(f"Template {name} not found")
                return False
            
            file_path.unlink()
            
            # Remove from cache
            self._template_cache.pop(name, None)
            
            logger.info(f"Template deleted: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete template {name}: {e}", exc_info=True)
            return False
    
    # ==================== SEARCH & QUERY ====================
    
    def search_templates(
        self,
        query: str,
        search_fields: Optional[List[str]] = None
    ) -> List[TemplateMetadata]:
        """
        Search templates by keyword
        
        Args:
            query: Search query
            search_fields: Fields to search (name, category, description)
            
        Returns:
            List of matching templates
        """
        if search_fields is None:
            search_fields = ['name', 'category', 'description']
        
        query_lower = query.lower()
        results = []
        
        for template in self.list_templates():
            for field in search_fields:
                field_value = getattr(template, field, '').lower()
                if query_lower in field_value:
                    results.append(template)
                    break
        
        return results
    
    # ==================== EXPORT & IMPORT ====================
    
    def export_template_to_json(self, name: str) -> Optional[str]:
        """
        Export template as JSON string
        
        Args:
            name: Template name
            
        Returns:
            JSON string or None if template not found
        """
        template = self.read_template(name)
        
        if template is None:
            return None
        
        return json.dumps(template, indent=2)
    
    def import_template_from_json(
        self,
        json_str: str,
        overwrite: bool = False
    ) -> bool:
        """
        Import template from JSON string
        
        Args:
            json_str: JSON template data
            overwrite: Overwrite if template exists
            
        Returns:
            True if imported successfully, False otherwise
        """
        try:
            template_data = json.loads(json_str)
            name = template_data.get('name')
            
            if not name:
                logger.error("Template must have a 'name' field")
                return False
            
            file_path = self.templates_dir / f"{name}.yaml"
            
            if file_path.exists() and not overwrite:
                logger.warning(f"Template {name} already exists, set overwrite=True")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)
            
            # Update cache
            self._template_cache[name] = template_data
            
            logger.info(f"Template imported: {name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to import template: {e}", exc_info=True)
            return False
    
    # ==================== UTILITY ====================
    
    def clear_cache(self):
        """Clear template cache"""
        self._template_cache.clear()
        logger.info("Template cache cleared")
    
    def reload_all(self):
        """Reload all templates from disk"""
        self.clear_cache()
        
        for template_metadata in self.list_templates():
            self.read_template(template_metadata.name, use_cache=False)
        
        logger.info(f"Reloaded {len(self._template_cache)} templates")


# Singleton instance
_template_manager: Optional[PresentationTemplateManager] = None


def get_template_manager() -> PresentationTemplateManager:
    """Get singleton instance of template manager"""
    global _template_manager
    
    if _template_manager is None:
        _template_manager = PresentationTemplateManager()
    
    return _template_manager


# Standalone test/demo
if __name__ == '__main__':
    import sys
    
    # Initialize manager
    manager = get_template_manager()
    
    print("="*60)
    print("Presentation Template Manager - Demo")
    print("="*60)
    
    # List all templates
    print("\n📋 Available Templates:")
    templates = manager.list_templates()
    for template in templates:
        print(f"  - {template.name} ({template.category}): {template.description}")
    
    # List categories
    print("\n📂 Categories:")
    categories = manager.get_categories()
    for category in categories:
        print(f"  - {category}")
    
    # Read a specific template
    print("\n📖 Reading 'process' template:")
    process_template = manager.read_template('process')
    if process_template:
        print(f"  Name: {process_template['name']}")
        print(f"  Category: {process_template['category']}")
        print(f"  Variations: {len(process_template.get('variations', []))}")
        
        # List variations
        print("\n  Variations:")
        for var in process_template.get('variations', []):
            print(f"    - {var['id']}: {var['name']}")
    
    # Search templates
    print("\n🔍 Search for 'flow':")
    results = manager.search_templates('flow')
    for result in results:
        print(f"  - {result.name}: {result.description}")
    
    # Export to JSON
    print("\n💾 Export 'cycle' template to JSON:")
    json_export = manager.export_template_to_json('cycle')
    if json_export:
        print(f"  Exported {len(json_export)} characters")
    
    print("\n" + "="*60)
    print("✅ Demo complete!")
