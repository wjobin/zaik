"""
Scout LLM API Integration
Provides interface for interacting with the Scout LLM service
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


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
            response = await self.client.post(
                f"{self.config.api_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise Exception(f"Scout LLM API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
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
        # This structure may need adjustment based on actual Scout API response format
        try:
            return response["choices"][0]["message"]["content"]
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
