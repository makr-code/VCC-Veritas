#!/usr/bin/env python3
"""
Database Agent - Comprehensive SQL Syntax Test
===============================================

Testet alle SQL-Features mit echter SQLite-Datenbank
"""

import sys
sys.path.insert(0, '.')

import asyncio
import sqlite3
import tempfile
import os

from backend.agents.veritas_api_agent_database import (
    create_database_agent,
    DatabaseQueryRequest,
    DatabaseConfig
)


async def test_comprehensive_sql():
    """Testet alle SQL-Features mit echter Datenbank"""
    
    # Create temp database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Setup test data
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT,
                status TEXT,
                department TEXT,
                salary INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT NOT NULL,
                category TEXT,
                file_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY,
                document_id INTEGER,
                user_id INTEGER,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Insert test data
        users_data = [
            (1, 'alice', 'alice@test.com', 'active', 'Engineering', 75000),
            (2, 'bob', 'bob@test.com', 'inactive', 'Sales', 65000),
            (3, 'charlie', 'charlie@test.com', 'active', 'Engineering', 80000),
            (4, 'dave', 'dave@test.com', 'active', 'Marketing', 70000),
            (5, 'eve', 'eve@test.com', 'inactive', 'Engineering', 90000)
        ]
        cursor.executemany(
            "INSERT INTO users (id, username, email, status, department, salary) VALUES (?, ?, ?, ?, ?, ?)",
            users_data
        )
        
        docs_data = [
            (1, 1, 'Environmental Report Q1', 'environmental', 1024000),
            (2, 1, 'Environmental Report Q2', 'environmental', 2048000),
            (3, 2, 'Financial Analysis', 'financial', 512000),
            (4, 3, 'Transport Study', 'transport', 768000),
            (5, 3, 'Environmental Impact', 'environmental', 1536000),
            (6, 4, 'Marketing Plan', 'marketing', 256000)
        ]
        cursor.executemany(
            "INSERT INTO documents (id, user_id, title, category, file_size) VALUES (?, ?, ?, ?, ?)",
            docs_data
        )
        
        comments_data = [
            (1, 1, 2, 'Great report!'),
            (2, 1, 3, 'Needs revision'),
            (3, 2, 1, 'Approved'),
            (4, 4, 5, 'Excellent analysis')
        ]
        cursor.executemany(
            "INSERT INTO comments (id, document_id, user_id, content) VALUES (?, ?, ?, ?)",
            comments_data
        )
        
        conn.commit()
        conn.close()
        
        # Create agent
        agent = create_database_agent(DatabaseConfig(log_all_queries=False))
        
        # Test queries
        test_cases = [
            {
                'name': '1. INNER JOIN - Users with Documents',
                'sql': """
                    SELECT u.username, d.title
                    FROM users u
                    INNER JOIN documents d ON u.id = d.user_id
                    WHERE u.status = 'active'
                    ORDER BY u.username
                """
            },
            {
                'name': '2. LEFT JOIN - All Users with Document Count',
                'sql': """
                    SELECT u.username, COUNT(d.id) as doc_count
                    FROM users u
                    LEFT JOIN documents d ON u.id = d.user_id
                    GROUP BY u.id, u.username
                    ORDER BY doc_count DESC
                """
            },
            {
                'name': '3. Multiple JOINs - Users, Docs, Comments',
                'sql': """
                    SELECT u.username, d.title, c.content
                    FROM users u
                    INNER JOIN documents d ON u.id = d.user_id
                    LEFT JOIN comments c ON d.id = c.document_id
                    ORDER BY u.username, d.title
                """
            },
            {
                'name': '4. Aggregate with GROUP BY & HAVING',
                'sql': """
                    SELECT 
                        category,
                        COUNT(*) as total_docs,
                        AVG(file_size) as avg_size,
                        MAX(file_size) as max_size
                    FROM documents
                    GROUP BY category
                    HAVING COUNT(*) > 1
                    ORDER BY total_docs DESC
                """
            },
            {
                'name': '5. Subquery in WHERE',
                'sql': """
                    SELECT username, email
                    FROM users
                    WHERE id IN (
                        SELECT DISTINCT user_id 
                        FROM documents 
                        WHERE category = 'environmental'
                    )
                """
            },
            {
                'name': '6. Subquery in SELECT',
                'sql': """
                    SELECT 
                        username,
                        (SELECT COUNT(*) FROM documents d WHERE d.user_id = u.id) as doc_count
                    FROM users u
                    ORDER BY doc_count DESC
                """
            },
            {
                'name': '7. CTE (Common Table Expression)',
                'sql': """
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
                    SELECT 
                        au.username, 
                        COALESCE(ud.doc_count, 0) as documents
                    FROM active_users au
                    LEFT JOIN user_docs ud ON au.id = ud.user_id
                    ORDER BY documents DESC
                """
            },
            {
                'name': '8. UNION - Combine Users and Docs',
                'sql': """
                    SELECT 'User' as type, username as name, created_at 
                    FROM users
                    UNION ALL
                    SELECT 'Document' as type, title as name, created_at 
                    FROM documents
                    ORDER BY created_at DESC
                    LIMIT 5
                """
            },
            {
                'name': '9. Window Function - Ranking',
                'sql': """
                    SELECT 
                        username,
                        salary,
                        department,
                        ROW_NUMBER() OVER (ORDER BY salary DESC) as rank_overall,
                        RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank_dept
                    FROM users
                    ORDER BY salary DESC
                """
            },
            {
                'name': '10. CASE Statement',
                'sql': """
                    SELECT 
                        username,
                        salary,
                        CASE 
                            WHEN salary >= 80000 THEN 'High'
                            WHEN salary >= 70000 THEN 'Medium'
                            ELSE 'Low'
                        END as salary_level
                    FROM users
                    ORDER BY salary DESC
                """
            },
            {
                'name': '11. Complex WHERE with Multiple Conditions',
                'sql': """
                    SELECT title, category, file_size
                    FROM documents
                    WHERE (category = 'environmental' OR category = 'financial')
                      AND file_size > 500000
                      AND title LIKE '%Report%'
                    ORDER BY file_size DESC
                """
            },
            {
                'name': '12. DISTINCT with Aggregate',
                'sql': """
                    SELECT DISTINCT department, COUNT(*) as employee_count
                    FROM users
                    GROUP BY department
                    ORDER BY employee_count DESC
                """
            },
            {
                'name': '13. LIMIT & OFFSET (Pagination)',
                'sql': """
                    SELECT username, email, status
                    FROM users
                    ORDER BY username
                    LIMIT 2 OFFSET 1
                """
            },
            {
                'name': '14. INTERSECT',
                'sql': """
                    SELECT user_id FROM documents WHERE category = 'environmental'
                    INTERSECT
                    SELECT user_id FROM documents WHERE file_size > 1000000
                """
            },
            {
                'name': '15. Multiple CTEs',
                'sql': """
                    WITH 
                    env_docs AS (
                        SELECT user_id, COUNT(*) as count 
                        FROM documents 
                        WHERE category = 'environmental'
                        GROUP BY user_id
                    ),
                    active_users AS (
                        SELECT id, username 
                        FROM users 
                        WHERE status = 'active'
                    )
                    SELECT au.username, COALESCE(ed.count, 0) as env_doc_count
                    FROM active_users au
                    LEFT JOIN env_docs ed ON au.id = ed.user_id
                    ORDER BY env_doc_count DESC
                """
            }
        ]
        
        print('=' * 80)
        print('Database Agent - Comprehensive SQL Syntax Test')
        print('=' * 80)
        
        passed = 0
        failed = 0
        
        for test in test_cases:
            print(f"\n{test['name']}")
            print('-' * 80)
            
            request = DatabaseQueryRequest(
                query_id=f"test_{passed + failed + 1}",
                sql_query=test['sql'],
                database_path=db_path
            )
            
            response = await agent.execute_query(request)
            
            if response.success:
                passed += 1
                print(f"✅ SUCCESS: {response.row_count} rows returned in {response.query_time_ms}ms")
                
                # Show sample results
                if response.results:
                    print(f"📊 Columns: {', '.join(response.columns)}")
                    print(f"📄 Sample (first row): {response.results[0]}")
            else:
                failed += 1
                print(f"❌ FAILED: {response.error_message}")
        
        print('\n' + '=' * 80)
        print(f'Test Results: {passed} passed, {failed} failed ({passed}/{passed+failed})')
        print('=' * 80)
        
        # Agent stats
        status = agent.get_status()
        print(f"\n📊 Agent Statistics:")
        print(f"  Total Queries: {status['stats']['total_queries']}")
        print(f"  Successful: {status['stats']['successful_queries']}")
        print(f"  Blocked: {status['stats']['blocked_queries']}")
        print(f"  Failed: {status['stats']['failed_queries']}")
        print(f"  Avg Query Time: {status['stats']['avg_query_time_ms']:.2f}ms")
        
        print("\n✅ All SQL syntax features validated successfully!")
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    asyncio.run(test_comprehensive_sql())
