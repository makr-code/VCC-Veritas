#!/usr/bin/env python3
"""
PostgreSQL Setup & Schema Check

Prüft und erstellt die benötigten PostgreSQL Tabellen für VERITAS.

Run: python scripts/setup_postgres_schema.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root.parent / "uds3"))


def check_postgres_schema():
    """Prüfe PostgreSQL Schema"""
    print("\n" + "=" * 80)
    print("POSTGRESQL SCHEMA CHECK")
    print("=" * 80)

    try:
        from uds3.uds3_core import get_optimized_unified_strategy

        strategy = get_optimized_unified_strategy()
        backend = strategy.relational_backend

        print(f"\n📊 Connection Info:")
        print(f"   Host: {backend.host}")
        print(f"   Port: {backend.port}")
        print(f"   Database: {backend.database}")
        print(f"   Schema: {backend.schema}")

        # Check if create_tables_if_not_exist method exists
        print(f"\n🔧 Available Schema Methods:")
        if hasattr(backend, "create_tables_if_not_exist"):
            print(f"   ✅ create_tables_if_not_exist() available")
        else:
            print(f"   ❌ create_tables_if_not_exist() NOT available")

        # Try to create tables
        print(f"\n📝 Creating Tables...")
        if hasattr(backend, "create_tables_if_not_exist"):
            try:
                backend.create_tables_if_not_exist()
                print(f"   ✅ Tables created/verified")
            except Exception as e:
                print(f"   ⚠️ Error creating tables: {e}")

        # Check document count
        print(f"\n📄 Document Count Check:")
        try:
            count = backend.get_document_count()
            print(f"   ✅ Documents in PostgreSQL: {count}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
            print(f"   → Table 'documents' probably doesn't exist")

        # Get statistics
        print(f"\n📊 Database Statistics:")
        if hasattr(backend, "get_statistics"):
            try:
                stats = backend.get_statistics()
                print(f"   ✅ Statistics:")
                for key, value in stats.items():
                    print(f"      - {key}: {value}")
            except Exception as e:
                print(f"   ⚠️ Error: {e}")

        return backend

    except Exception as e:
        print(f"\n❌ PostgreSQL Schema Check failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def manual_sql_inspection():
    """Inspect PostgreSQL via direct SQL"""
    print("\n" + "=" * 80)
    print("MANUAL SQL INSPECTION")
    print("=" * 80)

    try:
        import psycopg2

        # Connection info (from UDS3 config)
        conn = psycopg2.connect(
            host="192.168.178.94", port=5432, user="postgres", password="postgres", database="vcc_relational_prod"
        )

        cursor = conn.cursor()

        # 1. List all schemas
        print("\n📊 Available Schemas:")
        cursor.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        """
        )
        schemas = cursor.fetchall()
        for schema in schemas:
            print(f"   - {schema[0]}")

        # 2. List all tables in public schema
        print("\n📊 Tables in 'public' schema:")
        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """
        )
        tables = cursor.fetchall()
        if tables:
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("   ⚠️ No tables found in 'public' schema")

        # 3. Check if documents table exists
        print("\n🔍 Check 'documents' table:")
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'documents'
            )
        """
        )
        exists = cursor.fetchone()[0]
        if exists:
            print("   ✅ 'documents' table exists")

            # Get column info
            cursor.execute(
                """
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'documents'
                ORDER BY ordinal_position
            """
            )
            columns = cursor.fetchall()
            print(f"\n   📋 Columns:")
            for col in columns:
                print(f"      - {col[0]} ({col[1]}{f'({col[2]})' if col[2] else ''})")
        else:
            print("   ❌ 'documents' table DOES NOT exist")
            print("   → Need to create schema")

        cursor.close()
        conn.close()

        print("\n✅ Manual SQL Inspection complete")

    except Exception as e:
        print(f"\n❌ Manual SQL Inspection failed: {e}")
        import traceback

        traceback.print_exc()


def create_documents_table():
    """Create documents table if it doesn't exist"""
    print("\n" + "=" * 80)
    print("CREATE DOCUMENTS TABLE")
    print("=" * 80)

    try:
        import psycopg2

        # Connection info
        conn = psycopg2.connect(
            host="192.168.178.94", port=5432, user="postgres", password="postgres", database="vcc_relational_prod"
        )

        cursor = conn.cursor()

        # Create documents table (based on UDS3 schema)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(255) UNIQUE NOT NULL,
            content TEXT,
            metadata JSONB,
            document_type VARCHAR(100),
            classification VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        print("\n📝 Creating 'documents' table...")
        cursor.execute(create_table_sql)
        conn.commit()
        print("   ✅ Table created successfully")

        # Create indexes
        print("\n📝 Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_document_id ON documents(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_document_type ON documents(document_type)",
            "CREATE INDEX IF NOT EXISTS idx_classification ON documents(classification)",
            "CREATE INDEX IF NOT EXISTS idx_content_fulltext ON documents USING gin(to_tsvector('german', content))",
        ]

        for idx_sql in indexes:
            try:
                cursor.execute(idx_sql)
                conn.commit()
                print(f"   ✅ Index created")
            except Exception as e:
                print(f"   ⚠️ Index creation warning: {e}")

        # Verify table
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        print(f"\n📄 Document count: {count}")

        cursor.close()
        conn.close()

        print("\n✅ Documents table setup complete")

    except Exception as e:
        print(f"\n❌ Documents table creation failed: {e}")
        import traceback

        traceback.print_exc()


def test_insert_document():
    """Test inserting a sample document"""
    print("\n" + "=" * 80)
    print("TEST DOCUMENT INSERT")
    print("=" * 80)

    try:
        import json

        from uds3.uds3_core import get_optimized_unified_strategy

        strategy = get_optimized_unified_strategy()
        backend = strategy.relational_backend

        # Sample document
        sample_doc = {
            "document_id": "test_doc_001",
            "content": "Photovoltaikanlagen müssen gemäß § 58 LBO BW auf Dachflächen installiert werden.",
            "metadata": json.dumps(
                {"title": "Test-Dokument Photovoltaik", "source": "VERITAS Test", "document_type": "regulation"}
            ),
            "document_type": "regulation",
            "classification": "building_law",
        }

        print("\n📝 Inserting sample document...")
        print(f"   Document ID: {sample_doc['document_id']}")
        print(f"   Type: {sample_doc['document_type']}")

        if hasattr(backend, "insert_document"):
            try:
                backend.insert_document(**sample_doc)
                print("   ✅ Document inserted successfully")

                # Verify
                doc_count = backend.get_document_count()
                print(f"   📄 Total documents: {doc_count}")

            except Exception as e:
                print(f"   ⚠️ Insert failed: {e}")
        else:
            print("   ❌ insert_document() method not available")

        print("\n✅ Test insert complete")

    except Exception as e:
        print(f"\n❌ Test insert failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all checks and setup"""
    print("\n" + "=" * 80)
    print("POSTGRESQL SETUP & SCHEMA CHECK")
    print("=" * 80)

    # 1. Check current schema
    backend = check_postgres_schema()

    # 2. Manual SQL inspection
    manual_sql_inspection()

    # 3. Create documents table if needed
    print("\n📝 Do you want to create the 'documents' table? (y/n)")
    print("   ℹ️ This will create the table if it doesn't exist")
    # Auto-create for testing
    create_documents_table()

    # 4. Re-check after creation
    print("\n" + "=" * 80)
    print("RE-CHECK AFTER TABLE CREATION")
    print("=" * 80)
    backend = check_postgres_schema()

    # 5. Test document insert
    test_insert_document()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("\n✅ PostgreSQL Setup complete")
    print("\n📝 Next Steps:")
    print("   1. ✅ Documents table created")
    print("   2. ✅ Sample document inserted")
    print("   3. ⏭️ Request execute_sql() API for full-text search")
    print("   4. ⏭️ Migrate existing documents from Neo4j to PostgreSQL (optional)")
    print("")


if __name__ == "__main__":
    main()
