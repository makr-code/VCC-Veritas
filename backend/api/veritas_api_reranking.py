"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys.
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "covina_module_reranking"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...0ntovA=="  # Gekuerzt fuer Sicherheit
module_organization_key = "26a459d147f38a1935ebda0b017034703b8b3668c43c848352b0a98c4a235f7e"
module_file_key = "2cc748162b5a1bfe94069c3b85deebf2fb4083797c1dbdd84f8c297e66d61b88"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
import logging

# Importiere Funktionen zum Abrufen von Autorenstatistiken und Feedback-Scores
# Diese Funktionen würden normalerweise aus author_stats_generator.py kommen
# oder direkt von der Datenbankabstraktion, wenn diese komplexer ist.
# Für dieses Beispiel sind sie direkt importiert.
from author_stats_generator import (  # Stellen Sie sicher, dass diese importierbar sind
    get_author_document_count,
    get_author_feedback_summary,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def re_rank_documents(
    documents: list,
    user_experience_years: int,
    asking_user_author_id: str,  # Die author_id des fragenden Benutzers
    author_doc_counts: dict,  # Vorab geladene Map von author_id zu Doc-Count
    author_feedback_scores: dict,  # Vorab geladene Map von author_id zu (pos_count, neg_count)
) -> list:
    """
    Rerankt eine Liste von abgerufenen Dokumenten basierend auf verschiedenen Kriterien.

    Args:
        documents (list): Eine Liste von LangChain Document Objekten.
        user_experience_years (int): Die Erfahrungsjahre des fragenden Benutzers.
        asking_user_author_id (str): Die pseudonyme Author ID des fragenden Benutzers.
        author_doc_counts (dict): Ein Dictionary, das für jede Author ID die Anzahl
                                  der von diesem Autor erstellten Dokumente enthält.
                                  Format: {author_id: count}
        author_feedback_scores (dict): Ein Dictionary, das für jede Author ID die
                                       summierten positiven und negativen Feedback-Counts enthält.
                                       Format: {author_id: (positive_count, negative_count)}

    Returns:
        list: Die neu geordnete Liste von LangChain Document Objekten,
              mit einem hinzugefügten 'rerank_score' in den Metadaten.
    """
    logging.info(f"Starte Re-Ranking für {len(documents)} Dokumente.")

    reranked_docs = []

    # Gewichtungsfaktoren (können durch Konfiguration oder ML-Modelle optimiert werden)
    WEIGHT_BASE_SCORE = 1.0  # Grundgewicht des initialen Vektor-Scores
    WEIGHT_HIERARCHY = 0.2  # Gewicht für Hierarchie-Level (höher = besser)
    WEIGHT_DOC_TYPE = 0.1  # Gewicht für spezifische Dokumenttypen
    WEIGHT_USER_EXP_MATCH = 0.15  # Gewicht, wenn Dokument zum Erfahrungslevel des Nutzers passt
    WEIGHT_AUTHOR_EXPERTISE = 0.2  # Gewicht für Autoren-Expertise (mehr Docs = mehr Expertise)
    WEIGHT_AUTHOR_POPULARITY = 0.3  # Gewicht für Autor-Popularität (positives Feedback)
    WEIGHT_DOCUMENT_FEEDBACK = 0.4  # Gewicht für dokument-spezifisches Feedback
    WEIGHT_RECENCY = 0.05  # Gewicht für Aktualität des Dokuments (neuere sind besser)
    WEIGHT_SELF_REFERENCE = 0.0  # Gewicht, wenn Autor des Dokuments = fragender Nutzer (standardmäßig 0, kann erhöht werden)

    # Normalisierungskonstanten (können basierend auf Datenverteilung angepasst werden)
    MAX_HIERARCHY_LEVEL = 5.0  # Annahme: höchste Hierarchie ist 5
    MAX_AUTHOR_DOC_COUNT = 100.0  # Annahme: max. 100 Docs pro Autor
    MAX_USER_EXP = 10.0  # Annahme: max. 10 Jahre Erfahrung für signifikante Wirkung

    for doc in documents:
        # Initialer Score von der Vektorsuche (wichtig als Basis)
        initial_score = doc.metadata.get("relevance_score", 0.0)  # LangChain setzt oft 'relevance_score'

        # Metadaten sicher abrufen mit Fallbacks
        doc_type = doc.metadata.get("doc_type", "unbekannt")
        hierarchy_level = doc.metadata.get("hierarchy_level", 5)  # Annahme: Standard ist niedrigste Prio (höchste Zahl)
        author_id = doc.metadata.get("author_id", "UNKNOWN_AUTHOR")
        feedback_relevance_score = doc.metadata.get("feedback_relevance_score", 1.0)
        publication_date_str = doc.metadata.get("publication_date")  # Format YYYY-MM-DD

        # --- Berechnung der einzelnen Score-Komponenten ---

        # 1. Hierarchie-Score (niedrigere Zahl = höhere Hierarchie = höherer Score)
        # Beispiel: 1 (Gesetz) = hoher Score, 5 (Notiz) = niedriger Score
        hierarchy_score = 1.0 - (min(hierarchy_level, MAX_HIERARCHY_LEVEL) / MAX_HIERARCHY_LEVEL)

        # 2. Dokumenttyp-Score (Beispielhaft, könnte komplexer werden)
        doc_type_score = 0.0
        if doc_type in ["Gesetzestext", "Verordnung"]:
            doc_type_score = 1.0
        elif doc_type == "Urteil":
            doc_type_score = 0.8
        elif doc_type == "Bescheid":
            doc_type_score = 0.6
        elif doc_type == "internes_memo":
            doc_type_score = 0.3

        # 3. User Experience Match Score
        # Wenn der Nutzer z.B. weniger Erfahrung hat, könnten allgemeinere Dokumente höher gewichtet werden
        # Oder umgekehrt, wenn ein sehr erfahrenes Dokument (z.B. von einem Senior-Experten) besser passt.
        # Hier ein einfaches Beispiel: Dokumente mit niedrigem Hierarchielevel (grundlegende Gesetze)
        # könnten für weniger erfahrene Nutzer höher gewichtet werden.
        user_exp_match_score = 0.0
        if user_experience_years < 3 and hierarchy_level <= 2:  # Weniger erfahren bevorzugt grundlegende Gesetze
            user_exp_match_score = 1.0
        elif (
            user_experience_years >= 5 and hierarchy_level >= 3
        ):  # Erfahrenere bevorzugen ggf. detailliertere Bescheide/Urteile
            user_exp_match_score = 0.8  # Beispielwert, je nach Anwendungsfall anpassen

        # 4. Autor-Expertise-Score (basierend auf Anzahl der Dokumente des Autors)
        author_doc_count = author_doc_counts.get(author_id, 0)
        # Normalisierung: Mehr Dokumente = höhere Expertise
        expertise_score = min(author_doc_count / MAX_AUTHOR_DOC_COUNT, 1.0)

        # 5. Autor-Popularität-Score (basierend auf Feedback zu diesem Autor)
        pos_feedback, neg_feedback = author_feedback_scores.get(author_id, (0, 0))
        total_author_feedback = pos_feedback + neg_feedback
        popularity_score = 0.0
        if total_author_feedback > 0:
            popularity_score = (pos_feedback - neg_feedback) / total_author_feedback  # Von -1.0 bis 1.0
            popularity_score = (popularity_score + 1.0) / 2.0  # Auf 0.0 bis 1.0 normalisieren

        # 6. Dokument-spezifischer Feedback-Score
        # Dieser Score kommt direkt aus den Metadaten des Chunks in ChromaDB und wird dynamisch angepasst
        document_feedback_score = feedback_relevance_score  # Ist bereits ein Wert zwischen 0 und 1

        # 7. Aktualitäts-Score (Recency Score)
        recency_score = 0.0
        if publication_date_str and publication_date_str != "YYYY-MM-DD":
            try:
                from datetime import datetime

                doc_date = datetime.strptime(publication_date_str, "%Y-%m-%d")
                # Je näher am heutigen Datum, desto höher der Score
                days_ago = (datetime.now() - doc_date).days
                # Eine einfache logarithmische oder inverse Funktion: je älter, desto niedriger
                # Hier: je neuer, desto näher an 1.0
                recency_score = max(0.0, 1.0 - (days_ago / 365.0) * 0.1)  # Beispiel: 10% Abzug pro Jahr
            except ValueError:
                logging.warning(
                    f"Ungültiges Datumsformat für Dokument {doc.metadata.get('document_id')}: {publication_date_str}"
                )

        # 8. Selbst-Referenzierungs-Score
        # Wenn der Autor des Dokuments der fragende Nutzer ist, könnte das einen kleinen Bonus geben
        # (z.B. der Nutzer möchte seine eigenen Dokumente finden)
        self_reference_score = 0.0
        if asking_user_author_id and author_id == asking_user_author_id and author_id != "UNKNOWN_AUTHOR":
            self_reference_score = 1.0

        # --- Kombinierter Rerank-Score ---
        rerank_score = (
            initial_score * WEIGHT_BASE_SCORE
            + hierarchy_score * WEIGHT_HIERARCHY
            + doc_type_score * WEIGHT_DOC_TYPE
            + user_exp_match_score * WEIGHT_USER_EXP_MATCH
            + expertise_score * WEIGHT_AUTHOR_EXPERTISE
            + popularity_score * WEIGHT_AUTHOR_POPULARITY
            + document_feedback_score * WEIGHT_DOCUMENT_FEEDBACK
            + recency_score * WEIGHT_RECENCY
            + self_reference_score * WEIGHT_SELF_REFERENCE
        )

        # Fügen Sie den neuen Score den Metadaten hinzu
        doc.metadata["rerank_score"] = rerank_score
        reranked_docs.append(doc)
        logging.debug(
            f"Dokument {doc.metadata.get('document_id')} - Initial: {initial_score:.2f}, Reranked: {rerank_score:.2f}"
        )

    # Sortieren Sie die Dokumente basierend auf dem neuen Rerank-Score (absteigend)
    reranked_docs.sort(key=lambda x: x.metadata.get("rerank_score", 0.0), reverse=True)

    logging.info(
        f"Re-Ranking abgeschlossen. Top-Score: {reranked_docs[0].metadata.get('rerank_score', 'N / A'):.2f}"
        if reranked_docs
        else "Keine Dokumente nach Re-Ranking."
    )
    return reranked_docs


# --- Testfunktionen (optional, für interne Tests) ---
if __name__ == "__main__":
    print("Starte Modultest für covina_module_reranking.py...")

    # Dummy-Dokumente für den Test (LangChain Document Struktur imitieren)
    from langchain_core.documents import Document

    doc1 = Document(
        page_content="Inhalt zu Gesetz A, Paragraph 10. Dies ist ein wichtiger Gesetzestext.",
        metadata={
            "document_id": "doc_1",
            "source_file": "gesetz_a.pd",
            "hierarchy_level": 1,
            "doc_type": "Gesetzestext",
            "author_id": "AUTH_001",
            "publication_date": "2023 - 01-01",
            "feedback_relevance_score": 0.9,
            "relevance_score": 0.8,
        },
    )

    doc2 = Document(
        page_content="Detailierter Bescheid zur Anwendung des Paragraphen.",
        metadata={
            "document_id": "doc_2",
            "source_file": "bescheid_x.pd",
            "hierarchy_level": 3,
            "doc_type": "Bescheid",
            "author_id": "AUTH_002",
            "publication_date": "2024 - 03-15",
            "feedback_relevance_score": 0.7,
            "relevance_score": 0.9,
        },
    )

    doc3 = Document(
        page_content="Internes Memo über neue Verwaltungsprozesse.",
        metadata={
            "document_id": "doc_3",
            "source_file": "memo_intern.pd",
            "hierarchy_level": 4,
            "doc_type": "internes_memo",
            "author_id": "AUTH_001",
            "publication_date": "2024 - 07-25",
            "feedback_relevance_score": 0.5,
            "relevance_score": 0.7,
        },
    )

    doc4 = Document(
        page_content="Ein älteres Gesetz zur Raumplanung.",
        metadata={
            "document_id": "doc_4",
            "source_file": "altes_gesetz_y.pd",
            "hierarchy_level": 1,
            "doc_type": "Gesetzestext",
            "author_id": "AUTH_003",
            "publication_date": "2010 - 05-20",
            "feedback_relevance_score": 0.8,
            "relevance_score": 0.85,
        },
    )

    documents_for_reranking = [doc1, doc2, doc3, doc4]

    # Dummy-Autorenstatistiken
    # Normalerweise würden diese aus author_stats_generator.py oder einer DB geladen
    # Hier für den Test manuell gesetzt, da die echten Funktionen möglicherweise DB-Zugriff benötigen
    # Wir überschreiben temporär die Funktionen, falls sie nicht direkt importierbar sind
    def mock_get_author_document_count(author_id):
        counts = {"AUTH_001": 50, "AUTH_002": 5, "AUTH_003": 20, "UNKNOWN_AUTHOR": 0}
        return counts.get(author_id, 0)

    def mock_get_author_feedback_summary(author_id):
        feedback = {"AUTH_001": (100, 10), "AUTH_002": (3, 2), "AUTH_003": (15, 5), "UNKNOWN_AUTHOR": (0, 0)}
        return feedback.get(author_id, (0, 0))

    # Temporäre Überschreibung der Funktionen für den Test
    globals()["get_author_document_count"] = mock_get_author_document_count
    globals()["get_author_feedback_summary"] = mock_get_author_feedback_summary

    # Prepare author_doc_counts and author_feedback_scores for the reranker
    all_author_ids = list(
        set([doc.metadata.get("author_id") for doc in documents_for_reranking if doc.metadata.get("author_id")])
    )
    test_author_doc_counts = {aid: mock_get_author_document_count(aid) for aid in all_author_ids}
    test_author_feedback_scores = {aid: mock_get_author_feedback_summary(aid) for aid in all_author_ids}

    # Testfall 1: Standard-Nutzer
    print("\n--- Testfall 1: Standard-Nutzer (3 Jahre Erfahrung, nicht Autor) ---")
    reranked_1 = re_rank_documents(
        documents_for_reranking,
        user_experience_years=3,
        asking_user_author_id="USER_X",
        author_doc_counts=test_author_doc_counts,
        author_feedback_scores=test_author_feedback_scores,
    )
    for i, doc in enumerate(reranked_1):
        print(
            f"{i + 1}. Dok ID: {doc.metadata['document_id']}, Typ: {doc.metadata['doc_type']}, Hierarchie: {doc.metadata['hierarchy_level']}, Autor: {doc.metadata['author_id']}, Relevanz Score: {doc.metadata['relevance_score']:.2f}, Feedback Score (Doc): {doc.metadata['feedback_relevance_score']:.2f}, Rerank Score: {doc.metadata['rerank_score']:.2f}"
        )

    # Testfall 2: Erfahrener Nutzer (8 Jahre Erfahrung)
    print("\n--- Testfall 2: Erfahrener Nutzer (8 Jahre Erfahrung, nicht Autor) ---")
    reranked_2 = re_rank_documents(
        documents_for_reranking,
        user_experience_years=8,
        asking_user_author_id="USER_Y",
        author_doc_counts=test_author_doc_counts,
        author_feedback_scores=test_author_feedback_scores,
    )
    for i, doc in enumerate(reranked_2):
        print(
            f"{i + 1}. Dok ID: {doc.metadata['document_id']}, Typ: {doc.metadata['doc_type']}, Hierarchie: {doc.metadata['hierarchy_level']}, Autor: {doc.metadata['author_id']}, Relevanz Score: {doc.metadata['relevance_score']:.2f}, Feedback Score (Doc): {doc.metadata['feedback_relevance_score']:.2f}, Rerank Score: {doc.metadata['rerank_score']:.2f}"
        )

    # Testfall 3: Autor AUTH_001 fragt (Self-Reference)
    print("\n--- Testfall 3: Autor AUTH_001 fragt (5 Jahre Erfahrung) ---")
    reranked_3 = re_rank_documents(
        documents_for_reranking,
        user_experience_years=5,
        asking_user_author_id="AUTH_001",
        author_doc_counts=test_author_doc_counts,
        author_feedback_scores=test_author_feedback_scores,
    )
    for i, doc in enumerate(reranked_3):
        print(
            f"{i + 1}. Dok ID: {doc.metadata['document_id']}, Typ: {doc.metadata['doc_type']}, Hierarchie: {doc.metadata['hierarchy_level']}, Autor: {doc.metadata['author_id']}, Relevanz Score: {doc.metadata['relevance_score']:.2f}, Feedback Score (Doc): {doc.metadata['feedback_relevance_score']:.2f}, Rerank Score: {doc.metadata['rerank_score']:.2f}"
        )

    print("\nModultest beendet.")
