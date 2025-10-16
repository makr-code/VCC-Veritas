#!/usr/bin/env python3
"""
UDS3 REMOTE DATABASE SETUP & DIAGNOSTICS
=========================================

Prüft und konfiguriert Verbindung zu Remote-Datenbanken für UDS3.

Datenbanken:
- PostgreSQL (Relational DB) - Remote
- Neo4j (Graph DB) - Remote  
- ChromaDB (Vector DB) - Kann remote oder lokal sein

Author: VERITAS System
Date: 2025-10-06
Version: 1.0
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

# Projekt-Root zum sys.path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_postgresql_connection() -> Dict[str, Any]:
    """
    Testet PostgreSQL-Verbindung (Remote).
    
    Returns:
        Dict mit Status und Details
    """
    logger.info("🔍 Teste PostgreSQL-Verbindung...")
    
    try:
        import psycopg2
        
        # Connection-Parameter aus Environment oder Config
        pg_config = {
            'host': os.getenv('POSTGRES_HOST', os.getenv('COVINA_POSTGRES_HOST', 'localhost')),
            'port': int(os.getenv('POSTGRES_PORT', os.getenv('COVINA_POSTGRES_PORT', '5432'))),
            'database': os.getenv('POSTGRES_DB', os.getenv('COVINA_POSTGRES_DB', 'veritas')),
            'user': os.getenv('POSTGRES_USER', os.getenv('COVINA_POSTGRES_USER', 'postgres')),
            'password': os.getenv('POSTGRES_PASSWORD', os.getenv('COVINA_POSTGRES_PASSWORD', ''))
        }
        
        logger.info(f"  Host: {pg_config['host']}:{pg_config['port']}")
        logger.info(f"  Database: {pg_config['database']}")
        logger.info(f"  User: {pg_config['user']}")
        
        # Verbindungstest
        conn = psycopg2.connect(**pg_config, connect_timeout=5)
        cursor = conn.cursor()
        
        # Version abfragen
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        # Tabellen zählen
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL: Verbindung erfolgreich")
        return {
            'status': 'success',
            'host': pg_config['host'],
            'port': pg_config['port'],
            'database': pg_config['database'],
            'version': version.split(',')[0],  # Nur erste Zeile
            'table_count': table_count,
            'available': True
        }
        
    except ImportError:
        logger.error("❌ PostgreSQL: psycopg2 nicht installiert")
        return {
            'status': 'missing_driver',
            'error': 'psycopg2 nicht installiert',
            'available': False
        }
    except Exception as e:
        logger.error(f"❌ PostgreSQL: Verbindung fehlgeschlagen - {e}")
        return {
            'status': 'connection_failed',
            'error': str(e),
            'config': pg_config,
            'available': False
        }


async def test_neo4j_connection() -> Dict[str, Any]:
    """
    Testet Neo4j-Verbindung (Remote).
    
    Returns:
        Dict mit Status und Details
    """
    logger.info("🔍 Teste Neo4j-Verbindung...")
    
    try:
        from neo4j import GraphDatabase
        
        # Connection-Parameter
        neo4j_uri = os.getenv('NEO4J_URI', os.getenv('COVINA_NEO4J_URI', 'bolt://localhost:7687'))
        neo4j_user = os.getenv('NEO4J_USER', os.getenv('COVINA_NEO4J_USER', 'neo4j'))
        neo4j_password = os.getenv('NEO4J_PASSWORD', os.getenv('COVINA_NEO4J_PASSWORD', 'v3f3b1d7'))
        
        logger.info(f"  URI: {neo4j_uri}")
        logger.info(f"  User: {neo4j_user}")
        
        # Verbindungstest
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Version abfragen
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] as version")
            record = result.single()
            version = record['version'] if record else 'Unknown'
            
            # Node-Count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            
            # Relationship-Count
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
        
        driver.close()
        
        logger.info("✅ Neo4j: Verbindung erfolgreich")
        return {
            'status': 'success',
            'uri': neo4j_uri,
            'version': version,
            'node_count': node_count,
            'relationship_count': rel_count,
            'available': True
        }
        
    except ImportError:
        logger.error("❌ Neo4j: neo4j-driver nicht installiert")
        return {
            'status': 'missing_driver',
            'error': 'neo4j nicht installiert',
            'available': False
        }
    except Exception as e:
        logger.error(f"❌ Neo4j: Verbindung fehlgeschlagen - {e}")
        return {
            'status': 'connection_failed',
            'error': str(e),
            'available': False
        }


async def test_chromadb_connection() -> Dict[str, Any]:
    """
    Testet ChromaDB-Verbindung (kann remote oder lokal sein).
    
    Returns:
        Dict mit Status und Details
    """
    logger.info("🔍 Teste ChromaDB-Verbindung...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Check ob remote oder lokal
        chroma_host = os.getenv('CHROMA_HOST', os.getenv('COVINA_CHROMA_HOST'))
        chroma_port = os.getenv('CHROMA_PORT', os.getenv('COVINA_CHROMA_PORT'))
        
        if chroma_host and chroma_port:
            # Remote ChromaDB
            logger.info(f"  Remote: {chroma_host}:{chroma_port}")
            client = chromadb.HttpClient(host=chroma_host, port=int(chroma_port))
        else:
            # Lokales ChromaDB
            persist_dir = os.getenv('CHROMA_PERSIST_DIR', 'config/sqlite_db/chroma_vector_db')
            logger.info(f"  Lokal: {persist_dir}")
            client = chromadb.PersistentClient(path=persist_dir)
        
        # Heartbeat-Test
        heartbeat = client.heartbeat()
        
        # Collections zählen
        collections = client.list_collections()
        
        logger.info("✅ ChromaDB: Verbindung erfolgreich")
        return {
            'status': 'success',
            'mode': 'remote' if chroma_host else 'local',
            'host': chroma_host if chroma_host else 'localhost',
            'port': chroma_port if chroma_port else 'N/A',
            'heartbeat': heartbeat,
            'collection_count': len(collections),
            'collections': [c.name for c in collections],
            'available': True
        }
        
    except ImportError:
        logger.warning("⚠️  ChromaDB: Modul nicht installiert (optional)")
        return {
            'status': 'missing_driver',
            'error': 'chromadb nicht installiert',
            'available': False,
            'optional': True
        }
    except Exception as e:
        logger.error(f"❌ ChromaDB: Verbindung fehlgeschlagen - {e}")
        return {
            'status': 'connection_failed',
            'error': str(e),
            'available': False
        }


async def diagnose_uds3_setup():
    """
    Führt vollständige UDS3-Diagnostik durch.
    
    Prüft:
    - PostgreSQL (Relational DB)
    - Neo4j (Graph DB)
    - ChromaDB (Vector DB)
    - Environment-Variablen
    """
    logger.info("=" * 80)
    logger.info("UDS3 REMOTE DATABASE DIAGNOSTICS")
    logger.info("=" * 80)
    
    # 1. Environment-Variablen prüfen
    logger.info("\n📋 Environment-Variablen:")
    env_vars = {
        'POSTGRES_HOST': os.getenv('POSTGRES_HOST', os.getenv('COVINA_POSTGRES_HOST', 'NOT SET')),
        'POSTGRES_PORT': os.getenv('POSTGRES_PORT', os.getenv('COVINA_POSTGRES_PORT', 'NOT SET')),
        'POSTGRES_DB': os.getenv('POSTGRES_DB', os.getenv('COVINA_POSTGRES_DB', 'NOT SET')),
        'NEO4J_URI': os.getenv('NEO4J_URI', os.getenv('COVINA_NEO4J_URI', 'NOT SET')),
        'CHROMA_HOST': os.getenv('CHROMA_HOST', os.getenv('COVINA_CHROMA_HOST', 'NOT SET')),
    }
    
    for key, value in env_vars.items():
        logger.info(f"  {key}: {value}")
    
    # 2. Datenbankverbindungen testen
    logger.info("\n🔍 Teste Datenbankverbindungen...\n")
    
    results = {
        'postgresql': await test_postgresql_connection(),
        'neo4j': await test_neo4j_connection(),
        'chromadb': await test_chromadb_connection()
    }
    
    # 3. Summary
    logger.info("\n" + "=" * 80)
    logger.info("DIAGNOSTICS SUMMARY")
    logger.info("=" * 80)
    
    all_available = True
    
    for db_name, result in results.items():
        status_icon = "✅" if result['available'] else ("⚠️" if result.get('optional') else "❌")
        logger.info(f"{status_icon} {db_name.upper()}: {result['status']}")
        
        if result['available']:
            if db_name == 'postgresql':
                logger.info(f"   Tables: {result['table_count']}")
            elif db_name == 'neo4j':
                logger.info(f"   Nodes: {result['node_count']}, Relationships: {result['relationship_count']}")
            elif db_name == 'chromadb':
                logger.info(f"   Collections: {result['collection_count']}")
        else:
            if not result.get('optional'):
                all_available = False
            logger.info(f"   Error: {result.get('error', 'Unknown')}")
    
    logger.info("=" * 80)
    
    if all_available:
        logger.info("✅ UDS3-SETUP COMPLETE - Alle Datenbanken verfügbar!")
        logger.info("📋 Next: Echte Pipeline-Evaluation durchführen")
    else:
        logger.warning("⚠️  UDS3-SETUP INCOMPLETE - Einige Datenbanken fehlen")
        logger.info("📋 Next: Fehlende Datenbanken konfigurieren")
    
    logger.info("=" * 80)
    
    return results


async def create_env_file():
    """
    Erstellt .env-Template mit DB-Konfiguration.
    """
    env_template = """# UDS3 Remote Database Configuration
# =====================================

# PostgreSQL (Relational DB)
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432
POSTGRES_DB=veritas
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password

# Neo4j (Graph DB)
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=v3f3b1d7

# ChromaDB (Vector DB) - Optional Remote
# CHROMA_HOST=your-chroma-host
# CHROMA_PORT=8000

# Oder lokal:
CHROMA_PERSIST_DIR=config/sqlite_db/chroma_vector_db
"""
    
    env_file = project_root / '.env.template'
    with open(env_file, 'w') as f:
        f.write(env_template)
    
    logger.info(f"✅ .env Template erstellt: {env_file}")
    logger.info("📋 Kopiere .env.template → .env und fülle deine DB-Credentials ein")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='UDS3 Remote Database Setup & Diagnostics')
    parser.add_argument(
        '--action',
        choices=['diagnose', 'create-env', 'both'],
        default='diagnose',
        help='Aktion durchführen'
    )
    
    args = parser.parse_args()
    
    if args.action in ['diagnose', 'both']:
        asyncio.run(diagnose_uds3_setup())
    
    if args.action in ['create-env', 'both']:
        asyncio.run(create_env_file())
