"""
Perplexity API Client

Official Perplexity Sonar client for L4 Analytics with real-time context.
Uses online models for up-to-date market insights and citations.

API Docs: https://docs.perplexity.ai/reference/post_chat_completions
"""

import json
import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# API Configuration
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
# Модели: sonar (базовый), sonar-pro (продвинутый)
DEFAULT_MODEL = "sonar"
TIMEOUT_SECONDS = 120


class PerplexityClient:
    """
    Perplexity Sonar API client for analytics insights.

    Features:
    - Real-time web search integration
    - Citation support
    - Online models for current data
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize Perplexity client.

        Args:
            api_key: API key (defaults to env PERPLEXITY_API_KEY)
            model: Model to use (defaults to sonar-large-128k-online)
        """
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.model = model or os.getenv("PERPLEXITY_MODEL", DEFAULT_MODEL)

        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not configured")

        self._client = httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        logger.info(f"PerplexityClient initialized with model: {self.model}")

    async def generate_insights(
        self,
        normalized_data: dict[str, Any],
        context: Optional[str] = None,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """
        Generate analytics insights from normalized data.

        Args:
            normalized_data: Unified analytics data (GA4 + Metrika merged)
            context: Additional context for analysis
            temperature: Response creativity (0.0-1.0, lower = more factual)

        Returns:
            Dict with insights and citations
        """
        # Build analysis prompt
        system_prompt = """You are a senior marketing analytics expert. Analyze the provided unified web analytics data and generate actionable insights.

ANALYSIS REQUIREMENTS:
1. Focus on conversion optimization opportunities
2. Identify traffic quality issues
3. Spot anomalies and trends
4. Provide specific, actionable recommendations
5. Include relevant market context from your knowledge

OUTPUT FORMAT (JSON):
{
  "summary": "2-3 sentence executive summary",
  "anomalies": [
    {"metric": "...", "value": ..., "expected": ..., "severity": "HIGH/MEDIUM/LOW", "action": "..."}
  ],
  "opportunities": [
    {"area": "...", "potential_impact": "...", "effort": "LOW/MEDIUM/HIGH", "recommendation": "..."}
  ],
  "ads_recommendations": [
    {"platform": "...", "current_issue": "...", "recommendation": "...", "expected_result": "..."}
  ],
  "landing_issues": [
    {"page": "...", "issue": "...", "fix": "...", "priority": 1-5}
  ],
  "traffic_analysis": {
    "quality_score": 0-100,
    "best_sources": [...],
    "worst_sources": [...],
    "recommendations": [...]
  },
  "market_context": "Brief relevant market insights based on your knowledge"
}

Return ONLY valid JSON."""

        user_message = f"""Analyze this unified analytics data:

{json.dumps(normalized_data, indent=2, ensure_ascii=False)}

{f'Additional context: {context}' if context else ''}

Generate comprehensive insights following the JSON format."""

        try:
            response = await self._client.post(
                PERPLEXITY_API_URL,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": temperature,
                    "max_tokens": 4096,
                },
            )

            response.raise_for_status()
            data = response.json()

            # Extract content
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            # Parse JSON from response
            try:
                # Try to extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                insights = json.loads(content.strip())
            except json.JSONDecodeError:
                insights = {"raw_response": content, "parse_error": True}

            # Add metadata
            usage = data.get("usage", {})

            return {
                "insights": insights,
                "model": self.model,
                "tokens_input": usage.get("prompt_tokens", 0),
                "tokens_output": usage.get("completion_tokens", 0),
                "citations": data.get("citations", []),  # Perplexity provides citations
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Perplexity request failed: {e}")
            raise

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Generic chat completion with Perplexity.

        Args:
            messages: List of message dicts with role/content
            temperature: Response creativity
            max_tokens: Maximum response tokens

        Returns:
            Response dict with content and metadata
        """
        try:
            response = await self._client.post(
                PERPLEXITY_API_URL,
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()
            data = response.json()

            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return {
                "content": content,
                "model": self.model,
                "tokens_input": usage.get("prompt_tokens", 0),
                "tokens_output": usage.get("completion_tokens", 0),
                "citations": data.get("citations", []),
            }

        except Exception as e:
            logger.error(f"Perplexity chat failed: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Perplexity API is accessible."""
        try:
            response = await self._client.post(
                PERPLEXITY_API_URL,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": "ping"}],
                    "max_tokens": 5,
                },
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Perplexity health check failed: {e}")
            return False

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


# Convenience function
async def get_perplexity_insights(
    data: dict[str, Any],
    context: Optional[str] = None,
) -> dict[str, Any]:
    """
    Quick function to get insights from Perplexity.

    Args:
        data: Analytics data to analyze
        context: Optional additional context

    Returns:
        Insights dict
    """
    async with PerplexityClient() as client:
        return await client.generate_insights(data, context)
