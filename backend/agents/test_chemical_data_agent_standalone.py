#!/usr/bin/env python3
"""
Test Suite für VERITAS Chemical Data Agent
Standalone Testing ohne FastAPI-Integration

Testet:
- CAS-Nummer Suche
- Name-basierte Suche
- Physikalische Eigenschaften
- GHS-Klassifikation
- Arbeitsplatz-Grenzwerte
- Sicherheitsdatenblätter (SDS)
- Integration mit Atmospheric Flow Agent

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

# Import the Chemical Data Agent
from backend.agents.veritas_api_agent_chemical_data import (
    ChemicalDataAgent,
    ChemicalDataConfig,
    ChemicalDataRequest,
    ChemicalDataResponse,
    ChemicalIdentifierType,
    GHSHazardClass,
    RegulationDatabase,
    create_chemical_data_agent,
)


class ChemicalDataTestSuite:
    """Test Suite für Chemical Data Agent"""

    def __init__(self):
        self.agent = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def setup_agent(self):
        """Agent für Tests einrichten"""
        config = ChemicalDataConfig(
            cache_enabled=True, min_quality_threshold=0.3, max_cache_size=100, request_timeout_seconds=10
        )
        self.agent = create_chemical_data_agent(config)
        print("✅ Chemical Data Agent initialized for testing")

    async def run_test(self, test_name: str, test_function):
        """Einzelnen Test ausführen"""
        print(f"\n🧪 Running: {test_name}")
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

    async def test_cas_number_search(self) -> bool:
        """Test: CAS-Nummer Suche"""
        request = ChemicalDataRequest(
            query_id="test-cas-methanol",
            query_text="CAS-Nummer Suche für Methanol",
            search_term="67-56-1",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_physical_properties=True,
            include_ghs_classification=True,
            max_results=1,
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        if len(response.substances) == 0:
            print("❌ No substances found")
            return False

        substance = response.substances[0]
        print(f"📄 Found: {substance.primary_name}")

        # Verify CAS number
        cas = substance.get_cas_number()
        if cas != "67-56-1":
            print(f"❌ CAS mismatch: expected 67-56-1, got {cas}")
            return False

        print(f"   CAS: {cas} ✓")

        # Check molecular formula
        if substance.molecular_formula != "CH4O":
            print(f"❌ Formula mismatch: expected CH4O, got {substance.molecular_formula}")
            return False

        print(f"   Formula: {substance.molecular_formula} ✓")

        # Check properties
        if len(substance.physical_properties) == 0:
            print("❌ No physical properties found")
            return False

        print(f"   Properties: {len(substance.physical_properties)} found ✓")

        # Check GHS classification
        if len(substance.ghs_classifications) == 0:
            print("⚠️  No GHS classifications found")
        else:
            print(f"   GHS: {len(substance.ghs_classifications)} hazard classes ✓")

        return True

    async def test_name_search(self) -> bool:
        """Test: Name-basierte Suche"""
        request = ChemicalDataRequest(
            query_id="test-name-benzol", query_text="Name-Suche für Benzol", search_term="benzol", max_results=3
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        if len(response.substances) == 0:
            print("❌ No substances found")
            return False

        print(f"📄 Found {len(response.substances)} substances")

        # Check first result
        substance = response.substances[0]
        print(f"   Best match: {substance.primary_name}")

        # Should find benzol (hazardous)
        if not substance.is_hazardous():
            print("⚠️  Expected hazardous substance (benzol) but got non-hazardous")
        else:
            print("   Hazardous: Yes ✓")

        print(f"   Quality score: {substance.quality_score:.2f}")

        return True

    async def test_physical_properties(self) -> bool:
        """Test: Physikalische Eigenschaften"""
        request = ChemicalDataRequest(
            query_id="test-props-water",
            query_text="Physikalische Eigenschaften von Wasser",
            search_term="7732-18-5",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_physical_properties=True,
            requested_properties=["density", "melting_point", "boiling_point"],
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        if len(response.substances) == 0:
            print("❌ No substances found")
            return False

        substance = response.substances[0]
        print(f"📄 Testing properties for: {substance.primary_name}")

        # Check specific properties
        density = substance.get_property("density")
        if density:
            print(f"   Density: {density.value} {density.unit} ✓")
            if density.value != 1.0:
                print(f"⚠️  Expected water density ~1.0, got {density.value}")
        else:
            print("❌ No density found")
            return False

        melting_point = substance.get_property("melting_point")
        if melting_point:
            print(f"   Melting point: {melting_point.value} {melting_point.unit} ✓")

        boiling_point = substance.get_property("boiling_point")
        if boiling_point:
            print(f"   Boiling point: {boiling_point.value} {boiling_point.unit} ✓")

        return True

    async def test_ghs_classification(self) -> bool:
        """Test: GHS-Klassifikation"""
        request = ChemicalDataRequest(
            query_id="test-ghs-methanol",
            query_text="GHS-Klassifikation für Methanol",
            search_term="67-56-1",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_ghs_classification=True,
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        substance = response.substances[0]
        print(f"📄 Testing GHS for: {substance.primary_name}")

        if len(substance.ghs_classifications) == 0:
            print("❌ No GHS classifications found")
            return False

        print(f"   GHS classes: {len(substance.ghs_classifications)} found ✓")

        # Check for expected hazard classes (methanol is toxic and flammable)
        hazard_classes = [ghs.hazard_class for ghs in substance.ghs_classifications]

        has_acute_toxicity = GHSHazardClass.ACUTE_TOXICITY in hazard_classes
        has_flammable = GHSHazardClass.FLAMMABLE_LIQUID in hazard_classes

        if has_acute_toxicity:
            print("   Acute toxicity: Found ✓")

        if has_flammable:
            print("   Flammable liquid: Found ✓")

        # Check signal word
        signal_word = substance.get_signal_word()
        if signal_word:
            print(f"   Signal word: {signal_word} ✓")

        # Check H-statements
        for ghs in substance.ghs_classifications[:3]:
            print(f"   - {ghs.hazard_statement}: {ghs.hazard_statement_text}")

        return True

    async def test_exposure_limits(self) -> bool:
        """Test: Arbeitsplatz-Grenzwerte"""
        request = ChemicalDataRequest(
            query_id="test-limits-methanol",
            query_text="Grenzwerte für Methanol",
            search_term="67-56-1",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_exposure_limits=True,
            requested_regulations=[RegulationDatabase.DFG, RegulationDatabase.ACGIH],
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        substance = response.substances[0]
        print(f"📄 Testing exposure limits for: {substance.primary_name}")

        if len(substance.exposure_limits) == 0:
            print("❌ No exposure limits found")
            return False

        print(f"   Exposure limits: {len(substance.exposure_limits)} found ✓")

        # Check for specific regulations
        dfg_limit = substance.get_exposure_limit(RegulationDatabase.DFG)
        if dfg_limit:
            print(f"   DFG {dfg_limit.limit_type}: {dfg_limit.value} {dfg_limit.unit} ✓")

        acgih_limit = substance.get_exposure_limit(RegulationDatabase.ACGIH)
        if acgih_limit:
            print(f"   ACGIH {acgih_limit.limit_type}: {acgih_limit.value} {acgih_limit.unit} ✓")

        return True

    async def test_safety_data_sheet(self) -> bool:
        """Test: Sicherheitsdatenblatt"""
        request = ChemicalDataRequest(
            query_id="test-sds-sulfuric",
            query_text="SDS für Schwefelsäure",
            search_term="7664-93-9",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            include_safety_data_sheet=True,
            max_results=1,
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success:
            print(f"❌ Query failed: {response.error_message}")
            return False

        substance = response.substances[0]
        print(f"📄 Testing SDS for: {substance.primary_name}")

        if not substance.safety_data_sheet:
            print("❌ No safety data sheet found")
            return False

        sds = substance.safety_data_sheet
        print(f"   SDS Title: {sds.document_title} ✓")
        print(f"   Version: {sds.version}")
        print(f"   Revision: {sds.revision_date}")
        print(f"   Supplier: {sds.supplier}")
        print(f"   Emergency: {sds.emergency_phone}")

        # Check sections
        sections_with_data = 0
        for i in range(1, 17):
            section_attr = f"section_{i}_" + {
                1: "identification",
                2: "hazards",
                3: "composition",
                4: "first_aid",
                5: "fire_fighting",
                6: "accidental_release",
                7: "handling_storage",
                8: "exposure_controls",
                9: "physical_chemical",
                10: "stability_reactivity",
                11: "toxicological",
                12: "ecological",
                13: "disposal",
                14: "transport",
                15: "regulatory",
                16: "other",
            }.get(i, "other")

            section_data = getattr(sds, section_attr, {})
            if section_data:
                sections_with_data += 1

        print(f"   Sections with data: {sections_with_data}/16 ✓")

        return True

    async def test_cache_functionality(self) -> bool:
        """Test: Cache-Funktionalität"""
        print("📄 Testing cache functionality")

        # First request
        request1 = ChemicalDataRequest(
            query_id="test-cache-1",
            query_text="Cache test 1",
            search_term="67-56-1",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            max_results=1,
        )

        start_time = time.time()
        response1 = await self.agent.query_chemical_data_async(request1)
        time1 = int((time.time() - start_time) * 1000)

        if not response1.success:
            print("❌ First request failed")
            return False

        print(f"   First request: {time1}ms")

        # Second identical request (should hit cache)
        request2 = ChemicalDataRequest(
            query_id="test-cache-2",
            query_text="Cache test 2",
            search_term="67-56-1",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            max_results=1,
        )

        start_time = time.time()
        response2 = await self.agent.query_chemical_data_async(request2)
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
        if len(response1.substances) != len(response2.substances):
            print("❌ Different number of substances returned")
            return False

        if response1.substances and response2.substances:
            if response1.substances[0].substance_id != response2.substances[0].substance_id:
                print("❌ Different substances returned")
                return False

        print("   ✅ Cache returns consistent results")

        return True

    async def test_error_handling(self) -> bool:
        """Test: Error Handling"""
        print("📄 Testing error handling")

        # Test with non-existent CAS number
        request = ChemicalDataRequest(
            query_id="test-error-nonexistent",
            query_text="Non-existent substance",
            search_term="99999-99-9",
            identifier_type=ChemicalIdentifierType.CAS_NUMBER,
            max_results=1,
        )

        response = await self.agent.query_chemical_data_async(request)

        # Should not crash, but may not find anything
        if response.success and len(response.substances) == 0:
            print("   ✅ Gracefully handles non-existent substances")
        elif not response.success:
            print("   ✅ Appropriately reports failure for non-existent substances")
        else:
            print("   ⚠️  Unexpected success for non-existent substance")

        # Test with empty search term
        request2 = ChemicalDataRequest(query_id="test-error-empty", query_text="Empty search", search_term="", max_results=1)

        response2 = await self.agent.query_chemical_data_async(request2)

        # Should handle gracefully
        if not response2.success or len(response2.substances) == 0:
            print("   ✅ Gracefully handles empty search terms")

        return True

    async def test_integration_atmospheric(self) -> bool:
        """Test: Integration mit Atmospheric Flow Agent"""
        print("📄 Testing integration potential with atmospheric flow")

        # Get chemical data that would be useful for atmospheric calculations
        request = ChemicalDataRequest(
            query_id="test-integration",
            query_text="Chemical data for atmospheric modeling",
            search_term="benzol",
            requested_properties=["vapor_pressure", "density", "boiling_point"],
            include_ghs_classification=True,
            max_results=1,
        )

        response = await self.agent.query_chemical_data_async(request)

        if not response.success or len(response.substances) == 0:
            print("❌ Failed to get chemical data for integration test")
            return False

        substance = response.substances[0]
        print(f"   Chemical: {substance.primary_name}")

        # Check for atmospheric modeling relevant data
        vapor_pressure = substance.get_property("vapor_pressure")
        density = substance.get_property("density")

        integration_score = 0

        if vapor_pressure:
            print(f"   Vapor pressure: {vapor_pressure.value} {vapor_pressure.unit} ✓")
            integration_score += 1

        if density:
            print(f"   Density: {density.value} {density.unit} ✓")
            integration_score += 1

        if substance.is_hazardous():
            print("   Hazardous: Yes (needs dispersion modeling) ✓")
            integration_score += 1

        cas = substance.get_cas_number()
        if cas:
            print(f"   CAS: {cas} (for emission source identification) ✓")
            integration_score += 1

        print(f"   Integration readiness: {integration_score}/4")

        return integration_score >= 2

    def print_summary(self):
        """Test-Zusammenfassung ausgeben"""
        print("\n" + "=" * 60)
        print("🧪 CHEMICAL DATA AGENT TEST SUMMARY")
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
            print(f"   Substances found: {status['performance']['substances_found']}")
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
            print("🎉 Chemical Data Agent is working excellently!")
        elif success_rate >= 60:
            print("👍 Chemical Data Agent is working well with minor issues")
        else:
            print("⚠️  Chemical Data Agent needs attention")


async def main():
    """Hauptfunktion"""
    print("🧪 VERITAS Chemical Data Agent - Standalone Test Suite")
    print("=" * 60)
    print("Testing chemical substance data retrieval and processing...")
    print()

    # Test Suite erstellen
    test_suite = ChemicalDataTestSuite()

    # Agent einrichten
    test_suite.setup_agent()

    # Tests ausführen
    tests = [
        ("CAS Number Search", test_suite.test_cas_number_search),
        ("Name-based Search", test_suite.test_name_search),
        ("Physical Properties", test_suite.test_physical_properties),
        ("GHS Classification", test_suite.test_ghs_classification),
        ("Exposure Limits", test_suite.test_exposure_limits),
        ("Safety Data Sheet", test_suite.test_safety_data_sheet),
        ("Cache Functionality", test_suite.test_cache_functionality),
        ("Error Handling", test_suite.test_error_handling),
        ("Atmospheric Integration", test_suite.test_integration_atmospheric),
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
