"""Secure secrets management using Windows DPAPI or Azure KeyVault.

This module provides a secure way to store and retrieve secrets without
storing them in plaintext in .env files.

Supports:
- Windows: DPAPI (Data Protection API) for local encryption
- Azure: KeyVault for cloud-based secret management
- Fallback: Environment variables (development only)

Usage:
    from backend.security.secrets import secrets_manager
    
    # Set secret (encrypts automatically)
    secrets_manager.set_secret("db_password", "my_secure_password")
    
    # Get secret (decrypts automatically)
    password = secrets_manager.get_secret("db_password")

Author: VERITAS Security Team
Date: 22. Oktober 2025
Based on: Covina security/secrets.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Check Windows availability
WINDOWS_AVAILABLE = sys.platform == "win32"
if WINDOWS_AVAILABLE:
    try:
        import win32crypt
        DPAPI_AVAILABLE = True
    except ImportError:
        DPAPI_AVAILABLE = False
        logger.warning("⚠️  win32crypt not available - DPAPI disabled (install: pip install pywin32)")
else:
    DPAPI_AVAILABLE = False

# Check Azure KeyVault availability
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_KEYVAULT_AVAILABLE = True
except ImportError:
    AZURE_KEYVAULT_AVAILABLE = False
    logger.debug("Azure KeyVault SDK not available")


class SecretsBackend(ABC):
    """Abstract base class for secrets storage backends."""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret by key."""
        pass
    
    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret by key."""
        pass
    
    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete a secret by key."""
        pass
    
    @abstractmethod
    def list_secrets(self) -> list[str]:
        """List all secret keys."""
        pass


class DPAPISecretsBackend(SecretsBackend):
    """Windows DPAPI-based secrets storage (local machine encryption)."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        if not DPAPI_AVAILABLE:
            raise RuntimeError("DPAPI not available - install: pip install pywin32")
        
        self.storage_path = storage_path or Path("data/secrets/dpapi_secrets.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing secrets
        self._secrets: Dict[str, bytes] = {}
        self._load_secrets()
        
        logger.info(f"✅ DPAPI Secrets Backend initialized: {self.storage_path}")
    
    def _load_secrets(self):
        """Load encrypted secrets from disk."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    # Convert hex strings back to bytes
                    self._secrets = {k: bytes.fromhex(v) for k, v in data.items()}
                logger.info(f"✅ Loaded {len(self._secrets)} encrypted secrets from DPAPI storage")
            except Exception as e:
                logger.error(f"❌ Failed to load DPAPI secrets: {e}")
                self._secrets = {}
    
    def _save_secrets(self):
        """Save encrypted secrets to disk."""
        try:
            # Convert bytes to hex strings for JSON serialization
            data = {k: v.hex() for k, v in self._secrets.items()}
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self._secrets)} secrets to DPAPI storage")
        except Exception as e:
            logger.error(f"❌ Failed to save DPAPI secrets: {e}")
    
    def get_secret(self, key: str) -> Optional[str]:
        """Decrypt and retrieve a secret."""
        encrypted_data = self._secrets.get(key)
        if encrypted_data is None:
            return None
        
        try:
            # Decrypt using DPAPI
            decrypted_data = win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)
            return decrypted_data[1].decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Failed to decrypt secret '{key}': {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Encrypt and store a secret."""
        try:
            # Encrypt using DPAPI (local machine scope)
            encrypted_data = win32crypt.CryptProtectData(
                value.encode('utf-8'),
                f"VERITAS Secret: {key}",
                None,
                None,
                None,
                0
            )
            self._secrets[key] = encrypted_data
            self._save_secrets()
            logger.info(f"✅ Secret '{key}' encrypted and stored via DPAPI")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to encrypt secret '{key}': {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret."""
        if key in self._secrets:
            del self._secrets[key]
            self._save_secrets()
            logger.info(f"✅ Secret '{key}' deleted from DPAPI storage")
            return True
        return False
    
    def list_secrets(self) -> list[str]:
        """List all secret keys."""
        return list(self._secrets.keys())


class AzureKeyVaultBackend(SecretsBackend):
    """Azure KeyVault-based secrets storage (cloud-based)."""
    
    def __init__(self, vault_url: Optional[str] = None):
        if not AZURE_KEYVAULT_AVAILABLE:
            raise RuntimeError("Azure KeyVault SDK not available")
        
        self.vault_url = vault_url or os.getenv("AZURE_KEYVAULT_URL")
        if not self.vault_url:
            raise ValueError("AZURE_KEYVAULT_URL must be set")
        
        # Initialize KeyVault client with DefaultAzureCredential
        try:
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=credential)
            logger.info(f"✅ Azure KeyVault Backend initialized: {self.vault_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure KeyVault: {e}")
            raise
    
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from KeyVault."""
        try:
            secret = self.client.get_secret(key)
            return secret.value
        except Exception as e:
            logger.error(f"❌ Failed to get secret '{key}' from KeyVault: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Store a secret in KeyVault."""
        try:
            self.client.set_secret(key, value)
            logger.info(f"✅ Secret '{key}' stored in Azure KeyVault")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to set secret '{key}' in KeyVault: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret from KeyVault."""
        try:
            poller = self.client.begin_delete_secret(key)
            poller.wait()
            logger.info(f"✅ Secret '{key}' deleted from Azure KeyVault")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete secret '{key}' from KeyVault: {e}")
            return False
    
    def list_secrets(self) -> list[str]:
        """List all secret names in KeyVault."""
        try:
            return [secret.name for secret in self.client.list_properties_of_secrets()]
        except Exception as e:
            logger.error(f"❌ Failed to list secrets from KeyVault: {e}")
            return []


class EnvSecretsBackend(SecretsBackend):
    """Environment variable-based secrets storage (DEVELOPMENT ONLY)."""
    
    def __init__(self):
        logger.warning("⚠️  Using EnvSecretsBackend - NOT SECURE for production!")
        logger.warning("⚠️  Secrets are stored in plaintext environment variables")
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get secret from environment variable."""
        return os.getenv(key)
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set secret as environment variable (in-memory only)."""
        os.environ[key] = value
        logger.warning(f"⚠️  Secret '{key}' set as environment variable (not persistent)")
        return True
    
    def delete_secret(self, key: str) -> bool:
        """Delete secret from environment."""
        if key in os.environ:
            del os.environ[key]
            return True
        return False
    
    def list_secrets(self) -> list[str]:
        """Cannot list secrets from environment."""
        logger.warning("⚠️  EnvSecretsBackend cannot list secrets")
        return []


class SecretsManager:
    """High-level secrets management with automatic backend selection."""
    
    def __init__(self, backend: Optional[SecretsBackend] = None, enable_secure_storage: bool = True):
        self.enable_secure_storage = enable_secure_storage
        
        if backend:
            self.backend = backend
        else:
            # Auto-select backend based on environment
            self.backend = self._select_backend()
        
        logger.info(f"✅ SecretsManager initialized with {self.backend.__class__.__name__}")
    
    def _select_backend(self) -> SecretsBackend:
        """Automatically select the best available backend."""
        # Check if secure storage is disabled
        if not self.enable_secure_storage:
            logger.warning("⚠️  Secure storage disabled - using ENV fallback")
            return EnvSecretsBackend()
        
        # Priority 1: Azure KeyVault (production cloud)
        if AZURE_KEYVAULT_AVAILABLE and os.getenv("AZURE_KEYVAULT_URL"):
            try:
                return AzureKeyVaultBackend()
            except Exception as e:
                logger.warning(f"⚠️  Azure KeyVault unavailable: {e}")
        
        # Priority 2: Windows DPAPI (production on-premise)
        if DPAPI_AVAILABLE:
            try:
                return DPAPISecretsBackend()
            except Exception as e:
                logger.warning(f"⚠️  DPAPI unavailable: {e}")
        
        # Priority 3: Environment variables (development fallback)
        logger.warning("⚠️  No secure secrets backend available - using ENV fallback")
        return EnvSecretsBackend()
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret by key."""
        value = self.backend.get_secret(key)
        return value if value is not None else default
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret by key."""
        return self.backend.set_secret(key, value)
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret by key."""
        return self.backend.delete_secret(key)
    
    def list_secrets(self) -> list[str]:
        """List all secret keys."""
        return self.backend.list_secrets()
    
    def migrate_from_env(self, keys: list[str]):
        """Migrate secrets from environment variables to secure storage."""
        migrated = 0
        for key in keys:
            value = os.getenv(key)
            if value:
                if self.set_secret(key, value):
                    migrated += 1
                    logger.info(f"✅ Migrated secret '{key}' from ENV to secure storage")
        
        logger.info(f"✅ Migrated {migrated}/{len(keys)} secrets to secure storage")
        return migrated


# Global singleton instance (lazy initialization)
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """Get or create the global secrets manager instance."""
    global _secrets_manager
    if _secrets_manager is None:
        # Check if secure storage should be enabled
        enable_secure_storage = os.getenv("ENABLE_SECURE_SECRETS", "false").lower() == "true"
        _secrets_manager = SecretsManager(enable_secure_storage=enable_secure_storage)
    return _secrets_manager


# Convenience functions for common secrets
def get_jwt_secret() -> str:
    """Get JWT secret (fallback to ENV if not in secure storage)."""
    manager = get_secrets_manager()
    return manager.get_secret("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")


def get_database_password(db_name: str) -> Optional[str]:
    """Get database password (e.g., 'POSTGRES', 'NEO4J', 'COUCHDB', 'CHROMA')."""
    manager = get_secrets_manager()
    key = f"{db_name.upper()}_PASSWORD"
    return manager.get_secret(key) or os.getenv(key)


def get_vcc_ca_password() -> str:
    """Get VCC CA password for PKI."""
    manager = get_secrets_manager()
    return manager.get_secret("VCC_CA_PASSWORD") or os.getenv("VCC_CA_PASSWORD", "VCC-SecurePassword-2024")


# Migration helper
def migrate_secrets_from_env():
    """Migrate all known secrets from .env to secure storage."""
    secrets_to_migrate = [
        "JWT_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "NEO4J_PASSWORD",
        "COUCHDB_PASSWORD",
        "VCC_CA_PASSWORD",
    ]
    
    manager = get_secrets_manager()
    return manager.migrate_from_env(secrets_to_migrate)
