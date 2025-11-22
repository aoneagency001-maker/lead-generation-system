"""
LLM Processing Pipeline

Orchestrates the 3-layer LLM processing:
L1 (Raw) → L2 (Normalized) → L3 (Features) → L4 (Insights)

Key principle: Each layer processes data ONCE, stores in DB,
subsequent layers read from DB - not re-process.
"""

import logging
from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4

from data_intake.llm.normalization import NormalizationService
from data_intake.llm.features import FeatureService
from data_intake.llm.analysis import AnalysisService
from data_intake.models import VisitEvent, NormalizedEvent, SessionFeatures

logger = logging.getLogger(__name__)


class LLMPipeline:
    """
    Orchestrates multi-layer LLM processing pipeline.

    Flow:
    1. L2: Raw events → Normalized events (GPT-4)
    2. L3: Normalized events → Session features (Claude)
    3. L4: Features → Business insights (Perplexity/Claude)

    Each layer stores results in DB before passing to next layer.
    """

    def __init__(
        self,
        db_client: Optional[Any] = None,
        batch_size_l2: int = 50,
        batch_size_l3: int = 30,
    ):
        """
        Initialize pipeline with optional DB client.

        Args:
            db_client: Supabase client for storing results
            batch_size_l2: Batch size for normalization
            batch_size_l3: Batch size for feature engineering
        """
        self.db_client = db_client
        self.batch_size_l2 = batch_size_l2
        self.batch_size_l3 = batch_size_l3

        # Initialize services
        self.normalizer = NormalizationService()
        self.feature_engine = FeatureService()
        self.analyzer = AnalysisService()

        logger.info("LLM Pipeline initialized")

    async def process_raw_events(
        self,
        raw_events: list[VisitEvent],
        store_intermediate: bool = True,
    ) -> dict[str, Any]:
        """
        Process raw events through L2 normalization.

        Args:
            raw_events: List of raw VisitEvent objects
            store_intermediate: Whether to store results in DB

        Returns:
            Dict with normalized events and processing stats
        """
        logger.info(f"L2: Processing {len(raw_events)} raw events")
        start_time = datetime.now()

        # Convert VisitEvent to dict for LLM
        raw_dicts = [
            {
                "event_id": e.event_id,
                "source": e.source.value if e.source else None,
                "session_id": e.session_id,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                "url": e.url,
                "referrer": e.referrer,
                "utm_source": e.utm_source,
                "utm_medium": e.utm_medium,
                "utm_campaign": e.utm_campaign,
                "is_new_visitor": e.is_new_visitor,
                "page_views": e.page_views,
                "active_time_sec": e.active_time_sec,
                "country": e.country,
                "city": e.city,
                "device_type": e.device_type,
            }
            for e in raw_events
        ]

        # Process through L2
        result = await self.normalizer.normalize_batch(
            raw_events=raw_dicts,
            batch_size=self.batch_size_l2,
        )

        # Convert to NormalizedEvent models
        normalized_events = []
        for norm_data in result.get("normalized_events", []):
            try:
                event = self.normalizer.to_normalized_event(
                    data=norm_data,
                    raw_event_id=norm_data.get("event_id"),
                )
                normalized_events.append(event)
            except Exception as e:
                logger.warning(f"Failed to convert normalized event: {e}")

        # Store in DB if enabled
        if store_intermediate and self.db_client:
            await self._store_normalized_events(normalized_events)

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "layer": "L2",
            "normalized_events": normalized_events,
            "count": len(normalized_events),
            "tokens": result.get("tokens", {}),
            "processing_time_sec": processing_time,
        }

    async def process_normalized_events(
        self,
        normalized_events: list[NormalizedEvent],
        store_intermediate: bool = True,
    ) -> dict[str, Any]:
        """
        Process normalized events through L3 feature engineering.

        Args:
            normalized_events: List of NormalizedEvent objects
            store_intermediate: Whether to store results in DB

        Returns:
            Dict with features and processing stats
        """
        logger.info(f"L3: Processing {len(normalized_events)} normalized events")
        start_time = datetime.now()

        # Process through L3
        result = await self.feature_engine.calculate_features_batch(
            normalized_events=normalized_events,
            batch_size=self.batch_size_l3,
        )

        # Convert to SessionFeatures models
        session_features = []
        for feature_data in result.get("features", []):
            try:
                feature = self.feature_engine.to_session_features(
                    data=feature_data,
                    normalized_event_id=feature_data.get("session_id"),
                    source=feature_data.get("source"),
                )
                session_features.append(feature)
            except Exception as e:
                logger.warning(f"Failed to convert feature: {e}")

        # Store in DB if enabled
        if store_intermediate and self.db_client:
            await self._store_session_features(session_features)

        processing_time = (datetime.now() - start_time).total_seconds()

        return {
            "layer": "L3",
            "session_features": session_features,
            "count": len(session_features),
            "summary": result.get("summary", {}),
            "tokens": result.get("tokens", {}),
            "processing_time_sec": processing_time,
        }

    async def generate_insights(
        self,
        unified_metrics: list[dict[str, Any]],
        feature_store: list[dict[str, Any]],
        date_from: date,
        date_to: date,
        insight_type: str = "daily",
        store_result: bool = True,
    ) -> dict[str, Any]:
        """
        Generate L4 business insights from aggregated data.

        Args:
            unified_metrics: Daily unified metrics from DB
            feature_store: Session features from DB
            date_from: Analysis start date
            date_to: Analysis end date
            insight_type: 'daily', 'weekly', 'monthly'
            store_result: Whether to store in analytics_insights table

        Returns:
            Dict with insights and processing stats
        """
        logger.info(f"L4: Generating {insight_type} insights for {date_from} to {date_to}")
        start_time = datetime.now()

        # Generate insights
        result = await self.analyzer.generate_insights(
            unified_metrics=unified_metrics,
            feature_store=feature_store,
            date_from=date_from,
            date_to=date_to,
            insight_type=insight_type,
        )

        # Store in DB if enabled
        if store_result and self.db_client:
            record = self.analyzer.to_analytics_insight_record(result)
            await self._store_analytics_insight(record)

        processing_time = (datetime.now() - start_time).total_seconds()

        result["layer"] = "L4"
        result["processing_time_sec"] = processing_time

        return result

    async def run_full_pipeline(
        self,
        raw_events: list[VisitEvent],
        date_from: date,
        date_to: date,
        generate_insights: bool = True,
    ) -> dict[str, Any]:
        """
        Run complete pipeline: L2 → L3 → L4.

        Args:
            raw_events: Raw visit events to process
            date_from: Date range start
            date_to: Date range end
            generate_insights: Whether to run L4 analysis

        Returns:
            Complete pipeline results
        """
        pipeline_id = str(uuid4())[:8]
        logger.info(f"Pipeline {pipeline_id}: Starting full pipeline for {len(raw_events)} events")
        start_time = datetime.now()

        results = {
            "pipeline_id": pipeline_id,
            "started_at": start_time.isoformat(),
            "input_events": len(raw_events),
            "layers": {},
        }

        # L2: Normalization
        l2_result = await self.process_raw_events(raw_events)
        results["layers"]["L2"] = {
            "status": "completed",
            "count": l2_result["count"],
            "tokens": l2_result.get("tokens", {}),
            "processing_time_sec": l2_result["processing_time_sec"],
        }

        if not l2_result["normalized_events"]:
            logger.warning(f"Pipeline {pipeline_id}: No normalized events, stopping")
            results["status"] = "partial"
            return results

        # L3: Feature Engineering
        l3_result = await self.process_normalized_events(l2_result["normalized_events"])
        results["layers"]["L3"] = {
            "status": "completed",
            "count": l3_result["count"],
            "summary": l3_result.get("summary", {}),
            "tokens": l3_result.get("tokens", {}),
            "processing_time_sec": l3_result["processing_time_sec"],
        }

        # L4: Analysis (optional)
        if generate_insights and l3_result["session_features"]:
            # Prepare feature data for L4
            feature_dicts = [
                {
                    "session_id": f.session_id,
                    "segment_type": f.segment_type.value if f.segment_type else None,
                    "hot_score_base": f.hot_score_base,
                    "intent_score": f.intent_score,
                    "engagement_score": f.engagement_score,
                    "decision_stage": f.decision_stage.value if f.decision_stage else None,
                }
                for f in l3_result["session_features"]
            ]

            # Mock unified_metrics for analysis (should come from DB in production)
            unified_metrics = [{
                "date": date_from.isoformat(),
                "unified_sessions": len(raw_events),
                "unified_users": len(set(e.user_id for e in raw_events if e.user_id)),
                "unified_pageviews": sum(e.page_views or 0 for e in raw_events),
                "ga4_data_available": True,
                "metrika_data_available": False,
            }]

            l4_result = await self.generate_insights(
                unified_metrics=unified_metrics,
                feature_store=feature_dicts,
                date_from=date_from,
                date_to=date_to,
            )
            results["layers"]["L4"] = {
                "status": "completed",
                "has_insights": bool(l4_result.get("insights")),
                "tokens_input": l4_result.get("tokens_input", 0),
                "tokens_output": l4_result.get("tokens_output", 0),
                "processing_time_sec": l4_result["processing_time_sec"],
            }

        # Calculate totals
        total_time = (datetime.now() - start_time).total_seconds()
        total_tokens_input = sum(
            layer.get("tokens", {}).get("input", 0)
            for layer in results["layers"].values()
        )
        total_tokens_output = sum(
            layer.get("tokens", {}).get("output", 0)
            for layer in results["layers"].values()
        )

        results["completed_at"] = datetime.now().isoformat()
        results["total_processing_time_sec"] = total_time
        results["total_tokens"] = {
            "input": total_tokens_input,
            "output": total_tokens_output,
        }
        results["status"] = "completed"

        logger.info(
            f"Pipeline {pipeline_id}: Completed in {total_time:.2f}s, "
            f"tokens: {total_tokens_input + total_tokens_output}"
        )

        return results

    # Database storage methods (implement when DB client is available)
    async def _store_normalized_events(self, events: list[NormalizedEvent]) -> None:
        """Store normalized events in normalized_events table."""
        if not self.db_client:
            return

        try:
            records = [
                {
                    "id": str(uuid4()),
                    "source": e.source.value if e.source else None,
                    "session_id": e.session_id,
                    "user_id": e.user_id,
                    "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                    "url": e.url,
                    "landing_page": e.landing_page,
                    "utm_source": e.utm_source,
                    "utm_medium": e.utm_medium,
                    "traffic_source_type": e.traffic_source_type,
                    "device_type": e.device_type,
                    "country": e.country,
                    "city": e.city,
                    "page_views": e.page_views,
                    "raw_visit_duration": e.raw_visit_duration,
                    "events_count": e.events_count,
                    "is_new_visitor": e.is_new_visitor,
                    "is_bounce": e.is_bounce,
                }
                for e in events
            ]

            await self.db_client.table("normalized_events").insert(records).execute()
            logger.info(f"Stored {len(records)} normalized events")
        except Exception as e:
            logger.error(f"Failed to store normalized events: {e}")

    async def _store_session_features(self, features: list[SessionFeatures]) -> None:
        """Store session features in feature_store table."""
        if not self.db_client:
            return

        try:
            records = [
                {
                    "id": str(uuid4()),
                    "session_id": f.session_id,
                    "user_id": f.user_id,
                    "event_date": f.event_date.isoformat() if f.event_date else None,
                    "active_time_sec": f.active_time_sec,
                    "page_depth": f.page_depth,
                    "scroll_depth_avg": f.scroll_depth_avg,
                    "key_pages_visited": f.key_pages_visited,
                    "key_pages_count": f.key_pages_count,
                    "hot_score_base": f.hot_score_base,
                    "engagement_score": f.engagement_score,
                    "intent_score": f.intent_score,
                    "segment_type": f.segment_type.value if f.segment_type else None,
                    "decision_stage": f.decision_stage.value if f.decision_stage else None,
                    "bounce_flag": f.bounce_flag,
                    "return_flag": f.return_flag,
                }
                for f in features
            ]

            await self.db_client.table("feature_store").insert(records).execute()
            logger.info(f"Stored {len(records)} session features")
        except Exception as e:
            logger.error(f"Failed to store session features: {e}")

    async def _store_analytics_insight(self, record: dict[str, Any]) -> None:
        """Store analytics insight in analytics_insights table."""
        if not self.db_client:
            return

        try:
            record["id"] = str(uuid4())
            await self.db_client.table("analytics_insights").insert(record).execute()
            logger.info(f"Stored analytics insight")
        except Exception as e:
            logger.error(f"Failed to store analytics insight: {e}")


# Convenience function for quick processing
async def process_events(
    raw_events: list[VisitEvent],
    date_from: date,
    date_to: date,
    db_client: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Quick function to process events through full pipeline.

    Args:
        raw_events: Raw events to process
        date_from: Analysis start date
        date_to: Analysis end date
        db_client: Optional Supabase client

    Returns:
        Pipeline results
    """
    pipeline = LLMPipeline(db_client=db_client)
    return await pipeline.run_full_pipeline(
        raw_events=raw_events,
        date_from=date_from,
        date_to=date_to,
    )
