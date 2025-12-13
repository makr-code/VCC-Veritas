"""
Tests for Presentation Template Manager (CRUD Operations)
"""

import pytest
import json
from pathlib import Path
import sys
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.agents.presentation_template_manager import (
    PresentationTemplateManager,
    TemplateMetadata,
    get_template_manager
)


class TestTemplateManagerCRUD:
    """Test CRUD operations for template manager"""
    
    def setup_method(self):
        """Setup test environment"""
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = PresentationTemplateManager(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_template(self):
        """Test creating a new template"""
        success = self.manager.create_template(
            name="test_template",
            category="test",
            description="Test template",
            variations=[
                {
                    "id": "var1",
                    "name": "Variation 1",
                    "structure": {}
                }
            ]
        )
        
        assert success is True
        assert (self.temp_dir / "test_template.yaml").exists()
    
    def test_read_template(self):
        """Test reading a template"""
        # Create template first
        self.manager.create_template(
            name="read_test",
            category="test",
            description="Read test",
            variations=[]
        )
        
        # Read it back
        template = self.manager.read_template("read_test")
        
        assert template is not None
        assert template['name'] == "read_test"
        assert template['category'] == "test"
    
    def test_update_template(self):
        """Test updating a template"""
        # Create template
        self.manager.create_template(
            name="update_test",
            category="test",
            description="Original description",
            variations=[]
        )
        
        # Update it
        success = self.manager.update_template(
            "update_test",
            {"description": "Updated description", "version": "2.0.0"}
        )
        
        assert success is True
        
        # Verify update
        template = self.manager.read_template("update_test", use_cache=False)
        assert template['description'] == "Updated description"
        assert template['version'] == "2.0.0"
    
    def test_delete_template(self):
        """Test deleting a template"""
        # Create template
        self.manager.create_template(
            name="delete_test",
            category="test",
            description="To be deleted",
            variations=[]
        )
        
        # Delete it
        success = self.manager.delete_template("delete_test")
        
        assert success is True
        assert not (self.temp_dir / "delete_test.yaml").exists()
    
    def test_list_templates(self):
        """Test listing templates"""
        # Create multiple templates
        self.manager.create_template(
            name="template1",
            category="cat1",
            description="Template 1",
            variations=[]
        )
        self.manager.create_template(
            name="template2",
            category="cat2",
            description="Template 2",
            variations=[]
        )
        
        # List all
        templates = self.manager.list_templates()
        assert len(templates) >= 2  # At least our 2 templates
        
        # Filter by category
        cat1_templates = self.manager.list_templates(category="cat1")
        assert len(cat1_templates) >= 1  # At least 1 template in cat1
        template_names = [t.name for t in cat1_templates]
        assert "template1" in template_names
    
    def test_get_categories(self):
        """Test getting categories"""
        self.manager.create_template(
            name="t1", category="cat_a", description="", variations=[]
        )
        self.manager.create_template(
            name="t2", category="cat_b", description="", variations=[]
        )
        self.manager.create_template(
            name="t3", category="cat_a", description="", variations=[]
        )
        
        categories = self.manager.get_categories()
        assert len(categories) == 2
        assert "cat_a" in categories
        assert "cat_b" in categories
    
    def test_get_variations(self):
        """Test getting template variations"""
        variations = [
            {"id": "var1", "name": "Variation 1"},
            {"id": "var2", "name": "Variation 2"}
        ]
        
        self.manager.create_template(
            name="var_test",
            category="test",
            description="",
            variations=variations
        )
        
        retrieved_variations = self.manager.get_variations("var_test")
        assert len(retrieved_variations) == 2
        assert retrieved_variations[0]['id'] == "var1"
    
    def test_get_variation(self):
        """Test getting specific variation"""
        variations = [
            {"id": "specific_var", "name": "Specific", "data": "test"}
        ]
        
        self.manager.create_template(
            name="specific_test",
            category="test",
            description="",
            variations=variations
        )
        
        variation = self.manager.get_variation("specific_test", "specific_var")
        assert variation is not None
        assert variation['name'] == "Specific"
        assert variation['data'] == "test"
    
    def test_search_templates(self):
        """Test searching templates"""
        self.manager.create_template(
            name="flowchart",
            category="process",
            description="Process flow diagrams",
            variations=[]
        )
        self.manager.create_template(
            name="orgchart",
            category="hierarchy",
            description="Organization charts",
            variations=[]
        )
        
        # Search for "flow"
        results = self.manager.search_templates("flow")
        assert len(results) >= 1
        assert any("flow" in r.name.lower() or "flow" in r.description.lower() 
                  for r in results)
    
    def test_export_import_json(self):
        """Test JSON export/import"""
        # Create template
        self.manager.create_template(
            name="export_test",
            category="test",
            description="For export",
            variations=[{"id": "v1"}]
        )
        
        # Export to JSON
        json_str = self.manager.export_template_to_json("export_test")
        assert json_str is not None
        assert "export_test" in json_str
        
        # Delete template
        self.manager.delete_template("export_test")
        
        # Import from JSON
        success = self.manager.import_template_from_json(json_str)
        assert success is True
        
        # Verify import
        template = self.manager.read_template("export_test")
        assert template is not None
        assert template['name'] == "export_test"
    
    def test_cache_functionality(self):
        """Test template caching"""
        self.manager.create_template(
            name="cache_test",
            category="test",
            description="Cache test",
            variations=[]
        )
        
        # First read (from disk)
        template1 = self.manager.read_template("cache_test", use_cache=False)
        
        # Second read (from cache)
        template2 = self.manager.read_template("cache_test", use_cache=True)
        
        assert template1 == template2
        
        # Clear cache
        self.manager.clear_cache()
        assert "cache_test" not in self.manager._template_cache


class TestExistingTemplates:
    """Test the actual template files in the repository"""
    
    def test_all_templates_loadable(self):
        """Test that all existing templates can be loaded"""
        manager = get_template_manager()
        templates = manager.list_templates()
        
        assert len(templates) > 0, "No templates found"
        
        for template_meta in templates:
            template = manager.read_template(template_meta.name)
            assert template is not None, f"Failed to load {template_meta.name}"
            assert 'name' in template
            assert 'category' in template
            assert 'variations' in template
    
    def test_template_structure_validity(self):
        """Test that templates have required fields"""
        manager = get_template_manager()
        
        required_fields = ['name', 'category', 'description', 'version', 'variations']
        
        for template_meta in manager.list_templates():
            template = manager.read_template(template_meta.name)
            
            for field in required_fields:
                assert field in template, f"{template_meta.name} missing {field}"
    
    def test_all_variations_valid(self):
        """Test that all variations have required structure"""
        manager = get_template_manager()
        
        for template_meta in manager.list_templates():
            variations = manager.get_variations(template_meta.name)
            
            assert len(variations) > 0, f"{template_meta.name} has no variations"
            
            for variation in variations:
                assert 'id' in variation, f"Variation missing 'id'"
                assert 'name' in variation, f"Variation missing 'name'"
                assert 'structure' in variation, f"Variation missing 'structure'"
    
    def test_categories_defined(self):
        """Test that categories are properly defined"""
        manager = get_template_manager()
        categories = manager.get_categories()
        
        expected_categories = [
            'cycle', 'hierarchy', 'list', 'matrix', 
            'processes', 'pyramid', 'relationship', 'spiderweb'
        ]
        
        for expected in expected_categories:
            assert expected in categories, f"Missing category: {expected}"


# Standalone test execution
if __name__ == '__main__':
    print("="*60)
    print("Template Manager Tests")
    print("="*60)
    
    # Run CRUD tests
    print("\n📝 Running CRUD Tests...")
    test_crud = TestTemplateManagerCRUD()
    
    test_crud.setup_method()
    try:
        test_crud.test_create_template()
        print("  ✅ Create test passed")
        
        test_crud.test_read_template()
        print("  ✅ Read test passed")
        
        test_crud.test_update_template()
        print("  ✅ Update test passed")
        
        test_crud.test_delete_template()
        print("  ✅ Delete test passed")
        
        test_crud.test_list_templates()
        print("  ✅ List test passed")
        
        test_crud.test_search_templates()
        print("  ✅ Search test passed")
        
        test_crud.test_export_import_json()
        print("  ✅ Export/Import test passed")
    finally:
        test_crud.teardown_method()
    
    # Run existing templates tests
    print("\n📂 Running Existing Templates Tests...")
    test_existing = TestExistingTemplates()
    
    test_existing.test_all_templates_loadable()
    print("  ✅ All templates loadable")
    
    test_existing.test_template_structure_validity()
    print("  ✅ All templates have valid structure")
    
    test_existing.test_all_variations_valid()
    print("  ✅ All variations valid")
    
    test_existing.test_categories_defined()
    print("  ✅ All categories defined")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
