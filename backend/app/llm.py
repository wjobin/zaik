"""
Scout LLM API Integration
Provides interface for interacting with the Scout LLM service
"""

import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load .env file - check both /app/.env (Docker) and local .env
load_dotenv("/app/.env")
load_dotenv()  # Fallback to default behavior


class LLMMessage(BaseModel):
    """Represents a message in the conversation"""
    role: str  # 'user', 'assistant', or 'system'
    content: str


class LLMConfig:
    """Scout LLM API configuration"""
    def __init__(self):
        self.api_url = os.getenv("SCOUT_API_URL", "")
        self.access_token = os.getenv("SCOUT_API_ACCESS_TOKEN", "")
        self.model = os.getenv("SCOUT_MODEL", "gpt-5")

    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return bool(self.api_url and self.access_token)


class ScoutLLMService:
    """Service for interacting with Scout LLM API"""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        logger.info(f"Initializing Scout LLM Service")
        logger.info(f"API URL: {self.config.api_url}")
        logger.info(f"Model: {self.config.model}")
        logger.info(f"Token configured: {bool(self.config.access_token)}")
        logger.info(f"Token length: {len(self.config.access_token) if self.config.access_token else 0}")

        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json"
            }
        )

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the Scout LLM API is accessible and configured
        Returns status information about the LLM service
        """
        if not self.config.is_configured():
            return {
                "status": "not_configured",
                "message": "Scout LLM API credentials not configured"
            }

        try:
            # Try a simple health check or minimal request
            # This is a placeholder - adjust based on actual Scout API
            # Use a short timeout for health checks to avoid hanging
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.config.api_url}/health",
                    headers={"Authorization": f"Bearer {self.config.access_token}"}
                )

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "model": self.config.model
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"API returned status {response.status_code}"
                    }
        except (httpx.ConnectError, httpx.TimeoutException):
            return {
                "status": "unreachable",
                "message": "Cannot connect to Scout LLM API"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}"
            }

    async def chat_completion(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to Scout LLM

        Args:
            messages: List of conversation messages
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Dict containing the response from the LLM
        """
        if not self.config.is_configured():
            raise ValueError("Scout LLM API is not configured")

        # Prepare request payload
        # This structure may need adjustment based on actual Scout API spec
        payload = {
            "model": self.config.model,
            "messages": [msg.model_dump() for msg in messages],
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        try:
            # Scout API endpoint (singular 'completion' not 'completions')
            url = f"{self.config.api_url}/api/chat/completion"
            print(f">>> LLM Request: POST {url}")
            print(f">>> LLM Payload: {payload}")

            response = await self.client.post(url, json=payload)

            print(f">>> LLM Response Status: {response.status_code}")
            print(f">>> LLM Response Headers: {dict(response.headers)}")

            response_text = response.text
            print(f">>> LLM Response Body Length: {len(response_text)}")
            print(f">>> LLM Response Body: {response_text[:1000]}")  # First 1000 chars

            response.raise_for_status()

            if not response_text:
                raise Exception("Empty response body from Scout LLM API")

            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP Error: Status {e.response.status_code}")
            logger.error(f"LLM Error Response: {e.response.text}")
            raise Exception(f"Scout LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"LLM Request Failed: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to complete chat request: {str(e)}")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Simplified interface for generating text from a single prompt

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt to set context
            temperature: Controls randomness
            max_tokens: Maximum tokens in response

        Returns:
            Generated text string
        """
        messages = []

        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        messages.append(LLMMessage(role="user", content=prompt))

        response = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract the generated text from response
        # Scout API uses "messages" array, not "choices" like OpenAI
        try:
            # Scout API format: {"messages": [{"content": "...", "role": "assistant"}]}
            if "messages" in response and len(response["messages"]) > 0:
                return response["messages"][0]["content"]
            # Fallback to OpenAI format if needed
            elif "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Unexpected response structure: {response}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected response format from Scout LLM: {e}")


# Global service instance
_llm_service: Optional[ScoutLLMService] = None


def get_llm_service() -> ScoutLLMService:
    """Get or create the global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = ScoutLLMService()
    return _llm_service


async def close_llm_service():
    """Close the global LLM service instance"""
    global _llm_service
    if _llm_service is not None:
        await _llm_service.close()
        _llm_service = None
