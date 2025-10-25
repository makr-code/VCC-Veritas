"""
Integration Test für Multi-Agent System

Testet die komplette Integration:
    - DatabaseAgentTestServerExtension
    - ImmissionsschutzAgentTestServerExtension
    - ImmissionsschutzOrchestrator

Version: 1.0
Datum: 18. Oktober 2025
"""

import asyncio
import sys
import os

# Path setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.agents.immissionsschutz_orchestrator import (
    get_orchestrator,
    PriorityLevel
)


async def test_integration():
    """Integration Test"""
    print("=" * 80)
    print("🧪 INTEGRATION TEST - Multi-Agent System")
    print("=" * 80)
    
    orchestrator = get_orchestrator()
    test_results = []
    
    try:
        # Test-Anlage
        bst_nr = "10686360000"
        anl_nr = "4001"
        
        print(f"\n📍 Test-Anlage: {bst_nr}/{anl_nr}")
        print("-" * 80)
        
        # Test 1: Comprehensive Analysis
        print("\n1️⃣ Test: Comprehensive Analysis")
        try:
            analysis = await orchestrator.comprehensive_analysis(bst_nr, anl_nr)
            
            assert analysis is not None, "Analysis should not be None"
            assert analysis.bst_nr == bst_nr, "BST_NR should match"
            assert analysis.anl_nr == anl_nr, "ANL_NR should match"
            assert 0.0 <= analysis.compliance_report.compliance_score <= 1.0, "Score should be 0-1"
            assert 0.0 <= analysis.risiko_analyse.risiko_score <= 1.0, "Risk score should be 0-1"
            
            print(f"   ✅ Analysis completed")
            print(f"      Compliance: {analysis.compliance_report.compliance_score:.0%}")
            print(f"      Risiko: {analysis.risiko_analyse.risiko_score:.0%}")
            print(f"      Priorität: {analysis.prioritaet.value}")
            print(f"      Empfehlungen: {len(analysis.handlungsempfehlungen)}")
            
            test_results.append(("Comprehensive Analysis", True, None))
        
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            test_results.append(("Comprehensive Analysis", False, str(e)))
        
        # Test 2: Compliance Workflow
        print("\n2️⃣ Test: Compliance Workflow")
        try:
            compliance = await orchestrator.compliance_workflow(bst_nr, anl_nr)
            
            assert compliance is not None, "Compliance should not be None"
            assert 'compliance_score' in compliance, "Should have compliance_score"
            assert 'verfahren' in compliance, "Should have verfahren"
            assert 'maengel_offen' in compliance, "Should have maengel_offen"
            
            print(f"   ✅ Workflow completed")
            print(f"      Score: {compliance['compliance_score']:.0%}")
            print(f"      Status: {compliance['compliance_status']}")
            print(f"      Verfahren: {compliance['verfahren']['total']}")
            print(f"      Offene Mängel: {compliance['maengel_offen']}")
            
            test_results.append(("Compliance Workflow", True, None))
        
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            test_results.append(("Compliance Workflow", False, str(e)))
        
        # Test 3: Maintenance Planning
        print("\n3️⃣ Test: Maintenance Planning")
        try:
            maintenance = await orchestrator.maintenance_planning(bst_nr, anl_nr, 90)
            
            assert maintenance is not None, "Maintenance should not be None"
            assert 'wartungen_durchgefuehrt' in maintenance, "Should have wartungen_durchgefuehrt"
            assert 'wartungen_geplant' in maintenance, "Should have wartungen_geplant"
            assert 'kritische_wartungen' in maintenance, "Should have kritische_wartungen"
            
            print(f"   ✅ Planning completed")
            print(f"      Durchgeführt: {maintenance['wartungen_durchgefuehrt']}")
            print(f"      Geplant: {maintenance['wartungen_geplant']}")
            print(f"      Kritisch: {maintenance['kritische_wartungen']}")
            print(f"      Empfehlungen: {len(maintenance['empfehlungen'])}")
            
            test_results.append(("Maintenance Planning", True, None))
        
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            test_results.append(("Maintenance Planning", False, str(e)))
        
        # Test 4: Emission Monitoring
        print("\n4️⃣ Test: Emission Monitoring")
        try:
            monitoring = await orchestrator.emission_monitoring(bst_nr, anl_nr)
            
            assert monitoring is not None, "Monitoring should not be None"
            assert 'messungen_total' in monitoring, "Should have messungen_total"
            assert 'ueberschreitungen' in monitoring, "Should have ueberschreitungen"
            assert 'kritische_trends' in monitoring, "Should have kritische_trends"
            
            print(f"   ✅ Monitoring completed")
            print(f"      Messungen: {monitoring['messungen_total']}")
            print(f"      Überschreitungen: {monitoring['ueberschreitungen']}")
            print(f"      Kritische Trends: {monitoring['kritische_trends']}")
            print(f"      Messreihen: {monitoring['messreihen_total']}")
            
            test_results.append(("Emission Monitoring", True, None))
        
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            test_results.append(("Emission Monitoring", False, str(e)))
        
        # Test 5: Workflow Tracking
        print("\n5️⃣ Test: Workflow Tracking")
        try:
            active_workflows = orchestrator.list_active_workflows()
            
            assert len(active_workflows) > 0, "Should have active workflows"
            
            total_success_rate = sum(wf.success_rate for wf in active_workflows) / len(active_workflows)
            
            print(f"   ✅ Tracking functional")
            print(f"      Active Workflows: {len(active_workflows)}")
            print(f"      Avg Success Rate: {total_success_rate:.1f}%")
            
            for wf in active_workflows[-3:]:
                print(f"      • {wf.workflow_type.value}: {wf.status.value} ({wf.success_rate:.0f}%)")
            
            test_results.append(("Workflow Tracking", True, None))
        
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            test_results.append(("Workflow Tracking", False, str(e)))
        
        # Ergebnisse zusammenfassen
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for _, success, _ in test_results if success)
        failed = len(test_results) - passed
        
        for test_name, success, error in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status}: {test_name}")
            if error:
                print(f"         Error: {error}")
        
        print("\n" + "-" * 80)
        print(f"Total: {passed}/{len(test_results)} tests passed ({passed/len(test_results)*100:.0f}%)")
        
        if failed == 0:
            print("\n🎉 ALLE TESTS ERFOLGREICH!")
            return True
        else:
            print(f"\n⚠️ {failed} TEST(S) FEHLGESCHLAGEN")
            return False
    
    except Exception as e:
        print(f"\n❌ KRITISCHER FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await orchestrator.close()
        print("\n" + "=" * 80)


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    sys.exit(0 if success else 1)
