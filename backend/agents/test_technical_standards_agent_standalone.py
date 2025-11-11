#!/usr/bin/env python3
"""
Test Suite für VERITAS Technical Standards Agent
Standalone Testing ohne FastAPI-Integration

Testet:
- ISO, DIN, VDE, EN, IEC, IEEE Standards-Suche
- Standard-Nummer basierte Suche
- Organisation-spezifische Suche
- Kategorie-basierte Suche
- Compliance-Bewertung und Gap-Analyse
- Anforderungs-Management
- Cache-Funktionalität

Autor: VERITAS Agent System
Datum: 28. September 2025
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Projekt-Root für Paketimporte sicherstellen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from backend.agents.veritas_api_agent_technical_standards import (
    ComplianceLevel,
    StandardCategory,
    StandardsOrganization,
    StandardsSearchRequest,
    StandardStatus,
    TechnicalStandardsAgent,
    TechnicalStandardsConfig,
    TechnicalStandardsRequest,
    TechnicalStandardsResponse,
    create_technical_standards_agent,
)


class TechnicalStandardsTestSuite:
    """Test Suite für Technical Standards Agent"""

    def __init__(self):
        self.agent = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def setup_agent(self):
        """Agent für Tests einrichten"""
        config = TechnicalStandardsConfig(
            cache_enabled=True,
            min_relevance_threshold=0.3,
            max_cache_size=100,
            request_timeout_seconds=15,
            compliance_threshold=0.7,
        )
        self.agent = create_technical_standards_agent(config)
        print("✅ Technical Standards Agent initialized for testing")

    async def run_test(self, test_name: str, test_function):
        """Einzelnen Test ausführen"""
        print(f"\n🔍 Running: {test_name}")
        print("-" * 50)

        self.total_tests += 1
        start_time = time.time()

        try:
            success = await test_function()
            execution_time = int((time.time() - start_time) * 1000)

            if success:
                print(f"✅ PASSED: {test_name} ({execution_time}ms)")
                self.passed_tests += 1
                self.test_results.append(
                    {"name": test_name, "status": "PASSED", "execution_time_ms": execution_time, "error": None}
                )
            else:
                print(f"❌ FAILED: {test_name} ({execution_time}ms)")
                self.test_results.append(
                    {
                        "name": test_name,
                        "status": "FAILED",
                        "execution_time_ms": execution_time,
                        "error": "Test function returned False",
                    }
                )

        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            print(f"❌ ERROR: {test_name} ({execution_time}ms)")
            print(f"   Error: {str(e)}")
            self.test_results.append(
                {"name": test_name, "status": "ERROR", "execution_time_ms": execution_time, "error": str(e)}
            )

    async def test_iso_standard_search(self) -> bool:
        """Test: ISO-Standard Suche"""
        request = StandardsSearchRequest(
            query_id="test-iso-9001",
            query_text="ISO 9001 Qualitätsmanagement",
            search_term="ISO 9001",
            organization=StandardsOrganization.ISO,
            include_requirements=True,
            max_results=1,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        if len(response.standards) == 0:
            print("❌ No standards found")
            return False

        standard = response.standards[0]
        print(f"📄 Found: {standard.identifier.standard_number}")
        print(f"   Title: {standard.identifier.full_title}")

        # Verify ISO organization
        if standard.identifier.organization != StandardsOrganization.ISO:
            print(f"❌ Organization mismatch: expected ISO, got {standard.identifier.organization}")
            return False

        print(f"   Organization: {standard.identifier.organization.value.upper()} ✓")

        # Check if it's ISO 9001
        if "9001" not in standard.identifier.standard_number:
            print(f"❌ Standard number mismatch: expected ISO 9001, got {standard.identifier.standard_number}")
            return False

        print(f"   Standard: {standard.identifier.standard_number} ✓")

        # Check status
        if not standard.is_current():
            print("⚠️  Standard is not current")
        else:
            print(f"   Status: {standard.status.value} ✓")

        # Check requirements
        if len(standard.requirements) == 0:
            print("❌ No requirements found")
            return False

        print(f"   Requirements: {len(standard.requirements)} found ✓")

        # Check categories
        if StandardCategory.QUALITY not in standard.categories:
            print("⚠️  Expected QUALITY category")
        else:
            print("   Category: QUALITY ✓")

        return True

    async def test_vde_standard_search(self) -> bool:
        """Test: VDE-Standard Suche"""
        request = StandardsSearchRequest(
            query_id="test-vde-0100",
            query_text="VDE 0100 Niederspannungsanlagen",
            search_term="VDE 0100",
            organization=StandardsOrganization.VDE,
            category=StandardCategory.ELECTRICAL,
            max_results=1,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        if len(response.standards) == 0:
            print("❌ No VDE standards found")
            return False

        standard = response.standards[0]
        print(f"📄 Found: {standard.identifier.standard_number}")

        # Verify VDE organization
        if standard.identifier.organization != StandardsOrganization.VDE:
            print(f"❌ Organization mismatch: expected VDE, got {standard.identifier.organization}")
            return False

        print("   Organization: VDE ✓")

        # Check electrical category
        if StandardCategory.ELECTRICAL not in standard.categories:
            print("❌ Expected ELECTRICAL category")
            return False

        print(f"   Category: ELECTRICAL ✓")

        # Check requirements with electrical focus
        electrical_requirements = [
            req for req in standard.requirements if "schutz" in req.title.lower() or "elektrisch" in req.description.lower()
        ]

        if electrical_requirements:
            print(f"   Electrical Requirements: {len(electrical_requirements)} found ✓")
            for req in electrical_requirements[:2]:
                print(f"      - {req.title} ({req.compliance_level.value})")

        return True

    async def test_organization_search(self) -> bool:
        """Test: Organisations-spezifische Suche"""
        request = StandardsSearchRequest(
            query_id="test-org-din",
            query_text="DIN Standards Suche",
            search_term="bau",
            organization=StandardsOrganization.DIN,
            max_results=5,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        print(f"📄 Found {len(response.standards)} DIN standards")

        # All should be DIN standards
        for standard in response.standards:
            if standard.identifier.organization != StandardsOrganization.DIN:
                print(f"❌ Non-DIN standard found: {standard.identifier.organization}")
                return False

        print("   All results are DIN standards ✓")

        # Check for construction-related standards
        construction_standards = [std for std in response.standards if StandardCategory.CONSTRUCTION in std.categories]

        if construction_standards:
            print(f"   Construction standards: {len(construction_standards)} found ✓")

        # Show top results
        for i, standard in enumerate(response.standards[:3], 1):
            print(f"   {i}. {standard.identifier.standard_number}: {standard.identifier.full_title}")
            print(f"      Relevance: {standard.relevance_score:.2f}")

        return True

    async def test_category_search(self) -> bool:
        """Test: Kategorie-basierte Suche"""
        request = StandardsSearchRequest(
            query_id="test-category-safety",
            query_text="Sicherheitsnormen",
            search_term="sicherheit",
            category=StandardCategory.SAFETY,
            max_results=5,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        print(f"📄 Found {len(response.standards)} safety standards")

        # All should have SAFETY category
        safety_standards = 0
        for standard in response.standards:
            if StandardCategory.SAFETY in standard.categories:
                safety_standards += 1

        if safety_standards == 0:
            print("❌ No safety standards found")
            return False

        print(f"   Safety standards: {safety_standards}/{len(response.standards)} ✓")

        # Check for safety-related requirements
        safety_requirements_count = 0
        for standard in response.standards:
            for req in standard.requirements:
                if any(
                    word in req.title.lower() or word in req.description.lower() for word in ["sicherheit", "safety", "schutz"]
                ):
                    safety_requirements_count += 1

        if safety_requirements_count > 0:
            print(f"   Safety requirements: {safety_requirements_count} found ✓")

        # Check organizations involved
        organizations = set(std.identifier.organization for std in response.standards)
        print(f"   Organizations: {', '.join(org.value.upper() for org in organizations)} ✓")

        return True

    async def test_standard_number_recognition(self) -> bool:
        """Test: Standard-Nummern Erkennung"""
        test_numbers = [
            ("ISO 9001", True),
            ("DIN EN 1090", True),
            ("VDE 0100", True),
            ("IEC 61508", True),
            ("IEEE 802.11", True),
            ("random text", False),
            ("123456", False),
        ]

        correct_recognitions = 0
        total_tests = len(test_numbers)

        for number, should_be_recognized in test_numbers:
            is_recognized = self.agent._is_standard_number(number)

            if is_recognized == should_be_recognized:
                correct_recognitions += 1
                status = "✓"
            else:
                status = "❌"

            print(f"   '{number}': {'Standard' if is_recognized else 'Not standard'} {status}")

        recognition_rate = correct_recognitions / total_tests
        print(f"   Recognition rate: {recognition_rate:.1%}")

        return recognition_rate >= 0.8

    async def test_compliance_assessment(self) -> bool:
        """Test: Compliance-Bewertung"""
        # First get a standard
        search_request = StandardsSearchRequest(
            query_id="test-compliance-iso",
            query_text="ISO Standard für Compliance Test",
            search_term="ISO 9001",
            organization=StandardsOrganization.ISO,
            max_results=1,
        )

        search_response = await self.agent.search_standards_async(search_request)

        if not search_response.success or len(search_response.standards) == 0:
            print("❌ Could not get standard for compliance test")
            return False

        # Request with compliance assessment
        compliance_request = StandardsSearchRequest(
            query_id="test-compliance-assessment",
            query_text="Compliance Assessment for Manufacturing",
            search_term="ISO 9001",
            product_scope="Automotive Manufacturing",
            max_results=1,
        )

        response = await self.agent.search_standards_async(compliance_request)

        if not response.success:
            print(f"❌ Compliance query failed: {response.error_message}")
            return False

        if not response.compliance_assessment:
            print("❌ No compliance assessment generated")
            return False

        assessment = response.compliance_assessment
        print(f"📊 Compliance Assessment: {assessment.target_standard}")
        print(f"   Overall compliance: {assessment.overall_compliance_level:.1%}")
        print(f"   Compliant requirements: {assessment.compliant_requirements}")
        print(f"   Non-compliant requirements: {assessment.non_compliant_requirements}")
        print(f"   Partial compliance: {assessment.partial_compliance}")
        print(f"   Total requirements: {assessment.total_requirements}")

        # Verify numbers add up
        total_check = assessment.compliant_requirements + assessment.non_compliant_requirements + assessment.partial_compliance

        if total_check != assessment.total_requirements:
            print(f"❌ Requirement count mismatch: {total_check} != {assessment.total_requirements}")
            return False

        print("   Requirement counts: ✓")

        # Check certification readiness
        if assessment.certification_readiness > 0:
            print(f"   Certification readiness: {assessment.certification_readiness:.1%} ✓")

        # Check gaps and recommendations
        if assessment.compliance_gaps:
            print(f"   Compliance gaps: {len(assessment.compliance_gaps)} identified ✓")

        if assessment.recommendations:
            print(f"   Recommendations: {len(assessment.recommendations)} provided ✓")
            for rec in assessment.recommendations[:2]:
                print(f"      - {rec}")

        return True

    async def test_requirements_analysis(self) -> bool:
        """Test: Anforderungs-Analyse"""
        request = StandardsSearchRequest(
            query_id="test-requirements",
            query_text="Standard mit Anforderungen",
            search_term="IEC 61508",
            organization=StandardsOrganization.IEC,
            include_requirements=True,
            max_results=1,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success or len(response.standards) == 0:
            print("❌ Could not get standard with requirements")
            return False

        standard = response.standards[0]
        print(f"📄 Analyzing requirements for: {standard.identifier.standard_number}")

        if len(standard.requirements) == 0:
            print("❌ No requirements found")
            return False

        print(f"   Total requirements: {len(standard.requirements)}")

        # Analyze by compliance level
        mandatory_reqs = standard.get_mandatory_requirements()
        recommended_reqs = [req for req in standard.requirements if req.compliance_level == ComplianceLevel.RECOMMENDED]
        optional_reqs = [req for req in standard.requirements if req.compliance_level == ComplianceLevel.OPTIONAL]

        print(f"   Mandatory: {len(mandatory_reqs)}")
        print(f"   Recommended: {len(recommended_reqs)}")
        print(f"   Optional: {len(optional_reqs)}")

        # Check requirement structure
        requirements_with_tests = [req for req in standard.requirements if req.test_methods]
        requirements_with_docs = [req for req in standard.requirements if req.documentation_required]

        if requirements_with_tests:
            print(f"   With test methods: {len(requirements_with_tests)} ✓")

        if requirements_with_docs:
            print(f"   With documentation: {len(requirements_with_docs)} ✓")

        # Show sample requirements
        print("   Sample requirements:")
        for req in standard.requirements[:3]:
            print(f"      - {req.section}: {req.title}")
            print(f"        Level: {req.compliance_level.value}")
            if req.test_methods:
                print(f"        Tests: {', '.join(req.test_methods)}")

        return len(mandatory_reqs) > 0

    async def test_related_standards(self) -> bool:
        """Test: Verwandte Standards"""
        request = StandardsSearchRequest(
            query_id="test-related",
            query_text="Standard mit verwandten Normen",
            search_term="ISO 14001",
            include_related_standards=True,
            max_results=1,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success or len(response.standards) == 0:
            print("❌ Could not get standard")
            return False

        standard = response.standards[0]
        print(f"📄 Analyzing related standards for: {standard.identifier.standard_number}")

        # Check related standards
        if standard.related_standards:
            print(f"   Related standards: {len(standard.related_standards)} found ✓")
            for related in standard.related_standards[:3]:
                print(f"      - {related}")
        else:
            print("   No related standards found")

        # Check supersedes/superseded by
        if standard.supersedes:
            print(f"   Supersedes: {len(standard.supersedes)} standards")

        if standard.superseded_by:
            print(f"   Superseded by: {len(standard.superseded_by)} standards")

        # Check references
        if standard.referenced_by:
            print(f"   Referenced by: {len(standard.referenced_by)} standards")

        return True

    async def test_cache_functionality(self) -> bool:
        """Test: Cache-Funktionalität"""
        print("📄 Testing cache functionality")

        # First request
        request1 = StandardsSearchRequest(
            query_id="test-cache-1", query_text="Cache test 1", search_term="ISO 9001", max_results=1
        )

        start_time = time.time()
        response1 = await self.agent.search_standards_async(request1)
        time1 = int((time.time() - start_time) * 1000)

        if not response1.success:
            print("❌ First request failed")
            return False

        print(f"   First request: {time1}ms")

        # Second identical request (should hit cache)
        request2 = StandardsSearchRequest(
            query_id="test-cache-2", query_text="Cache test 2", search_term="ISO 9001", max_results=1
        )

        start_time = time.time()
        response2 = await self.agent.search_standards_async(request2)
        time2 = int((time.time() - start_time) * 1000)

        if not response2.success:
            print("❌ Second request failed")
            return False

        print(f"   Second request: {time2}ms")

        # Cache should make second request faster
        if time2 < time1:
            print("   ✅ Cache hit detected (faster response)")
        else:
            print("   ⚠️  No clear cache benefit detected")

        # Verify same results
        if len(response1.standards) != len(response2.standards):
            print("❌ Different number of standards returned")
            return False

        if response1.standards and response2.standards:
            if response1.standards[0].standard_id != response2.standards[0].standard_id:
                print("❌ Different standards returned")
                return False

        print("   ✅ Cache returns consistent results")

        return True

    async def test_error_handling(self) -> bool:
        """Test: Error Handling"""
        print("📄 Testing error handling")

        # Test with invalid organization search
        request = StandardsSearchRequest(
            query_id="test-error-invalid", query_text="Invalid search", search_term="nonexistentstandard12345", max_results=1
        )

        response = await self.agent.search_standards_async(request)

        # Should not crash, but may not find anything
        if response.success and len(response.standards) == 0:
            print("   ✅ Gracefully handles non-existent standards")
        elif not response.success:
            print("   ✅ Appropriately reports failure for invalid searches")
        else:
            print("   ⚠️  Unexpected success for non-existent standard")

        # Test with empty search term
        request2 = StandardsSearchRequest(
            query_id="test-error-empty", query_text="Empty search", search_term="", max_results=1
        )

        response2 = await self.agent.search_standards_async(request2)

        # Should handle gracefully
        if not response2.success or len(response2.standards) == 0:
            print("   ✅ Gracefully handles empty search terms")

        return True

    async def test_multi_organization_search(self) -> bool:
        """Test: Multi-Organisation Suche"""
        request = StandardsSearchRequest(
            query_id="test-multi-org",
            query_text="Multi-organization search",
            search_term="management",
            organization=None,  # Search all organizations
            max_results=10,
        )

        response = await self.agent.search_standards_async(request)

        if not response.success:
            print(f"❌ Multi-org query failed: {response.error_message}")
            return False

        print(f"📄 Found {len(response.standards)} standards across organizations")

        # Check diversity of organizations
        organizations = set(std.identifier.organization for std in response.standards)
        print(f"   Organizations represented: {len(organizations)}")

        org_counts = {}
        for std in response.standards:
            org = std.identifier.organization.value.upper()
            org_counts[org] = org_counts.get(org, 0) + 1

        for org, count in org_counts.items():
            print(f"      {org}: {count} standards")

        # Should have standards from multiple organizations
        if len(organizations) > 1:
            print("   ✅ Multiple organizations represented")
        else:
            print("   ⚠️  Only one organization found")

        return len(response.standards) > 0

    def print_summary(self):
        """Test-Zusammenfassung ausgeben"""
        print("\n" + "=" * 60)
        print("🔍 TECHNICAL STANDARDS AGENT TEST SUMMARY")
        print("=" * 60)

        success_rate = (self.passed_tests / self.total_tests) * 100 if self.total_tests > 0 else 0

        print(f"📊 Tests run: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.total_tests - self.passed_tests}")
        print(f"📈 Success rate: {success_rate:.1f}%")

        # Execution times
        if self.test_results:
            total_time = sum(result["execution_time_ms"] for result in self.test_results)
            avg_time = total_time / len(self.test_results)
            print(f"⏱️  Total execution time: {total_time}ms")
            print(f"⏱️  Average per test: {avg_time:.1f}ms")

        # Agent status
        if self.agent:
            status = self.agent.get_status()
            print("\n📊 Agent Performance:")
            print(f"   Queries processed: {status['performance']['queries_processed']}")
            print(f"   Standards found: {status['performance']['standards_found']}")
            print(f"   Compliance assessments: {status['performance']['compliance_assessments']}")
            print(f"   Cache hits: {status['performance']['cache_hits']}")
            print(f"   Success rate: {status['performance']['success_rate']:.2%}")

        # Individual test results
        print("\n📋 Individual Results:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            print(f"   {status_icon} {result['name']} ({result['execution_time_ms']}ms)")
            if result["error"]:
                print(f"      Error: {result['error']}")

        print("\n" + "=" * 60)

        if success_rate >= 80:
            print("🎉 Technical Standards Agent is working excellently!")
        elif success_rate >= 60:
            print("👍 Technical Standards Agent is working well with minor issues")
        else:
            print("⚠️  Technical Standards Agent needs attention")


async def main():
    """Hauptfunktion"""
    print("🔍 VERITAS Technical Standards Agent - Standalone Test Suite")
    print("=" * 60)
    print("Testing technical standards search and compliance assessment...")
    print()

    # Test Suite erstellen
    test_suite = TechnicalStandardsTestSuite()

    # Agent einrichten
    test_suite.setup_agent()

    # Tests ausführen
    tests = [
        ("ISO Standard Search", test_suite.test_iso_standard_search),
        ("VDE Standard Search", test_suite.test_vde_standard_search),
        ("Organization Search", test_suite.test_organization_search),
        ("Category Search", test_suite.test_category_search),
        ("Standard Number Recognition", test_suite.test_standard_number_recognition),
        ("Compliance Assessment", test_suite.test_compliance_assessment),
        ("Requirements Analysis", test_suite.test_requirements_analysis),
        ("Related Standards", test_suite.test_related_standards),
        ("Cache Functionality", test_suite.test_cache_functionality),
        ("Error Handling", test_suite.test_error_handling),
        ("Multi-Organization Search", test_suite.test_multi_organization_search),
    ]

    for test_name, test_function in tests:
        await test_suite.run_test(test_name, test_function)

    # Zusammenfassung
    test_suite.print_summary()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Run test suite
    asyncio.run(main())
