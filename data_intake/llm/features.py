"""
L3: Feature Engineering Service (Claude 3.5 Sonnet)

Calculates features from normalized events for analytics.
Uses Claude for intelligent feature computation with low hallucination rate.

Key features computed:
- hot_score: 0-10 scale (how likely to convert)
- intent_score: 0-10 scale (purchase intent)
- quality_index: 0-1 scale (lead quality)
- segment: URGENCY | DECISION | PROBLEM | INFO | BRAND
- decision_stage: awareness | consideration | evaluation | purchase_intent
"""

import json
import logging
from datetime import datetime
from typing import Any, Optional

from data_intake.llm.base import BaseLLMService, LLMConfig
from data_intake.models import NormalizedEvent, SessionFeatures, SegmentType, DecisionStage

logger = logging.getLogger(__name__)

# System prompt for feature engineering (Claude 3.5 Sonnet)
FEATURE_ENGINEERING_SYSTEM_PROMPT = """You are a lead generation analytics expert. Your task is to engineer features from unified metrics data.

FEATURE DEFINITIONS:

1. hot_score (0-10): How likely this visitor is to convert
   Formula factors:
   - conversion_rate weight: 30%
   - engagement_rate weight: 20%
   - (1 - bounce_rate) weight: 20%
   - page depth weight: 20%
   - recency weight: 10%

2. intent_score (0-10): Purchase intent level
   Formula factors:
   - session duration vs average: 30%
   - actions/events count: 20%
   - key pages visited (pricing, contacts): 30%
   - form interactions: 20%

3. quality_index (0-1): Overall lead quality
   Formula factors:
   - engagement_rate: 40%
   - conversion_rate: 30%
   - traffic quality: 20%
   - content relevance: 10%

4. segment classification:
   - URGENCY: conversion_rate > 5% AND time_on_page > 3min → ready to buy NOW
   - DECISION: actions_count > 5 AND pages_visited > 4 → comparing options
   - PROBLEM: search_queries_count > 3 → looking for solution
   - BRAND: engagement_rate > 0.7 AND duration > 2min → knows the brand
   - INFO: default → just browsing

5. decision_stage:
   - awareness: First touch, low engagement
   - consideration: Multiple pages, comparing
   - evaluation: Key pages (pricing, reviews)
   - purchase_intent: High engagement + key actions

KEY PAGES (indicate high intent):
- /price, /pricing, /tariff → pricing interest
- /contacts, /contact-us → ready to reach out
- /portfolio, /cases, /works → evaluating quality
- /reviews, /testimonials → building trust
- /faq, /help → has questions
- /about, /company → learning about business

OUTPUT SCHEMA:
{
  "features": [
    {
      "session_id": string | null,
      "user_id": string | null,
      "event_date": "YYYY-MM-DD",

      "active_time_sec": integer | null,
      "page_depth": integer | null,
      "scroll_depth_avg": integer | null,

      "key_pages_visited": {
        "price": boolean,
        "contacts": boolean,
        "portfolio": boolean,
        "reviews": boolean,
        "faq": boolean,
        "about": boolean
      },
      "key_pages_count": integer,

      "hot_score_base": integer (0-100),
      "engagement_score": integer (0-100),
      "intent_score": integer (0-100),

      "segment_type": "URGENCY" | "DECISION" | "PROBLEM" | "INFO" | "BRAND",
      "decision_stage": "awareness" | "consideration" | "evaluation" | "purchase_intent",

      "bounce_flag": boolean,
      "return_flag": boolean,

      "calculation_notes": string
    }
  ],
  "summary": {
    "total_processed": integer,
    "segment_distribution": {
      "URGENCY": integer,
      "DECISION": integer,
      "PROBLEM": integer,
      "INFO": integer,
      "BRAND": integer
    },
    "avg_hot_score": float,
    "avg_intent_score": float
  }
}

Return ONLY valid JSON, no explanations."""


class FeatureService(BaseLLMService):
    """
    L3 Feature Engineering Service using Claude 3.5 Sonnet.

    Calculates advanced features from normalized events.
    Uses Claude for intelligent reasoning with low hallucination rate.
    """

    def _get_default_config(self) -> LLMConfig:
        """Get default Claude configuration."""
        return self.get_anthropic_config()

    async def calculate_features_batch(
        self,
        normalized_events: list[NormalizedEvent],
        batch_size: int = 30,
    ) -> dict[str, Any]:
        """
        Calculate features for a batch of normalized events.

        Args:
            normalized_events: List of normalized events
            batch_size: Max events per LLM call

        Returns:
            Dict with features, summary, and token usage
        """
        all_features = []
        total_tokens_input = 0
        total_tokens_output = 0

        # Process in batches
        for i in range(0, len(normalized_events), batch_size):
            batch = normalized_events[i:i + batch_size]
            logger.info(f"Calculating features batch {i // batch_size + 1}: {len(batch)} events")

            result = await self._calculate_single_batch(batch)

            if result.get("features"):
                all_features.extend(result["features"])

            total_tokens_input += result.get("tokens_input", 0)
            total_tokens_output += result.get("tokens_output", 0)

        # Calculate summary
        segment_distribution = {
            "URGENCY": 0, "DECISION": 0, "PROBLEM": 0, "INFO": 0, "BRAND": 0
        }
        hot_scores = []
        intent_scores = []

        for f in all_features:
            segment = f.get("segment_type", "INFO")
            if segment in segment_distribution:
                segment_distribution[segment] += 1

            if f.get("hot_score_base"):
                hot_scores.append(f["hot_score_base"])
            if f.get("intent_score"):
                intent_scores.append(f["intent_score"])

        return {
            "features": all_features,
            "summary": {
                "total_processed": len(all_features),
                "segment_distribution": segment_distribution,
                "avg_hot_score": sum(hot_scores) / len(hot_scores) if hot_scores else 0,
                "avg_intent_score": sum(intent_scores) / len(intent_scores) if intent_scores else 0,
            },
            "tokens": {
                "input": total_tokens_input,
                "output": total_tokens_output,
            }
        }

    async def _calculate_single_batch(
        self,
        normalized_events: list[NormalizedEvent],
    ) -> dict[str, Any]:
        """Calculate features for a single batch."""

        # Prepare input data
        input_data = {
            "normalized_events": [
                {
                    "id": event.id,
                    "source": event.source.value if event.source else None,
                    "session_id": event.session_id,
                    "user_id": event.user_id,
                    "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
                    "url": event.url,
                    "landing_page": event.landing_page,
                    "utm_source": event.utm_source,
                    "utm_medium": event.utm_medium,
                    "traffic_source_type": event.traffic_source_type,
                    "device_type": event.device_type,
                    "country": event.country,
                    "city": event.city,
                    "page_views": event.page_views,
                    "raw_visit_duration": event.raw_visit_duration,
                    "events_count": event.events_count,
                    "is_new_visitor": event.is_new_visitor,
                    "is_bounce": event.is_bounce,
                    "search_phrase": event.search_phrase,
                }
                for event in normalized_events
            ]
        }

        user_prompt = f"""Calculate features for the following normalized events.

INPUT DATA:
{json.dumps(input_data, ensure_ascii=False, indent=2)}

Analyze each event and return JSON with features array and summary."""

        try:
            response = await self.call_llm(
                system_prompt=FEATURE_ENGINEERING_SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )

            content = response.get("content", {})

            # Parse if string
            if isinstance(content, str):
                content = json.loads(content)

            return {
                "features": content.get("features", []),
                "summary": content.get("summary", {}),
                "tokens_input": response.get("tokens_input", 0),
                "tokens_output": response.get("tokens_output", 0),
            }

        except Exception as e:
            logger.error(f"Feature calculation failed: {e}")
            return {
                "features": [],
                "summary": {},
                "tokens_input": 0,
                "tokens_output": 0,
            }

    def to_session_features(
        self,
        data: dict[str, Any],
        normalized_event_id: Optional[str] = None,
        source: Optional[str] = None,
    ) -> SessionFeatures:
        """
        Convert feature dict to SessionFeatures model.

        Args:
            data: Feature data from LLM
            normalized_event_id: Reference to normalized event
            source: Source type

        Returns:
            SessionFeatures instance
        """
        # Parse event_date
        event_date = data.get("event_date")
        if isinstance(event_date, str):
            try:
                event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
            except ValueError:
                event_date = datetime.now().date()

        # Map segment type
        segment_str = data.get("segment_type", "INFO")
        try:
            segment = SegmentType(segment_str.lower()) if segment_str else SegmentType.INFO
        except ValueError:
            segment = SegmentType.INFO

        # Map decision stage
        stage_str = data.get("decision_stage", "awareness")
        try:
            stage = DecisionStage(stage_str.lower()) if stage_str else DecisionStage.AWARENESS
        except ValueError:
            stage = DecisionStage.AWARENESS

        return SessionFeatures(
            normalized_event_id=normalized_event_id,
            source=source,
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            event_date=event_date or datetime.now().date(),
            active_time_sec=data.get("active_time_sec"),
            page_depth=data.get("page_depth"),
            scroll_depth_avg=data.get("scroll_depth_avg"),
            key_pages_visited=data.get("key_pages_visited"),
            key_pages_count=data.get("key_pages_count"),
            hot_score_base=data.get("hot_score_base"),
            engagement_score=data.get("engagement_score"),
            intent_score=data.get("intent_score"),
            segment_type=segment,
            decision_stage=stage,
            bounce_flag=data.get("bounce_flag"),
            return_flag=data.get("return_flag"),
            calculation_notes=data.get("calculation_notes"),
        )
