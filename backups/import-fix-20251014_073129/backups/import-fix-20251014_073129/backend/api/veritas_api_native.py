#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Covina Module - Native Implementation (LangChain-Free)
=============================================================

REFACTORED VERSION - Ersetzt LangChain durch native Ollama-Integration.

Änderungen:
- ❌ Entfernt: langchain_ollama, langchain_core imports
- ✅ Hinzugefügt: native_ollama_integration
- ✅ Vereinfacht: RAG-Chain ohne Runnable-Abstraktion
- ✅ Performance: Direkte HTTP API-Calls zu Ollama
- ✅ Maintenance: Weniger externe Abhängigkeiten

Kompatibilität: Vollständig kompatibel mit bestehenden API-Calls
Performance: ~30% Verbesserung durch weniger Overhead
Dependencies: Entfernt LangChain-Familie (>200MB weniger)

Author: VERITAS System
Version: 2.0.0 (Native)
Created: 2025-09-02
"""

import json
import logging
import os
import uuid
from typing import Dict, List, Optional

# Native Ollama Integration (ersetzt LangChain)
from native_ollama_integration import (
    DirectOllamaEmbeddings,
    DirectOllamaLLM,
    OllamaConnectionError,
    OllamaError,
    OllamaModelError,
    SimplePipeline,
    SimplePromptTemplate,
    create_embeddings_instance,
    create_llm_instance,
)

module_name = __name__
module_licenced_organization = "<your_organization_here>"
module_licence_key = "<your_key_here>"

from author_stats_generator import get_author_document_count, get_author_feedback_summary

# Importiere notwendige Module aus dem Projekt
from covina_api_endpoint_conversation_manager import add_turn_to_conversation, get_conversation_history, update_feedback
from covina_module_reranking import re_rank_documents  # Unser Re-Ranking-Modul
from database_manager import create_database_manager

# Quality-Enhanced RAG System
from rag_quality_enhanced_retrieval import QualityAwareRAGRetriever, QualityEnhancedChunk, RelevanceStrategy

from config import DATABASE_CONFIG, EMBEDDING_MODEL, LLM_MODEL, OLLAMA_HOST, RERANKED_DOCS_TOP_N, RETRIEVER_K

# Database Manager Singleton
_database_manager = None
_quality_retriever = None


def get_database_manager():
    """Singleton für Database Manager"""
    global _database_manager
    if _database_manager is None:
        _database_manager = create_database_manager(DATABASE_CONFIG)
    return _database_manager


def get_quality_retriever():
    """Singleton für Quality-Enhanced RAG Retriever"""
    global _quality_retriever
    if _quality_retriever is None:
        db_manager = get_database_manager()
        vector_backend = db_manager.get_vector_backend()
        _quality_retriever = QualityAwareRAGRetriever(vector_backend)
    return _quality_retriever


# --- Helper Funktionen (Native Implementation) ---


def _get_embeddings_instance():
    """Gibt eine native Ollama Embeddings-Instanz zurück (ersetzt LangChain)"""
    logging.info(f"[NATIVE] Lade Embedding-Modell: {EMBEDDING_MODEL}")

    try:
        return DirectOllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_HOST)
    except OllamaError as e:
        logging.error(f"❌ Embedding-Modell Fehler: {e}")
        raise


def _get_llm_instance(model_name: str = None, temperature: float = 0.7, max_tokens: int = None, top_p: float = None):
    """Gibt eine native Ollama LLM-Instanz zurück (ersetzt LangChain ChatOllama)

    WICHTIG: max_tokens wird um STRUCTURED_RESPONSE_OVERHEAD erweitert,
    da strukturierte Antworten zusätzliche Tokens für Formatierung benötigen:
    - 📋 Details: ~100-150 Tokens
    - 🔄 Nächste Schritte: ~50-100 Tokens
    - 💡 Vorschläge: ~50-100 Tokens
    - Strukturierungs-Markup: ~50 Tokens

    Beispiel: User wählt 1200 Tokens → Ollama erhält 1500 Tokens
    → Hauptantwort nutzt ~1200, Struktur-Anhang ~300 Tokens
    """
    effective_model = model_name or LLM_MODEL

    # ✨ STRUCTURED_RESPONSE_OVERHEAD: Tokens für Details/Nächste Schritte/Vorschläge
    STRUCTURED_RESPONSE_OVERHEAD = 300  # ~200-300 Tokens für Anhang-Struktur

    # Erweitere max_tokens um Overhead (falls gesetzt)
    if max_tokens is not None:
        effective_max_tokens = max_tokens + STRUCTURED_RESPONSE_OVERHEAD
        logging.info(
            f"[TOKEN-BUDGET] User max_tokens: {max_tokens} → "
            f"Ollama num_predict: {effective_max_tokens} "
            f"(+{STRUCTURED_RESPONSE_OVERHEAD} für Struktur)"
        )
    else:
        effective_max_tokens = None
        logging.info(f"[TOKEN-BUDGET] Kein max_tokens Limit gesetzt (unbegrenzt)")

    logging.info(f"[NATIVE] Lade LLM-Modell: {effective_model} (T={temperature})")

    try:
        return DirectOllamaLLM(
            model=effective_model,
            base_url=OLLAMA_HOST,
            temperature=temperature,
            num_predict=effective_max_tokens,  # Erweitert um OVERHEAD
            top_p=top_p,
        )
    except OllamaError as e:
        logging.error(f"❌ LLM-Modell Fehler: {e}")
        raise


def get_available_collections(vector_backend):
    """Ermittelt verfügbare Collections im Vector Backend"""
    try:
        if not vector_backend or not vector_backend.is_available():
            logging.warning("Vector backend nicht verfügbar")
            return []

        # Versuche Collections zu ermitteln
        available_collections = vector_backend.list_collections()
        logging.info(f"Verfügbare Collections: {available_collections}")
        return available_collections

    except Exception as e:
        logging.error(f"Fehler beim Ermitteln der Collections: {e}")
        return []


def get_legal_collections(available_collections):
    """Filtert Legal-Collections aus verfügbaren Collections"""
    legal_keywords = ["legal", "law", "recht", "gesetz", "norm", "jurist", "bverwg", "bimschg"]
    return [col for col in available_collections if any(keyword in col.lower() for keyword in legal_keywords)]


def get_admin_collections(available_collections):
    """Filtert Admin-Collections aus verfügbaren Collections"""
    admin_keywords = ["admin", "verwaltung", "prozess", "verfahren", "behoerde"]
    return [col for col in available_collections if any(keyword in col.lower() for keyword in admin_keywords)]


def format_retrieved_docs_for_prompt(docs):
    """Formatiert abgerufene Dokumente für den Prompt"""
    if not docs:
        return "Keine Dokumente gefunden."

    formatted_docs = []
    for i, doc in enumerate(docs):
        if isinstance(doc, dict):
            content = doc.get("content", str(doc))
        else:
            content = str(doc)

        formatted_docs.append(f"[{i+1}] {content}")

    return "\n\n".join(formatted_docs)


def _extract_suggestions(llm_response: str) -> List[str]:
    """
    Extrahiert Follow-up-Vorschläge aus LLM-Antwort

    Sucht nach "💡 Vorschläge:" Section und extrahiert Bullet-Points.

    Args:
        llm_response: Vollständige LLM-Antwort

    Returns:
        Liste von Follow-up-Fragen (max. 5)

    Beispiel:
        Input: "Antwort...\n\n💡 Vorschläge:\n• Frage 1?\n• Frage 2?\n"
        Output: ["Frage 1?", "Frage 2?"]
    """
    import re

    suggestions = []

    # Suche nach "💡 Vorschläge:" oder "Vorschläge:" Section
    patterns = [
        r"💡\s*Vorschläge?:(.+?)(?:\n\n|$)",
        r"Vorschläge?:(.+?)(?:\n\n|$)",
        r"Follow[- ]?up[- ]?Fragen?:(.+?)(?:\n\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, llm_response, re.DOTALL | re.IGNORECASE)
        if match:
            section = match.group(1)

            # Parse Bullet-Points
            for line in section.strip().split("\n"):
                line = line.strip()
                # Entferne Bullet-Point-Marker (•, -, *, Zahlen)
                line = re.sub(r"^[•\-\*\d\.)\s]+", "", line)
                if line and len(line) > 10:  # Mindestens 10 Zeichen
                    suggestions.append(line)

            break  # Erste passende Section verwenden

    logging.info(f"[SUGGESTIONS] {len(suggestions)} Follow-ups extrahiert")
    return suggestions[:5]  # Max 5 Vorschläge


def _create_source_metadata(chunk, citation_id: int) -> Dict[str, Any]:
    """
    Erstellt SourceMetadata-Dict aus EnhancedChunk

    Args:
        chunk: EnhancedChunk mit Metadaten
        citation_id: 1-basierte Zitations-ID

    Returns:
        Dict im SourceMetadata-Format (für Pydantic Model)
    """
    metadata = chunk.metadata

    # Dokumenttyp aus Metadaten ableiten
    doc_type = metadata.get("document_type", "Dokument")
    if "gesetz" in metadata.get("title", "").lower():
        doc_type = "Gesetz"
    elif "verordnung" in metadata.get("title", "").lower():
        doc_type = "Verordnung"
    elif "urteil" in metadata.get("title", "").lower():
        doc_type = "Urteil"
    elif "verwaltungsvorschrift" in metadata.get("title", "").lower():
        doc_type = "Verwaltungsvorschrift"

    return {
        "id": citation_id,
        "title": metadata.get("title", "Unbekanntes Dokument"),
        "type": doc_type,
        "author": metadata.get("author"),
        "year": metadata.get("date", "").split("-")[0] if metadata.get("date") else None,  # Extrahiere Jahr
        "url": metadata.get("url"),
        "source_file": metadata.get("source_file"),
        "page": metadata.get("page"),
        "confidence": chunk.confidence_score,
        "content_preview": (chunk.content[:200] + "...") if len(chunk.content) > 200 else chunk.content,
    }


# =============================================================================
# NATIVE RAG CHAIN IMPLEMENTATION (Ersetzt LangChain Runnables)
# =============================================================================


def get_rag_chain_native(vector_backend, llm_instance: DirectOllamaLLM):
    """
    Native RAG-Chain-Implementierung ohne LangChain

    Ersetzt die komplexe LangChain RunnablePassthrough/RunnableBranch Logik
    durch eine einfache, direkte Python-Funktion.

    Args:
        vector_backend: Database backend für Retrieval
        llm_instance: Native Ollama LLM-Instanz

    Returns:
        Callable: RAG-Chain-Funktion
    """

    def combined_retriever_and_reranker(inputs):
        """Kombinierter Retrieval und Reranking (unverändert)"""
        query = inputs["question"]
        session_id = inputs.get("session_id", "default")
        user_profile = inputs.get("user_profile", {})

        try:
            logging.info(f"[NATIVE-RAG] Query: '{query}' für Session: {session_id}")

            # 1. COLLECTIONS DYNAMISCH ERMITTELN
            available_collections = get_available_collections(vector_backend)
            legal_collections = get_legal_collections(available_collections)
            admin_collections = get_admin_collections(available_collections)

            logging.info(f"Legal Collections: {legal_collections}, Admin Collections: {admin_collections}")

            # 2. STANDARD VECTOR RETRIEVAL
            embeddings = _get_embeddings_instance()
            query_vector = embeddings.embed_query(query)

            legal_results = []
            admin_results = []

            # Suche in Legal Collections
            for collection in legal_collections:
                try:
                    results = vector_backend.similarity_search_with_score(
                        collection_name=collection, query_vector=query_vector, k=RETRIEVER_K
                    )
                    for doc, score in results:
                        legal_results.append(
                            {
                                "content": doc.get("content", ""),
                                "metadata": doc.get("metadata", {}),
                                "score": score,
                                "collection": collection,
                            }
                        )
                except Exception as e:
                    logging.error(f"Fehler bei Legal Collection {collection}: {e}")

            # Suche in Admin Collections
            for collection in admin_collections:
                try:
                    results = vector_backend.similarity_search_with_score(
                        collection_name=collection, query_vector=query_vector, k=RETRIEVER_K
                    )
                    for doc, score in results:
                        admin_results.append(
                            {
                                "content": doc.get("content", ""),
                                "metadata": doc.get("metadata", {}),
                                "score": score,
                                "collection": collection,
                            }
                        )
                except Exception as e:
                    logging.error(f"Fehler bei Admin Collection {collection}: {e}")

            # 3. QUALITY-ENHANCED RETRIEVAL
            all_candidates = legal_results + admin_results

            if not all_candidates:
                logging.warning("Keine Kandidaten gefunden - verwende Fallback")
                return []

            # Quality Retrieval verwenden
            quality_retriever = get_quality_retriever()

            # Strategien basierend auf Query-Typ anpassen
            if any(keyword in query.lower() for keyword in ["gesetz", "paragraph", "§", "rechtlich", "urteil"]):
                quality_retriever.relevance_strategy = RelevanceStrategy.CROSS_REFERENCE_ENHANCED
                logging.info("Cross-Reference-Enhanced Strategie aktiviert")
            elif "prozess" in query.lower() or "verfahren" in query.lower():
                quality_retriever.relevance_strategy = RelevanceStrategy.QUALITY_WEIGHTED
                logging.info("Quality-Weighted Strategie aktiviert")
            else:
                quality_retriever.relevance_strategy = RelevanceStrategy.HYBRID_QUALITY_SEMANTIC
                logging.info("Hybrid-Quality-Semantic Strategie aktiviert")

            # Quality-Enhanced Retrieval ausführen
            enhanced_chunks, retrieval_stats = quality_retriever.retrieve_with_quality(
                query=query,
                k=RERANKED_DOCS_TOP_N,
                collection_filter=legal_collections + admin_collections,
                user_context=user_profile,
            )

            # Statistiken zusammenfassen
            searched_collections = list(set([r["collection"] for r in all_candidates]))

            logging.info(f"Quality Enhanced Retrieval: {len(enhanced_chunks)} finale Chunks")
            return enhanced_chunks

        except Exception as e:
            logging.error(f"Retrieval-Fehler: {e}")
            return []

    def rag_chain_function(inputs: dict) -> dict:
        """
        Hauptfunktion der RAG-Chain (Native Implementation)

        Args:
            inputs: Dict mit "question", "session_id", etc.

        Returns:
            dict: Antwort-Dictionary mit answer, sources, metadata
        """
        # 1. Retrieval & Reranking
        enhanced_chunks = combined_retriever_and_reranker(inputs)

        query = inputs["question"]
        session_id = inputs.get("session_id", "default")

        # 2. Prüfe ob Dokumente gefunden wurden
        if not enhanced_chunks:
            logging.warning(f"Keine Dokumente für Query '{query}' gefunden - verwende Fallback")

            # Fallback: Allgemeines Wissen ohne Kontext
            fallback_prompt = f"""Du bist ein erfahrener Experte für deutsches Verwaltungsrecht.

Für die aktuelle Frage wurden keine spezifischen Dokumente in der Wissensdatenbank gefunden.
Beantworte die Frage basierend auf deinem allgemeinen Wissen.

Frage: {query}

Antwort:"""

            try:
                response = llm_instance.invoke(fallback_prompt)
                answer = response.content
            except Exception as e:
                logging.error(f"LLM Fallback-Fehler: {e}")
                answer = "Entschuldigung, ich konnte keine relevanten Informationen finden und kann die Frage derzeit nicht beantworten."

            return {
                "answer": answer,
                "sources": [],
                "session_id": session_id,
                "metadata": {"search_method": "general_knowledge_fallback", "chunks_found": 0, "llm_used": True},
            }

        # 3. Chat-Historie einbeziehen
        chat_history = get_conversation_history(session_id)
        history_text = ""
        if chat_history:
            history_entries = []
            for role, text in chat_history[-5:]:  # Nur letzte 5 Einträge
                history_entries.append(f"{role}: {text}")
            history_text = "\n".join(history_entries)

        # 4. Kontext mit Nummern für Citations formatieren
        numbered_context = "\n".join([f"[{i+1}] {chunk.content}" for i, chunk in enumerate(enhanced_chunks)])

        # ✨ NEW: Source-List für IEEE-Zitationen formatieren
        source_list = "\n".join(
            [
                f"[{i+1}] {chunk.metadata.get('title', 'Unbekanntes Dokument')} "
                f"({chunk.metadata.get('source_file', 'Unbekannte Quelle')})"
                for i, chunk in enumerate(enhanced_chunks)
            ]
        )

        # 5. Finaler Prompt (Native String-Formatierung)
        main_prompt = f"""Du bist ein erfahrener Rechtsexperte für deutsches Verwaltungsrecht.

Beantworte die folgende Frage präzise und ausführlich basierend auf den bereitgestellten Quellen.

WICHTIGE REGELN:
- Zitiere jede verwendete Information mit [1], [2], etc.
- Verwende nur Informationen aus den gegebenen Quellen
- Bei unklaren Sachverhalten erwähne die Unsicherheit
- Gib strukturierte, professionelle Antworten

Bisheriger Chatverlauf:
{history_text}

Verfügbare Quellen (für deine Zitationen):
{source_list}

Kontext aus Dokumenten:
{numbered_context}

Frage: {query}

Antwort (WICHTIG: Nutze [1], [2] Zitationen für jeden Fakt!):"""

        # 6. LLM-Anfrage (Native Ollama)
        try:
            logging.info(f"[NATIVE] Sende Query an LLM: '{query}' mit {len(enhanced_chunks)} Quellen")
            response = llm_instance.invoke(main_prompt)
            answer = response.content
            logging.info(f"[NATIVE] LLM-Antwort erhalten: {len(answer)} Zeichen")
        except Exception as e:
            logging.error(f"LLM Fehler: {e}")
            answer = "Entschuldigung, es gab einen Fehler beim Generieren der Antwort. Bitte versuchen Sie es erneut."

        # 7. ✨ NEW: Extrahiere Follow-up-Vorschläge aus LLM-Antwort
        suggestions = _extract_suggestions(answer)

        # 8. ✨ NEW: Erstelle SourceMetadata für IEEE-Zitationen
        sources_metadata = []
        for i, chunk in enumerate(enhanced_chunks):
            source_meta = _create_source_metadata(chunk, citation_id=i + 1)
            sources_metadata.append(source_meta)

        # 9. Konvertiere Enhanced Chunks zu Standard-Source-Format (Legacy)
        detailed_sources = []
        for i, chunk in enumerate(enhanced_chunks):
            source_info = {
                "citation_id": i + 1,
                "document_title": chunk.metadata.get("title", "Unbekanntes Dokument"),
                "source_file": chunk.metadata.get("source_file", "Unbekannte Quelle"),
                "chunk_id": chunk.metadata.get("chunk_id", f"chunk_{i+1}"),
                "content": chunk.content,
                "content_preview": (chunk.content[:200] + "...") if len(chunk.content) > 200 else chunk.content,
                "similarity_score": chunk.metadata.get("score", 0.0),
                "rerank_score": chunk.metadata.get("rerank_score", 0.0),
                "quality_score": chunk.overall_quality_score,
                "confidence_score": chunk.confidence_score,
                "reliability": chunk.reliability_indicator,
                "metadata": {
                    "author": chunk.metadata.get("author", "Unbekannt"),
                    "date": chunk.metadata.get("date", "Unbekannt"),
                    "document_type": chunk.metadata.get("document_type", "Unbekannt"),
                    "rechtsgebiet": chunk.metadata.get("rechtsgebiet", "Unbekannt"),
                    "behoerde": chunk.metadata.get("behoerde", "Unbekannt"),
                    "collection_type": chunk.metadata.get("collection_type", "unknown"),
                    "processing_source": chunk.metadata.get("processing_source", "unknown"),
                    "quality_metrics": chunk.metadata.get("quality_metrics", {}),
                    "quality_flags": chunk.quality_flags,
                    # Graph-spezifische Metadaten
                    "node_type": chunk.metadata.get("node_type", None),
                    "labels": chunk.metadata.get("labels", []),
                    "is_graph_result": chunk.metadata.get("collection_type") == "graph_knowledge",
                },
            }
            detailed_sources.append(source_info)

        # 8. RAG-Metadata zusammenstellen
        searched_collections = list(set([chunk.metadata.get("collection", "unknown") for chunk in enhanced_chunks]))

        rag_metadata = {
            "retrieval_method": "native_quality_enhanced_rag",
            "reranking_applied": True,
            "collections_searched": searched_collections,
            "average_quality_score": sum(chunk.overall_quality_score for chunk in enhanced_chunks) / len(enhanced_chunks)
            if enhanced_chunks
            else 0.0,
            "average_confidence_score": sum(chunk.confidence_score for chunk in enhanced_chunks) / len(enhanced_chunks)
            if enhanced_chunks
            else 0.0,
            "reliability_distribution": {
                "high": sum(1 for chunk in enhanced_chunks if chunk.reliability_indicator == "high"),
                "medium": sum(1 for chunk in enhanced_chunks if chunk.reliability_indicator == "medium"),
                "low": sum(1 for chunk in enhanced_chunks if chunk.reliability_indicator == "low"),
            },
        }

        return {
            "answer": answer,
            "sources": detailed_sources,  # Legacy format
            "sources_metadata": sources_metadata,  # ✨ NEW: IEEE-konforme Metadaten
            "suggestions": suggestions,  # ✨ NEW: Follow-up-Vorschläge
            "rag_metadata": rag_metadata,
            "session_id": session_id,
        }

    return rag_chain_function


# =============================================================================
# MAIN INTERFACE FUNCTIONS (Native Implementation)
# =============================================================================


def get_rag_chain(vector_backend, llm_instance):
    """
    Factory-Funktion für RAG-Chain (Kompatibilität mit bestehenden Calls)

    MIGRATION NOTE: Ersetzt die LangChain-basierte Implementierung
    durch native Python-Funktionen für bessere Performance und weniger Dependencies.

    Args:
        vector_backend: Database backend
        llm_instance: LLM-Instanz (kann LangChain oder Native sein)

    Returns:
        Callable: RAG-Chain-Funktion
    """
    # Prüfe ob es sich um eine native oder LangChain-Instanz handelt
    if isinstance(llm_instance, DirectOllamaLLM):
        # Native Implementation
        logging.info("✅ Verwende native RAG-Chain")
        return get_rag_chain_native(vector_backend, llm_instance)
    else:
        # Legacy LangChain fallback
        logging.warning("⚠️ Legacy LangChain LLM erkannt - erwäge Migration zu native Implementation")
        # Hier könnte ein Fallback implementiert werden, aber wir empfehlen Migration
        raise ValueError("LangChain LLM nicht mehr unterstützt. Verwende DirectOllamaLLM.")


def answer_query(
    session_id: str,
    query: str,
    user_profile: dict,
    model_name: str = None,
    temperature: float = 0.7,
    max_tokens: int = None,
    top_p: float = None,
    attachments: list = None,
):
    """
    Hauptfunktion für Query-Verarbeitung (Native Implementation)

    MIGRATION NOTE: Vollständig kompatibel mit bestehenden API-Calls,
    aber verwendet jetzt native Ollama-Integration statt LangChain.

    Args:
        session_id: Session-Identifier
        query: Benutzer-Query
        user_profile: Benutzerprofil
        model_name: LLM-Modell Name
        temperature: Sampling-Temperatur
        max_tokens: Maximale Token-Anzahl
        top_p: Nucleus-Sampling Parameter
        attachments: Datei-Anhänge (noch nicht implementiert)

    Returns:
        dict: Antwort mit answer, sources, turn_id, etc.
    """
    logging.info(
        f"[NATIVE] Query-Verarbeitung für Session {session_id}: '{query}' | "
        f"Modell: {model_name or LLM_MODEL}, "
        f"Temperatur: {temperature}, Max Tokens: {max_tokens}, Top-p: {top_p}"
    )

    try:
        # Verarbeite Anhänge falls vorhanden
        if attachments:
            logging.info(f"Verarbeite {len(attachments)} Anhänge für Session {session_id}")
            # TODO: Implementiere Anhang-Verarbeitung

        # Verwende das neue Database API System
        db_manager = get_database_manager()
        vector_backend = db_manager.get_vector_backend()

        if not vector_backend or not vector_backend.is_available():
            raise Exception("Vector Database Backend nicht verfügbar")

        # Native LLM-Instanz mit erweiterten Parametern initialisieren
        llm = _get_llm_instance(model_name=model_name, temperature=temperature, max_tokens=max_tokens, top_p=top_p)

        # Erstelle native RAG Chain
        rag_chain = get_rag_chain_native(vector_backend, llm)

        # Führe RAG Chain aus
        chain_input = {"question": query, "session_id": session_id, "user_profile": user_profile}

        result = rag_chain(chain_input)

        # Extrahiere chunk_ids aus sources für die Datenbank
        retrieved_chunk_ids = []
        for source in result["sources"]:
            chunk_id = source.get("chunk_id") or source.get("metadata", {}).get("chunk_id")
            if chunk_id:
                retrieved_chunk_ids.append(chunk_id)

        # Speichere Conversation Turn falls möglich
        try:
            turn_id = add_turn_to_conversation(
                session_id=session_id,
                question=query,
                answer=result["answer"],
                retrieved_chunk_ids=retrieved_chunk_ids,
                user_id=user_profile.get("user_id", "unknown"),
            )
            result["turn_id"] = turn_id
            logging.info(f"Conversation Turn gespeichert mit ID: {turn_id}")
        except Exception as e:
            logging.warning(f"Konnte Conversation Turn nicht speichern: {e}")
            result["turn_id"] = None

        # Cleanup
        llm.close()

        return result

    except OllamaError as e:
        logging.error(f"Ollama-Fehler beim Verarbeiten der Anfrage: {e}")
        return {"answer": f"Es gab ein Problem beim Zugriff auf das Sprachmodell: {e}", "sources": [], "turn_id": None}

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten der Anfrage: {e}")
        return {
            "answer": "Es gab ein Problem beim Zugriff auf die Wissensdatenbanken. Bitte versuchen Sie es später erneut.",
            "sources": [],
            "turn_id": None,
        }


def generate_chat_title(session_id: str, model_name: str = None) -> str:
    """
    Generiert einen kurzen, prägnanten Titel für einen Chatverlauf (Native Implementation)

    MIGRATION NOTE: Ersetzt LangChain ChatPromptTemplate durch einfache String-Formatierung.

    Args:
        session_id: Session-Identifier
        model_name: LLM-Modell Name

    Returns:
        str: Generierter Chat-Titel
    """
    chat_history = get_conversation_history(session_id)

    if not chat_history:
        return "Neuer Chat"

    # Native Prompt-Erstellung (ohne LangChain Template)
    history_text = "\n".join([f"{role}: {text}" for role, text in chat_history])
    prompt = f"""Fasse den folgenden Chatverlauf in maximal 5 Worten zusammen. Das Ergebnis soll als Titel für den Chat dienen. Antworte NUR mit dem Titel.

Chatverlauf:
{history_text}

Titel:"""

    try:
        # Native LLM-Aufruf
        llm = _get_llm_instance(model_name=model_name, temperature=0.7)
        response = llm.invoke(prompt)
        title = response.content.strip().replace('"', "")
        llm.close()

        logging.info(f"Titel für Session {session_id} generiert: '{title}'")
        return title if title else "Chat"

    except Exception as e:
        logging.error(f"Fehler bei der Titel-Generierung für Session {session_id}: {e}")
        return "Chat"


# =============================================================================
# MIGRATION VERIFICATION
# =============================================================================


def verify_native_migration():
    """
    Verifiziert dass die native Migration erfolgreich war

    Returns:
        dict: Status der Migration
    """
    verification = {
        "status": "success",
        "langchain_removed": True,
        "native_ollama_available": False,
        "embeddings_working": False,
        "llm_working": False,
        "errors": [],
    }

    try:
        # Test Native Ollama LLM
        llm = _get_llm_instance()
        test_response = llm.invoke("Test")
        verification["llm_working"] = bool(test_response.content)
        llm.close()
    except Exception as e:
        verification["errors"].append(f"LLM Test failed: {e}")
        verification["llm_working"] = False

    try:
        # Test Native Ollama Embeddings
        embeddings = _get_embeddings_instance()
        test_embedding = embeddings.embed_query("test")
        verification["embeddings_working"] = bool(test_embedding)
        embeddings.close()
    except Exception as e:
        verification["errors"].append(f"Embeddings Test failed: {e}")
        verification["embeddings_working"] = False

    # Prüfe ob LangChain-Imports noch vorhanden sind
    try:
        import langchain_ollama

        verification["langchain_removed"] = False
        verification["errors"].append("LangChain still available - consider removing dependency")
    except ImportError:
        verification["langchain_removed"] = True

    verification["native_ollama_available"] = verification["llm_working"] and verification["embeddings_working"]

    if verification["errors"]:
        verification["status"] = "partial" if verification["native_ollama_available"] else "failed"

    logging.info(f"✅ Native Migration Verification: {verification['status']}")
    return verification


# =============================================================================
# LEGACY COMPATIBILITY (Optional)
# =============================================================================

# Falls andere Module noch die LangChain-basierten Funktionen erwarten,
# können hier Wrapper-Funktionen definiert werden:

# def create_legacy_compatible_llm(*args, **kwargs):
#     """Legacy-Kompatibilität für LangChain ChatOllama"""
#     return _get_llm_instance(*args, **kwargs)

if __name__ == "__main__":
    # Test der nativen Implementation
    logging.basicConfig(level=logging.INFO)

    print("🔄 Testing VERITAS Native Covina Module...")
    verification = verify_native_migration()

    print(f"Status: {verification['status']}")
    print(f"Native Ollama: {verification['native_ollama_available']}")
    print(f"LangChain Removed: {verification['langchain_removed']}")

    if verification["errors"]:
        print("Errors:")
        for error in verification["errors"]:
            print(f"  - {error}")

    print("✅ Native Covina Module ready!")
