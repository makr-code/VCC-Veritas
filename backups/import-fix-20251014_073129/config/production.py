"""
VERITAS Framework - Production Configuration

This module provides production-ready configuration settings for the VERITAS
framework. It loads settings from environment variables and provides sensible
defaults with security best practices.

Features:
- Environment variable loading with validation
- Type conversion and validation
- Secure defaults for production
- Configuration validation
- Secrets management
- Multi-environment support

Usage:
    from config.production import ProductionConfig
    
    config = ProductionConfig()
    
    # Access settings
    db_url = config.database_url
    jwt_secret = config.jwt_secret_key
    
    # Validate configuration
    config.validate()

Author: VERITAS Team
Date: 2025-10-08
Version: 1.0.0
"""

import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import timedelta
import secrets
import logging


@dataclass
class DatabaseConfig:
    """Database configuration."""
    type: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = "veritas"
    user: str = "veritas_user"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    ssl_mode: str = "prefer"
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        if self.type == "sqlite":
            sqlite_path = os.getenv("SQLITE_DB_PATH", "./data/veritas.sqlite")
            return f"sqlite:///{sqlite_path}"
        elif self.type == "postgresql":
            return (
                f"postgresql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}"
            )
        elif self.type == "mysql":
            return (
                f"mysql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.name}"
            )
        else:
            raise ValueError(f"Unsupported database type: {self.type}")


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    ssl: bool = False
    pool_size: int = 10
    pool_timeout: int = 5
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        protocol = "rediss" if self.ssl else "redis"
        auth = f":{self.password}@" if self.password else ""
        return f"{protocol}://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 30
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digits: bool = True
    password_require_special: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    api_key_expiry_days: int = 365
    session_max_age: int = 86400
    cors_origins: List[str] = field(default_factory=list)


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "json"
    output: str = "both"
    file_path: str = "./logs/veritas.log"
    max_bytes: int = 10485760
    backup_count: int = 10
    include_timestamp: bool = True
    include_level: bool = True
    include_module: bool = True
    include_function: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    metrics_enabled: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"
    health_check_enabled: bool = True
    health_check_path: str = "/health"
    apm_enabled: bool = False
    apm_service_name: str = "veritas"
    apm_server_url: str = ""
    grafana_enabled: bool = False
    grafana_url: str = ""


@dataclass
class BackupConfig:
    """Backup configuration."""
    enabled: bool = True
    path: str = "./backups"
    schedule: str = "0 2 * * *"
    retention_days: int = 30
    db_backup_enabled: bool = True
    db_backup_compression: bool = True
    file_backup_enabled: bool = True
    remote_backup_enabled: bool = False
    remote_backup_type: str = "s3"
    remote_backup_bucket: str = ""
    remote_backup_region: str = "us-east-1"


@dataclass
class AgentConfig:
    """Agent orchestration configuration."""
    max_concurrent_agents: int = 10
    timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 5
    quality_gate_min_score: float = 0.7
    quality_gate_enabled: bool = True


@dataclass
class OllamaConfig:
    """Ollama integration configuration."""
    enabled: bool = True
    api_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:latest"
    timeout: int = 120
    embedding_model: str = "nomic-embed-text"
    embedding_dimension: int = 768


class ProductionConfig:
    """
    Production configuration for VERITAS framework.
    
    Loads configuration from environment variables with validation
    and provides sensible defaults.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Application settings
        self.app_env = os.getenv("APP_ENV", "production")
        self.app_name = os.getenv("APP_NAME", "VERITAS")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug = self._get_bool("DEBUG", False)
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Component configurations
        self.database = self._load_database_config()
        self.redis = self._load_redis_config()
        self.security = self._load_security_config()
        self.logging = self._load_logging_config()
        self.monitoring = self._load_monitoring_config()
        self.backup = self._load_backup_config()
        self.agent = self._load_agent_config()
        self.ollama = self._load_ollama_config()
        
        # Additional settings
        self.websocket_enabled = self._get_bool("WEBSOCKET_ENABLED", True)
        self.websocket_port = int(os.getenv("WEBSOCKET_PORT", "8001"))
        self.cache_enabled = self._get_bool("CACHE_ENABLED", True)
        self.queue_enabled = self._get_bool("QUEUE_ENABLED", True)
        
        # Feature flags
        self.feature_flags = self._load_feature_flags()
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean from environment variable."""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_list(self, key: str, default: List[str] = None) -> List[str]:
        """Get list from environment variable (comma-separated)."""
        if default is None:
            default = []
        value = os.getenv(key, "")
        if not value:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration."""
        return DatabaseConfig(
            type=os.getenv("DB_TYPE", "postgresql"),
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "veritas"),
            user=os.getenv("DB_USER", "veritas_user"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            ssl_mode=os.getenv("DB_SSL_MODE", "prefer")
        )
    
    def _load_redis_config(self) -> RedisConfig:
        """Load Redis configuration."""
        return RedisConfig(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", ""),
            db=int(os.getenv("REDIS_DB", "0")),
            ssl=self._get_bool("REDIS_SSL", False),
            pool_size=int(os.getenv("REDIS_POOL_SIZE", "10")),
            pool_timeout=int(os.getenv("REDIS_POOL_TIMEOUT", "5"))
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration."""
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key or secret_key == "your-secret-key-here-change-me":
            if self.app_env == "production":
                raise ValueError("SECRET_KEY must be set in production!")
            secret_key = secrets.token_hex(32)
        
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret or jwt_secret == "your-jwt-secret-key-here-change-me":
            if self.app_env == "production":
                raise ValueError("JWT_SECRET_KEY must be set in production!")
            jwt_secret = secrets.token_hex(32)
        
        return SecurityConfig(
            secret_key=secret_key,
            jwt_secret_key=jwt_secret,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            jwt_access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            jwt_refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")),
            password_min_length=int(os.getenv("PASSWORD_MIN_LENGTH", "8")),
            password_require_uppercase=self._get_bool("PASSWORD_REQUIRE_UPPERCASE", True),
            password_require_lowercase=self._get_bool("PASSWORD_REQUIRE_LOWERCASE", True),
            password_require_digits=self._get_bool("PASSWORD_REQUIRE_DIGITS", True),
            password_require_special=self._get_bool("PASSWORD_REQUIRE_SPECIAL", True),
            rate_limit_enabled=self._get_bool("RATE_LIMIT_ENABLED", True),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
            api_key_expiry_days=int(os.getenv("API_KEY_EXPIRY_DAYS", "365")),
            session_max_age=int(os.getenv("SESSION_MAX_AGE", "86400")),
            cors_origins=self._get_list("CORS_ORIGINS", [])
        )
    
    def _load_logging_config(self) -> LoggingConfig:
        """Load logging configuration."""
        return LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "json"),
            output=os.getenv("LOG_OUTPUT", "both"),
            file_path=os.getenv("LOG_FILE_PATH", "./logs/veritas.log"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "10")),
            include_timestamp=self._get_bool("LOG_INCLUDE_TIMESTAMP", True),
            include_level=self._get_bool("LOG_INCLUDE_LEVEL", True),
            include_module=self._get_bool("LOG_INCLUDE_MODULE", True),
            include_function=self._get_bool("LOG_INCLUDE_FUNCTION", True)
        )
    
    def _load_monitoring_config(self) -> MonitoringConfig:
        """Load monitoring configuration."""
        return MonitoringConfig(
            metrics_enabled=self._get_bool("METRICS_ENABLED", True),
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            metrics_path=os.getenv("METRICS_PATH", "/metrics"),
            health_check_enabled=self._get_bool("HEALTH_CHECK_ENABLED", True),
            health_check_path=os.getenv("HEALTH_CHECK_PATH", "/health"),
            apm_enabled=self._get_bool("APM_ENABLED", False),
            apm_service_name=os.getenv("APM_SERVICE_NAME", "veritas"),
            apm_server_url=os.getenv("APM_SERVER_URL", ""),
            grafana_enabled=self._get_bool("GRAFANA_ENABLED", False),
            grafana_url=os.getenv("GRAFANA_URL", "")
        )
    
    def _load_backup_config(self) -> BackupConfig:
        """Load backup configuration."""
        return BackupConfig(
            enabled=self._get_bool("BACKUP_ENABLED", True),
            path=os.getenv("BACKUP_PATH", "./backups"),
            schedule=os.getenv("BACKUP_SCHEDULE", "0 2 * * *"),
            retention_days=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
            db_backup_enabled=self._get_bool("DB_BACKUP_ENABLED", True),
            db_backup_compression=self._get_bool("DB_BACKUP_COMPRESSION", True),
            file_backup_enabled=self._get_bool("FILE_BACKUP_ENABLED", True),
            remote_backup_enabled=self._get_bool("REMOTE_BACKUP_ENABLED", False),
            remote_backup_type=os.getenv("REMOTE_BACKUP_TYPE", "s3"),
            remote_backup_bucket=os.getenv("REMOTE_BACKUP_BUCKET", ""),
            remote_backup_region=os.getenv("REMOTE_BACKUP_REGION", "us-east-1")
        )
    
    def _load_agent_config(self) -> AgentConfig:
        """Load agent configuration."""
        return AgentConfig(
            max_concurrent_agents=int(os.getenv("MAX_CONCURRENT_AGENTS", "10")),
            timeout=int(os.getenv("AGENT_TIMEOUT", "300")),
            max_retries=int(os.getenv("AGENT_MAX_RETRIES", "3")),
            retry_delay=int(os.getenv("AGENT_RETRY_DELAY", "5")),
            quality_gate_min_score=float(os.getenv("QUALITY_GATE_MIN_SCORE", "0.7")),
            quality_gate_enabled=self._get_bool("QUALITY_GATE_ENABLED", True)
        )
    
    def _load_ollama_config(self) -> OllamaConfig:
        """Load Ollama configuration."""
        return OllamaConfig(
            enabled=self._get_bool("OLLAMA_ENABLED", True),
            api_url=os.getenv("OLLAMA_API_URL", "http://localhost:11434"),
            default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:latest"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "120")),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text"),
            embedding_dimension=int(os.getenv("OLLAMA_EMBEDDING_DIMENSION", "768"))
        )
    
    def _load_feature_flags(self) -> Dict[str, bool]:
        """Load feature flags."""
        return {
            "agent_orchestration": self._get_bool("FEATURE_AGENT_ORCHESTRATION", True),
            "quality_gates": self._get_bool("FEATURE_QUALITY_GATES", True),
            "streaming": self._get_bool("FEATURE_STREAMING", True),
            "monitoring": self._get_bool("FEATURE_MONITORING", True),
            "analytics": self._get_bool("FEATURE_ANALYTICS", False),
            "ai_insights": self._get_bool("FEATURE_AI_INSIGHTS", False),
            "multi_tenancy": self._get_bool("EXPERIMENTAL_MULTI_TENANCY", False),
            "graph_database": self._get_bool("EXPERIMENTAL_GRAPH_DATABASE", False),
            "vector_search": self._get_bool("EXPERIMENTAL_VECTOR_SEARCH", False)
        }
    
    def validate(self) -> List[str]:
        """
        Validate configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate secrets in production
        if self.app_env == "production":
            if not self.security.secret_key:
                errors.append("SECRET_KEY must be set in production")
            if not self.security.jwt_secret_key:
                errors.append("JWT_SECRET_KEY must be set in production")
            if not self.database.password:
                errors.append("DB_PASSWORD must be set in production")
        
        # Validate database configuration
        if self.database.type not in ("sqlite", "postgresql", "mysql"):
            errors.append(f"Unsupported database type: {self.database.type}")
        
        # Validate ports
        if not (1 <= self.port <= 65535):
            errors.append(f"Invalid PORT: {self.port}")
        if not (1 <= self.websocket_port <= 65535):
            errors.append(f"Invalid WEBSOCKET_PORT: {self.websocket_port}")
        
        # Validate log level
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.logging.level not in valid_levels:
            errors.append(f"Invalid LOG_LEVEL: {self.logging.level}")
        
        # Validate paths exist or can be created
        paths = [
            Path(self.logging.file_path).parent,
            Path(self.backup.path) if self.backup.enabled else None
        ]
        
        for path in paths:
            if path and not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create directory {path}: {str(e)}")
        
        return errors
    
    def summary(self) -> Dict[str, Any]:
        """
        Get configuration summary.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "app_env": self.app_env,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "debug": self.debug,
            "database_type": self.database.type,
            "redis_enabled": bool(self.redis.host),
            "security": {
                "rate_limiting": self.security.rate_limit_enabled,
                "cors_configured": bool(self.security.cors_origins)
            },
            "monitoring": {
                "metrics": self.monitoring.metrics_enabled,
                "health_check": self.monitoring.health_check_enabled,
                "apm": self.monitoring.apm_enabled
            },
            "backup": {
                "enabled": self.backup.enabled,
                "remote": self.backup.remote_backup_enabled
            },
            "features": self.feature_flags
        }


# Global configuration instance
_config_instance: Optional[ProductionConfig] = None


def get_config() -> ProductionConfig:
    """
    Get singleton configuration instance.
    
    Returns:
        ProductionConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ProductionConfig()
        
        # Validate on first load
        errors = _config_instance.validate()
        if errors:
            print("Configuration validation errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            if _config_instance.app_env == "production":
                sys.exit(1)
    
    return _config_instance


# Convenience function for testing
def reset_config():
    """Reset global configuration instance (for testing)."""
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # Test configuration loading
    print("=" * 80)
    print("VERITAS Production Configuration Test")
    print("=" * 80)
    print()
    
    # Set test environment to avoid production validation
    os.environ["APP_ENV"] = "development"
    
    config = get_config()
    
    print("Configuration Summary:")
    print("-" * 80)
    summary = config.summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
    print()
    
    print("Validation:")
    print("-" * 80)
    errors = config.validate()
    if errors:
        print("❌ Configuration has errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ Configuration is valid!")
    print()
    
    print("Database URL (masked):")
    print("-" * 80)
    db_url = config.database.url
    if config.database.password:
        db_url = db_url.replace(config.database.password, "***MASKED***")
    print(db_url)
    print()
    
    print("Redis URL (masked):")
    print("-" * 80)
    redis_url = config.redis.url
    if config.redis.password:
        redis_url = redis_url.replace(config.redis.password, "***MASKED***")
    print(redis_url)
    print()
    
    print("=" * 80)
    print("✅ Configuration test complete!")
    print("=" * 80)
