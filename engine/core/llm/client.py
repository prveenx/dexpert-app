# FILE: core/llm/client.py
"""
Production LLM Client powered by LiteLLM.

Adapted from PCAgent MAF prototype. Provides:
  - Async generation with retries
  - Streaming support for real-time responses
  - Provider-agnostic caching (Gemini/Anthropic/OpenAI)
  - Multimodal (Vision) payload construction
"""

import os
import json
import time
import asyncio
import logging
from typing import List, Dict, Optional, Any, Union, Callable, Awaitable, AsyncGenerator

import litellm
from litellm import acompletion

# Silence LiteLLM verbose logging
litellm.suppress_debug_info = True
litellm.set_verbose = False
litellm.drop_params = True

_lite_logger = logging.getLogger("LiteLLM")
_lite_logger.setLevel(logging.CRITICAL)
_lite_logger.propagate = False

log = logging.getLogger(__name__)


class LLMClient:
    """Production-grade Async LLM Client with streaming."""

    def __init__(
        self,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 8192,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        agent_name: str = "Unknown",
        session_id: Optional[str] = None,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_base = api_base
        self.agent_name = agent_name
        self.session_id = session_id

        log.info(f"LLMClient initialized: model={self.model}, agent={self.agent_name}")

    async def generate(
        self,
        system: Optional[str] = None,
        messages: List[Dict[str, Any]] = [],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> str:
        """Non-streaming generation. Returns full response text."""
        payload = self._build_payload(system, messages)

        kwargs: Dict[str, Any] = {
            "model": model or self.model,
            "messages": payload,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        attempts = 0
        while attempts < 5:
            try:
                response = await acompletion(**kwargs, timeout=60.0)

                content = response.choices[0].message.content
                if not content or not content.strip():
                    raise ValueError("Empty response from LLM")

                log.debug(
                    f"LLM [{self.agent_name}] generated {len(content)} chars "
                    f"with model={kwargs['model']}"
                )
                return str(content)

            except Exception as e:
                attempts += 1
                wait_time = min(attempts * 5, 30)

                log.error(
                    f"LLM [{self.agent_name}] attempt {attempts} failed: {e}",
                    exc_info=attempts <= 1,
                )

                if attempts >= 5:
                    raise RuntimeError(
                        f"LLM generation failed after {attempts} attempts: {e}"
                    ) from e

                await asyncio.sleep(wait_time)
        
        raise RuntimeError(f"LLM [{self.agent_name}] failed to generate content")

    async def stream(
        self,
        system: Optional[str] = None,
        messages: List[Dict[str, Any]] = [],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Streaming generation. Yields text chunks as they arrive."""
        payload = self._build_payload(system, messages)

        kwargs: Dict[str, Any] = {
            "model": model or self.model,
            "messages": payload,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": True,
        }

        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base

        attempts = 0
        while True:
            try:
                response = await acompletion(**kwargs, timeout=60.0)

                async for chunk in response:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, "content") and delta.content:
                        yield delta.content

                return  # Successful stream complete

            except Exception as e:
                attempts += 1
                wait_time = min(attempts * 5, 30)

                log.error(
                    f"LLM stream [{self.agent_name}] attempt {attempts} failed: {e}"
                )

                if attempts >= 3:
                    raise RuntimeError(
                        f"LLM streaming failed after {attempts} attempts: {e}"
                    ) from e

                await asyncio.sleep(wait_time)

    async def generate_with_image(
        self,
        system: str,
        prompt: str,
        image_base64: str,
        image_type: str = "image/png",
        max_tokens: Optional[int] = None,
    ) -> str:
        """Multimodal generation with image input."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_type};base64,{image_base64}",
                        },
                    },
                ],
            }
        ]

        return await self.generate(
            system=system,
            messages=messages,
            max_tokens=max_tokens or 2048,
        )

    def _build_payload(
        self, system: Optional[str], messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build the message payload with optional system prompt."""
        payload = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend(messages)
        return payload
