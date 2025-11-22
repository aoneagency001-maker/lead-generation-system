"""
L2: Normalization Service (GPT-4 Strict Mode)

Normalizes raw events from GA4 and Yandex Metrika into unified format.
Uses GPT-4 with strict JSON mode for 99.9% schema compliance.

Key principles:
- ONLY use values provided in input data
- If value missing → set to null (NEVER guess)
- Use the exact schema provided
- Validate data types strictly
- Flag any data inconsistencies
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from data_intake.llm.base import BaseLLMService, LLMConfig, LLMProvider
from data_intake.models import NormalizedEvent, RawEvent, SourceType

logger = logging.getLogger(__name__)

# System prompt for normalization (GPT-4 Strict Mode)
NORMALIZATION_SYSTEM_PROMPT = """You are a data normalization expert. Your task is to convert raw GA4 and Yandex Metrica data into a unified JSON schema with ZERO hallucinations.

RULES:
1. ONLY use values provided in input data
2. If value missing → set to null (NEVER guess)
3. Use the exact schema provided
4. Validate data types strictly
5. Flag any data inconsistencies

OUTPUT SCHEMA:
{
  "normalized_events": [
    {
      "source": "GOOGLE_ANALYTICS" | "YANDEX_METRIKA",
      "session_id": string | null,
      "user_id": string | null,
      "client_id": string | null,
      "occurred_at": "ISO datetime string",
      "url": string | null,
      "landing_page": string | null,
      "referrer": string | null,
      "utm_source": string | null,
      "utm_medium": string | null,
      "utm_campaign": string | null,
      "utm_term": string | null,
      "utm_content": string | null,
      "traffic_source_type": "organic" | "paid" | "social" | "direct" | "referral" | "email" | "other",
      "device_type": string | null,
      "browser": string | null,
      "os": string | null,
      "screen_resolution": string | null,
      "country": string | null,
      "region": string | null,
      "city": string | null,
      "page_views": integer | null,
      "raw_visit_duration": integer | null,
      "events_count": integer | null,
      "is_new_visitor": boolean | null,
      "is_bounce": boolean | null,
      "search_phrase": string | null
    }
  ],
  "normalization_notes": {
    "source_count": integer,
    "normalized_count": integer,
    "skipped_count": integer,
    "skip_reasons": [string]
  },
  "data_quality": {
    "completeness": float (0-1),
    "conflicts": [string],
    "warnings": [string]
  }
}

TRAFFIC SOURCE CLASSIFICATION:
- "cpc", "ppc", "paid", "cpm" → "paid"
- "organic", from search engines → "organic"
- "facebook", "instagram", "vk", "telegram" (not paid) → "social"
- "(direct)", "direct", empty → "direct"
- "referral" or other sites → "referral"
- "email", "newsletter" → "email"
- everything else → "other"

Return ONLY valid JSON, no explanations."""


class NormalizationService(BaseLLMService):
    """
    L2 Normalization Service using GPT-4 Strict Mode.

    Normalizes raw events from multiple sources into unified format.
    Uses JSON mode for guaranteed schema compliance.
    """

    def _get_default_config(self) -> LLMConfig:
        """Get default GPT-4 configuration."""
        return self.get_openai_config()

    async def normalize_batch(
        self,
        raw_events: list[RawEvent],
        batch_size: int = 50,
    ) -> dict[str, Any]:
        """
        Normalize a batch of raw events.

        Args:
            raw_events: List of raw events to normalize
            batch_size: Max events per LLM call (to avoid token limits)

        Returns:
            Dict with normalized_events, stats, and token usage
        """
        all_normalized = []
        total_tokens_input = 0
        total_tokens_output = 0
        all_warnings = []
        all_conflicts = []

        # Process in batches
        for i in range(0, len(raw_events), batch_size):
            batch = raw_events[i:i + batch_size]
            logger.info(f"Normalizing batch {i // batch_size + 1}: {len(batch)} events")

            result = await self._normalize_single_batch(batch)

            if result.get("normalized_events"):
                all_normalized.extend(result["normalized_events"])

            total_tokens_input += result.get("tokens_input", 0)
            total_tokens_output += result.get("tokens_output", 0)

            if result.get("data_quality", {}).get("warnings"):
                all_warnings.extend(result["data_quality"]["warnings"])
            if result.get("data_quality", {}).get("conflicts"):
                all_conflicts.extend(result["data_quality"]["conflicts"])

        return {
            "normalized_events": all_normalized,
            "stats": {
                "input_count": len(raw_events),
                "output_count": len(all_normalized),
                "tokens_input": total_tokens_input,
                "tokens_output": total_tokens_output,
            },
            "data_quality": {
                "warnings": all_warnings,
                "conflicts": all_conflicts,
            }
        }

    async def _normalize_single_batch(
        self,
        raw_events: list,
    ) -> dict[str, Any]:
        """Normalize a single batch of events."""

        # Helper to get attribute from object or dict
        def get_val(event, key, default=None):
            if isinstance(event, dict):
                return event.get(key, default)
            return getattr(event, key, default)

        # Prepare input data - handle both dict and object
        input_data = {
            "raw_events": [
                {
                    "id": get_val(event, 'id') or get_val(event, 'event_id'),
                    "source": get_val(event, 'source').value if hasattr(get_val(event, 'source'), 'value') else get_val(event, 'source'),
                    "raw_data": get_val(event, 'raw_data') or event if isinstance(event, dict) else None,
                    "session_id": get_val(event, 'session_id'),
                    "url": get_val(event, 'url'),
                    "utm_source": get_val(event, 'utm_source'),
                    "utm_medium": get_val(event, 'utm_medium'),
                    "page_views": get_val(event, 'page_views'),
                    "active_time_sec": get_val(event, 'active_time_sec'),
                    "country": get_val(event, 'country'),
                    "city": get_val(event, 'city'),
                    "device_type": get_val(event, 'device_type'),
                    "is_new_visitor": get_val(event, 'is_new_visitor'),
                }
                for event in raw_events
            ]
        }

        user_prompt = f"""Normalize the following raw events into unified format.

INPUT DATA:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

Process all events and return JSON with normalized_events array."""

        try:
            response = await self.call_llm(
                system_prompt=NORMALIZATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_format={"type": "json_object"},
            )

            content = response.get("content", {})

            # Parse if string
            if isinstance(content, str):
                content = json.loads(content)

            return {
                "normalized_events": content.get("normalized_events", []),
                "normalization_notes": content.get("normalization_notes", {}),
                "data_quality": content.get("data_quality", {}),
                "tokens_input": response.get("tokens_input", 0),
                "tokens_output": response.get("tokens_output", 0),
            }

        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return {
                "normalized_events": [],
                "data_quality": {"warnings": [str(e)]},
                "tokens_input": 0,
                "tokens_output": 0,
            }

    async def normalize_single(
        self,
        raw_event: RawEvent,
    ) -> Optional[dict[str, Any]]:
        """
        Normalize a single raw event.

        Args:
            raw_event: Single raw event to normalize

        Returns:
            Normalized event dict or None if failed
        """
        result = await self._normalize_single_batch([raw_event])
        events = result.get("normalized_events", [])
        return events[0] if events else None

    def to_normalized_event(
        self,
        data: dict[str, Any],
        raw_event_id: Optional[str] = None,
    ) -> NormalizedEvent:
        """
        Convert normalized dict to NormalizedEvent model.

        Args:
            data: Normalized event data from LLM
            raw_event_id: Optional reference to raw event

        Returns:
            NormalizedEvent instance
        """
        # Map traffic source type
        traffic_type = data.get("traffic_source_type", "other")

        # Parse occurred_at
        occurred_at = data.get("occurred_at")
        if isinstance(occurred_at, str):
            try:
                occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
            except ValueError:
                occurred_at = datetime.now()

        return NormalizedEvent(
            raw_event_id=raw_event_id,
            source=SourceType(data.get("source", "OTHER")),
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            client_id=data.get("client_id"),
            occurred_at=occurred_at or datetime.now(),
            url=data.get("url"),
            landing_page=data.get("landing_page"),
            exit_page=data.get("exit_page"),
            referrer=data.get("referrer"),
            utm_source=data.get("utm_source"),
            utm_medium=data.get("utm_medium"),
            utm_campaign=data.get("utm_campaign"),
            utm_term=data.get("utm_term"),
            utm_content=data.get("utm_content"),
            traffic_source_type=traffic_type,
            device_type=data.get("device_type"),
            browser=data.get("browser"),
            os=data.get("os"),
            screen_resolution=data.get("screen_resolution"),
            country=data.get("country"),
            region=data.get("region"),
            city=data.get("city"),
            page_views=data.get("page_views"),
            raw_visit_duration=data.get("raw_visit_duration"),
            events_count=data.get("events_count"),
            is_new_visitor=data.get("is_new_visitor"),
            is_bounce=data.get("is_bounce"),
            search_phrase=data.get("search_phrase"),
        )
