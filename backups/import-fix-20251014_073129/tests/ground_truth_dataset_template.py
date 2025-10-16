"""
Ground-Truth Evaluation Dataset for Phase 5

This template helps create labeled test queries for evaluating the
Advanced RAG Pipeline (Hybrid Search + Query Expansion).

Format:
    Each test case includes:
    - query: The search query
    - expected_doc_ids: List of relevant document IDs (in order of relevance)
    - relevance_scores: Dict mapping doc_id to relevance score (0.0-1.0)
    - category: Query category (legal, technical, environmental, multi_topic)
    - description: Human-readable description

Usage:
    1. Fill in real document IDs from your corpus
    2. Assign relevance scores based on manual review
    3. Load this dataset in test_phase5_evaluation.py
    4. Run evaluation with real UDS3 strategy

Relevance Score Guidelines:
    1.0 = Perfect match (exactly answers the query)
    0.8-0.9 = Highly relevant (directly addresses most aspects)
    0.6-0.7 = Relevant (addresses some aspects)
    0.4-0.5 = Somewhat relevant (mentions topic but tangential)
    0.1-0.3 = Marginally relevant (mentions related terms)
    0.0 = Not relevant
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class GroundTruthTestCase:
    """Labeled test case for evaluation."""
    query: str
    expected_doc_ids: List[str]
    relevance_scores: Dict[str, float]
    category: str
    description: str


# ============================================================================
# TEMPLATE: Replace with real document IDs from your corpus
# ============================================================================

GROUND_TRUTH_DATASET = [
    # ========================================================================
    # CATEGORY: Legal Queries
    # ========================================================================
    
    GroundTruthTestCase(
        query="§ 242 BGB Treu und Glauben",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "bgb_242_treu_und_glauben",  # Perfect match - BGB § 242 text
            "bgb_allgemeiner_teil_overview",  # High relevance - contains § 242
            "vertragsrecht_grundlagen",  # Relevant - discusses Treu und Glauben
            "baurecht_overview",  # Somewhat relevant - mentions § 242
        ],
        relevance_scores={
            "bgb_242_treu_und_glauben": 1.0,  # Perfect
            "bgb_allgemeiner_teil_overview": 0.8,  # High
            "vertragsrecht_grundlagen": 0.6,  # Relevant
            "baurecht_overview": 0.4,  # Somewhat relevant
        },
        category="legal",
        description="Exact legal paragraph lookup with context"
    ),
    
    GroundTruthTestCase(
        query="Baurecht BGB VOB Vorschriften",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "baurecht_overview",
            "vob_teil_b_vertragsrecht",
            "bgb_werkvertragsrecht",
            "bauordnung_grundlagen",
        ],
        relevance_scores={
            "baurecht_overview": 1.0,
            "vob_teil_b_vertragsrecht": 0.9,
            "bgb_werkvertragsrecht": 0.8,
            "bauordnung_grundlagen": 0.7,
        },
        category="legal",
        description="Multi-keyword legal query spanning BGB and VOB"
    ),
    
    # ========================================================================
    # CATEGORY: Technical Norms
    # ========================================================================
    
    GroundTruthTestCase(
        query="DIN 18040-1 Barrierefreies Bauen",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "din_18040_1_barrierefreiheit",  # Exact norm
            "barrierefreiheit_oeffentliche_gebaeude",
            "din_18040_2_wohnungen",  # Related norm
            "bauordnung_barrierefreiheit",
        ],
        relevance_scores={
            "din_18040_1_barrierefreiheit": 1.0,
            "barrierefreiheit_oeffentliche_gebaeude": 0.9,
            "din_18040_2_wohnungen": 0.7,
            "bauordnung_barrierefreiheit": 0.6,
        },
        category="technical",
        description="Exact DIN norm lookup"
    ),
    
    GroundTruthTestCase(
        query="Barrierefreiheit öffentliche Gebäude Normen",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "din_18040_1_barrierefreiheit",
            "barrierefreiheit_oeffentliche_gebaeude",
            "bauordnung_barrierefreiheit",
            "din_18024_accessibility",  # Older related norm
        ],
        relevance_scores={
            "din_18040_1_barrierefreiheit": 1.0,
            "barrierefreiheit_oeffentliche_gebaeude": 1.0,
            "bauordnung_barrierefreiheit": 0.8,
            "din_18024_accessibility": 0.5,  # Outdated but related
        },
        category="technical",
        description="Semantic technical query without exact norm number"
    ),
    
    # ========================================================================
    # CATEGORY: Environmental Law
    # ========================================================================
    
    GroundTruthTestCase(
        query="Umweltverträglichkeitsprüfung UVPG",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "uvpg_gesetz_text",
            "uvp_verfahren_leitfaden",
            "umweltrecht_grundlagen",
            "baugenehmigung_uvp",
        ],
        relevance_scores={
            "uvpg_gesetz_text": 1.0,
            "uvp_verfahren_leitfaden": 0.9,
            "umweltrecht_grundlagen": 0.7,
            "baugenehmigung_uvp": 0.6,
        },
        category="environmental",
        description="Environmental law with acronym UVP/UVPG"
    ),
    
    # ========================================================================
    # CATEGORY: Multi-Topic Queries
    # ========================================================================
    
    GroundTruthTestCase(
        query="Nachhaltiges barrierefreies Bauen mit Umweltverträglichkeitsprüfung",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "nachhaltiges_bauen_leitfaden",
            "din_18040_1_barrierefreiheit",
            "uvp_verfahren_leitfaden",
            "energieeffizienz_gebaeude",
            "umweltrecht_grundlagen",
        ],
        relevance_scores={
            "nachhaltiges_bauen_leitfaden": 1.0,  # All topics
            "din_18040_1_barrierefreiheit": 0.8,  # Barrierefreiheit
            "uvp_verfahren_leitfaden": 0.8,  # UVP
            "energieeffizienz_gebaeude": 0.7,  # Nachhaltigkeit
            "umweltrecht_grundlagen": 0.6,  # UVP context
        },
        category="multi_topic",
        description="Complex query spanning sustainability, accessibility, environment"
    ),
    
    GroundTruthTestCase(
        query="Wie baue ich ein energieeffizientes Haus nach aktuellen Normen?",
        expected_doc_ids=[
            # TODO: Replace with actual document IDs
            "energieeffizienz_gebaeude",
            "enev_gebaeudeenergiegesetz",
            "din_4108_waermeschutz",
            "kfw_foerderung_effizienzhaus",
            "bauordnung_grundlagen",
        ],
        relevance_scores={
            "energieeffizienz_gebaeude": 1.0,
            "enev_gebaeudeenergiegesetz": 0.9,
            "din_4108_waermeschutz": 0.8,
            "kfw_foerderung_effizienzhaus": 0.7,
            "bauordnung_grundlagen": 0.5,
        },
        category="multi_topic",
        description="Natural language question, energy + norms"
    ),
    
    # ========================================================================
    # ADD MORE TEST CASES HERE
    # ========================================================================
    
    # TODO: Add 15-20 more test cases covering:
    # - Edge cases (very short queries, very long queries)
    # - Specialized legal terms
    # - Technical abbreviations (DIN, VOB, BGB, UVPG, etc.)
    # - Multi-word phrases
    # - Questions vs keywords
    # - Ambiguous queries
    
]


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_dataset(dataset: List[GroundTruthTestCase]) -> List[str]:
    """Validate ground-truth dataset.
    
    Checks:
        - Relevance scores between 0.0 and 1.0
        - All expected_doc_ids have relevance scores
        - Relevance scores sorted in descending order
        - At least one doc with score >= 0.8
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    for i, test_case in enumerate(dataset):
        # Check relevance scores range
        for doc_id, score in test_case.relevance_scores.items():
            if not 0.0 <= score <= 1.0:
                errors.append(
                    f"Test case {i} ('{test_case.query}'): "
                    f"Invalid relevance score {score} for {doc_id}"
                )
        
        # Check all expected docs have scores
        missing_scores = set(test_case.expected_doc_ids) - set(test_case.relevance_scores.keys())
        if missing_scores:
            errors.append(
                f"Test case {i} ('{test_case.query}'): "
                f"Missing relevance scores for: {missing_scores}"
            )
        
        # Check at least one highly relevant doc
        max_score = max(test_case.relevance_scores.values()) if test_case.relevance_scores else 0.0
        if max_score < 0.8:
            errors.append(
                f"Test case {i} ('{test_case.query}'): "
                f"No highly relevant docs (max score {max_score:.2f})"
            )
        
        # Check relevance scores are sorted
        expected_scores = [
            test_case.relevance_scores.get(doc_id, 0.0)
            for doc_id in test_case.expected_doc_ids
        ]
        if expected_scores != sorted(expected_scores, reverse=True):
            errors.append(
                f"Test case {i} ('{test_case.query}'): "
                f"Expected docs not sorted by relevance"
            )
    
    return errors


def get_dataset_stats(dataset: List[GroundTruthTestCase]) -> Dict[str, any]:
    """Get statistics about the dataset."""
    categories = {}
    total_docs = 0
    avg_relevance = []
    
    for test_case in dataset:
        # Category distribution
        categories[test_case.category] = categories.get(test_case.category, 0) + 1
        
        # Document counts
        total_docs += len(test_case.expected_doc_ids)
        
        # Average relevance
        if test_case.relevance_scores:
            avg_relevance.append(
                sum(test_case.relevance_scores.values()) / len(test_case.relevance_scores)
            )
    
    return {
        "total_queries": len(dataset),
        "categories": categories,
        "avg_docs_per_query": total_docs / len(dataset) if dataset else 0,
        "avg_relevance_score": sum(avg_relevance) / len(avg_relevance) if avg_relevance else 0,
    }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=== Ground-Truth Dataset Validation ===\n")
    
    # Validate dataset
    errors = validate_dataset(GROUND_TRUTH_DATASET)
    
    if errors:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"   - {error}")
        print()
    else:
        print("✅ Dataset validation passed!\n")
    
    # Show statistics
    stats = get_dataset_stats(GROUND_TRUTH_DATASET)
    print("📊 Dataset Statistics:")
    print(f"   Total queries: {stats['total_queries']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Avg docs per query: {stats['avg_docs_per_query']:.1f}")
    print(f"   Avg relevance score: {stats['avg_relevance_score']:.2f}")
    print()
    
    # Show sample
    print("📝 Sample test case:")
    sample = GROUND_TRUTH_DATASET[0]
    print(f"   Query: {sample.query}")
    print(f"   Category: {sample.category}")
    print(f"   Expected docs: {len(sample.expected_doc_ids)}")
    print(f"   Top relevance: {max(sample.relevance_scores.values()):.2f}")
    print()
    
    print("⚠️  NEXT STEPS:")
    print("   1. Replace TODO doc IDs with real document IDs from your corpus")
    print("   2. Add 15-20 more test cases for comprehensive coverage")
    print("   3. Review and adjust relevance scores based on manual inspection")
    print("   4. Import this dataset in test_phase5_evaluation.py")
    print("   5. Run evaluation with: python tests/test_phase5_evaluation.py")
