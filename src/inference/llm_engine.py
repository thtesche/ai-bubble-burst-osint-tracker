import os
import json
import re
import httpx
from typing import Optional, Dict, Any, AsyncIterator, Tuple
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

    async def generate_async(
        self, prompt: str, system_prompt: str = ""
    ) -> LLMResponse:
        """
        Non-streaming async LLM call. Returns a full LLMResponse.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        api_url = f"{self.base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(api_url, json=payload, headers=headers)

                if response.status_code != 200:
                    error_text = response.text[:500]
                    return LLMResponse(
                        content="",
                        model=self.model,
                        error=f"API error {response.status_code}: {error_text}"
                    )

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    return LLMResponse(
                        content="",
                        model=self.model,
                        error="No choices in API response"
                    )

                content = choices[0].get("message", {}).get("content", "")
                if content:
                    content = re.sub(r"<thinking>.*?</thinking>\s*", "", content, flags=re.DOTALL)
                
                usage = data.get("usage", {})

                return LLMResponse(
                    content=content or "",
                    model=self.model,
                    usage=usage,
                )

        except httpx.TimeoutException:
            return LLMResponse(
                content="",
                model=self.model,
                error=f"API request timed out after {self.timeout}s"
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                error=f"Request failed: {e}"
            )

    async def generate_stream_async(
        self, prompt: str, system_prompt: str = ""
    ) -> AsyncIterator[Tuple[str, str]]:
        """
        Streams the LLM response asynchronously chunk by chunk.
        
        Yields:
            Tuple[str, str]: ('thinking', token) or ('content', token)
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "stream": True,  # <-- Wichtig für Streaming!
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        api_url = f"{self.base_url}/chat/completions"

        try:
            # client.stream() statt client.post() nutzen
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", api_url, json=payload, headers=headers) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield "error", f"API error {response.status_code}: {error_text.decode()[:500]}"
                        return

                    # Zeile für Zeile den SSE-Stream auslesen
                    async for line in response.aiter_lines():
                        line = line.strip()
                        
                        if not line or not line.startswith("data: "):
                            continue
                        
                        # Das "data: " Präfix abschneiden
                        json_str = line[6:]
                        
                        if json_str == "[DONE]":
                            break
                            
                        try:
                            chunk = json.loads(json_str)
                            choices = chunk.get("choices", [])
                            if not choices:
                                continue
                                
                            delta = choices[0].get("delta", {})
                            
                            # 1. Thread: Thinking extrahieren (OpenAI / DeepSeek Standard)
                            if "reasoning_content" in delta and delta["reasoning_content"]:
                                yield "thinking", delta["reasoning_content"]
                                
                            # 2. Thread: Die eigentliche Antwort extrahieren
                            if "content" in delta and delta["content"]:
                                yield "content", delta["content"]
                                
                        except json.JSONDecodeError:
                            continue

        except httpx.TimeoutException:
            yield "error", f"API request timed out after {self.timeout}s"
        except Exception as e:
            yield "error", f"Streaming failed: {e}"