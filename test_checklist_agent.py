#!/usr/bin/env python3
"""
Test script for ChecklistAgent functionality
===========================================

Tests the checklist generation without requiring full backend setup.

Author: VERITAS Development Team
Date: December 2025
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_intent_detection():
    """Test NLP intent detection for checklist queries"""
    print("=" * 80)
    print("TEST 1: Intent Detection for Checklist Queries")
    print("=" * 80)
    
    from backend.services.nlp_service import NLPService
    from backend.models.nlp_models import IntentType
    
    nlp = NLPService()
    
    test_queries = [
        "Erstelle eine Checkliste für Bauantrag",
        "Checkliste für Genehmigungsverfahren",
        "Was muss ich beachten bei Umweltgenehmigung",
        "Welche Schritte sind nötig für Bauvoranfrage",
        "Generiere Compliance Checkliste",
    ]
    
    print("\nTesting checklist intent detection:\n")
    for query in test_queries:
        result = nlp.analyze(query)
        print(f"Query: '{query}'")
        print(f"  Intent: {result.intent.intent_type.value}")
        print(f"  Confidence: {result.intent.confidence:.2%}")
        print(f"  Is Checklist: {result.intent.intent_type == IntentType.CHECKLIST_GENERATION}")
        print()
    
    print("✅ Intent detection test completed")


def test_checklist_agent_creation():
    """Test ChecklistAgent can be created"""
    print("\n" + "=" * 80)
    print("TEST 2: ChecklistAgent Creation")
    print("=" * 80 + "\n")
    
    from backend.agents.specialized.checklist_agent import create_checklist_agent
    
    try:
        agent = create_checklist_agent(
            config={"model": "llama3.2", "temperature": 0.3}
        )
        print(f"Agent created: {agent.agent_id}")
        print(f"Agent type: {agent.get_agent_type()}")
        print(f"Capabilities: {', '.join(agent.get_capabilities()[:5])}...")
        print("\n✅ ChecklistAgent creation test passed")
        return agent
    except Exception as e:
        print(f"❌ ChecklistAgent creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_template_checklist():
    """Test template-based checklist generation (without LLM)"""
    print("\n" + "=" * 80)
    print("TEST 3: Template-Based Checklist Generation")
    print("=" * 80 + "\n")
    
    from backend.agents.specialized.checklist_agent import create_checklist_agent
    
    try:
        agent = create_checklist_agent()
        
        # Generate simple checklist without ThemisDB or LLM
        result = agent._generate_template_checklist(
            topic="Bauantrag für Einfamilienhaus",
            checklist_type="construction",
            themisdb_data={},
            regulations_data={}
        )
        
        print(f"Generated checklist:")
        print(f"  Title: {result['title']}")
        print(f"  Type: {result['checklist_type']}")
        print(f"  Categories: {len(result['categories'])}")
        
        for cat in result['categories']:
            print(f"\n  Category: {cat['category_name']}")
            print(f"    Items: {len(cat['items'])}")
            for item in cat['items'][:2]:  # Show first 2 items
                print(f"      - {item['title']}")
        
        print("\n✅ Template checklist generation test passed")
        return result
    except Exception as e:
        print(f"❌ Template checklist generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_request_response_models():
    """Test request/response models can be created"""
    print("\n" + "=" * 80)
    print("TEST 4: Request/Response Models")
    print("=" * 80 + "\n")
    
    from backend.models.request import ChecklistGenerationRequest
    from backend.models.response import (
        ChecklistGenerationResponse, 
        ChecklistData, 
        ChecklistCategory, 
        ChecklistItem
    )
    
    try:
        # Create request
        request = ChecklistGenerationRequest(
            topic="Bauantrag",
            checklist_type="construction",
            include_regulations=True,
            include_themisdb=True
        )
        print(f"Request created:")
        print(f"  Topic: {request.topic}")
        print(f"  Type: {request.checklist_type}")
        
        # Create checklist data
        item = ChecklistItem(
            item_id=1,
            title="Grundriss einreichen",
            description="Bauplan mit Maßstab 1:100",
            required=True,
            priority="high"
        )
        
        category = ChecklistCategory(
            category_name="Dokumente",
            items=[item]
        )
        
        checklist = ChecklistData(
            title="Bauantrag Checkliste",
            description="Checkliste für Bauantrag",
            checklist_type="construction",
            categories=[category]
        )
        
        response = ChecklistGenerationResponse(
            status="success",
            checklist=checklist,
            sources=["Template"]
        )
        
        print(f"\nResponse created:")
        print(f"  Status: {response.status}")
        print(f"  Checklist title: {response.checklist.title}")
        print(f"  Categories: {len(response.checklist.categories)}")
        print(f"  Items: {len(response.checklist.categories[0].items)}")
        
        print("\n✅ Request/Response models test passed")
        return True
    except Exception as e:
        print(f"❌ Request/Response models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("CHECKLIST AGENT TEST SUITE")
    print("=" * 80 + "\n")
    
    tests_passed = 0
    tests_total = 4
    
    # Test 1: Intent detection
    try:
        test_intent_detection()
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Agent creation
    try:
        agent = test_checklist_agent_creation()
        if agent:
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Template generation
    try:
        result = test_template_checklist()
        if result:
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")
    
    # Test 4: Models
    try:
        if test_request_response_models():
            tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4 failed: {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print(f"TEST SUMMARY: {tests_passed}/{tests_total} tests passed")
    print("=" * 80)
    
    if tests_passed == tests_total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {tests_total - tests_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
