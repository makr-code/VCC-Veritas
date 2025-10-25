"""
Secrets Migration Script for VERITAS
=====================================

Migrates secrets from plaintext .env file to encrypted DPAPI storage.

This script:
1. Reads secrets from .env file
2. Encrypts them using Windows DPAPI
3. Stores them in data/secrets/dpapi_secrets.json
4. Optionally backs up and deletes .env

Usage:
    python tools/migrate_secrets.py [--backup] [--delete-env]

Options:
    --backup      Create backup of .env before migration
    --delete-env  Delete .env after successful migration (USE WITH CAUTION!)

Requirements:
    - Windows OS with DPAPI support
    - pywin32 package (pip install pywin32)

Author: VERITAS Security Team
Date: 22. Oktober 2025
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from shutil import copy2

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.security.secrets import get_secrets_manager, DPAPI_AVAILABLE


# ============================================================================
# Configuration
# ============================================================================

ENV_FILE = project_root / ".env"
ENV_BACKUP_DIR = project_root / "data" / "backups"

# Secrets to migrate
SECRETS_TO_MIGRATE = [
    "JWT_SECRET_KEY",
    "POSTGRES_PASSWORD",
    "NEO4J_PASSWORD",
    "COUCHDB_PASSWORD",
    "VCC_CA_PASSWORD",
]


# ============================================================================
# Helper Functions
# ============================================================================

def print_header(text: str):
    """Print section header"""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")


def backup_env_file():
    """Create backup of .env file"""
    if not ENV_FILE.exists():
        print_warning(".env file not found - nothing to backup")
        return None
    
    # Create backup directory
    ENV_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = ENV_BACKUP_DIR / f".env.backup_{timestamp}"
    
    try:
        copy2(ENV_FILE, backup_path)
        print_success(f"Backed up .env to: {backup_path}")
        return backup_path
    except Exception as e:
        print_error(f"Failed to backup .env: {e}")
        return None


def load_env_secrets():
    """Load secrets from .env file"""
    if not ENV_FILE.exists():
        print_error(f".env file not found: {ENV_FILE}")
        return {}
    
    secrets = {}
    
    try:
        with open(ENV_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Only include secrets we want to migrate
                    if key in SECRETS_TO_MIGRATE:
                        secrets[key] = value
        
        print_success(f"Loaded {len(secrets)} secrets from .env")
        return secrets
    
    except Exception as e:
        print_error(f"Failed to load .env: {e}")
        return {}


def migrate_secrets(secrets: dict):
    """Migrate secrets to DPAPI storage"""
    if not secrets:
        print_warning("No secrets to migrate")
        return 0
    
    # Get secrets manager
    try:
        # Force enable secure storage for migration
        os.environ["ENABLE_SECURE_SECRETS"] = "true"
        manager = get_secrets_manager()
    except Exception as e:
        print_error(f"Failed to initialize secrets manager: {e}")
        return 0
    
    # Migrate each secret
    migrated = 0
    for key, value in secrets.items():
        print_info(f"Migrating: {key}")
        
        if manager.set_secret(key, value):
            migrated += 1
            print_success(f"  ✅ Encrypted and stored: {key}")
        else:
            print_error(f"  ❌ Failed to migrate: {key}")
    
    print_success(f"Migrated {migrated}/{len(secrets)} secrets")
    return migrated


def verify_migration(secrets: dict):
    """Verify that secrets can be decrypted"""
    manager = get_secrets_manager()
    
    verified = 0
    for key in secrets.keys():
        value = manager.get_secret(key)
        if value:
            verified += 1
            print_success(f"  ✅ Verified: {key}")
        else:
            print_error(f"  ❌ Failed to retrieve: {key}")
    
    print_success(f"Verified {verified}/{len(secrets)} secrets")
    return verified == len(secrets)


def delete_env_file():
    """Delete .env file after successful migration"""
    if not ENV_FILE.exists():
        print_warning(".env file not found")
        return False
    
    try:
        ENV_FILE.unlink()
        print_success("Deleted .env file")
        return True
    except Exception as e:
        print_error(f"Failed to delete .env: {e}")
        return False


# ============================================================================
# Main Migration Flow
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Migrate VERITAS secrets to DPAPI storage")
    parser.add_argument("--backup", action="store_true", help="Backup .env before migration")
    parser.add_argument("--delete-env", action="store_true", help="Delete .env after migration")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing secrets")
    
    args = parser.parse_args()
    
    print_header("VERITAS Secrets Migration Tool")
    print_info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Project Root: {project_root}")
    print_info(f"ENV File: {ENV_FILE}")
    
    # Check prerequisites
    print_header("Prerequisites Check")
    
    if not DPAPI_AVAILABLE:
        print_error("DPAPI not available!")
        print_error("This script requires Windows and pywin32 package")
        print_info("Install with: pip install pywin32")
        sys.exit(1)
    
    print_success("DPAPI available")
    
    # Verify-only mode
    if args.verify_only:
        print_header("Verification Mode")
        
        manager = get_secrets_manager()
        stored_secrets = manager.list_secrets()
        
        if not stored_secrets:
            print_warning("No secrets found in DPAPI storage")
            sys.exit(0)
        
        print_info(f"Found {len(stored_secrets)} stored secrets:")
        for key in stored_secrets:
            value = manager.get_secret(key)
            if value:
                print_success(f"  ✅ {key}: {'*' * min(len(value), 20)}")
            else:
                print_error(f"  ❌ {key}: Failed to decrypt")
        
        sys.exit(0)
    
    # Backup .env if requested
    if args.backup:
        print_header("Backup Phase")
        backup_path = backup_env_file()
        if not backup_path:
            print_error("Backup failed!")
            sys.exit(1)
    
    # Load secrets from .env
    print_header("Loading Secrets from .env")
    secrets = load_env_secrets()
    
    if not secrets:
        print_error("No secrets found in .env file!")
        print_info("Expected secrets:")
        for key in SECRETS_TO_MIGRATE:
            print_info(f"  - {key}")
        sys.exit(1)
    
    print_info("Found secrets:")
    for key, value in secrets.items():
        print_info(f"  - {key}: {'*' * min(len(value), 20)}")
    
    # Migrate secrets
    print_header("Migration Phase")
    migrated = migrate_secrets(secrets)
    
    if migrated == 0:
        print_error("Migration failed!")
        sys.exit(1)
    
    # Verify migration
    print_header("Verification Phase")
    if not verify_migration(secrets):
        print_error("Verification failed!")
        print_warning("Secrets were migrated but cannot be retrieved")
        print_warning("DO NOT delete .env file!")
        sys.exit(1)
    
    # Delete .env if requested
    if args.delete_env:
        print_header("Cleanup Phase")
        print_warning("About to delete .env file!")
        print_warning("This action cannot be undone!")
        print_info("Backup location: " + str(ENV_BACKUP_DIR))
        
        response = input("\nAre you sure? Type 'yes' to confirm: ")
        if response.lower() == "yes":
            if delete_env_file():
                print_success("Migration complete - .env deleted")
            else:
                print_error("Failed to delete .env")
                sys.exit(1)
        else:
            print_info("Skipped .env deletion")
    
    # Summary
    print_header("Migration Summary")
    print_success("✅ Migration successful!")
    print_info(f"Migrated: {migrated} secrets")
    print_info(f"Storage: data/secrets/dpapi_secrets.json")
    print_info(f"Backend: Windows DPAPI")
    
    if args.backup:
        print_info(f"Backup: {backup_path}")
    
    print_header("Next Steps")
    print_info("1. Update backend to use secrets manager:")
    print_info("   from backend.security.secrets import get_database_password")
    print_info("   password = get_database_password('POSTGRES')")
    print_info("")
    print_info("2. Set ENABLE_SECURE_SECRETS=true in .env")
    print_info("")
    print_info("3. Test backend with encrypted secrets")
    print_info("")
    print_info("4. (Optional) Delete .env file:")
    print_info("   python tools/migrate_secrets.py --delete-env")


if __name__ == "__main__":
    main()
