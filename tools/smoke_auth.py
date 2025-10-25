"""
Quick smoke test for JWT secret retrieval via SecretsManager.
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.security.auth import SECRET_KEY, ALGORITHM

print("SECRET_KEY length:", len(SECRET_KEY) if isinstance(SECRET_KEY, str) else 'N/A')
print("ALGORITHM:", ALGORITHM)

if not SECRET_KEY or len(SECRET_KEY) < 32:
    raise SystemExit("JWT SECRET invalid or too short")
print("OK: JWT secret loaded from secure storage.")
