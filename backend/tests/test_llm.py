"""
Tests for Scout LLM service integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.llm import ScoutLLMService, LLMConfig, LLMMessage


@pytest.fixture
def mock_config():
    """Create a mock LLM config"""
    config = LLMConfig()
    config.api_url = "https://test-api.example.com"
    config.access_token = "test-token"
    config.model = "gpt-5"
    return config


@pytest.fixture
def llm_service(mock_config):
    """Create an LLM service with mock config"""
    return ScoutLLMService(mock_config)


@pytest.mark.asyncio
async def test_health_check_not_configured():
    """Test health check when LLM is not configured"""
    config = LLMConfig()
    config.api_url = ""
    config.access_token = ""

    service = ScoutLLMService(config)
    result = await service.health_check()

    assert result["status"] == "not_configured"
    assert "not configured" in result["message"].lower()
    await service.close()


@pytest.mark.asyncio
async def test_health_check_success(llm_service, mock_config):
    """Test successful health check"""
    # Mock the HTTP client
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(llm_service.client, 'get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response

        result = await llm_service.health_check()

        assert result["status"] == "healthy"
        assert result["model"] == mock_config.model
        mock_get.assert_called_once_with(f"{mock_config.api_url}/health")

    await llm_service.close()


@pytest.mark.asyncio
async def test_chat_completion_not_configured():
    """Test chat completion when service is not configured"""
    config = LLMConfig()
    config.api_url = ""
    config.access_token = ""

    service = ScoutLLMService(config)

    messages = [LLMMessage(role="user", content="Hello")]

    with pytest.raises(ValueError, match="not configured"):
        await service.chat_completion(messages)

    await service.close()


@pytest.mark.asyncio
async def test_chat_completion_success(llm_service, mock_config):
    """Test successful chat completion"""
    messages = [LLMMessage(role="user", content="Hello")]

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! How can I help you?"
                }
            }
        ]
    }

    with patch.object(llm_service.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await llm_service.chat_completion(messages)

        assert "choices" in result
        assert result["choices"][0]["message"]["content"] == "Hello! How can I help you?"

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == f"{mock_config.api_url}/chat/completions"

        payload = call_args[1]["json"]
        assert payload["model"] == mock_config.model
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["content"] == "Hello"

    await llm_service.close()


@pytest.mark.asyncio
async def test_generate_text_simple(llm_service, mock_config):
    """Test simple text generation"""
    prompt = "What is the capital of France?"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "The capital of France is Paris."
                }
            }
        ]
    }

    with patch.object(llm_service.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await llm_service.generate_text(prompt)

        assert result == "The capital of France is Paris."

    await llm_service.close()


@pytest.mark.asyncio
async def test_generate_text_with_system_prompt(llm_service, mock_config):
    """Test text generation with system prompt"""
    system_prompt = "You are a helpful assistant."
    user_prompt = "Hello"

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hi there!"
                }
            }
        ]
    }

    with patch.object(llm_service.client, 'post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await llm_service.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt
        )

        assert result == "Hi there!"

        # Verify both system and user messages were sent
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == system_prompt
        assert payload["messages"][1]["role"] == "user"
        assert payload["messages"][1]["content"] == user_prompt

    await llm_service.close()


@pytest.mark.asyncio
async def test_config_is_configured():
    """Test LLMConfig.is_configured method"""
    # Configured
    config = LLMConfig()
    config.api_url = "https://api.example.com"
    config.access_token = "token"
    assert config.is_configured() is True

    # Not configured - missing URL
    config = LLMConfig()
    config.api_url = ""
    config.access_token = "token"
    assert config.is_configured() is False

    # Not configured - missing token
    config = LLMConfig()
    config.api_url = "https://api.example.com"
    config.access_token = ""
    assert config.is_configured() is False
