"""
Base LLM Service

Provides common functionality for all LLM services.
Supports OpenAI (GPT-4), Anthropic (Claude), and Perplexity (Sonar).
"""

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"


@dataclass
class LLMConfig:
    """Configuration for LLM service."""
    provider: LLMProvider
    model: str
    api_key: str
    max_tokens: int = 4096
    temperature: float = 0.0  # Low temperature for deterministic output
    timeout: float = 60.0


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMAuthError(LLMError):
    """Authentication error."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMResponseError(LLMError):
    """Invalid response from LLM."""
    pass


class BaseLLMService(ABC):
    """
    Base class for LLM services.

    Handles common functionality:
    - API client initialization
    - Error handling
    - Response parsing
    - Token counting
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM service.

        Args:
            config: LLM configuration. If None, uses default from env.
        """
        self.config = config or self._get_default_config()
        self._client = None
        self._init_client()

    @abstractmethod
    def _get_default_config(self) -> LLMConfig:
        """Get default configuration for this service."""
        raise NotImplementedError

    def _init_client(self) -> None:
        """Initialize the appropriate API client."""
        if self.config.provider == LLMProvider.OPENAI:
            self._init_openai_client()
        elif self.config.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic_client()
        elif self.config.provider == LLMProvider.PERPLEXITY:
            self._init_perplexity_client()
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _init_openai_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            logger.info(f"OpenAI client initialized (model: {self.config.model})")
        except ImportError:
            raise LLMError("openai package not installed. Run: pip install openai")

    def _init_anthropic_client(self) -> None:
        """Initialize Anthropic client."""
        try:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            logger.info(f"Anthropic client initialized (model: {self.config.model})")
        except ImportError:
            raise LLMError("anthropic package not installed. Run: pip install anthropic")

    def _init_perplexity_client(self) -> None:
        """Initialize Perplexity client (uses OpenAI-compatible API)."""
        try:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url="https://api.perplexity.ai",
                timeout=self.config.timeout
            )
            logger.info(f"Perplexity client initialized (model: {self.config.model})")
        except ImportError:
            raise LLMError("openai package not installed. Run: pip install openai")

    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[dict] = None,
    ) -> dict[str, Any]:
        """
        Call the LLM and return parsed response.

        Args:
            system_prompt: System instructions
            user_prompt: User message with data
            response_format: Optional JSON schema for structured output

        Returns:
            Dict with:
                - content: Parsed response (dict if JSON, str otherwise)
                - tokens_input: Input token count
                - tokens_output: Output token count
                - model: Model used
        """
        if self.config.provider == LLMProvider.OPENAI:
            return await self._call_openai(system_prompt, user_prompt, response_format)
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(system_prompt, user_prompt)
        elif self.config.provider == LLMProvider.PERPLEXITY:
            return await self._call_perplexity(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Call OpenAI API."""
        try:
            kwargs = {
                "model": self.config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }

            # Add JSON response format for GPT-4 Strict Mode
            if response_format:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self._client.chat.completions.create(**kwargs)

            content = response.choices[0].message.content

            # Parse JSON if expected
            if response_format:
                try:
                    content = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")

            return {
                "content": content,
                "tokens_input": response.usage.prompt_tokens,
                "tokens_output": response.usage.completion_tokens,
                "model": self.config.model,
            }

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise LLMAuthError(f"OpenAI authentication failed: {e}")
            elif "429" in error_msg:
                raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
            else:
                raise LLMError(f"OpenAI API error: {e}")

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Anthropic API."""
        try:
            response = await self._client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )

            content = response.content[0].text

            # Try to parse as JSON
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass  # Keep as string

            return {
                "content": content,
                "tokens_input": response.usage.input_tokens,
                "tokens_output": response.usage.output_tokens,
                "model": self.config.model,
            }

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authentication" in error_msg.lower():
                raise LLMAuthError(f"Anthropic authentication failed: {e}")
            elif "429" in error_msg:
                raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}")
            else:
                raise LLMError(f"Anthropic API error: {e}")

    async def _call_perplexity(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> dict[str, Any]:
        """Call Perplexity API (OpenAI-compatible)."""
        try:
            response = await self._client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            content = response.choices[0].message.content

            # Try to parse as JSON
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass

            return {
                "content": content,
                "tokens_input": response.usage.prompt_tokens if response.usage else 0,
                "tokens_output": response.usage.completion_tokens if response.usage else 0,
                "model": self.config.model,
            }

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise LLMAuthError(f"Perplexity authentication failed: {e}")
            elif "429" in error_msg:
                raise LLMRateLimitError(f"Perplexity rate limit exceeded: {e}")
            else:
                raise LLMError(f"Perplexity API error: {e}")

    @staticmethod
    def get_openai_config() -> LLMConfig:
        """Get OpenAI configuration from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMAuthError("OPENAI_API_KEY not set")

        return LLMConfig(
            provider=LLMProvider.OPENAI,
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            api_key=api_key,
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
        )

    @staticmethod
    def get_anthropic_config() -> LLMConfig:
        """Get Anthropic configuration from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMAuthError("ANTHROPIC_API_KEY not set")

        return LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=api_key,
            max_tokens=4096,
        )

    @staticmethod
    def get_perplexity_config() -> LLMConfig:
        """Get Perplexity configuration from environment."""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            raise LLMAuthError("PERPLEXITY_API_KEY not set")

        return LLMConfig(
            provider=LLMProvider.PERPLEXITY,
            model=os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
            api_key=api_key,
            max_tokens=4096,
        )
