#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Quality Test für v3.19.0 - Enhanced mit Golden Dataset
Testet Antwortqualität, IEEE-Zitationen, Follow-up-Generierung und direkte Zitate
Version: 2.0 (10. Oktober 2025)
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Backend-URL
BACKEND_URL = "http://localhost:5000"

# ============================================================================
# GOLDEN DATASET CONFIGURATION
# ============================================================================

@dataclass
class TimingMetrics:
    """Detaillierte Zeitmessung für Performance-Analyse"""
    total_time: float
    retrieval_time: float = 0.0
    generation_time: float = 0.0
    post_processing_time: float = 0.0
    network_latency: float = 0.0

@dataclass
class QuoteMetrics:
    """Metriken für direkte Zitate aus Rechtsquellen"""
    direct_quotes_count: int = 0
    quote_length_avg: float = 0.0
    quotes_with_source: int = 0
    quotes: List[str] = None
    
    def __post_init__(self):
        if self.quotes is None:
            self.quotes = []

@dataclass
class GoldenDatasetEntry:
    """
    Ein Eintrag im Golden Dataset für Feedback-Schleife
    Enthält Frage, erwartete Antwortqualität und tatsächliche Ergebnisse
    """
    question_id: str
    question: str
    expected_aspects: List[str]
    expected_citations_min: int
    expected_quotes_min: int
    expected_legal_refs_min: int
    
    # Tatsächliche Ergebnisse pro Modell
    model_results: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.model_results is None:
            self.model_results = {}


def get_available_models() -> List[str]:
    """Holt verfügbare LLM-Modelle vom Backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/get_models", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Verschiedene Response-Formate unterstützen
        if isinstance(data, dict):
            models = data.get('models', data.get('available_models', []))
        elif isinstance(data, list):
            models = data
        else:
            models = []
        
        # Extrahiere Modellnamen (falls Objekte statt Strings)
        model_names = []
        for m in models:
            if isinstance(m, dict):
                model_names.append(m.get('name', m.get('model', str(m))))
            else:
                model_names.append(str(m))
        
        return model_names
    except Exception as e:
        print(f"⚠️ Konnte Modelle nicht abrufen: {e}")
        print("📌 Verwende Fallback-Modelle")
        return ["llama3:instruct", "llama3:latest", "mistral:latest"]

# Test-Queries (komplex, multi-aspekt) - GOLDEN DATASET
TEST_QUERIES = [
    {
        "id": "Q1",
        "query": "Welche rechtlichen Voraussetzungen, Fristen und Kosten sind bei der Beantragung einer Baugenehmigung für einen Wohnhaus-Neubau in Baden-Württemberg zu beachten? Bitte erläutere auch mögliche Ausnahmen und vereinfachte Verfahren.",
        "expected_aspects": [
            "Rechtliche Voraussetzungen (§§ LBO BW)",
            "Fristen (Bearbeitungsdauer)",
            "Kosten (Gebühren)",
            "Ausnahmen (Genehmigungsfreistellung)",
            "Vereinfachtes Verfahren"
        ],
        "min_citations": 3,
        "min_sources": 3,
        "min_suggestions": 3,
        "min_quotes": 2,  # NEU: Erwartete direkte Zitate
        "min_legal_refs": 3  # NEU: Erwartete Paragraphen-Referenzen
    },
    {
        "id": "Q2",
        "query": "Erkläre detailliert den Unterschied zwischen Baugenehmigungsverfahren, vereinfachtem Genehmigungsverfahren und Genehmigungsfreistellung nach der Landesbauordnung Baden-Württemberg. Welche Bauvorhaben fallen jeweils darunter und welche Unterlagen sind erforderlich?",
        "expected_aspects": [
            "Baugenehmigungsverfahren (§§)",
            "Vereinfachtes Verfahren (Unterschiede)",
            "Genehmigungsfreistellung (Kriterien)",
            "Bauvorhaben-Kategorien",
            "Erforderliche Unterlagen"
        ],
        "min_citations": 4,
        "min_sources": 4,
        "min_suggestions": 4,
        "min_quotes": 3,
        "min_legal_refs": 5
    },
    {
        "id": "Q3",
        "query": "Was regelt § 58 LBO BW konkret? Wie unterscheidet sich die Regelung von anderen Bundesländern? Welche Änderungen gab es in den letzten Jahren und welche praktischen Auswirkungen haben diese für Bauherren?",
        "expected_aspects": [
            "§ 58 LBO BW Inhalt",
            "Bundesländer-Vergleich",
            "Historische Änderungen",
            "Praktische Auswirkungen",
            "Bauherren-Perspektive"
        ],
        "min_citations": 3,
        "min_sources": 2,
        "min_suggestions": 4,
        "min_quotes": 2,
        "min_legal_refs": 4
    },
    {
        "id": "Q4",
        "query": "Welche Anforderungen gelten für den Brandschutz bei Wohngebäuden in Baden-Württemberg? Berücksichtige dabei Gebäudeklassen, Rettungswege, Baustoffe und besondere Anforderungen für Mehrfamilienhäuser. Nenne auch relevante DIN-Normen.",
        "expected_aspects": [
            "Brandschutz-Anforderungen",
            "Gebäudeklassen",
            "Rettungswege",
            "Baustoffe/Brandschutzklassen",
            "Mehrfamilienhäuser (besondere Anforderungen)",
            "DIN-Normen"
        ],
        "min_citations": 4,
        "min_sources": 3,
        "min_suggestions": 4,
        "min_quotes": 3,
        "min_legal_refs": 5
    },
    {
        "id": "Q5",
        "query": "Wie ist der Ablauf eines Baugenehmigungsverfahrens in Baden-Württemberg vom Antrag bis zur Genehmigung? Welche Behörden sind beteiligt, welche Fristen gelten, was passiert bei Ablehnung und welche Rechtsmittel stehen dem Bauherrn zur Verfügung?",
        "expected_aspects": [
            "Verfahrensablauf (Schritte)",
            "Beteiligte Behörden",
            "Gesetzliche Fristen",
            "Ablehnungsgründe",
            "Rechtsmittel (Widerspruch, Klage)"
        ],
        "min_citations": 4,
        "min_sources": 3,
        "min_suggestions": 5,
        "min_quotes": 2,
        "min_legal_refs": 6
    }
]

def send_rag_query(query: str, model: str = "llama3:instruct", max_tokens: int = 800) -> Dict[str, Any]:
    """Sendet Query an RAG-Backend und gibt Response zurück mit detaillierter Zeitmessung"""
    timing = TimingMetrics(total_time=0.0)
    
    try:
        start_total = time.time()
        
        payload = {
            "question": query,  # Backend erwartet "question", nicht "query"
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "model": model
        }
        
        # Network + Total Time
        start_request = time.time()
        response = requests.post(
            f"{BACKEND_URL}/ask",
            json=payload,
            timeout=120  # 2 Minuten für komplexe Queries
        )
        end_request = time.time()
        
        response.raise_for_status()
        result = response.json()
        
        # Timing-Metriken hinzufügen
        timing.total_time = end_request - start_total
        timing.network_latency = end_request - start_request
        
        # Backend-Timing (falls verfügbar)
        if 'processing_time_seconds' in result:
            timing.generation_time = result['processing_time_seconds']
        
        result['timing'] = asdict(timing)
        return result
        
    except requests.exceptions.HTTPError as e:
        # Bei HTTP-Fehler: Response-Details ausgeben
        try:
            error_detail = e.response.json()
            return {"error": f"{e} - {error_detail}"}
        except:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def extract_direct_quotes(answer: str) -> List[str]:
    """
    Extrahiert direkte Zitate aus der Antwort
    
    Erkennt:
    - "..." (Anführungszeichen)
    - „..." (deutsche Anführungszeichen)
    - Längere zusammenhängende Passagen (>50 Zeichen)
    
    Returns:
        Liste der gefundenen Zitate
    """
    quotes = []
    
    # Pattern für Anführungszeichen
    quote_patterns = [
        r'"([^"]{20,})"',        # "langes Zitat"
        r'„([^"]{20,})"',        # „deutsches Zitat"
        r'\'([^\']{20,})\'',     # 'alternatives Zitat'
    ]
    
    for pattern in quote_patterns:
        found = re.findall(pattern, answer)
        quotes.extend(found)
    
    # Deduplizieren
    unique_quotes = list(set(quotes))
    
    return unique_quotes


def extract_quote_metrics(answer: str, sources_metadata: List[Dict]) -> QuoteMetrics:
    """
    Analysiert Zitat-Qualität in der Antwort
    
    Args:
        answer: LLM-generierte Antwort
        sources_metadata: Metadaten der Quellen
    
    Returns:
        QuoteMetrics mit detaillierten Zitat-Statistiken
    """
    quotes = extract_direct_quotes(answer)
    
    # Quotes mit Quellenangabe (z.B. "Text..." [1])
    quotes_with_source = 0
    for quote in quotes:
        # Prüfe ob nach dem Zitat eine Zitation folgt
        quote_pos = answer.find(quote)
        if quote_pos != -1:
            # Prüfe die nächsten 10 Zeichen nach dem Zitat
            after_quote = answer[quote_pos + len(quote):quote_pos + len(quote) + 10]
            if re.search(r'\[\d+\]', after_quote):
                quotes_with_source += 1
    
    # Durchschnittliche Zitat-Länge
    avg_length = sum(len(q) for q in quotes) / len(quotes) if quotes else 0.0
    
    return QuoteMetrics(
        direct_quotes_count=len(quotes),
        quote_length_avg=avg_length,
        quotes_with_source=quotes_with_source,
        quotes=quotes
    )


def analyze_response(response: Dict, test_case: Dict, model_name: str = "unknown") -> Dict[str, Any]:
    """Analysiert RAG-Response auf Qualität inkl. Zitate und Timing"""
    
    analysis = {
        "test_id": test_case["id"],
        "query": test_case["query"],
        "model": model_name,
        "success": False,
        "metrics": {},
        "issues": [],
        "strengths": []
    }
    
    # Prüfe auf Fehler
    if "error" in response:
        analysis["issues"].append(f"❌ Backend-Fehler: {response['error']}")
        return analysis
    
    answer = response.get("answer", "")
    sources = response.get("sources", [])
    sources_metadata = response.get("sources_metadata", [])
    suggestions = response.get("suggestions", [])
    
    # === METRIK 1: Antwortlänge ===
    answer_length = len(answer)
    analysis["metrics"]["answer_length"] = answer_length
    
    if answer_length < 200:
        analysis["issues"].append(f"⚠️ Antwort zu kurz: {answer_length} Zeichen (erwartet >500)")
    elif answer_length > 500:
        analysis["strengths"].append(f"✅ Ausführliche Antwort: {answer_length} Zeichen")
    
    # === METRIK 2: IEEE-Zitationen ===
    import re
    citations = re.findall(r'\[(\d+)\]', answer)
    citation_count = len(citations)
    unique_citations = len(set(citations))
    
    analysis["metrics"]["citation_count"] = citation_count
    analysis["metrics"]["unique_citations"] = unique_citations
    
    if citation_count < test_case["min_citations"]:
        analysis["issues"].append(
            f"⚠️ Zu wenig Zitationen: {citation_count}/{test_case['min_citations']} erwartet"
        )
    else:
        analysis["strengths"].append(
            f"✅ Ausreichend Zitationen: {citation_count} (davon {unique_citations} unique)"
        )
    
    # Prüfe fortlaufende Nummerierung
    if citations:
        expected = list(range(1, unique_citations + 1))
        actual = sorted(set(int(c) for c in citations))
        if actual != expected:
            analysis["issues"].append(
                f"⚠️ Zitations-Nummerierung nicht fortlaufend: {actual} (erwartet {expected})"
            )
    
    # === METRIK 3: Quellen-Metadaten ===
    sources_count = len(sources_metadata) if sources_metadata else len(sources)
    analysis["metrics"]["sources_count"] = sources_count
    
    if sources_count < test_case["min_sources"]:
        analysis["issues"].append(
            f"⚠️ Zu wenig Quellen: {sources_count}/{test_case['min_sources']} erwartet"
        )
    else:
        analysis["strengths"].append(f"✅ Ausreichend Quellen: {sources_count}")
    
    # === METRIK 4: Direkte Zitate (NEU) ===
    quote_metrics = extract_quote_metrics(answer, sources_metadata)
    analysis["metrics"]["direct_quotes_count"] = quote_metrics.direct_quotes_count
    analysis["metrics"]["quotes_with_source"] = quote_metrics.quotes_with_source
    analysis["metrics"]["quote_length_avg"] = quote_metrics.quote_length_avg
    
    # Erwartete Zitate (falls im Test definiert)
    min_quotes = test_case.get("min_quotes", 2)
    
    if quote_metrics.direct_quotes_count < min_quotes:
        analysis["issues"].append(
            f"⚠️ Zu wenig direkte Zitate: {quote_metrics.direct_quotes_count}/{min_quotes} erwartet"
        )
    else:
        analysis["strengths"].append(
            f"✅ Direkte Zitate vorhanden: {quote_metrics.direct_quotes_count}"
        )
    
    # Prüfe ob Zitate Quellen haben
    if quote_metrics.direct_quotes_count > 0:
        quote_source_ratio = quote_metrics.quotes_with_source / quote_metrics.direct_quotes_count
        analysis["metrics"]["quote_source_ratio"] = quote_source_ratio
        
        if quote_source_ratio < 0.5:
            analysis["issues"].append(
                f"⚠️ Viele Zitate ohne Quellenangabe: {quote_metrics.quotes_with_source}/{quote_metrics.direct_quotes_count}"
            )
        elif quote_source_ratio >= 0.8:
            analysis["strengths"].append(
                f"✅ Zitate mit Quellenangaben: {quote_metrics.quotes_with_source}/{quote_metrics.direct_quotes_count}"
            )
    
    # Speichere Zitate für Golden Dataset
    analysis["quotes"] = quote_metrics.quotes[:3]  # Erste 3 Zitate als Beispiel
    
    # === METRIK 5: Follow-up-Vorschläge ===
    suggestions_count = len(suggestions)
    analysis["metrics"]["suggestions_count"] = suggestions_count
    
    if suggestions_count < test_case["min_suggestions"]:
        analysis["issues"].append(
            f"⚠️ Zu wenig Vorschläge: {suggestions_count}/{test_case['min_suggestions']} erwartet"
        )
    else:
        analysis["strengths"].append(
            f"✅ Ausreichend Follow-up-Vorschläge: {suggestions_count}"
        )
    
    # === METRIK 6: Aspekt-Abdeckung ===
        analysis["strengths"].append(f"✅ Ausreichend Vorschläge: {suggestions_count}")
    
    # Prüfe Vorschlag-Qualität (Länge)
    if suggestions:
        avg_suggestion_length = sum(len(s) for s in suggestions) / len(suggestions)
        analysis["metrics"]["avg_suggestion_length"] = avg_suggestion_length
        
        if avg_suggestion_length < 30:
            analysis["issues"].append(
                f"⚠️ Vorschläge zu kurz: Ø {avg_suggestion_length:.0f} Zeichen"
            )
    
    # === METRIK 5: Aspekt-Abdeckung ===
    covered_aspects = []
    for aspect in test_case["expected_aspects"]:
        # Einfache Keyword-Suche (könnte verbessert werden)
        keywords = aspect.lower().split()
        if any(kw in answer.lower() for kw in keywords if len(kw) > 3):
            covered_aspects.append(aspect)
    
    aspect_coverage = len(covered_aspects) / len(test_case["expected_aspects"])
    analysis["metrics"]["aspect_coverage"] = aspect_coverage
    
    if aspect_coverage < 0.6:
        analysis["issues"].append(
            f"⚠️ Unzureichende Aspekt-Abdeckung: {len(covered_aspects)}/{len(test_case['expected_aspects'])} "
            f"({aspect_coverage:.0%})"
        )
        analysis["issues"].append(
            f"   Fehlende Aspekte: {[a for a in test_case['expected_aspects'] if a not in covered_aspects]}"
        )
    else:
        analysis["strengths"].append(
            f"✅ Gute Aspekt-Abdeckung: {len(covered_aspects)}/{len(test_case['expected_aspects'])} "
            f"({aspect_coverage:.0%})"
        )
    
    # === METRIK 6: Struktur ===
    has_sections = any(marker in answer for marker in ['📋', '🔄', '💡', '**'])
    if has_sections:
        analysis["strengths"].append("✅ Strukturierte Antwort (mit Sections/Markdown)")
    else:
        analysis["issues"].append("⚠️ Antwort unstrukturiert (keine erkennbaren Sections)")
    
    # === GESAMT-BEWERTUNG ===
    critical_issues = sum(1 for issue in analysis["issues"] if "❌" in issue)
    warnings = sum(1 for issue in analysis["issues"] if "⚠️" in issue)
    
    if critical_issues == 0 and warnings <= 2:
        analysis["success"] = True
        analysis["rating"] = "EXCELLENT"
    elif critical_issues == 0 and warnings <= 4:
        analysis["success"] = True
        analysis["rating"] = "GOOD"
    elif critical_issues <= 1:
        analysis["success"] = False
        analysis["rating"] = "NEEDS IMPROVEMENT"
    else:
        analysis["success"] = False
        analysis["rating"] = "POOR"
    
    return analysis

def print_analysis(analysis: Dict):
    """Gibt Analyse formatiert aus"""
    print(f"\n{'='*80}")
    rating = analysis.get('rating', 'UNKNOWN')
    model = analysis.get('model', 'unknown')
    print(f"TEST {analysis['test_id']} [{model}]: {rating}")
    print(f"{'='*80}")
    print(f"\nQuery: {analysis['query'][:100]}...")
    
    print(f"\n📊 METRIKEN:")
    for key, value in analysis['metrics'].items():
        if isinstance(value, float):
            print(f"  • {key}: {value:.2f}")
        else:
            print(f"  • {key}: {value}")
    
    if analysis['strengths']:
        print(f"\n💪 STÄRKEN:")
        for strength in analysis['strengths']:
            print(f"  {strength}")
    
    if analysis['issues']:
        print(f"\n⚠️ PROBLEME:")
        for issue in analysis['issues']:
            print(f"  {issue}")

def run_tests():
    """Führt alle Tests aus - ALLE Modelle mit Golden Dataset"""
    print("\n" + "="*80)
    print("RAG QUALITY TEST v3.19.1 - GOLDEN DATASET (ALLE MODELLE)")
    print("="*80)
    print(f"\nBackend: {BACKEND_URL}")
    print(f"Test-Cases: {len(TEST_QUERIES)}")
    print(f"Start: {time.strftime('%H:%M:%S')}\n")
    
    # === SCHRITT 1: Hole verfügbare Modelle ===
    print("📡 Rufe verfügbare LLM-Modelle ab...")
    available_models = get_available_models()
    
    if not available_models:
        print("❌ Keine Modelle gefunden - Test abgebrochen")
        return
    
    print(f"✅ Gefundene Modelle: {len(available_models)}")
    for i, model in enumerate(available_models, 1):
        print(f"   {i}. {model}")
    
    # ALLE Modelle testen (nicht nur 3)
    test_models = available_models
    print(f"\n🎯 Teste ALLE {len(test_models)} Modelle für Golden Dataset")
    
    # Golden Dataset initialisieren
    golden_dataset = {}
    for test_case in TEST_QUERIES:
        golden_dataset[test_case["id"]] = GoldenDatasetEntry(
            question_id=test_case["id"],
            question=test_case["query"],
            expected_aspects=test_case["expected_aspects"],
            expected_citations_min=test_case["min_citations"],
            expected_quotes_min=test_case.get("min_quotes", 2),
            expected_legal_refs_min=test_case.get("min_legal_refs", 3)
        )
    
    all_results = []
    
    # === SCHRITT 2: Teste jedes Modell ===
    for model_idx, model_name in enumerate(test_models, 1):
        print(f"\n{'='*80}")
        print(f"🤖 MODELL {model_idx}/{len(test_models)}: {model_name}")
        print(f"{'='*80}")
        
        model_results = []
        model_start_time = time.time()
        
        for test_idx, test_case in enumerate(TEST_QUERIES, 1):
            print(f"\n[{test_idx}/{len(TEST_QUERIES)}] Query: {test_case['id']} mit {model_name}...")
            
            query_start_time = time.time()
            response = send_rag_query(test_case["query"], model=model_name, max_tokens=800)
            duration = time.time() - query_start_time
            
            print(f"    Response in {duration:.1f}s erhalten")
            
            analysis = analyze_response(response, test_case, model_name)
            analysis["duration"] = duration
            
            print_analysis(analysis)
            model_results.append(analysis)
            all_results.append(analysis)
            
            # Pause zwischen Queries (Backend-Schonung)
            if test_idx < len(TEST_QUERIES):
                print("\n⏸️  Pause 2s...")
                time.sleep(2)
        
        # Zwischen-Zusammenfassung für dieses Modell
        print(f"\n{'─'*80}")
        print(f"📊 ZUSAMMENFASSUNG FÜR {model_name}")
        print(f"{'─'*80}")
        
        passed = sum(1 for r in model_results if r["success"])
        print(f"Ergebnis: {passed}/{len(model_results)} Tests bestanden ({passed/len(model_results)*100:.0f}%)")
        
        # Durchschnittliche Metriken für dieses Modell
        if model_results:
            avg_answer_length = sum(r["metrics"].get("answer_length", 0) for r in model_results) / len(model_results)
            avg_citations = sum(r["metrics"].get("citation_count", 0) for r in model_results) / len(model_results)
            avg_sources = sum(r["metrics"].get("sources_count", 0) for r in model_results) / len(model_results)
            avg_suggestions = sum(r["metrics"].get("suggestions_count", 0) for r in model_results) / len(model_results)
            
            print(f"\nØ Antwortlänge: {avg_answer_length:.0f} Zeichen")
            print(f"Ø Zitationen: {avg_citations:.1f}")
            print(f"Ø Quellen: {avg_sources:.1f}")
            print(f"Ø Vorschläge: {avg_suggestions:.1f}")
        
        # Längere Pause zwischen Modellen
        if model_idx < len(test_models):
            print(f"\n⏸️  Pause 5s vor nächstem Modell...")
            time.sleep(5)
    
    # === ZUSAMMENFASSUNG ===
    print("\n" + "="*80)
    print("🎯 GESAMT-ZUSAMMENFASSUNG (ALLE MODELLE)")
    print("="*80)
    
    total = len(all_results)
    passed = sum(1 for r in all_results if r["success"])
    
    print(f"\nErgebnis: {passed}/{total} Tests bestanden ({passed/total*100:.0f}%)")
    
    # Vergleich nach Modellen
    print(f"\n📊 MODELL-VERGLEICH:")
    for model_name in test_models:
        model_results = [r for r in all_results if r.get("model") == model_name]
        if model_results:
            model_passed = sum(1 for r in model_results if r["success"])
            avg_answer_length = sum(r["metrics"].get("answer_length", 0) for r in model_results) / len(model_results)
            avg_citations = sum(r["metrics"].get("citation_count", 0) for r in model_results) / len(model_results)
            
            print(f"\n  🤖 {model_name}:")
            print(f"     Success Rate: {model_passed}/{len(model_results)} ({model_passed/len(model_results)*100:.0f}%)")
            print(f"     Ø Antwortlänge: {avg_answer_length:.0f} Zeichen")
            print(f"     Ø Zitationen: {avg_citations:.1f}")
    
    # Durchschnittliche Metriken über ALLE Tests
    avg_metrics = {}
    for key in all_results[0]["metrics"].keys():
        values = [r["metrics"][key] for r in all_results if key in r["metrics"]]
        if values:
            avg_metrics[key] = sum(values) / len(values)
    
    print(f"\n📊 DURCHSCHNITTLICHE METRIKEN (ALLE MODELLE):")
    for key, value in avg_metrics.items():
        if isinstance(value, float):
            print(f"  • {key}: {value:.2f}")
        else:
            print(f"  • {key}: {value}")
    
    # Häufigste Probleme
    all_issues = []
    for r in all_results:
        all_issues.extend(r["issues"])
    
    if all_issues:
        print(f"\n⚠️ HÄUFIGSTE PROBLEME:")
        from collections import Counter
        issue_counts = Counter(all_issues)
        for issue, count in issue_counts.most_common(5):
            print(f"  [{count}x] {issue}")
    
    # Ratings
    ratings = {}
    for r in all_results:
        rating = r.get("rating", "UNKNOWN")
        ratings[rating] = ratings.get(rating, 0) + 1
    
    print(f"\n🎯 BEWERTUNGEN (GESAMT):")
    for rating in ["EXCELLENT", "GOOD", "NEEDS IMPROVEMENT", "POOR"]:
        count = ratings.get(rating, 0)
        if count > 0:
            print(f"  • {rating}: {count}/{total} ({count/total*100:.0f}%)")
    
    # Speichere Ergebnisse
    output_file = f"rag_test_results_{int(time.time())}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Ergebnisse gespeichert: {output_file}")
    print(f"\n⏱️  Gesamtdauer: {sum(r['duration'] for r in all_results):.1f}s")
    print(f"Ende: {time.strftime('%H:%M:%S')}\n")

if __name__ == "__main__":
    try:
        run_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Test abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
