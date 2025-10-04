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

    async def generate_image(
        self,
        prompt: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        max_wait_time: int = 60
    ) -> str:
        """
        NOTE: Scout image generation API currently not fully supported via async job pattern.
        The /protected/ endpoints require browser authentication and /api/async_jobs endpoints
        are not publicly documented. This method will raise an exception until we have proper
        API documentation or webhook support.
        """
        """
        Generate an image using Scout's image generation API (async job pattern)

        Args:
            prompt: The image generation prompt
            model: Image model to use (dall-e-3, dall-e-2, etc.)
            size: Image size (1024x1024, 512x512, etc.)
            quality: Image quality (standard, hd)
            max_wait_time: Maximum time to wait for job completion (seconds)

        Returns:
            Base64-encoded image data
        """
        if not self.config.is_configured():
            raise ValueError("Scout LLM API is not configured")

        payload = {
            "prompt": prompt,
            "aspect_ratio": "landscape",
            "model": "black-forest-labs/flux-schnell"
        }

        try:
            # Step 1: Submit image generation job
            url = f"{self.config.api_url}/api/image/generate"
            logger.info(f"Submitting image generation for prompt: {prompt[:100]}...")

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            # Extract job URL from response
            # Expected format: {"run_protected_url": "/protected/async_jobs/{job_id}/run.json"}
            if "run_protected_url" not in result:
                raise Exception(f"No job URL in response: {result}")

            # Convert protected URL to API URL
            # /protected/async_jobs/{id}/run.json -> /api/async_jobs/{id}
            protected_url = result['run_protected_url']
            logger.info(f"Received protected URL: {protected_url}")

            # Try to extract job ID and use API endpoint instead
            import re
            match = re.search(r'/async_jobs/([^/]+)', protected_url)
            if match:
                job_id = match.group(1)
                job_url = f"{self.config.api_url}/api/async_jobs/{job_id}"
                logger.info(f"Converted to API URL: {job_url}")
            else:
                # Fallback to protected URL (may not work)
                job_url = f"{self.config.api_url}{protected_url}"
                logger.warning(f"Could not extract job ID, using protected URL: {job_url}")

            # Step 2: Poll the job until completion
            import asyncio
            import time
            start_time = time.time()
            poll_interval = 2  # seconds

            while time.time() - start_time < max_wait_time:
                await asyncio.sleep(poll_interval)

                job_response = await self.client.get(job_url)
                logger.info(f"Job poll response status: {job_response.status_code}")
                logger.info(f"Job poll response headers: {dict(job_response.headers)}")
                logger.info(f"Job poll response body (first 500 chars): {job_response.text[:500]}")

                job_response.raise_for_status()

                # Check content type before parsing JSON
                content_type = job_response.headers.get('content-type', '')
                if 'application/json' not in content_type:
                    logger.error(f"Unexpected content type: {content_type}")
                    logger.error(f"Response body: {job_response.text[:1000]}")
                    raise Exception(f"Job endpoint returned non-JSON response (content-type: {content_type})")

                job_data = job_response.json()

                logger.info(f"Job status: {job_data.get('status', 'unknown')}")

                # Check if job is complete
                if job_data.get("status") == "completed":
                    # Extract image URL or data from completed job
                    if "result" in job_data:
                        result_data = job_data["result"]

                        # Handle different response formats
                        if "data" in result_data and len(result_data["data"]) > 0:
                            image_data = result_data["data"][0]

                            if "b64_json" in image_data:
                                return image_data["b64_json"]
                            elif "url" in image_data:
                                # Fetch image from URL and convert to base64
                                img_response = await self.client.get(image_data["url"])
                                img_response.raise_for_status()
                                import base64
                                return base64.b64encode(img_response.content).decode('utf-8')

                        elif "url" in result_data:
                            # Direct URL in result
                            img_response = await self.client.get(result_data["url"])
                            img_response.raise_for_status()
                            import base64
                            return base64.b64encode(img_response.content).decode('utf-8')

                        else:
                            raise Exception(f"Unexpected result format: {result_data}")
                    else:
                        raise Exception(f"No result in completed job: {job_data}")

                elif job_data.get("status") == "failed":
                    error_msg = job_data.get("error", "Unknown error")
                    raise Exception(f"Image generation failed: {error_msg}")

            raise Exception(f"Image generation timed out after {max_wait_time} seconds")

        except httpx.HTTPStatusError as e:
            logger.error(f"Image Generation HTTP Error: Status {e.response.status_code}")
            logger.error(f"Error Response: {e.response.text}")
            raise Exception(f"Scout Image API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            logger.error(f"Image Generation Failed: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")


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
