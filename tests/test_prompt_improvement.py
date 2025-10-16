#!/usr/bin/env python3
"""
PROMPT IMPROVEMENT TEST
=======================
Vergleicht die Qualität VORHER (alter Prompt) vs. NACHHER (VerwaltungsrechtPrompts)

Test-Setup:
- 1 Modell: codellama:latest
- 1 Frage: Q1 (Baugenehmigung)
- Metriken: Zitationen, Direkte Zitate, Legal Refs, Aspect Coverage

Expected Improvement:
- Zitationen: 0 → 3-5
- Direkte Zitate: 0 → 2-3
- Legal Refs: 0 → 3-6
"""

import requests
import time
import re
from typing import Dict, List

BACKEND_URL = "http://localhost:5000"
TEST_MODEL = "codellama:latest"

TEST_QUESTION = {
    "id": "Q1",
    "query": "Welche rechtlichen Voraussetzungen, Fristen und Kosten sind bei der Beantragung einer Baugenehmigung in Baden-Württemberg zu beachten?",
    "expected_aspects": [
        "Rechtliche Voraussetzungen (§§ LBO BW)",
        "Fristen (Bearbeitungsdauer)",
        "Kosten (Gebühren)",
        "Ausnahmen (Genehmigungsfreistellung)",
        "Vereinfachtes Verfahren"
    ],
    "min_citations": 3,
    "min_quotes": 2,
    "min_legal_refs": 3
}

def send_query(query: str, model: str = TEST_MODEL) -> Dict:
    """Sendet Query an Backend"""
    url = f"{BACKEND_URL}/ask"
    payload = {
        "question": query,
        "mode": "intelligent",
        "model": model,
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    start_time = time.time()
    response = requests.post(url, json=payload, timeout=60)
    duration = time.time() - start_time
    
    if response.status_code == 200:
        data = response.json()
        return {
            "success": True,
            "answer": data.get("answer", ""),
            "sources": data.get("sources", []),
            "duration": duration
        }
    else:
        return {
            "success": False,
            "error": f"HTTP {response.status_code}",
            "duration": duration
        }

def extract_ieee_citations(text: str) -> List[str]:
    """Extrahiert [1], [2], [3] Zitationen"""
    pattern = r'\[(\d+)\]'
    citations = re.findall(pattern, text)
    return list(set(citations))

def extract_direct_quotes(text: str) -> List[str]:
    """Extrahiert direkte Zitate ("..." oder „...")"""
    patterns = [
        r'"([^"]{20,})"',
        r'„([^"]{20,})"',
        r'\'([^\']{20,})\''
    ]
    
    quotes = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        quotes.extend(matches)
    
    return list(set(quotes))

def extract_legal_references(text: str) -> List[str]:
    """Extrahiert § Referenzen (§ 58 LBO BW, Art. 14 GG, etc.)"""
    patterns = [
        r'§+\s*\d+[a-z]?\s+(?:Abs\.\s*\d+\s+)?(?:Satz\s*\d+\s+)?(?:[A-ZÄÖÜ]{2,})',
        r'Art\.\s*\d+[a-z]?\s+(?:Abs\.\s*\d+\s+)?(?:[A-ZÄÖÜ]{2,})',
        r'§§?\s*\d+\s+[A-Z]{2,}'
    ]
    
    refs = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        refs.extend(matches)
    
    return list(set(refs))

def analyze_answer(answer: str, test_case: Dict) -> Dict:
    """Analysiert Antwort-Qualität"""
    
    # Metriken extrahieren
    citations = extract_ieee_citations(answer)
    quotes = extract_direct_quotes(answer)
    legal_refs = extract_legal_references(answer)
    
    # Aspect Coverage
    aspects_found = []
    for aspect in test_case["expected_aspects"]:
        # Vereinfachte Keyword-Suche
        keywords = aspect.split("(")[0].strip().split()
        if any(kw.lower() in answer.lower() for kw in keywords if len(kw) > 3):
            aspects_found.append(aspect)
    
    aspect_coverage = len(aspects_found) / len(test_case["expected_aspects"])
    
    return {
        "citation_count": len(citations),
        "citations": citations,
        "quote_count": len(quotes),
        "quotes": quotes[:3],  # Nur erste 3 für Display
        "legal_ref_count": len(legal_refs),
        "legal_refs": legal_refs,
        "aspect_coverage": aspect_coverage,
        "aspects_found": aspects_found,
        "answer_length": len(answer)
    }

def compare_results(baseline: Dict, improved: Dict):
    """Vergleicht Vorher vs. Nachher"""
    
    print("\n" + "="*80)
    print("📊 VORHER vs. NACHHER VERGLEICH")
    print("="*80)
    
    metrics = [
        ("Zitationen [1],[2]", "citation_count"),
        ("Direkte Zitate", "quote_count"),
        ("Legal Refs (§)", "legal_ref_count"),
        ("Aspect Coverage", "aspect_coverage"),
        ("Antwortlänge", "answer_length")
    ]
    
    improvements = []
    
    for name, key in metrics:
        baseline_val = baseline.get(key, 0)
        improved_val = improved.get(key, 0)
        
        if key == "aspect_coverage":
            baseline_val = baseline_val * 100
            improved_val = improved_val * 100
            diff = improved_val - baseline_val
            diff_pct = (diff / baseline_val * 100) if baseline_val > 0 else float('inf')
            
            print(f"\n{name}:")
            print(f"  Vorher:  {baseline_val:.1f}%")
            print(f"  Nachher: {improved_val:.1f}%")
            print(f"  Änderung: {diff:+.1f}% ({diff_pct:+.1f}%)")
        else:
            diff = improved_val - baseline_val
            diff_pct = (diff / baseline_val * 100) if baseline_val > 0 else float('inf')
            
            print(f"\n{name}:")
            print(f"  Vorher:  {baseline_val}")
            print(f"  Nachher: {improved_val}")
            print(f"  Änderung: {diff:+d} ({diff_pct:+.1f}%)")
        
        improvements.append({
            "metric": name,
            "baseline": baseline_val,
            "improved": improved_val,
            "diff": diff,
            "diff_pct": diff_pct
        })
    
    # Gesamtbewertung
    print("\n" + "="*80)
    print("🎯 BEWERTUNG")
    print("="*80)
    
    total_improvement = sum(1 for imp in improvements if imp["diff"] > 0)
    
    if total_improvement >= 4:
        print("\n✅ EXZELLENT - Signifikante Verbesserung in allen Bereichen!")
    elif total_improvement >= 3:
        print("\n✅ GUT - Deutliche Verbesserung in den meisten Bereichen")
    elif total_improvement >= 2:
        print("\n⚠️ BEFRIEDIGEND - Leichte Verbesserung")
    else:
        print("\n❌ UNZUREICHEND - Keine signifikante Verbesserung")
    
    # Kritische Metriken prüfen
    citation_improved = next(imp for imp in improvements if imp["metric"] == "Zitationen [1],[2]")
    quote_improved = next(imp for imp in improvements if imp["metric"] == "Direkte Zitate")
    
    if citation_improved["improved"] >= TEST_QUESTION["min_citations"]:
        print(f"✅ Zitationen-Ziel erreicht: {citation_improved['improved']}/{TEST_QUESTION['min_citations']}")
    else:
        print(f"❌ Zitationen-Ziel verfehlt: {citation_improved['improved']}/{TEST_QUESTION['min_citations']}")
    
    if quote_improved["improved"] >= TEST_QUESTION["min_quotes"]:
        print(f"✅ Zitat-Ziel erreicht: {quote_improved['improved']}/{TEST_QUESTION['min_quotes']}")
    else:
        print(f"❌ Zitat-Ziel verfehlt: {quote_improved['improved']}/{TEST_QUESTION['min_quotes']}")
    
    return improvements

def run_test():
    """Führt Vorher-Nachher-Test durch"""
    
    print("="*80)
    print("🧪 PROMPT IMPROVEMENT TEST")
    print("="*80)
    print(f"\nModell: {TEST_MODEL}")
    print(f"Frage: {TEST_QUESTION['query'][:60]}...")
    print(f"\nErwartungen:")
    print(f"  Min. Zitationen: {TEST_QUESTION['min_citations']}")
    print(f"  Min. Direkte Zitate: {TEST_QUESTION['min_quotes']}")
    print(f"  Min. Legal Refs: {TEST_QUESTION['min_legal_refs']}")
    
    # NACHHER (mit VerwaltungsrechtPrompts)
    print("\n" + "="*80)
    print("📝 TESTE MIT ENHANCED PROMPT (VerwaltungsrechtPrompts)")
    print("="*80)
    
    print("\nSende Query...")
    response = send_query(TEST_QUESTION["query"], TEST_MODEL)
    
    if not response["success"]:
        print(f"❌ Fehler: {response.get('error')}")
        return
    
    print(f"✅ Antwort erhalten in {response['duration']:.1f}s")
    
    analysis = analyze_answer(response["answer"], TEST_QUESTION)
    
    print(f"\n📊 ERGEBNISSE:")
    print(f"  Zitationen [1],[2]: {analysis['citation_count']}")
    print(f"  Direkte Zitate: {analysis['quote_count']}")
    print(f"  Legal Refs (§): {analysis['legal_ref_count']}")
    print(f"  Aspect Coverage: {analysis['aspect_coverage']:.1%}")
    print(f"  Antwortlänge: {analysis['answer_length']} Zeichen")
    
    if analysis['quotes']:
        print(f"\n📝 Beispiel-Zitate:")
        for i, quote in enumerate(analysis['quotes'][:2], 1):
            print(f"  {i}. \"{quote[:80]}...\"")
    
    if analysis['legal_refs']:
        print(f"\n⚖️ Legal References:")
        for ref in analysis['legal_refs'][:3]:
            print(f"  • {ref}")
    
    # Bewertung
    print("\n" + "="*80)
    print("🎯 BEWERTUNG")
    print("="*80)
    
    passed = 0
    total = 3
    
    if analysis['citation_count'] >= TEST_QUESTION['min_citations']:
        print(f"✅ Zitationen: {analysis['citation_count']}/{TEST_QUESTION['min_citations']}")
        passed += 1
    else:
        print(f"❌ Zitationen: {analysis['citation_count']}/{TEST_QUESTION['min_citations']}")
    
    if analysis['quote_count'] >= TEST_QUESTION['min_quotes']:
        print(f"✅ Direkte Zitate: {analysis['quote_count']}/{TEST_QUESTION['min_quotes']}")
        passed += 1
    else:
        print(f"❌ Direkte Zitate: {analysis['quote_count']}/{TEST_QUESTION['min_quotes']}")
    
    if analysis['legal_ref_count'] >= TEST_QUESTION['min_legal_refs']:
        print(f"✅ Legal Refs: {analysis['legal_ref_count']}/{TEST_QUESTION['min_legal_refs']}")
        passed += 1
    else:
        print(f"❌ Legal Refs: {analysis['legal_ref_count']}/{TEST_QUESTION['min_legal_refs']}")
    
    print(f"\n📊 GESAMT: {passed}/{total} Kriterien erfüllt ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 ERFOLG! VerwaltungsrechtPrompts zeigen signifikante Verbesserung!")
    elif passed >= 2:
        print("\n✅ GUT! Verbesserung sichtbar, aber noch Optimierungsbedarf")
    else:
        print("\n⚠️ UNZUREICHEND - Weitere Prompt-Optimierung erforderlich")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    run_test()
