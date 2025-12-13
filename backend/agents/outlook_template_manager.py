"""
Outlook Template Manager - CRUD operations for Outlook templates

Manages email, calendar, task, and contact templates for the Outlook Agent.
"""

import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class OutlookTemplateManager:
    """
    Manager for Outlook templates (emails, calendar events, tasks, contacts)
    
    Provides CRUD operations for template management.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize Outlook Template Manager
        
        Args:
            templates_dir: Directory containing template YAML files
        """
        if templates_dir is None:
            self.templates_dir = Path(__file__).parent / "outlook_templates"
        else:
            self.templates_dir = Path(templates_dir)
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._cache = {}
        
        logger.info(f"OutlookTemplateManager initialized with dir: {self.templates_dir}")
    
    def create_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """
        Create a new template
        
        Args:
            template_id: Unique identifier for template
            template_data: Template configuration data
            
        Returns:
            True if created successfully
        """
        try:
            template_path = self.templates_dir / f"{template_id}.yaml"
            
            if template_path.exists():
                logger.warning(f"Template {template_id} already exists")
                return False
            
            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)
            
            # Invalidate cache
            self._cache.pop(template_id, None)
            
            logger.info(f"Created template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template {template_id}: {e}")
            return False
    
    def read_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a template
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template data or None if not found
        """
        # Check cache first
        if template_id in self._cache:
            return self._cache[template_id]
        
        try:
            template_path = self.templates_dir / f"{template_id}.yaml"
            
            if not template_path.exists():
                logger.warning(f"Template {template_id} not found")
                return None
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            # Cache the result
            self._cache[template_id] = template_data
            
            return template_data
            
        except Exception as e:
            logger.error(f"Error reading template {template_id}: {e}")
            return None
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """
        Update an existing template
        
        Args:
            template_id: Template identifier
            template_data: New template data
            
        Returns:
            True if updated successfully
        """
        try:
            template_path = self.templates_dir / f"{template_id}.yaml"
            
            if not template_path.exists():
                logger.warning(f"Template {template_id} not found for update")
                return False
            
            with open(template_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, allow_unicode=True, sort_keys=False)
            
            # Invalidate cache
            self._cache.pop(template_id, None)
            
            logger.info(f"Updated template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template
        
        Args:
            template_id: Template identifier
            
        Returns:
            True if deleted successfully
        """
        try:
            template_path = self.templates_dir / f"{template_id}.yaml"
            
            if not template_path.exists():
                logger.warning(f"Template {template_id} not found for deletion")
                return False
            
            template_path.unlink()
            
            # Invalidate cache
            self._cache.pop(template_id, None)
            
            logger.info(f"Deleted template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False
    
    def list_templates(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all templates, optionally filtered by category
        
        Args:
            category: Optional category filter (email, calendar, task, contact)
            
        Returns:
            List of template summaries
        """
        templates = []
        
        try:
            for template_file in self.templates_dir.glob("*.yaml"):
                template_id = template_file.stem
                template_data = self.read_template(template_id)
                
                if template_data is None:
                    continue
                
                # Filter by category if specified
                if category and template_data.get('category') != category:
                    continue
                
                templates.append({
                    'id': template_id,
                    'category': template_data.get('category', 'unknown'),
                    'name': template_data.get('name', template_id),
                    'description': template_data.get('description', '')
                })
            
            logger.info(f"Listed {len(templates)} templates (category={category})")
            return templates
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """
        Search templates by query
        
        Args:
            query: Search query
            
        Returns:
            List of matching template summaries
        """
        query_lower = query.lower()
        templates = self.list_templates()
        
        matches = []
        for template in templates:
            if (query_lower in template['id'].lower() or
                query_lower in template['name'].lower() or
                query_lower in template['description'].lower()):
                matches.append(template)
        
        logger.info(f"Search '{query}' found {len(matches)} templates")
        return matches
    
    def export_templates(self, output_path: Path) -> bool:
        """
        Export all templates to JSON file
        
        Args:
            output_path: Path to output JSON file
            
        Returns:
            True if exported successfully
        """
        try:
            all_templates = {}
            
            for template_file in self.templates_dir.glob("*.yaml"):
                template_id = template_file.stem
                template_data = self.read_template(template_id)
                
                if template_data:
                    all_templates[template_id] = template_data
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_templates, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(all_templates)} templates to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting templates: {e}")
            return False
    
    def import_templates(self, input_path: Path) -> bool:
        """
        Import templates from JSON file
        
        Args:
            input_path: Path to input JSON file
            
        Returns:
            True if imported successfully
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                all_templates = json.load(f)
            
            count = 0
            for template_id, template_data in all_templates.items():
                if self.create_template(template_id, template_data):
                    count += 1
            
            logger.info(f"Imported {count}/{len(all_templates)} templates from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing templates: {e}")
            return False
    
    def clear_cache(self):
        """Clear the template cache"""
        self._cache.clear()
        logger.info("Template cache cleared")


# Singleton instance
_outlook_template_manager = None


@lru_cache(maxsize=1)
def get_outlook_template_manager() -> OutlookTemplateManager:
    """
    Get singleton instance of OutlookTemplateManager
    
    Returns:
        OutlookTemplateManager instance
    """
    global _outlook_template_manager
    if _outlook_template_manager is None:
        _outlook_template_manager = OutlookTemplateManager()
    return _outlook_template_manager
