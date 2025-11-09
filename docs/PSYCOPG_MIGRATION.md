# Migration Guide: psycopg2 → psycopg3

## Problem

`psycopg2-binary==2.9.9` ist nicht mit Python 3.13 kompatibel und schlägt beim Build fehl:
```
Error: pg_config executable not found.
```

## Lösung

### Option 1: psycopg3 verwenden (EMPFOHLEN)

**Installation:**
```bash
pip install "psycopg[binary]>=3.1.0"
```

**Code-Migration:**

```python
# ALT: psycopg2
import psycopg2
conn = psycopg2.connect("dbname=test user=postgres")
cursor = conn.cursor()
cursor.execute("SELECT * FROM table")
rows = cursor.fetchall()

# NEU: psycopg3
import psycopg
conn = psycopg.connect("dbname=test user=postgres")
cursor = conn.cursor()
cursor.execute("SELECT * FROM table")
rows = cursor.fetchall()
```

**Async Support:**
```python
# psycopg3 hat natives async
import psycopg
async with await psycopg.AsyncConnection.connect("dbname=test") as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT * FROM table")
        rows = await cur.fetchall()
```

**Hauptunterschiede:**
- Import: `psycopg` statt `psycopg2`
- Bessere Performance
- Native async/await Support
- Modern Python Type Hints
- Binary Protocol für schnellere Datenübertragung

### Option 2: asyncpg verwenden (Nur Async)

**Installation:**
```bash
pip install asyncpg>=0.29.0
```

**Code:**
```python
import asyncpg

async def main():
    conn = await asyncpg.connect(user='postgres', database='test')
    rows = await conn.fetch('SELECT * FROM table')
    await conn.close()
```

**Vorteile:**
- Sehr schnell (schneller als psycopg)
- Pure async
- Optimiert für hohe Performance

**Nachteile:**
- Nur async (kein sync)
- Andere API als psycopg

### Option 3: Python 3.12 oder älter verwenden

Falls Migration nicht möglich:
```bash
# Python 3.12 installieren
pyenv install 3.12
pyenv local 3.12

# Dann funktioniert psycopg2-binary==2.9.9
pip install psycopg2-binary==2.9.9
```

## Empfohlene Migration für VERITAS

1. **requirements.txt aktualisieren:**
   ```txt
   # Ersetze:
   psycopg2-binary==2.9.9

   # Mit:
   psycopg[binary]>=3.1.0
   ```

2. **Code aktualisieren:**
   - Suche alle `import psycopg2` → Ersetze mit `import psycopg`
   - Prüfe connection strings (meist kompatibel)
   - Teste alle Datenbankoperationen

3. **Testen:**
   ```bash
   pytest tests/ -k postgres
   ```

## Kompatibilitätstabelle

| Python Version | psycopg2 | psycopg3 | asyncpg |
|----------------|----------|----------|---------|
| 3.8            | ✅       | ✅       | ✅      |
| 3.9            | ✅       | ✅       | ✅      |
| 3.10           | ✅       | ✅       | ✅      |
| 3.11           | ✅       | ✅       | ✅      |
| 3.12           | ✅       | ✅       | ✅      |
| 3.13           | ❌       | ✅       | ✅      |

## Quick Fix für Entwicklung

**Sofort funktionierende Installation:**
```bash
# Verwende requirements-py313.txt
pip install -r requirements-py313.txt
```

## Ressourcen

- [psycopg3 Docs](https://www.psycopg.org/psycopg3/docs/)
- [Migration Guide](https://www.psycopg.org/psycopg3/docs/basic/from_pg2.html)
- [asyncpg Docs](https://magicstack.github.io/asyncpg/)
