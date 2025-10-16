"""
Ground-Truth Dataset für Phase 5 Hybrid Search Evaluation
Enthält 25 Test-Queries mit expected results und relevance scores
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum


class QueryCategory(str, Enum):
    """Query-Kategorien für verschiedene Use-Cases"""
    LEGAL_SPECIFIC = "legal_specific"  # Spezifische Rechtsnormen
    LEGAL_GENERAL = "legal_general"  # Allgemeine Rechtsthemen
    ADMINISTRATIVE = "administrative"  # Verwaltungsrecht
    ENVIRONMENTAL = "environmental"  # Umweltrecht
    SOCIAL = "social"  # Sozialrecht
    TRAFFIC = "traffic"  # Verkehrsrecht
    CONSTRUCTION = "construction"  # Baurecht


@dataclass
class RelevantDocument:
    """Ein relevantes Dokument für eine Query"""
    doc_id: str
    relevance_score: float  # 0.0 = nicht relevant, 1.0 = perfekt relevant
    explanation: str = ""  # Warum ist dieses Dokument relevant?


@dataclass
class GroundTruthQuery:
    """Eine Test-Query mit erwarteten Ergebnissen"""
    query_id: str
    query_text: str
    category: QueryCategory
    relevant_docs: List[RelevantDocument] = field(default_factory=list)
    expected_top1: str = ""  # Expected Top-1 Result (doc_id)
    expected_top3: List[str] = field(default_factory=list)  # Expected Top-3 Results
    description: str = ""  # Was testet diese Query?
    
    def get_relevance_score(self, doc_id: str) -> float:
        """Get relevance score for a document"""
        for doc in self.relevant_docs:
            if doc.doc_id == doc_id:
                return doc.relevance_score
        return 0.0
    
    def get_dcg_weights(self) -> Dict[str, float]:
        """Get DCG weights for all documents"""
        return {doc.doc_id: doc.relevance_score for doc in self.relevant_docs}


# =============================================================================
# GROUND-TRUTH DATASET
# =============================================================================

GROUND_TRUTH_DATASET = [
    
    # -------------------------------------------------------------------------
    # LEGAL_SPECIFIC: Spezifische Rechtsnormen
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="legal_001",
        query_text="BGB Taschengeldparagraph Minderjährige",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="bgb_110",
        expected_top3=["bgb_110", "bgb_107", "bgb_108"],
        relevant_docs=[
            RelevantDocument("bgb_110", 1.0, "Direkt relevanter Taschengeldparagraph"),
            RelevantDocument("bgb_107", 0.8, "Vertragsschluss von Minderjährigen (Kontext)"),
            RelevantDocument("bgb_108", 0.7, "Minderjährige ohne Einwilligung (Kontext)"),
            RelevantDocument("bgb_433", 0.3, "Kaufvertrag allgemein (schwach relevant)"),
        ],
        description="Test: Findet spezifische Rechtsnorm mit Synonym (Taschengeldparagraph = § 110 BGB)"
    ),
    
    GroundTruthQuery(
        query_id="legal_002",
        query_text="§ 433 BGB Kaufvertrag Pflichten",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="bgb_433",
        expected_top3=["bgb_433", "bgb_434", "bgb_437"],
        relevant_docs=[
            RelevantDocument("bgb_433", 1.0, "Exakte Übereinstimmung § 433 BGB"),
            RelevantDocument("bgb_434", 0.9, "Sachmängelhaftung beim Kaufvertrag"),
            RelevantDocument("bgb_437", 0.8, "Mängelrechte des Käufers"),
            RelevantDocument("bgb_311", 0.5, "Vertragsschluss allgemein"),
        ],
        description="Test: Paragraph-Suche mit § Zeichen"
    ),
    
    GroundTruthQuery(
        query_id="legal_003",
        query_text="Verwaltungsakt Definition VwVfG",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="vwvfg_35",
        expected_top3=["vwvfg_35", "vwvfg_28", "vwvfg_48"],
        relevant_docs=[
            RelevantDocument("vwvfg_35", 1.0, "Begriff des Verwaltungsaktes"),
            RelevantDocument("vwvfg_28", 0.7, "Bekanntgabe des Verwaltungsaktes"),
            RelevantDocument("vwvfg_48", 0.7, "Rücknahme des Verwaltungsaktes"),
            RelevantDocument("vwvfg_24", 0.5, "Anhörung (prozeduraler Kontext)"),
        ],
        description="Test: Verwaltungsrecht Definition-Query"
    ),
    
    # -------------------------------------------------------------------------
    # LEGAL_GENERAL: Allgemeine Rechtsthemen
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="legal_004",
        query_text="Kaufvertrag Rechtsmängel Gewährleistung",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="bgb_434",
        expected_top3=["bgb_434", "bgb_437", "bgb_433"],
        relevant_docs=[
            RelevantDocument("bgb_434", 1.0, "Sachmängel beim Kaufvertrag"),
            RelevantDocument("bgb_437", 0.9, "Gewährleistungsrechte"),
            RelevantDocument("bgb_433", 0.7, "Kaufvertrag Pflichten"),
            RelevantDocument("bgb_311", 0.4, "Vertragsschluss"),
        ],
        description="Test: Thematische Suche ohne Paragraphen-Nummer"
    ),
    
    GroundTruthQuery(
        query_id="legal_005",
        query_text="Vertragsschluss Rechtsgeschäft Willenserklärung",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="bgb_145",
        expected_top3=["bgb_145", "bgb_147", "bgb_311"],
        relevant_docs=[
            RelevantDocument("bgb_145", 1.0, "Angebot (Willenserklärung)"),
            RelevantDocument("bgb_147", 0.9, "Annahme der Willenserklärung"),
            RelevantDocument("bgb_311", 0.8, "Vertragsschluss allgemein"),
            RelevantDocument("bgb_433", 0.5, "Kaufvertrag als Beispiel"),
        ],
        description="Test: Multi-Konzept Query (3 verwandte Begriffe)"
    ),
    
    # -------------------------------------------------------------------------
    # ADMINISTRATIVE: Verwaltungsrecht
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="admin_001",
        query_text="Anhörung Verwaltungsverfahren Beteiligung",
        category=QueryCategory.ADMINISTRATIVE,
        expected_top1="vwvfg_24",
        expected_top3=["vwvfg_24", "vwvfg_28", "vwvfg_13"],
        relevant_docs=[
            RelevantDocument("vwvfg_24", 1.0, "Anhörung Beteiligter"),
            RelevantDocument("vwvfg_28", 0.7, "Bekanntgabe (prozeduraler Kontext)"),
            RelevantDocument("vwvfg_13", 0.6, "Beteiligte im Verfahren"),
            RelevantDocument("vwvfg_35", 0.4, "Verwaltungsakt Definition"),
        ],
        description="Test: Prozedurales Verwaltungsrecht"
    ),
    
    GroundTruthQuery(
        query_id="admin_002",
        query_text="Rücknahme rechtswidriger Verwaltungsakt",
        category=QueryCategory.ADMINISTRATIVE,
        expected_top1="vwvfg_48",
        expected_top3=["vwvfg_48", "vwvfg_49", "vwvfg_35"],
        relevant_docs=[
            RelevantDocument("vwvfg_48", 1.0, "Rücknahme rechtswidriger VA"),
            RelevantDocument("vwvfg_49", 0.8, "Widerruf rechtmäßiger VA"),
            RelevantDocument("vwvfg_35", 0.5, "VA Definition (Kontext)"),
            RelevantDocument("vwvfg_28", 0.3, "Bekanntgabe"),
        ],
        description="Test: Spezifisches Verwaltungsakt-Thema"
    ),
    
    # -------------------------------------------------------------------------
    # ENVIRONMENTAL: Umweltrecht
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="env_001",
        query_text="Emissionsschutz Luftreinhaltung Grenzwerte",
        category=QueryCategory.ENVIRONMENTAL,
        expected_top1="bundes_immissionsschutzgesetz_45",
        expected_top3=["bundes_immissionsschutzgesetz_45", "bundes_immissionsschutzgesetz_48", "ta_luft_4"],
        relevant_docs=[
            RelevantDocument("bundes_immissionsschutzgesetz_45", 1.0, "Emissionsgrenzwerte"),
            RelevantDocument("bundes_immissionsschutzgesetz_48", 0.8, "Luftreinhaltung"),
            RelevantDocument("ta_luft_4", 0.8, "Technische Anleitung Luft"),
            RelevantDocument("umweltvertraeglichkeitspruefungsgesetz_3", 0.5, "UVP allgemein"),
        ],
        description="Test: Umweltrecht Emissionen"
    ),
    
    GroundTruthQuery(
        query_id="env_002",
        query_text="Umweltverträglichkeitsprüfung UVP Voraussetzungen",
        category=QueryCategory.ENVIRONMENTAL,
        expected_top1="uvpg_3",
        expected_top3=["uvpg_3", "uvpg_7", "uvpg_2"],
        relevant_docs=[
            RelevantDocument("uvpg_3", 1.0, "UVP-Pflicht"),
            RelevantDocument("uvpg_7", 0.9, "Verfahrensschritte UVP"),
            RelevantDocument("uvpg_2", 0.7, "Anwendungsbereich"),
        ],
        description="Test: UVP-Recht"
    ),
    
    # -------------------------------------------------------------------------
    # SOCIAL: Sozialrecht
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="social_001",
        query_text="Arbeitslosengeld Anspruch Voraussetzungen",
        category=QueryCategory.SOCIAL,
        expected_top1="sgb_iii_137",
        expected_top3=["sgb_iii_137", "sgb_iii_138", "sgb_iii_142"],
        relevant_docs=[
            RelevantDocument("sgb_iii_137", 1.0, "Anspruch auf Arbeitslosengeld"),
            RelevantDocument("sgb_iii_138", 0.9, "Anspruchsdauer"),
            RelevantDocument("sgb_iii_142", 0.7, "Höhe des Arbeitslosengeldes"),
            RelevantDocument("sgb_i_11", 0.4, "Sozialleistungen allgemein"),
        ],
        description="Test: Sozialrecht Arbeitslosengeld"
    ),
    
    GroundTruthQuery(
        query_id="social_002",
        query_text="Kindergeld Anspruch Familie",
        category=QueryCategory.SOCIAL,
        expected_top1="estg_62",
        expected_top3=["estg_62", "estg_63", "estg_66"],
        relevant_docs=[
            RelevantDocument("estg_62", 1.0, "Anspruch auf Kindergeld"),
            RelevantDocument("estg_63", 0.9, "Höhe des Kindergeldes"),
            RelevantDocument("estg_66", 0.7, "Zahlung des Kindergeldes"),
        ],
        description="Test: Familienrecht Kindergeld"
    ),
    
    # -------------------------------------------------------------------------
    # TRAFFIC: Verkehrsrecht
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="traffic_001",
        query_text="Geschwindigkeitsüberschreitung Bußgeld Fahrverbot",
        category=QueryCategory.TRAFFIC,
        expected_top1="stvo_3",
        expected_top3=["stvo_3", "bukat_11", "stvo_49"],
        relevant_docs=[
            RelevantDocument("stvo_3", 1.0, "Geschwindigkeit § 3 StVO"),
            RelevantDocument("bukat_11", 0.9, "Bußgeldkatalog Geschwindigkeit"),
            RelevantDocument("stvo_49", 0.7, "Ordnungswidrigkeiten"),
        ],
        description="Test: Verkehrsrecht Geschwindigkeit"
    ),
    
    GroundTruthQuery(
        query_id="traffic_002",
        query_text="Verkehrsunfall Haftung Schadensersatz",
        category=QueryCategory.TRAFFIC,
        expected_top1="strassenverkehrsgesetz_7",
        expected_top3=["strassenverkehrsgesetz_7", "bgb_823", "strassenverkehrsgesetz_18"],
        relevant_docs=[
            RelevantDocument("strassenverkehrsgesetz_7", 1.0, "Haftung Fahrzeughalter"),
            RelevantDocument("bgb_823", 0.8, "Schadensersatzpflicht allgemein"),
            RelevantDocument("strassenverkehrsgesetz_18", 0.7, "Versicherungspflicht"),
        ],
        description="Test: Verkehrsunfall Haftung"
    ),
    
    # -------------------------------------------------------------------------
    # CONSTRUCTION: Baurecht
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="construction_001",
        query_text="Baugenehmigung Voraussetzungen Bauantrag",
        category=QueryCategory.CONSTRUCTION,
        expected_top1="bauo_58",
        expected_top3=["bauo_58", "bauo_59", "bauo_63"],
        relevant_docs=[
            RelevantDocument("bauo_58", 1.0, "Baugenehmigung"),
            RelevantDocument("bauo_59", 0.9, "Bauantrag"),
            RelevantDocument("bauo_63", 0.7, "Genehmigungsfreistellung"),
        ],
        description="Test: Baurecht Genehmigung"
    ),
    
    # -------------------------------------------------------------------------
    # COMPLEX QUERIES: Multi-Themen
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="complex_001",
        query_text="Menschenwürde Grundrechte Verfassung",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="gg_1",
        expected_top3=["gg_1", "gg_2", "gg_19"],
        relevant_docs=[
            RelevantDocument("gg_1", 1.0, "Menschenwürde Art. 1 GG"),
            RelevantDocument("gg_2", 0.8, "Persönliche Freiheitsrechte"),
            RelevantDocument("gg_19", 0.6, "Einschränkung von Grundrechten"),
        ],
        description="Test: Verfassungsrecht Grundrechte"
    ),
    
    GroundTruthQuery(
        query_id="complex_002",
        query_text="Diebstahl § 242 StGB Straftat",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="stgb_242",
        expected_top3=["stgb_242", "stgb_243", "stgb_249"],
        relevant_docs=[
            RelevantDocument("stgb_242", 1.0, "Diebstahl § 242 StGB"),
            RelevantDocument("stgb_243", 0.8, "Besonders schwerer Diebstahl"),
            RelevantDocument("stgb_249", 0.7, "Raub (verwandte Straftat)"),
        ],
        description="Test: Strafrecht Diebstahl"
    ),
    
    # -------------------------------------------------------------------------
    # EDGE CASES: Spezialfälle
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="edge_001",
        query_text="110",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="bgb_110",
        expected_top3=["bgb_110", "stgb_110", "vwvfg_110"],
        relevant_docs=[
            RelevantDocument("bgb_110", 1.0, "Wahrscheinlich BGB § 110 gemeint"),
            RelevantDocument("stgb_110", 0.5, "Könnte auch StGB sein"),
            RelevantDocument("vwvfg_110", 0.3, "Oder VwVfG"),
        ],
        description="Test: Nur Paragraph-Nummer (Ambiguität)"
    ),
    
    GroundTruthQuery(
        query_id="edge_002",
        query_text="Paragraph 433",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="bgb_433",
        expected_top3=["bgb_433", "stgb_433", "hgb_433"],
        relevant_docs=[
            RelevantDocument("bgb_433", 1.0, "Kaufvertrag BGB häufigste Bedeutung"),
            RelevantDocument("stgb_433", 0.4, "Weniger wahrscheinlich"),
        ],
        description="Test: 'Paragraph' statt '§' Symbol"
    ),
    
    GroundTruthQuery(
        query_id="edge_003",
        query_text="BGB Vertragsrecht",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="bgb_311",
        expected_top3=["bgb_311", "bgb_433", "bgb_434"],
        relevant_docs=[
            RelevantDocument("bgb_311", 1.0, "Vertragsschluss (Kern des Vertragsrechts)"),
            RelevantDocument("bgb_433", 0.9, "Kaufvertrag (häufiger Vertragstyp)"),
            RelevantDocument("bgb_434", 0.7, "Sachmängel (Vertragsrecht)"),
            RelevantDocument("bgb_145", 0.8, "Angebot (Vertragsschluss)"),
        ],
        description="Test: Sehr allgemeine Query (breite Relevanz)"
    ),
    
    # -------------------------------------------------------------------------
    # SYNONYME & UMGANGSSPRACHE
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="synonym_001",
        query_text="Jugendlicher Vertrag Taschengeld",
        category=QueryCategory.LEGAL_SPECIFIC,
        expected_top1="bgb_110",
        expected_top3=["bgb_110", "bgb_107", "bgb_108"],
        relevant_docs=[
            RelevantDocument("bgb_110", 1.0, "Jugendlicher = Minderjähriger, Taschengeld"),
            RelevantDocument("bgb_107", 0.8, "Minderjährige Verträge"),
        ],
        description="Test: Synonyme (Jugendlicher statt Minderjähriger)"
    ),
    
    GroundTruthQuery(
        query_id="synonym_002",
        query_text="Kauf verkaufen Gewährleistung Mangel",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="bgb_433",
        expected_top3=["bgb_433", "bgb_434", "bgb_437"],
        relevant_docs=[
            RelevantDocument("bgb_433", 1.0, "Kaufvertrag"),
            RelevantDocument("bgb_434", 1.0, "Sachmängel"),
            RelevantDocument("bgb_437", 0.9, "Gewährleistungsrechte"),
        ],
        description="Test: Umgangssprache statt Fachbegriffe"
    ),
    
    # -------------------------------------------------------------------------
    # LONG-TAIL QUERIES
    # -------------------------------------------------------------------------
    
    GroundTruthQuery(
        query_id="longtail_001",
        query_text="Was muss ich beachten wenn ich als Minderjähriger etwas kaufen möchte mit meinem Taschengeld",
        category=QueryCategory.LEGAL_GENERAL,
        expected_top1="bgb_110",
        expected_top3=["bgb_110", "bgb_107", "bgb_433"],
        relevant_docs=[
            RelevantDocument("bgb_110", 1.0, "Taschengeldparagraph exakt relevant"),
            RelevantDocument("bgb_107", 0.7, "Minderjährige allgemein"),
            RelevantDocument("bgb_433", 0.5, "Kaufvertrag"),
        ],
        description="Test: Natürlichsprachige Frage (long-tail)"
    ),
    
    GroundTruthQuery(
        query_id="longtail_002",
        query_text="Wie funktioniert das Verwaltungsverfahren wenn eine Behörde eine Entscheidung gegen mich treffen will",
        category=QueryCategory.ADMINISTRATIVE,
        expected_top1="vwvfg_24",
        expected_top3=["vwvfg_24", "vwvfg_28", "vwvfg_35"],
        relevant_docs=[
            RelevantDocument("vwvfg_24", 1.0, "Anhörung vor Verwaltungsakt"),
            RelevantDocument("vwvfg_28", 0.8, "Bekanntgabe"),
            RelevantDocument("vwvfg_35", 0.7, "Was ist ein Verwaltungsakt"),
        ],
        description="Test: Natürlichsprachige Frage Verwaltungsrecht"
    ),
]


def get_dataset_statistics():
    """Get statistics about the ground-truth dataset"""
    stats = {
        "total_queries": len(GROUND_TRUTH_DATASET),
        "by_category": {},
        "avg_relevant_docs": 0,
        "total_relevant_docs": 0,
    }
    
    for query in GROUND_TRUTH_DATASET:
        category = query.category.value
        stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
        stats["total_relevant_docs"] += len(query.relevant_docs)
    
    stats["avg_relevant_docs"] = stats["total_relevant_docs"] / stats["total_queries"]
    
    return stats


def print_dataset_info():
    """Print dataset information"""
    print("=" * 80)
    print("GROUND-TRUTH DATASET INFORMATION")
    print("=" * 80)
    print()
    
    stats = get_dataset_statistics()
    
    print(f"Total Queries: {stats['total_queries']}")
    print(f"Avg Relevant Docs per Query: {stats['avg_relevant_docs']:.1f}")
    print()
    
    print("Queries by Category:")
    for category, count in sorted(stats['by_category'].items()):
        print(f"   {category}: {count}")
    print()
    
    print("Sample Queries:")
    for i, query in enumerate(GROUND_TRUTH_DATASET[:5], 1):
        print(f"   {i}. [{query.category.value}] {query.query_text}")
        print(f"      Expected Top-1: {query.expected_top1}")
    print(f"   ... ({stats['total_queries'] - 5} more)")
    print()


if __name__ == "__main__":
    print_dataset_info()
    
    print("=" * 80)
    print("DATASET READY FOR EVALUATION")
    print("=" * 80)
    print()
    print("Usage:")
    print("   from tests.ground_truth_dataset import GROUND_TRUTH_DATASET")
    print("   for query in GROUND_TRUTH_DATASET:")
    print("       results = retriever.retrieve(query.query_text, top_k=10)")
    print("       ndcg = calculate_ndcg(results, query.get_dcg_weights())")
    print()
