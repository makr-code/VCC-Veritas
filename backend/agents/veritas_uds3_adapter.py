"""
UDS3 Vector Search Adapter
Provides vector_search() interface for UDS3 Database API compatibility
"""
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Standardized vector search result"""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class UDS3VectorSearchAdapter:
    """
    Adapter zwischen HybridRetriever und UDS3 Database API.
    
    Problem:
    --------
    - HybridRetriever erwartet: dense_retriever.vector_search(query, top_k)
    - UDS3 bietet: query_across_databases(vector_params={...}, ...)
    
    Lösung:
    -------
    - Adapter implementiert vector_search() Methode
    - Intern mapping zu query_across_databases()
    - Result-Transformation: PolyglotQueryResult → List[Dict]
    
    Usage:
    ------
    ```python
    from uds3.uds3_core import get_optimized_unified_strategy
    from backend.agents.veritas_uds3_adapter import UDS3VectorSearchAdapter
    
    uds3 = get_optimized_unified_strategy()
    adapter = UDS3VectorSearchAdapter(uds3)
    
    # Jetzt kompatibel mit HybridRetriever
    results = await adapter.vector_search("BGB Vertragsrecht", top_k=5)
    ```
    """
    
    def __init__(self, uds3_strategy: Any):
        """
        Initialisiert UDS3 Adapter.
        
        Args:
            uds3_strategy: UDS3 UnifiedDatabaseStrategy Instance
            
        Raises:
            RuntimeError: Wenn uds3_strategy None ist
        """
        if uds3_strategy is None:
            raise RuntimeError(
                "❌ UDS3 Strategy ist None! "
                "UDS3 muss verfügbar sein für den VectorSearchAdapter. "
                "Bitte UDS3 korrekt initialisieren."
            )
        
        self.uds3 = uds3_strategy
        self._stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'empty_results': 0,
            'total_latency_ms': 0.0
        }
        
        logger.info("✅ UDS3VectorSearchAdapter initialisiert")
        logger.info("ℹ️ Hinweis: UDS3 benötigt konfigurierte Datenbanken (Vector/Graph/Relational) für Ergebnisse")
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Vector Search via UDS3 query_across_databases.
        
        Args:
            query: Suchanfrage
            top_k: Anzahl Top-Ergebnisse
            threshold: Mindest-Score (0.0 = keine Filterung)
            **kwargs: Zusätzliche Parameter (werden ignoriert)
            
        Returns:
            Liste von Dokumenten mit 'doc_id', 'content', 'score', 'metadata'
        """
        import time
        start_time = time.time()
        
        self._stats['total_queries'] += 1
        
        try:
            # Call UDS3 query_across_databases
            result = self.uds3.query_across_databases(
                vector_params={
                    "query_text": query,
                    "top_k": top_k,
                    "threshold": threshold
                },
                graph_params=None,
                relational_params=None,
                join_strategy="union",
                execution_mode="smart"
            )
            
            # Transform PolyglotQueryResult → List[Dict]
            documents = self._transform_results(result)
            
            # Update stats
            latency_ms = (time.time() - start_time) * 1000
            self._stats['total_latency_ms'] += latency_ms
            
            if documents:
                self._stats['successful_queries'] += 1
                logger.debug(
                    f"✅ Vector Search: {len(documents)} docs, "
                    f"{latency_ms:.1f}ms, query: {query[:50]}"
                )
            else:
                self._stats['empty_results'] += 1
                logger.debug(
                    f"ℹ️ Vector Search: 0 results, {latency_ms:.1f}ms, query: {query[:50]}"
                )
            
            return documents
            
        except Exception as e:
            self._stats['failed_queries'] += 1
            
            # Unterscheide zwischen Config-Problemen und echten Fehlern
            error_str = str(e)
            if "No database queries configured" in error_str or "connection" in error_str.lower():
                logger.debug(f"ℹ️ UDS3 Vector Search: DB-Konfiguration/Verbindung erforderlich ({error_str})")
            else:
                logger.error(f"❌ Vector Search Error: {e}", exc_info=True)
            
            # Return empty list on error (graceful degradation)
            return []
    
    def _transform_results(self, polyglot_result: Any) -> List[Dict[str, Any]]:
        """
        Transformiert PolyglotQueryResult → List[Dict].
        
        Args:
            polyglot_result: UDS3 PolyglotQueryResult
            
        Returns:
            Liste von Dokumenten
        """
        documents = []
        
        try:
            # Check if successful
            if not polyglot_result or not hasattr(polyglot_result, 'success'):
                logger.debug("ℹ️ Invalid PolyglotQueryResult (möglicherweise keine DB konfiguriert)")
                return documents
            
            if not polyglot_result.success:
                error_msg = getattr(polyglot_result, 'error', 'Unknown error')
                # Nur bei echten Fehlern warnen, nicht bei fehlender DB-Config
                if "No database queries configured" in str(error_msg):
                    logger.debug(f"ℹ️ UDS3 Query: {error_msg} (DB-Konfiguration erforderlich)")
                else:
                    logger.warning(f"⚠️ UDS3 Query failed: {error_msg}")
                return documents
            
            # Extract joined results
            if hasattr(polyglot_result, 'joined_results') and polyglot_result.joined_results:
                documents = self._parse_joined_results(polyglot_result.joined_results)
            
            # Fallback: Extract from database_results
            elif hasattr(polyglot_result, 'database_results') and polyglot_result.database_results:
                documents = self._parse_database_results(polyglot_result.database_results)
            
            logger.debug(f"📄 Transformed {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"❌ Result transformation error: {e}", exc_info=True)
        
        return documents
    
    def _parse_joined_results(self, joined_results: List[Any]) -> List[Dict[str, Any]]:
        """Parse joined_results to standard format"""
        documents = []
        
        for item in joined_results:
            try:
                doc = {
                    'doc_id': self._extract_field(item, ['doc_id', 'id', 'document_id']),
                    'content': self._extract_field(item, ['content', 'text', 'document']),
                    'score': self._extract_field(item, ['score', 'relevance', 'similarity'], default=0.0),
                    'metadata': self._extract_field(item, ['metadata', 'meta'], default={})
                }
                
                # Only add if we have at least doc_id and content
                if doc['doc_id'] and doc['content']:
                    documents.append(doc)
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse joined result: {e}")
                continue
        
        return documents
    
    def _parse_database_results(self, database_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse database_results (fallback)"""
        documents = []
        
        try:
            # Try vector results first
            if 'vector' in database_results:
                vector_result = database_results['vector']
                
                if hasattr(vector_result, 'documents'):
                    for doc in vector_result.documents:
                        documents.append({
                            'doc_id': getattr(doc, 'doc_id', getattr(doc, 'id', 'unknown')),
                            'content': getattr(doc, 'content', getattr(doc, 'text', '')),
                            'score': getattr(doc, 'score', getattr(doc, 'similarity', 0.0)),
                            'metadata': getattr(doc, 'metadata', {})
                        })
            
            # Try relational results as fallback
            if not documents and 'relational' in database_results:
                relational_result = database_results['relational']
                
                if hasattr(relational_result, 'records'):
                    for record in relational_result.records:
                        documents.append({
                            'doc_id': record.get('doc_id', record.get('id', 'unknown')),
                            'content': record.get('content', record.get('text', '')),
                            'score': record.get('score', 0.5),  # Default score
                            'metadata': record.get('metadata', {})
                        })
                        
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse database_results: {e}")
        
        return documents
    
    def _extract_field(
        self,
        obj: Any,
        field_names: List[str],
        default: Any = None
    ) -> Any:
        """Extract field from object, trying multiple field names"""
        
        # Try as dict
        if isinstance(obj, dict):
            for name in field_names:
                if name in obj:
                    return obj[name]
        
        # Try as object
        else:
            for name in field_names:
                if hasattr(obj, name):
                    value = getattr(obj, name)
                    if value is not None:
                        return value
        
        return default
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        total = self._stats['total_queries']
        avg_latency = (
            self._stats['total_latency_ms'] / total
            if total > 0 else 0.0
        )
        
        return {
            **self._stats,
            'avg_latency_ms': avg_latency,
            'success_rate': (
                self._stats['successful_queries'] / total
                if total > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'empty_results': 0,
            'total_latency_ms': 0.0
        }


# Convenience function
def get_uds3_adapter(uds3_strategy: Any = None) -> UDS3VectorSearchAdapter:
    """
    Get UDS3 Vector Search Adapter.
    
    Args:
        uds3_strategy: UDS3 Strategy (if None, creates new one)
        
    Returns:
        UDS3VectorSearchAdapter instance
    """
    if uds3_strategy is None:
        try:
            from uds3.uds3_core import get_optimized_unified_strategy
            uds3_strategy = get_optimized_unified_strategy()
        except ImportError:
            logger.error("❌ UDS3 nicht verfügbar")
            raise RuntimeError("UDS3 ist erforderlich für Vector Search Adapter")
    
    return UDS3VectorSearchAdapter(uds3_strategy)


# Example Usage
if __name__ == "__main__":
    import asyncio
    
    async def test_adapter():
        """Test UDS3 Adapter"""
        print("=" * 80)
        print("UDS3 VECTOR SEARCH ADAPTER TEST")
        print("=" * 80)
        print()
        
        # Initialize
        from uds3.uds3_core import get_optimized_unified_strategy
        
        print("🔄 Initialisiere UDS3...")
        uds3 = get_optimized_unified_strategy()
        
        print("🔄 Erstelle Adapter...")
        adapter = get_uds3_adapter(uds3)
        print()
        
        # Test query
        test_query = "BGB Vertragsrecht Minderjährige"
        print(f"Query: \"{test_query}\"")
        print()
        
        results = await adapter.vector_search(test_query, top_k=3)
        
        print(f"📄 Results: {len(results)}")
        
        if results:
            print()
            print("Top Results:")
            for i, doc in enumerate(results, 1):
                print(f"   {i}. {doc['doc_id']} (Score: {doc['score']:.3f})")
                print(f"      {doc['content'][:100]}...")
        else:
            print("⚠️ Keine Results (Vector DB möglicherweise leer)")
        
        print()
        print("📊 Stats:")
        stats = adapter.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print()
        print("=" * 80)
        print("✅ Adapter Test abgeschlossen")
        print("=" * 80)
    
    asyncio.run(test_adapter())


class MockDenseRetriever:
    """
    Mock Dense Retriever für Testing/Development ohne UDS3.
    
    Gibt leere Resultate zurück mit Warnung.
    Kompatibel mit HybridRetriever Interface.
    """
    
    def __init__(self):
        logger.warning("⚠️ MockDenseRetriever aktiv - keine echte Vector Search")
        self._call_count = 0
    
    async def vector_search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.0,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Mock vector_search - gibt leere Liste zurück.
        
        Args:
            query: Suchanfrage
            top_k: Anzahl Ergebnisse
            threshold: Score-Threshold
            **kwargs: Zusätzliche Parameter
            
        Returns:
            Leere Liste (Mock hat keine Daten)
        """
        self._call_count += 1
        
        if self._call_count == 1:
            logger.warning(
                f"⚠️ MockDenseRetriever.vector_search() aufgerufen mit query='{query[:50]}...' "
                f"- gibt leere Ergebnisse zurück (UDS3 nicht verfügbar)"
            )
        
        # Leere Liste zurückgeben
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Mock-Statistiken zurück."""
        return {
            'type': 'MockDenseRetriever',
            'total_calls': self._call_count,
            'uds3_available': False,
            'warning': 'No real vector search - UDS3 not initialized'
        }

