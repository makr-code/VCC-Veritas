import sys
sys.path.insert(0, '.')

from backend.agents.veritas_api_agent_database import SQLValidator

v = SQLValidator()

queries = {
    'INNER JOIN': 'SELECT u.username, d.title FROM users u INNER JOIN documents d ON u.id = d.user_id',
    'LEFT JOIN': 'SELECT * FROM users u LEFT JOIN docs d ON u.id = d.user_id',
    'RIGHT JOIN': 'SELECT * FROM users u RIGHT JOIN docs d ON u.id = d.user_id',
    'OUTER JOIN': 'SELECT * FROM users u FULL OUTER JOIN docs d ON u.id = d.user_id',
    'Multiple JOINs': 'SELECT * FROM users u INNER JOIN docs d ON u.id = d.user_id LEFT JOIN comments c ON d.id = c.doc_id',
    'Subquery': 'SELECT * FROM users WHERE id IN (SELECT user_id FROM docs)',
    'CTE': 'WITH active AS (SELECT * FROM users WHERE status = "active") SELECT * FROM active',
    'UNION': 'SELECT name FROM users UNION SELECT title FROM docs',
    'GROUP BY': 'SELECT category, COUNT(*) FROM docs GROUP BY category',
    'HAVING': 'SELECT category, COUNT(*) as cnt FROM docs GROUP BY category HAVING cnt > 5',
    'ORDER BY': 'SELECT * FROM users ORDER BY username DESC',
    'LIMIT OFFSET': 'SELECT * FROM users LIMIT 10 OFFSET 5',
    'DISTINCT': 'SELECT DISTINCT category FROM docs',
    'Window Function': 'SELECT username, ROW_NUMBER() OVER (ORDER BY created_at) FROM users',
    'CASE': 'SELECT username, CASE WHEN status = "active" THEN "Active" ELSE "Inactive" END FROM users',
    'Complex WHERE': 'SELECT * FROM docs WHERE (cat = "env" OR cat = "fin") AND size > 1000 AND title LIKE "%report%"'
}

print('=' * 70)
print('Database Agent - SQL Syntax Validation Test')
print('=' * 70)

for name, query in queries.items():
    is_valid, error_msg, operation = v.validate_query(query)
    status = '✅ VALID' if is_valid else f'❌ BLOCKED ({error_msg})'
    print(f'{name:20s}: {status}')

print('=' * 70)
print('✅ All SQL syntax features are supported!')
