#!/usr/bin/env python3
"""
Direct Test: HypothesisService Initialisierung
"""
import sys
sys.path.append('c:/VCC/veritas')

print("=" * 60)
print("HYPOTHESIS SERVICE DIRECT TEST")
print("=" * 60)

# Test 1: Import HypothesisService
print("\n1️⃣  Import HypothesisService...")
try:
    from backend.services.hypothesis_service import HypothesisService
    print("   ✅ Import erfolgreich")
except Exception as e:
    print(f"   ❌ Import fehlgeschlagen: {e}")
    sys.exit(1)

# Test 2: Initialisiere Service
print("\n2️⃣  Initialisiere HypothesisService...")
try:
    service = HypothesisService(
        model_name="llama3.1:8b",
        temperature=0.3
    )
    print(f"   ✅ Service initialisiert")
    print(f"   • Model: {service.model_name}")
    print(f"   • Temperature: {service.temperature}")
    print(f"   • Ollama Client: {'✅ vorhanden' if service.ollama_client else '❌ None'}")
except Exception as e:
    print(f"   ❌ Init fehlgeschlagen: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Generiere Hypothese
print("\n3️⃣  Generiere Test-Hypothese...")
try:
    hypothesis = service.generate_hypothesis(
        query="Welche Genehmigungen brauche ich für einen Neubau?",
        rag_context=[],
        timeout=15.0
    )
    print(f"   ✅ Hypothese generiert!")
    print(f"   • Question Type: {hypothesis.question_type.value}")
    print(f"   • Confidence: {hypothesis.confidence.value}")
    print(f"   • Primary Intent: {hypothesis.primary_intent}")
    print(f"   • Information Gaps: {len(hypothesis.information_gaps)}")
    for i, gap in enumerate(hypothesis.information_gaps, 1):
        print(f"      {i}. {gap.gap_type} ({gap.severity}) - {gap.suggested_query}")
    print(f"   • Assumptions: {len(hypothesis.assumptions)}")
    for i, assumption in enumerate(hypothesis.assumptions, 1):
        print(f"      {i}. {assumption}")
    print(f"   • Clarification Questions: {len(hypothesis.get_clarification_questions())}")
    for i, question in enumerate(hypothesis.get_clarification_questions(), 1):
        print(f"      {i}. {question}")
except Exception as e:
    print(f"   ❌ Generierung fehlgeschlagen: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ ALLE TESTS ERFOLGREICH")
print("=" * 60)
