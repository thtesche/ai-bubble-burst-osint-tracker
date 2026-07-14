import os
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class LLMResponse:
    """Standardized response from any OpenAI-compatible API."""
    content: str
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.error is None


class LLMEngine:
    """
    OpenAI-compatible API client for LLM inference.

    Supports any API that follows the OpenAI chat completions format:
    - OpenAI (default)
    - Firecrawl (Atlantis) local instance
    - Ollama
    - Any OpenAI-compatible endpoint

    Configuration via environment variables:
    - LLM_API_KEY: API key for authentication
    - LLM_API_BASE_URL: Base URL (default: https://api.openai.com/v1)
    - LLM_MODEL: Model name (default: gpt-4o-mini)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("LLM_API_KEY", "")
        self.base_url = (
            base_url or os.getenv("LLM_API_BASE_URL", "")
            or "https://api.openai.com/v1"
        ).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout

        if not self.api_key:
            print("[!] WARNING: LLM_API_KEY not set — API may require one")

    def generate(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """
        Send a single prompt to the LLM and return the response.

        Args:
            prompt: The user message content.
            system_prompt: Optional system instruction.

        Returns:
            LLMResponse with content or error information.
        """

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        api_url = f"{self.base_url}/chat/completions"

        print(f"[*] Sending inference request to {api_url} (model: {self.model})...")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(api_url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text[:500]
                    return LLMResponse(
                        content="",
                        error=f"API error {response.status_code}: {error_text}",
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                print(f"[+] LLM inference successful (model: {self.model})")
                return LLMResponse(
                    content=content,
                    model=self.model,
                    usage=usage,
                )

        except httpx.TimeoutException:
            return LLMResponse(
                content="",
                error=f"API request timed out after {self.timeout}s",
            )
        except Exception as e:
            return LLMResponse(
                content="",
                error=f"Inference failed: {e}",
            )

    async def generate_async(
        self, prompt: str, system_prompt: str = ""
    ) -> LLMResponse:
        """Async version of generate()."""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        api_url = f"{self.base_url}/chat/completions"

        print(
            f"[*] Sending async inference request to {api_url} "
            f"(model: {self.model})..."
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    api_url, json=payload, headers=headers
                )

                if response.status_code != 200:
                    error_text = response.text[:500]
                    return LLMResponse(
                        content="",
                        error=f"API error {response.status_code}: {error_text}",
                    )

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                print(f"[+] LLM inference successful (model: {self.model})")
                return LLMResponse(
                    content=content,
                    model=self.model,
                    usage=usage,
                )

        except httpx.TimeoutException:
            return LLMResponse(
                content="",
                error=f"API request timed out after {self.timeout}s",
            )
        except Exception as e:
            return LLMResponse(
                content="",
                error=f"Inference failed: {e}",
            )
