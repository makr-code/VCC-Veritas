"""
UDS3 Direct Database API Integration for VERITAS Agent Framework
================================================================

Direct access to UDS3 database backends without UnifiedDatabaseStrategy.
All databases run on remote servers (192.168.178.94).

Provides simple factory functions to get database clients:
- ChromaDB Remote API (Vector search)
- Neo4j Driver (Knowledge graph)
- PostgreSQL (Relational data)
- CouchDB (Document store)

Usage:
    from backend.database.uds3_direct import get_chromadb, get_neo4j, get_postgresql

    # Vector search
    chromadb = get_chromadb()
    results = chromadb.query_vectors(...)

    # Graph query
    neo4j = get_neo4j()
    results = neo4j.execute_cypher(...)

    # Relational query
    postgres = get_postgresql()
    results = postgres.execute_query(...)

Author: GitHub Copilot
Date: 24. Oktober 2025
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add UDS3 to path
uds3_path = Path(__file__).parent.parent.parent.parent / "uds3"
if str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

logger = logging.getLogger(__name__)

# Singleton instances
_chromadb_instance = None
_neo4j_instance = None
_postgresql_instance = None
_couchdb_instance = None


def get_chromadb(config: Optional[Dict[str, Any]] = None):
    """
    Get ChromaDB remote client instance.

    Args:
        config: Optional configuration. If None, uses environment variables.

    Returns:
        ChromaRemoteVectorBackend instance

    Example:
        chromadb = get_chromadb()
        results = chromadb.query_vectors(
            query_embeddings=[[0.1, 0.2, ...]],
            n_results=10
        )
    """
    global _chromadb_instance

    if _chromadb_instance is None:
        from uds3.database.database_api_chromadb_remote import ChromaRemoteVectorBackend

        if config is None:
            config = {
                "remote": {
                    "host": os.getenv("CHROMA_HOST", "192.168.178.94"),
                    "port": int(os.getenv("CHROMA_PORT", "8000")),
                    "protocol": "http",
                },
                "collection": os.getenv("CHROMA_COLLECTION", "veritas_documents"),
                "use_embeddings": True,
            }

        _chromadb_instance = ChromaRemoteVectorBackend(config)
        _chromadb_instance.connect()
        logger.info(f"✅ ChromaDB connected: {config['remote']['host']}:{config['remote']['port']}")

    return _chromadb_instance


def get_neo4j(config: Optional[Dict[str, Any]] = None):
    """
    Get Neo4j graph database client instance.

    Args:
        config: Optional configuration. If None, uses environment variables.

    Returns:
        Neo4jGraphBackend instance

    Example:
        neo4j = get_neo4j()
        results = neo4j.execute_cypher(
            "MATCH (d:Document) RETURN d.title LIMIT 10"
        )
    """
    global _neo4j_instance

    if _neo4j_instance is None:
        from uds3.database.database_api_neo4j import Neo4jGraphBackend

        if config is None:
            config = {
                "uri": os.getenv("NEO4J_URI", "bolt://192.168.178.94:7687"),
                "user": os.getenv("NEO4J_USER", "neo4j"),
                "password": os.getenv("NEO4J_PASSWORD", "neo4j"),
                "database": os.getenv("NEO4J_DATABASE", "neo4j"),
            }

        _neo4j_instance = Neo4jGraphBackend(config)
        _neo4j_instance.connect()
        logger.info(f"✅ Neo4j connected: {config['uri']}")

    return _neo4j_instance


def get_postgresql(config: Optional[Dict[str, Any]] = None):
    """
    Get PostgreSQL relational database client instance.

    Args:
        config: Optional configuration. If None, uses environment variables.

    Returns:
        PostgreSQLRelationalBackend instance

    Example:
        postgres = get_postgresql()
        results = postgres.execute_query(
            "SELECT * FROM documents WHERE domain = %s",
            ("environmental",)
        )
    """
    global _postgresql_instance

    if _postgresql_instance is None:
        from uds3.database.database_api_postgresql import PostgreSQLRelationalBackend

        if config is None:
            config = {
                "host": os.getenv("POSTGRES_HOST", "192.168.178.94"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "database": os.getenv("POSTGRES_DATABASE", "veritas"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
                "table": "documents",
            }

        _postgresql_instance = PostgreSQLRelationalBackend(config)
        _postgresql_instance.connect()
        logger.info(f"✅ PostgreSQL connected: {config['host']}:{config['port']}/{config['database']}")

    return _postgresql_instance


def get_couchdb(config: Optional[Dict[str, Any]] = None):
    """
    Get CouchDB document store client instance.

    Args:
        config: Optional configuration. If None, uses environment variables.

    Returns:
        CouchDBDocumentBackend instance

    Example:
        couchdb = get_couchdb()
        doc = couchdb.get_document(doc_id)
    """
    global _couchdb_instance

    if _couchdb_instance is None:
        from uds3.database.database_api_couchdb import CouchDBBackend

        if config is None:
            couchdb_port = os.getenv("COUCHDB_PORT", "32769")  # Default to custom port
            config = {
                "url": f"http://{os.getenv('COUCHDB_HOST', '192.168.178.94')}:{couchdb_port}",
                "database": os.getenv("COUCHDB_DATABASE", "veritas_documents"),
                "user": os.getenv("COUCHDB_USER", "admin"),
                "password": os.getenv("COUCHDB_PASSWORD", "admin"),
            }

        _couchdb_instance = CouchDBBackend(config)
        _couchdb_instance.connect()
        logger.info(f"✅ CouchDB connected: {config['url']}")

    return _couchdb_instance


def get_all_databases(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get all database clients at once.

    Args:
        config: Optional configuration dict with keys: chromadb, neo4j, postgresql, couchdb

    Returns:
        Dictionary with database clients:
            - vector: ChromaDB client
            - graph: Neo4j client
            - relational: PostgreSQL client
            - document: CouchDB client

    Example:
        dbs = get_all_databases()
        vector_results = dbs['vector'].query_vectors(...)
        graph_results = dbs['graph'].execute_cypher(...)
    """
    databases = {}

    # Try to connect to each database
    try:
        databases["vector"] = get_chromadb(config.get("chromadb") if config else None)
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        databases["vector"] = None

    try:
        databases["graph"] = get_neo4j(config.get("neo4j") if config else None)
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        databases["graph"] = None

    try:
        databases["relational"] = get_postgresql(config.get("postgresql") if config else None)
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        databases["relational"] = None

    try:
        databases["document"] = get_couchdb(config.get("couchdb") if config else None)
    except Exception as e:
        logger.error(f"❌ CouchDB connection failed: {e}")
        databases["document"] = None

    # Count connected databases
    connected = sum(1 for db in databases.values() if db is not None)
    logger.info(f"✅ Connected to {connected}/4 databases")

    return databases


def disconnect_all():
    """Disconnect from all databases."""
    global _chromadb_instance, _neo4j_instance, _postgresql_instance, _couchdb_instance

    if _chromadb_instance:
        try:
            _chromadb_instance.disconnect()
            logger.info("✅ ChromaDB disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting ChromaDB: {e}")
        _chromadb_instance = None

    if _neo4j_instance:
        try:
            _neo4j_instance.disconnect()
            logger.info("✅ Neo4j disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Neo4j: {e}")
        _neo4j_instance = None

    if _postgresql_instance:
        try:
            _postgresql_instance.disconnect()
            logger.info("✅ PostgreSQL disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting PostgreSQL: {e}")
        _postgresql_instance = None

    if _couchdb_instance:
        try:
            _couchdb_instance.disconnect()
            logger.info("✅ CouchDB disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting CouchDB: {e}")
        _couchdb_instance = None


# Convenience aliases
get_vector_db = get_chromadb
get_graph_db = get_neo4j
get_relational_db = get_postgresql
get_document_db = get_couchdb
