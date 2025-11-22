"""
Data Intake Storage Service

Handles persistence for the three-tier data architecture:
- L1: raw_events (all incoming data as-is)
- L2: normalized_events (unified format)
- L3: feature_store (computed features)

Uses Supabase/PostgreSQL for storage.
"""

import logging
import os
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from supabase import Client, create_client

from data_intake.models import (
    NormalizedEvent,
    NormalizedEventCreate,
    ProcessingStatus,
    RawEvent,
    RawEventCreate,
    SessionFeatures,
    SessionFeaturesCreate,
    SourceType,
)

logger = logging.getLogger(__name__)

# Table names
TABLE_RAW_EVENTS = "raw_events"
TABLE_NORMALIZED_EVENTS = "normalized_events"
TABLE_FEATURE_STORE = "feature_store"
TABLE_USER_AGGREGATES = "user_feature_aggregates"
TABLE_INTAKE_LOG = "data_intake_log"


class StorageError(Exception):
    """Base exception for storage errors."""
    pass


class DataIntakeStorage:
    """
    Storage service for Data Intake module.

    Handles CRUD operations for all three data layers.
    Follows the principle: "This module only stores, does not analyze."
    """

    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Initialize storage with Supabase client.

        Args:
            supabase_client: Optional pre-configured client.
                            If not provided, creates from env vars.
        """
        if supabase_client:
            self._client = supabase_client
        else:
            self._client = self._create_client()

    def _create_client(self) -> Client:
        """Create Supabase client from environment variables."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise StorageError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment"
            )

        return create_client(url, key)

    # =========================================================================
    # L1: RAW EVENTS
    # =========================================================================

    async def save_raw_event(self, event: RawEventCreate) -> RawEvent:
        """
        Save raw event to L1 storage.

        This is the "any garbage is saved" layer - complete API response.
        """
        data = {
            "source": event.source.value,
            "source_event_id": event.source_event_id,
            "counter_id": event.counter_id,
            "raw_data": event.raw_data,
            "api_endpoint": event.api_endpoint,
            "api_version": event.api_version,
            "request_params": event.request_params,
            "date_from": event.date_from.isoformat() if event.date_from else None,
            "date_to": event.date_to.isoformat() if event.date_to else None,
            "batch_id": event.batch_id,
            "processing_status": ProcessingStatus.PENDING.value,
            "fetched_at": datetime.utcnow().isoformat(),
        }

        try:
            result = self._client.table(TABLE_RAW_EVENTS).insert(data).execute()
            if result.data:
                return self._row_to_raw_event(result.data[0])
            raise StorageError("Failed to insert raw event")
        except Exception as e:
            logger.error(f"Failed to save raw event: {e}")
            raise StorageError(f"Failed to save raw event: {e}")

    async def save_raw_events_batch(
        self,
        events: list[RawEventCreate],
    ) -> list[RawEvent]:
        """Save multiple raw events in batch."""
        if not events:
            return []

        data_list = []
        for event in events:
            data_list.append({
                "source": event.source.value,
                "source_event_id": event.source_event_id,
                "counter_id": event.counter_id,
                "raw_data": event.raw_data,
                "api_endpoint": event.api_endpoint,
                "api_version": event.api_version,
                "request_params": event.request_params,
                "date_from": event.date_from.isoformat() if event.date_from else None,
                "date_to": event.date_to.isoformat() if event.date_to else None,
                "batch_id": event.batch_id,
                "processing_status": ProcessingStatus.PENDING.value,
                "fetched_at": datetime.utcnow().isoformat(),
            })

        try:
            result = self._client.table(TABLE_RAW_EVENTS).insert(data_list).execute()
            return [self._row_to_raw_event(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to save raw events batch: {e}")
            raise StorageError(f"Failed to save raw events batch: {e}")

    async def get_pending_raw_events(
        self,
        source: Optional[SourceType] = None,
        limit: int = 100,
    ) -> list[RawEvent]:
        """Get raw events pending processing."""
        query = self._client.table(TABLE_RAW_EVENTS)\
            .select("*")\
            .eq("processing_status", ProcessingStatus.PENDING.value)\
            .limit(limit)

        if source:
            query = query.eq("source", source.value)

        try:
            result = query.execute()
            return [self._row_to_raw_event(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to get pending raw events: {e}")
            raise StorageError(f"Failed to get pending raw events: {e}")

    async def update_raw_event_status(
        self,
        event_id: str,
        status: ProcessingStatus,
        error: Optional[str] = None,
    ) -> None:
        """Update processing status of raw event."""
        data = {
            "processing_status": status.value,
            "processed_at": datetime.utcnow().isoformat() if status != ProcessingStatus.PENDING else None,
        }
        if error:
            data["processing_error"] = error

        try:
            self._client.table(TABLE_RAW_EVENTS)\
                .update(data)\
                .eq("id", event_id)\
                .execute()
        except Exception as e:
            logger.error(f"Failed to update raw event status: {e}")
            raise StorageError(f"Failed to update raw event status: {e}")

    def _row_to_raw_event(self, row: dict) -> RawEvent:
        """Convert database row to RawEvent model."""
        return RawEvent(
            id=row.get("id"),
            source=SourceType(row["source"]),
            source_event_id=row.get("source_event_id"),
            counter_id=row.get("counter_id"),
            raw_data=row.get("raw_data", {}),
            api_endpoint=row.get("api_endpoint"),
            api_version=row.get("api_version"),
            request_params=row.get("request_params"),
            processing_status=ProcessingStatus(row.get("processing_status", "pending")),
            processing_error=row.get("processing_error"),
            processed_at=row.get("processed_at"),
            date_from=row.get("date_from"),
            date_to=row.get("date_to"),
            pipeline_version=row.get("pipeline_version", "1.0"),
            batch_id=row.get("batch_id"),
            fetched_at=row.get("fetched_at"),
            created_at=row.get("created_at"),
        )

    # =========================================================================
    # L2: NORMALIZED EVENTS
    # =========================================================================

    async def save_normalized_event(
        self,
        event: NormalizedEventCreate,
    ) -> NormalizedEvent:
        """Save normalized event to L2 storage."""
        data = self._normalized_event_to_dict(event)

        try:
            result = self._client.table(TABLE_NORMALIZED_EVENTS).insert(data).execute()
            if result.data:
                return self._row_to_normalized_event(result.data[0])
            raise StorageError("Failed to insert normalized event")
        except Exception as e:
            logger.error(f"Failed to save normalized event: {e}")
            raise StorageError(f"Failed to save normalized event: {e}")

    async def save_normalized_events_batch(
        self,
        events: list[NormalizedEventCreate],
    ) -> list[NormalizedEvent]:
        """Save multiple normalized events in batch."""
        if not events:
            return []

        data_list = [self._normalized_event_to_dict(e) for e in events]

        try:
            result = self._client.table(TABLE_NORMALIZED_EVENTS).insert(data_list).execute()
            return [self._row_to_normalized_event(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to save normalized events batch: {e}")
            raise StorageError(f"Failed to save normalized events batch: {e}")

    async def get_normalized_events(
        self,
        source: Optional[SourceType] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
    ) -> list[NormalizedEvent]:
        """Get normalized events with optional filters."""
        query = self._client.table(TABLE_NORMALIZED_EVENTS)\
            .select("*")\
            .limit(limit)\
            .order("occurred_at", desc=True)

        if source:
            query = query.eq("source", source.value)
        if date_from:
            query = query.gte("occurred_at", date_from)
        if date_to:
            query = query.lte("occurred_at", date_to)

        try:
            result = query.execute()
            return [self._row_to_normalized_event(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to get normalized events: {e}")
            raise StorageError(f"Failed to get normalized events: {e}")

    def _normalized_event_to_dict(self, event: NormalizedEventCreate) -> dict:
        """Convert NormalizedEventCreate to dict for storage."""
        return {
            "raw_event_id": event.raw_event_id,
            "source": event.source.value,
            "session_id": event.session_id,
            "user_id": event.user_id,
            "client_id": event.client_id,
            "occurred_at": event.occurred_at.isoformat(),
            "url": event.url,
            "landing_page": event.landing_page,
            "exit_page": event.exit_page,
            "referrer": event.referrer,
            "utm_source": event.utm_source,
            "utm_medium": event.utm_medium,
            "utm_campaign": event.utm_campaign,
            "utm_term": event.utm_term,
            "utm_content": event.utm_content,
            "traffic_source_type": event.traffic_source_type.value if event.traffic_source_type else None,
            "device_type": event.device_type,
            "browser": event.browser,
            "os": event.os,
            "screen_resolution": event.screen_resolution,
            "country": event.country,
            "region": event.region,
            "city": event.city,
            "page_views": event.page_views,
            "raw_visit_duration": event.raw_visit_duration,
            "events_count": event.events_count,
            "is_new_visitor": event.is_new_visitor,
            "is_bounce": event.is_bounce,
            "search_phrase": event.search_phrase,
            "internal_search_query": event.internal_search_query,
            "goals_reached": event.goals_reached,
            "raw_hits": event.raw_hits,
            "normalized_at": datetime.utcnow().isoformat(),
        }

    def _row_to_normalized_event(self, row: dict) -> NormalizedEvent:
        """Convert database row to NormalizedEvent model."""
        from data_intake.models import TrafficSourceType

        traffic_type = None
        if row.get("traffic_source_type"):
            try:
                traffic_type = TrafficSourceType(row["traffic_source_type"])
            except ValueError:
                pass

        return NormalizedEvent(
            id=row.get("id"),
            raw_event_id=row.get("raw_event_id"),
            source=SourceType(row["source"]),
            session_id=row.get("session_id"),
            user_id=row.get("user_id"),
            client_id=row.get("client_id"),
            occurred_at=row["occurred_at"],
            url=row.get("url"),
            landing_page=row.get("landing_page"),
            exit_page=row.get("exit_page"),
            referrer=row.get("referrer"),
            utm_source=row.get("utm_source"),
            utm_medium=row.get("utm_medium"),
            utm_campaign=row.get("utm_campaign"),
            utm_term=row.get("utm_term"),
            utm_content=row.get("utm_content"),
            traffic_source_type=traffic_type,
            device_type=row.get("device_type"),
            browser=row.get("browser"),
            os=row.get("os"),
            screen_resolution=row.get("screen_resolution"),
            country=row.get("country"),
            region=row.get("region"),
            city=row.get("city"),
            page_views=row.get("page_views"),
            raw_visit_duration=row.get("raw_visit_duration"),
            events_count=row.get("events_count"),
            is_new_visitor=row.get("is_new_visitor"),
            is_bounce=row.get("is_bounce"),
            search_phrase=row.get("search_phrase"),
            internal_search_query=row.get("internal_search_query"),
            goals_reached=row.get("goals_reached"),
            raw_hits=row.get("raw_hits"),
        )

    # =========================================================================
    # L3: FEATURE STORE
    # =========================================================================

    async def save_features(self, features: SessionFeaturesCreate) -> SessionFeatures:
        """Save session features to L3 storage (Feature Store)."""
        data = self._features_to_dict(features)

        try:
            result = self._client.table(TABLE_FEATURE_STORE).insert(data).execute()
            if result.data:
                return self._row_to_features(result.data[0])
            raise StorageError("Failed to insert features")
        except Exception as e:
            logger.error(f"Failed to save features: {e}")
            raise StorageError(f"Failed to save features: {e}")

    async def save_features_batch(
        self,
        features_list: list[SessionFeaturesCreate],
    ) -> list[SessionFeatures]:
        """Save multiple feature records in batch."""
        if not features_list:
            return []

        data_list = [self._features_to_dict(f) for f in features_list]

        try:
            result = self._client.table(TABLE_FEATURE_STORE).insert(data_list).execute()
            return [self._row_to_features(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to save features batch: {e}")
            raise StorageError(f"Failed to save features batch: {e}")

    async def get_features(
        self,
        source: Optional[SourceType] = None,
        min_hot_score: Optional[int] = None,
        segment_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
    ) -> list[SessionFeatures]:
        """
        Get features from Feature Store.

        This is the main method for the analytics agent to fetch data.
        """
        query = self._client.table(TABLE_FEATURE_STORE)\
            .select("*")\
            .limit(limit)\
            .order("event_date", desc=True)

        if source:
            query = query.eq("source", source.value)
        if min_hot_score is not None:
            query = query.gte("hot_score_base", min_hot_score)
        if segment_type:
            query = query.eq("segment_type", segment_type)
        if date_from:
            query = query.gte("event_date", date_from)
        if date_to:
            query = query.lte("event_date", date_to)

        try:
            result = query.execute()
            return [self._row_to_features(row) for row in result.data]
        except Exception as e:
            logger.error(f"Failed to get features: {e}")
            raise StorageError(f"Failed to get features: {e}")

    async def get_hot_leads(
        self,
        min_score: int = 50,
        limit: int = 100,
    ) -> list[SessionFeatures]:
        """Get hot leads from feature store (convenience method)."""
        return await self.get_features(min_hot_score=min_score, limit=limit)

    def _features_to_dict(self, features: SessionFeaturesCreate) -> dict:
        """Convert SessionFeaturesCreate to dict for storage."""
        return {
            "normalized_event_id": features.normalized_event_id,
            "source": features.source.value,
            "session_id": features.session_id,
            "user_id": features.user_id,
            "client_id": features.client_id,
            "event_date": features.event_date.isoformat(),
            "active_time_sec": features.active_time_sec,
            "idle_time_sec": features.idle_time_sec,
            "page_depth": features.page_depth,
            "key_pages_visited": features.key_pages_visited,
            "key_pages_count": features.key_pages_count,
            "bounce_flag": features.bounce_flag,
            "return_flag": features.return_flag,
            "hot_score_base": features.hot_score_base,
            "engagement_score": features.engagement_score,
            "intent_score": features.intent_score,
            "segment_type": features.segment_type.value if features.segment_type else None,
            "decision_stage": features.decision_stage.value if features.decision_stage else None,
            "device_type": features.device_type,
            "is_mobile": features.is_mobile,
            "traffic_source_type": features.traffic_source_type.value if features.traffic_source_type else None,
            "calculated_at": datetime.utcnow().isoformat(),
        }

    def _row_to_features(self, row: dict) -> SessionFeatures:
        """Convert database row to SessionFeatures model."""
        from data_intake.models import DecisionStage, SegmentType, TrafficSourceType

        segment = None
        if row.get("segment_type"):
            try:
                segment = SegmentType(row["segment_type"])
            except ValueError:
                pass

        stage = None
        if row.get("decision_stage"):
            try:
                stage = DecisionStage(row["decision_stage"])
            except ValueError:
                pass

        traffic = None
        if row.get("traffic_source_type"):
            try:
                traffic = TrafficSourceType(row["traffic_source_type"])
            except ValueError:
                pass

        return SessionFeatures(
            id=row.get("id"),
            normalized_event_id=row.get("normalized_event_id"),
            source=SourceType(row["source"]),
            session_id=row.get("session_id"),
            user_id=row.get("user_id"),
            client_id=row.get("client_id"),
            event_date=row["event_date"],
            active_time_sec=row.get("active_time_sec"),
            idle_time_sec=row.get("idle_time_sec"),
            page_depth=row.get("page_depth"),
            key_pages_visited=row.get("key_pages_visited"),
            key_pages_count=row.get("key_pages_count"),
            bounce_flag=row.get("bounce_flag"),
            return_flag=row.get("return_flag"),
            hot_score_base=row.get("hot_score_base"),
            engagement_score=row.get("engagement_score"),
            intent_score=row.get("intent_score"),
            segment_type=segment,
            decision_stage=stage,
            device_type=row.get("device_type"),
            is_mobile=row.get("is_mobile"),
            traffic_source_type=traffic,
        )

    # =========================================================================
    # LOGGING
    # =========================================================================

    async def log_operation(
        self,
        operation: str,
        status: str,
        source: Optional[SourceType] = None,
        records_processed: int = 0,
        records_failed: int = 0,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        batch_id: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> None:
        """Log a pipeline operation for monitoring."""
        data = {
            "operation": operation,
            "status": status,
            "source": source.value if source else None,
            "records_processed": records_processed,
            "records_failed": records_failed,
            "duration_ms": duration_ms,
            "error_message": error_message,
            "batch_id": batch_id,
            "params": params,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat() if status in ("completed", "failed") else None,
        }

        try:
            self._client.table(TABLE_INTAKE_LOG).insert(data).execute()
        except Exception as e:
            logger.error(f"Failed to log operation: {e}")


# Singleton instance
_storage_instance: Optional[DataIntakeStorage] = None


def get_storage() -> DataIntakeStorage:
    """Get or create the storage instance."""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = DataIntakeStorage()
    return _storage_instance


def reset_storage() -> None:
    """Reset storage instance (for testing)."""
    global _storage_instance
    _storage_instance = None
