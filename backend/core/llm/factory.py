#!/usr/bin/env python3
"""
VERITAS LLM FACTORY
===================

Unified factory for LLM client creation supporting multiple providers:
- Ollama (local, self-hosted)
- vLLM (high-performance inference server)

This factory allows seamless switching between LLM providers based on
configuration, making the system flexible and provider-agnostic.

Features:
- Provider-agnostic interface
- Configuration-based provider selection
- Health checking and automatic fallback
- Unified API across providers

Author: VERITAS System
Date: 2025-11-22
Version: 1.0
"""

import os
import logging
from enum import Enum
from typing import Optional, Union, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# LLM PROVIDER TYPES
# ============================================================================

class LLMProvider(Enum):
    """Supported LLM Provider Types"""
    OLLAMA = "ollama"
    VLLM = "vllm"

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    base_url: str
    api_key: Optional[str] = None
    default_model: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    
    @classmethod
    def from_env(cls, provider: Optional[str] = None) -> "LLMConfig":
        """
        Create LLM configuration from environment variables
        
        Args:
            provider: Override provider (otherwise from env)
            
        Returns:
            LLMConfig instance
        """
        # Determine provider
        provider_str = provider or os.getenv("LLM_PROVIDER", "ollama")
        llm_provider = LLMProvider(provider_str.lower())
        
        # Get configuration based on provider
        if llm_provider == LLMProvider.OLLAMA:
            base_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            default_model = os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.2:latest")
            api_key = None
            timeout = int(os.getenv("OLLAMA_TIMEOUT", "120"))
        elif llm_provider == LLMProvider.VLLM:
            base_url = os.getenv("VLLM_API_URL", "http://localhost:8000")
            default_model = os.getenv("VLLM_DEFAULT_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
            api_key = os.getenv("VLLM_API_KEY")
            timeout = int(os.getenv("VLLM_TIMEOUT", "120"))
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")
        
        max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        
        return cls(
            provider=llm_provider,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            timeout=timeout,
            max_retries=max_retries
        )

# ============================================================================
# LLM FACTORY
# ============================================================================

class VeritasLLMFactory:
    """
    Factory for creating LLM clients with provider abstraction
    
    Usage:
        # Using environment configuration
        client = await VeritasLLMFactory.create_client()
        
        # Using specific provider
        client = await VeritasLLMFactory.create_client(provider="vllm")
        
        # Using custom configuration
        config = LLMConfig(
            provider=LLMProvider.VLLM,
            base_url="http://my-vllm-server:8000",
            default_model="my-model"
        )
        client = await VeritasLLMFactory.create_client(config=config)
    """
    
    @staticmethod
    async def create_client(
        provider: Optional[str] = None,
        config: Optional[LLMConfig] = None,
        **kwargs
    ) -> Union["VeritasOllamaClient", "VeritasVLLMClient"]:
        """
        Create an LLM client based on configuration
        
        Args:
            provider: Provider name ("ollama" or "vllm"), overrides config/env
            config: LLMConfig instance, overrides env
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            LLM client instance (Ollama or vLLM)
        """
        # Determine configuration
        if config is None:
            config = LLMConfig.from_env(provider=provider)
        
        # Import clients here to avoid circular imports
        from backend.agents.veritas_ollama_client import VeritasOllamaClient
        from backend.agents.veritas_vllm_client import VeritasVLLMClient
        
        # Create client based on provider
        if config.provider == LLMProvider.OLLAMA:
            logger.info(f"🤖 Creating Ollama client: {config.base_url}")
            client = VeritasOllamaClient(
                base_url=config.base_url,
                timeout=config.timeout,
                max_retries=config.max_retries,
                **kwargs
            )
            if config.default_model:
                client.default_model = config.default_model
            
        elif config.provider == LLMProvider.VLLM:
            logger.info(f"🤖 Creating vLLM client: {config.base_url}")
            client = VeritasVLLMClient(
                base_url=config.base_url,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=config.max_retries,
                **kwargs
            )
            if config.default_model:
                client.default_model = config.default_model
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
        
        # Initialize client
        await client.initialize()
        
        return client
    
    @staticmethod
    async def create_client_with_fallback(
        primary_provider: Optional[str] = None,
        fallback_provider: Optional[str] = None
    ) -> Union["VeritasOllamaClient", "VeritasVLLMClient"]:
        """
        Create an LLM client with automatic fallback
        
        Tries primary provider first, falls back to secondary if unavailable
        
        Args:
            primary_provider: Primary provider to try ("ollama" or "vllm")
            fallback_provider: Fallback provider if primary fails
            
        Returns:
            LLM client instance
        """
        # Default providers
        if primary_provider is None:
            primary_provider = os.getenv("LLM_PROVIDER", "ollama")
        if fallback_provider is None:
            fallback_provider = "ollama" if primary_provider == "vllm" else "vllm"
        
        # Try primary provider
        try:
            logger.info(f"🔄 Trying primary LLM provider: {primary_provider}")
            client = await VeritasLLMFactory.create_client(provider=primary_provider)
            
            # Check if initialized successfully
            if not client.offline_mode:
                logger.info(f"✅ Primary provider {primary_provider} is available")
                return client
            else:
                logger.warning(f"⚠️ Primary provider {primary_provider} is offline")
        except Exception as e:
            logger.warning(f"⚠️ Primary provider {primary_provider} failed: {e}")
        
        # Try fallback provider
        try:
            logger.info(f"🔄 Trying fallback LLM provider: {fallback_provider}")
            client = await VeritasLLMFactory.create_client(provider=fallback_provider)
            
            if not client.offline_mode:
                logger.info(f"✅ Fallback provider {fallback_provider} is available")
                return client
            else:
                logger.error(f"❌ Fallback provider {fallback_provider} is also offline")
        except Exception as e:
            logger.error(f"❌ Fallback provider {fallback_provider} failed: {e}")
        
        # Both providers failed, return primary in offline mode
        logger.warning("⚠️ All providers failed, returning offline client")
        return await VeritasLLMFactory.create_client(provider=primary_provider)

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def get_llm_client(provider: Optional[str] = None) -> Union["VeritasOllamaClient", "VeritasVLLMClient"]:
    """
    Convenience function to get an LLM client
    
    Args:
        provider: Optional provider override
        
    Returns:
        LLM client instance
    """
    return await VeritasLLMFactory.create_client(provider=provider)

async def get_llm_client_with_fallback() -> Union["VeritasOllamaClient", "VeritasVLLMClient"]:
    """
    Convenience function to get an LLM client with automatic fallback
    
    Returns:
        LLM client instance
    """
    return await VeritasLLMFactory.create_client_with_fallback()

# ============================================================================
# TESTING
# ============================================================================

async def main():
    """Test the LLM factory"""
    import asyncio
    
    print("🧪 Testing VERITAS LLM Factory")
    print("=" * 50)
    
    # Test 1: Create client from environment
    print("\n📋 Test 1: Create client from environment")
    try:
        client = await get_llm_client()
        print(f"✅ Created {client.__class__.__name__}")
        print(f"   Provider: {client.get_client_statistics()['client_info'].get('provider', 'ollama')}")
        print(f"   Base URL: {client.base_url}")
        print(f"   Default Model: {client.default_model}")
        await client.close()
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Create vLLM client explicitly
    print("\n📋 Test 2: Create vLLM client explicitly")
    try:
        config = LLMConfig(
            provider=LLMProvider.VLLM,
            base_url="http://localhost:8000",
            default_model="meta-llama/Meta-Llama-3-8B-Instruct"
        )
        client = await VeritasLLMFactory.create_client(config=config)
        print(f"✅ Created {client.__class__.__name__}")
        print(f"   Available models: {len(client.available_models)}")
        await client.close()
    except Exception as e:
        print(f"⚠️ Failed (expected if vLLM not running): {e}")
    
    # Test 3: Create with automatic fallback
    print("\n📋 Test 3: Create with automatic fallback")
    try:
        client = await get_llm_client_with_fallback()
        print(f"✅ Created {client.__class__.__name__} with fallback")
        stats = client.get_client_statistics()
        print(f"   Offline mode: {stats['status']['offline_mode']}")
        await client.close()
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n✅ LLM Factory tests complete")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
