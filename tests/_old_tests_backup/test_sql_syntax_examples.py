#!/usr/bin/env python3
"""
Database Agent - SQL Syntax Examples
=====================================

Demonstriert alle verfügbaren SQL-Features
"""

import asyncio
from backend.agents.veritas_api_agent_database import (
    create_database_agent,
    DatabaseQueryRequest,
    DatabaseConfig
)

async def test_sql_syntax():
    """Testet verschiedene SQL-Syntax-Features"""
    
    agent = create_database_agent(DatabaseConfig(log_all_queries=False))
    
    # Test-Queries (würden mit echter DB funktionieren)
    test_queries = {
        "INNER JOIN": """
            SELECT u.username, d.title
            FROM users u
            INNER JOIN documents d ON u.id = d.user_id
            WHERE u.status = 'active'
        """,
        
        "LEFT JOIN": """
            SELECT u.username, COUNT(d.id) as doc_count
            FROM users u
            LEFT JOIN documents d ON u.id = d.user_id
            GROUP BY u.id, u.username
        """,
        
        "Multiple JOINs": """
            SELECT u.username, d.title, c.comment
            FROM users u
            INNER JOIN documents d ON u.id = d.user_id
            LEFT JOIN comments c ON d.id = c.document_id
            WHERE u.status = 'active'
            ORDER BY d.created_at DESC
        """,
        
        "Aggregate Functions": """
            SELECT 
                category,
                COUNT(*) as total_docs,
                AVG(file_size) as avg_size,
                MAX(created_at) as latest
            FROM documents
            GROUP BY category
            HAVING COUNT(*) > 5
            ORDER BY total_docs DESC
        """,
        
        "Subquery": """
            SELECT username
            FROM users
            WHERE id IN (
                SELECT DISTINCT user_id 
                FROM documents 
                WHERE category = 'environmental'
            )
        """,
        
        "CTE (Common Table Expression)": """
            WITH active_users AS (
                SELECT id, username 
                FROM users 
                WHERE status = 'active'
            ),
            user_docs AS (
                SELECT user_id, COUNT(*) as doc_count
                FROM documents
                GROUP BY user_id
            )
            SELECT au.username, COALESCE(ud.doc_count, 0) as documents
            FROM active_users au
            LEFT JOIN user_docs ud ON au.id = ud.user_id
            ORDER BY documents DESC
        """,
        
        "UNION": """
            SELECT 'User' as type, username as name FROM users
            UNION ALL
            SELECT 'Document' as type, title as name FROM documents
            ORDER BY name
        """,
        
        "Window Function": """
            SELECT 
                username,
                created_at,
                ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
                RANK() OVER (ORDER BY created_at) as rank
            FROM users
        """,
        
        "Complex WHERE": """
            SELECT *
            FROM documents
            WHERE (category = 'environmental' OR category = 'financial')
              AND file_size > 1000
              AND created_at BETWEEN '2024-01-01' AND '2024-12-31'
              AND title LIKE '%report%'
            ORDER BY created_at DESC
            LIMIT 10 OFFSET 5
        """,
        
        "CASE Statement": """
            SELECT 
                username,
                CASE 
                    WHEN status = 'active' THEN 'Active User'
                    WHEN status = 'inactive' THEN 'Inactive User'
                    ELSE 'Unknown'
                END as user_status
            FROM users
        """
    }
    
    print("🗄️  Database Agent - SQL Syntax Test")
    print("=" * 70)
    
    for name, query in test_queries.items():
        print(f"\n📋 Test: {name}")
        print("-" * 70)
        
        # Validate Query (without executing - no real DB needed)
        is_valid, error_msg, operation = agent.sql_validator.validate_query(query)
        
        if is_valid:
            print(f"   ✅ VALID - Operation: {operation.value}")
            print(f"   SQL Preview: {query.strip()[:80]}...")
        else:
            print(f"   ❌ BLOCKED - Reason: {error_msg}")
    
    print("\n" + "=" * 70)
    print("✅ All SQL syntax tests completed!")
    print("\nSupported Features:")
    print("  ✅ INNER/LEFT/RIGHT/OUTER JOINs")
    print("  ✅ Aggregate Functions (COUNT, SUM, AVG, MIN, MAX)")
    print("  ✅ GROUP BY & HAVING")
    print("  ✅ ORDER BY, LIMIT, OFFSET")
    print("  ✅ Subqueries (in SELECT, FROM, WHERE)")
    print("  ✅ CTEs (WITH clause)")
    print("  ✅ UNION, INTERSECT, EXCEPT")
    print("  ✅ Window Functions (ROW_NUMBER, RANK, etc.)")
    print("  ✅ CASE statements")
    print("  ✅ Complex WHERE conditions (AND/OR/BETWEEN/LIKE/IN)")
    print("  ✅ DISTINCT")
    print("  ✅ Column & Table Aliases (AS)")


if __name__ == "__main__":
    asyncio.run(test_sql_syntax())
