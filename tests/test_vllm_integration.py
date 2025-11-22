#!/usr/bin/env python3
"""
Test suite for vLLM integration in VERITAS

This test suite verifies:
1. vLLM client initialization and health checks
2. Model management and listing
3. Request/response handling
4. Pipeline integration
5. Factory pattern and provider switching

Author: VERITAS System
Date: 2025-11-22
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from backend.agents.veritas_vllm_client import (
    VeritasVLLMClient,
    VLLMRequest,
    VLLMResponse,
    VLLMModel
)
from backend.agents.veritas_llm_factory import (
    VeritasLLMFactory,
    LLMConfig,
    LLMProvider
)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def vllm_client():
    """Create a vLLM client for testing"""
    return VeritasVLLMClient(
        base_url="http://localhost:8000",
        timeout=30,
        max_retries=2
    )

@pytest.fixture
def mock_vllm_response():
    """Mock vLLM API response"""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from vLLM."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        }
    }

@pytest.fixture
def mock_models_response():
    """Mock vLLM models API response"""
    return {
        "object": "list",
        "data": [
            {
                "id": "meta-llama/Meta-Llama-3-8B-Instruct",
                "object": "model",
                "created": 1234567890,
                "owned_by": "meta"
            },
            {
                "id": "mistralai/Mistral-7B-Instruct-v0.3",
                "object": "model",
                "created": 1234567890,
                "owned_by": "mistralai"
            }
        ]
    }

# ============================================================================
# TEST VLLM CLIENT
# ============================================================================

class TestVeritasVLLMClient:
    """Test suite for VeritasVLLMClient"""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, vllm_client):
        """Test client initialization"""
        assert vllm_client.base_url == "http://localhost:8000"
        assert vllm_client.timeout == 30
        assert vllm_client.max_retries == 2
        assert not vllm_client.offline_mode
        assert vllm_client.default_model == VLLMModel.LLAMA3_8B.value
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, vllm_client):
        """Test successful health check"""
        with patch.object(vllm_client.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = await vllm_client.health_check()
            assert result is True
            mock_get.assert_called_once_with(f"{vllm_client.base_url}/v1/models")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, vllm_client):
        """Test failed health check"""
        with patch.object(vllm_client.client, 'get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            
            result = await vllm_client.health_check()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_load_available_models(self, vllm_client, mock_models_response):
        """Test loading available models"""
        with patch.object(vllm_client.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_models_response
            mock_get.return_value = mock_response
            
            models = await vllm_client.load_available_models()
            
            assert len(models) == 2
            assert "meta-llama/Meta-Llama-3-8B-Instruct" in models
            assert "mistralai/Mistral-7B-Instruct-v0.3" in models
            assert not vllm_client.offline_mode
    
    @pytest.mark.asyncio
    async def test_list_models(self, vllm_client, mock_models_response):
        """Test listing models for API"""
        with patch.object(vllm_client.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_models_response
            mock_get.return_value = mock_response
            
            models = await vllm_client.list_models()
            
            assert len(models) == 2
            assert models[0]["provider"] == "vllm"
            assert "name" in models[0]
            assert "size" in models[0]
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, vllm_client, mock_vllm_response):
        """Test successful response generation"""
        with patch.object(vllm_client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vllm_response
            mock_post.return_value = mock_response
            
            request = VLLMRequest(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                prompt="Test prompt",
                temperature=0.7,
                max_tokens=100
            )
            
            response = await vllm_client.generate_response(request)
            
            assert isinstance(response, VLLMResponse)
            assert response.response == "This is a test response from vLLM."
            assert response.model == "meta-llama/Meta-Llama-3-8B-Instruct"
            assert response.total_tokens == 18
            assert response.done is True
    
    @pytest.mark.asyncio
    async def test_generate_response_with_system_prompt(self, vllm_client, mock_vllm_response):
        """Test response generation with system prompt"""
        with patch.object(vllm_client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vllm_response
            mock_post.return_value = mock_response
            
            request = VLLMRequest(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                prompt="Test prompt",
                system="You are a helpful assistant.",
                temperature=0.7,
                max_tokens=100
            )
            
            response = await vllm_client.generate_response(request)
            
            # Verify system message was included in payload
            call_args = mock_post.call_args
            payload = call_args.kwargs['json']
            messages = payload['messages']
            
            assert len(messages) == 2
            assert messages[0]['role'] == 'system'
            assert messages[0]['content'] == 'You are a helpful assistant.'
            assert messages[1]['role'] == 'user'
    
    @pytest.mark.asyncio
    async def test_generate_response_retry_on_failure(self, vllm_client):
        """Test retry logic on failure"""
        with patch.object(vllm_client.client, 'post') as mock_post:
            # First two attempts fail, third succeeds
            mock_post.side_effect = [
                Exception("Connection error"),
                Exception("Timeout"),
            ]
            
            request = VLLMRequest(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                prompt="Test prompt"
            )
            
            response = await vllm_client.generate_response(request)
            
            # Should return error response after retries
            assert "Error" in response.response
            assert response.confidence_score == 0.0
            assert mock_post.call_count == 2  # max_retries
    
    @pytest.mark.asyncio
    async def test_statistics_tracking(self, vllm_client, mock_vllm_response):
        """Test statistics tracking"""
        with patch.object(vllm_client.client, 'post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_vllm_response
            mock_post.return_value = mock_response
            
            request = VLLMRequest(
                model="meta-llama/Meta-Llama-3-8B-Instruct",
                prompt="Test prompt"
            )
            
            await vllm_client.generate_response(request)
            
            stats = vllm_client.get_client_statistics()
            assert stats['usage_stats']['requests_sent'] == 1
            assert stats['usage_stats']['requests_successful'] == 1
            assert stats['usage_stats']['total_tokens'] == 18
            assert stats['usage_stats']['prompt_tokens'] == 10
            assert stats['usage_stats']['completion_tokens'] == 8

# ============================================================================
# TEST LLM FACTORY
# ============================================================================

class TestVeritasLLMFactory:
    """Test suite for VeritasLLMFactory"""
    
    @pytest.mark.asyncio
    async def test_create_vllm_client(self):
        """Test creating vLLM client via factory"""
        config = LLMConfig(
            provider=LLMProvider.VLLM,
            base_url="http://localhost:8000",
            default_model="meta-llama/Meta-Llama-3-8B-Instruct",
            timeout=30
        )
        
        with patch('backend.agents.veritas_vllm_client.VeritasVLLMClient.initialize') as mock_init:
            mock_init.return_value = True
            
            client = await VeritasLLMFactory.create_client(config=config)
            
            assert client.__class__.__name__ == "VeritasVLLMClient"
            assert client.base_url == "http://localhost:8000"
            assert client.default_model == "meta-llama/Meta-Llama-3-8B-Instruct"
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_create_ollama_client(self):
        """Test creating Ollama client via factory"""
        config = LLMConfig(
            provider=LLMProvider.OLLAMA,
            base_url="http://localhost:11434",
            default_model="llama3.2:latest",
            timeout=30
        )
        
        with patch('backend.agents.veritas_ollama_client.VeritasOllamaClient.initialize') as mock_init:
            mock_init.return_value = True
            
            client = await VeritasLLMFactory.create_client(config=config)
            
            assert client.__class__.__name__ == "VeritasOllamaClient"
            assert client.base_url == "http://localhost:11434"
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_create_client_from_env(self):
        """Test creating client from environment variables"""
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'vllm',
            'VLLM_API_URL': 'http://test-vllm:8000',
            'VLLM_DEFAULT_MODEL': 'test-model'
        }):
            with patch('backend.agents.veritas_vllm_client.VeritasVLLMClient.initialize') as mock_init:
                mock_init.return_value = True
                
                client = await VeritasLLMFactory.create_client()
                
                assert client.__class__.__name__ == "VeritasVLLMClient"
                assert client.base_url == "http://test-vllm:8000"
                
                await client.close()
    
    @pytest.mark.asyncio
    async def test_create_client_with_fallback(self):
        """Test creating client with automatic fallback"""
        with patch('backend.agents.veritas_vllm_client.VeritasVLLMClient.initialize') as mock_vllm_init:
            with patch('backend.agents.veritas_ollama_client.VeritasOllamaClient.initialize') as mock_ollama_init:
                # vLLM initialization fails
                mock_vllm_init.return_value = False
                # Ollama initialization succeeds
                mock_ollama_init.return_value = True
                
                # Mock offline_mode property
                with patch('backend.agents.veritas_vllm_client.VeritasVLLMClient.offline_mode', True):
                    with patch('backend.agents.veritas_ollama_client.VeritasOllamaClient.offline_mode', False):
                        client = await VeritasLLMFactory.create_client_with_fallback(
                            primary_provider="vllm",
                            fallback_provider="ollama"
                        )
                        
                        # Should fall back to Ollama
                        assert client.__class__.__name__ == "VeritasOllamaClient"
                        
                        await client.close()

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestVLLMIntegration:
    """Integration tests for vLLM (requires running vLLM server)"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_vllm_connection(self):
        """Test real connection to vLLM server (skip if not available)"""
        client = VeritasVLLMClient(base_url="http://localhost:8000")
        
        try:
            health = await client.health_check()
            if not health:
                pytest.skip("vLLM server not available")
            
            # Test model listing
            models = await client.list_models()
            assert len(models) > 0
            
            # Test simple query
            request = VLLMRequest(
                model=client.default_model,
                prompt="Say 'Hello, VERITAS!' in one sentence.",
                max_tokens=50,
                temperature=0.7
            )
            
            response = await client.generate_response(request)
            assert len(response.response) > 0
            assert response.total_tokens is not None
            
        finally:
            await client.close()

# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
