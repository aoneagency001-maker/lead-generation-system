"""
Data Intake ETL Pipeline

Orchestrates the full data flow:
1. Fetch raw data from sources (providers)
2. Save to L1 (raw_events)
3. Normalize to unified format
4. Save to L2 (normalized_events)
5. Calculate features
6. Save to L3 (feature_store)

Principle: This pipeline is a "dumb pipeline" - it only moves and transforms data.
It does NOT make business decisions or deep analysis.
"""

import asyncio
import logging
import time
from datetime import date, datetime
from typing import Any, Optional
from uuid import uuid4

from data_intake.database.storage import DataIntakeStorage, get_storage
from data_intake.feature_calculator import FeatureCalculator, get_feature_calculator
from data_intake.models import (
    NormalizedEvent,
    NormalizedEventCreate,
    PipelineStatus,
    ProcessingStatus,
    RawEvent,
    RawEventCreate,
    SessionFeaturesCreate,
    SourceType,
    TrafficSourceType,
)
from data_intake.providers.base import BaseAnalyticsProvider
from data_intake.providers.yandex_metrika import YandexMetrikaProvider
from data_intake.providers.google_analytics import GoogleAnalyticsProvider

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Pipeline execution error."""
    pass


class DataIntakePipeline:
    """
    Main ETL pipeline for data intake.

    Flow:
    Source API → Raw Events (L1) → Normalized Events (L2) → Features (L3)

    This pipeline does NOT:
    - Make business decisions
    - Send notifications
    - Perform deep analysis

    It ONLY:
    - Fetches data
    - Normalizes data
    - Calculates basic features
    - Stores data in three layers
    """

    def __init__(
        self,
        storage: Optional[DataIntakeStorage] = None,
        calculator: Optional[FeatureCalculator] = None,
    ):
        """
        Initialize pipeline.

        Args:
            storage: Storage service (uses default if not provided)
            calculator: Feature calculator (uses default if not provided)
        """
        self.storage = storage or get_storage()
        self.calculator = calculator or get_feature_calculator()
        self.providers: dict[SourceType, BaseAnalyticsProvider] = {}

        # Auto-register available providers
        self._register_providers()

    def _register_providers(self) -> None:
        """Register available data providers."""
        # Register Yandex.Metrika
        try:
            yandex = YandexMetrikaProvider()
            self.providers[SourceType.YANDEX_METRIKA] = yandex
            logger.info("✅ Registered Yandex.Metrika provider")
        except Exception as e:
            logger.warning(f"⚠️ Yandex.Metrika provider not available: {e}")

        # Register Google Analytics 4
        try:
            ga = GoogleAnalyticsProvider()
            self.providers[SourceType.GOOGLE_ANALYTICS] = ga
            logger.info("✅ Registered Google Analytics 4 provider")
        except Exception as e:
            logger.warning(f"⚠️ Google Analytics provider not available: {e}")

    async def run_full_pipeline(
        self,
        source: SourceType,
        date_from: date,
        date_to: date,
    ) -> PipelineStatus:
        """
        Run the complete ETL pipeline for a source.

        Steps:
        1. Fetch raw data from provider
        2. Save to raw_events (L1)
        3. Normalize data
        4. Save to normalized_events (L2)
        5. Calculate features
        6. Save to feature_store (L3)

        Args:
            source: Data source to fetch from
            date_from: Start date
            date_to: End date

        Returns:
            PipelineStatus with execution results
        """
        batch_id = f"pipeline_{source.value}_{uuid4().hex[:8]}"
        started_at = datetime.utcnow()
        start_time = time.time()

        status = PipelineStatus(
            batch_id=batch_id,
            status="running",
            started_at=started_at,
        )

        logger.info(f"Starting pipeline {batch_id}: {source.value} {date_from} to {date_to}")

        try:
            # Step 1: Fetch raw data
            raw_data = await self._fetch_raw_data(source, date_from, date_to, batch_id)
            status.raw_count = len(raw_data) if raw_data else 0

            if not raw_data:
                logger.warning(f"No data fetched for {source.value}")
                status.status = "completed"
                status.completed_at = datetime.utcnow()
                return status

            # Step 2: Save raw events
            raw_events = await self._save_raw_events(source, raw_data, batch_id, date_from, date_to)

            # Step 3 & 4: Normalize and save
            normalized_events = await self._normalize_and_save(raw_events)
            status.normalized_count = len(normalized_events)

            # Step 5 & 6: Calculate features and save
            features_count = await self._calculate_and_save_features(normalized_events)
            status.features_count = features_count

            # Mark raw events as processed
            for raw_event in raw_events:
                if raw_event.id:
                    await self.storage.update_raw_event_status(
                        raw_event.id,
                        ProcessingStatus.PROCESSED,
                    )

            status.status = "completed"
            status.completed_at = datetime.utcnow()
            status.duration_ms = int((time.time() - start_time) * 1000)

            # Log success
            await self.storage.log_operation(
                operation="full_pipeline",
                status="completed",
                source=source,
                records_processed=status.normalized_count,
                duration_ms=status.duration_ms,
                batch_id=batch_id,
            )

            logger.info(
                f"Pipeline {batch_id} completed: "
                f"raw={status.raw_count}, normalized={status.normalized_count}, "
                f"features={status.features_count}"
            )

        except Exception as e:
            logger.error(f"Pipeline {batch_id} failed: {e}")
            status.status = "failed"
            status.errors.append(str(e))
            status.completed_at = datetime.utcnow()
            status.duration_ms = int((time.time() - start_time) * 1000)

            await self.storage.log_operation(
                operation="full_pipeline",
                status="failed",
                source=source,
                error_message=str(e),
                batch_id=batch_id,
            )

        return status

    async def _fetch_raw_data(
        self,
        source: SourceType,
        date_from: date,
        date_to: date,
        batch_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Fetch raw data from provider.

        Returns the complete API response as-is.
        """
        if source not in self.providers:
            raise PipelineError(f"Provider not available for {source.value}")

        provider = self.providers[source]

        logger.info(f"Fetching data from {source.value}")

        try:
            # For Yandex.Metrika, we need to get raw response
            # The current provider returns normalized data, so we'll fetch raw
            if isinstance(provider, YandexMetrikaProvider):
                raw_response = await self._fetch_yandex_raw(provider, date_from, date_to)
                return raw_response
            else:
                # For other providers, use the standard fetch
                events = await provider.fetch_visits(date_from, date_to)
                return {"events": [e.model_dump() for e in events]}

        except Exception as e:
            logger.error(f"Failed to fetch from {source.value}: {e}")
            raise PipelineError(f"Failed to fetch data: {e}")

    async def _fetch_yandex_raw(
        self,
        provider: YandexMetrikaProvider,
        date_from: date,
        date_to: date,
    ) -> dict[str, Any]:
        """
        Fetch raw data from Yandex.Metrika API.

        Returns the complete API response for storage in L1.
        """
        import httpx

        params = {
            "ids": provider.counter_id,
            "date1": date_from.isoformat(),
            "date2": date_to.isoformat(),
            "metrics": "ym:s:visits,ym:s:pageviews,ym:s:bounceRate",
            "dimensions": ",".join([
                "ym:s:date",
                "ym:s:startURL",
                "ym:s:referer",
                "ym:s:UTMSource",
                "ym:s:UTMMedium",
                "ym:s:UTMCampaign",
                "ym:s:isNewUser",
                "ym:s:deviceCategory",
                "ym:s:browser",
                "ym:s:operatingSystem",
                "ym:s:regionCountry",
                "ym:s:regionCity",
            ]),
            "limit": "10000",
            "accuracy": "full",
        }

        headers = {
            "Authorization": f"OAuth {provider.token}",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(
                    "https://api-metrika.yandex.net/stat/v1/data",
                    params=params,
                    headers=headers,
                )
            except httpx.TimeoutException as e:
                logger.error(f"Yandex.Metrika API timeout: {e}")
                raise PipelineError(f"API request timed out: {e}")
            except httpx.RequestError as e:
                logger.error(f"Yandex.Metrika API request error: {e}")
                raise PipelineError(f"API request failed: {e}")

            # Handle response errors
            if response.status_code == 401:
                logger.error("Yandex.Metrika authentication failed")
                raise PipelineError("Invalid OAuth token - check YANDEX_METRIKA_TOKEN")
            
            if response.status_code == 403:
                logger.error("Yandex.Metrika access denied")
                raise PipelineError("Access denied - check token permissions and counter access")
            
            if response.status_code != 200:
                error_text = response.text[:500] if response.text else "No error details"
                logger.error(f"Yandex.Metrika API error: status={response.status_code}, body={error_text}")
                raise PipelineError(
                    f"API returned status {response.status_code}: {error_text}"
                )

            try:
                return response.json()
            except Exception as e:
                logger.error(f"Failed to parse Yandex.Metrika response: {e}")
                raise PipelineError(f"Invalid JSON response from API: {e}")

    async def _save_raw_events(
        self,
        source: SourceType,
        raw_data: dict[str, Any],
        batch_id: str,
        date_from: date,
        date_to: date,
    ) -> list[RawEvent]:
        """Save raw data to L1 storage."""
        # For now, save the entire response as one raw event
        # In production, you might split by day or other criteria

        raw_event = RawEventCreate(
            source=source,
            raw_data=raw_data,
            api_endpoint="stat/v1/data",
            api_version="v1",
            request_params={
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
            },
            date_from=date_from,
            date_to=date_to,
            batch_id=batch_id,
        )

        saved = await self.storage.save_raw_event(raw_event)
        return [saved]

    async def _normalize_and_save(
        self,
        raw_events: list[RawEvent],
    ) -> list[NormalizedEvent]:
        """
        Normalize raw events and save to L2.

        Transforms source-specific format to unified schema.
        """
        normalized_list = []

        for raw_event in raw_events:
            try:
                # Parse raw data based on source
                if raw_event.source == SourceType.YANDEX_METRIKA:
                    events = self._normalize_yandex_data(raw_event)
                else:
                    # Generic normalization
                    events = self._normalize_generic(raw_event)

                normalized_list.extend(events)

            except Exception as e:
                logger.error(f"Failed to normalize raw event {raw_event.id}: {e}")
                if raw_event.id:
                    await self.storage.update_raw_event_status(
                        raw_event.id,
                        ProcessingStatus.FAILED,
                        str(e),
                    )

        if normalized_list:
            saved = await self.storage.save_normalized_events_batch(normalized_list)
            return saved

        return []

    def _normalize_yandex_data(
        self,
        raw_event: RawEvent,
    ) -> list[NormalizedEventCreate]:
        """Normalize Yandex.Metrika data to unified format."""
        normalized = []
        raw_data = raw_event.raw_data

        rows = raw_data.get("data", [])

        for idx, row in enumerate(rows):
            try:
                dims = row.get("dimensions", [])

                # Extract dimension values
                def get_dim(index: int) -> Optional[str]:
                    if index < len(dims):
                        val = dims[index].get("name", "")
                        if val in ("", "null", "(not set)", "(прямой трафик)"):
                            return None
                        return val
                    return None

                date_str = get_dim(0)
                url = get_dim(1)
                referrer = get_dim(2)
                utm_source = get_dim(3)
                utm_medium = get_dim(4)
                utm_campaign = get_dim(5)
                is_new_str = get_dim(6)
                device = get_dim(7)
                browser = get_dim(8)
                os = get_dim(9)
                country = get_dim(10)
                city = get_dim(11)

                # Parse date
                try:
                    occurred_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.utcnow()
                except ValueError:
                    occurred_at = datetime.utcnow()

                # Parse is_new_visitor
                is_new = None
                if is_new_str:
                    is_new = is_new_str.lower() in ("да", "yes", "1", "true")

                # Determine traffic source type
                traffic_type = self._determine_traffic_type(referrer, utm_source, utm_medium)

                # Get metrics
                metrics = row.get("metrics", [])
                visits = int(metrics[0]) if metrics else 1
                page_views = int(metrics[1]) if len(metrics) > 1 else None
                bounce_rate = float(metrics[2]) if len(metrics) > 2 else None

                normalized.append(NormalizedEventCreate(
                    raw_event_id=raw_event.id,
                    source=SourceType.YANDEX_METRIKA,
                    session_id=f"ym_{raw_event.counter_id}_{date_str}_{idx}",
                    occurred_at=occurred_at,
                    url=url,
                    landing_page=url,
                    referrer=referrer,
                    utm_source=utm_source,
                    utm_medium=utm_medium,
                    utm_campaign=utm_campaign,
                    traffic_source_type=traffic_type,
                    device_type=device,
                    browser=browser,
                    os=os,
                    country=country,
                    city=city,
                    page_views=page_views or visits,
                    is_new_visitor=is_new,
                    is_bounce=bounce_rate is not None and bounce_rate > 80,
                ))

            except Exception as e:
                logger.warning(f"Failed to normalize row {idx}: {e}")
                continue

        return normalized

    def _normalize_generic(
        self,
        raw_event: RawEvent,
    ) -> list[NormalizedEventCreate]:
        """
        Generic normalization for other sources (GA4, etc.).
        
        For GA4, raw_data contains {"events": [VisitEvent.model_dump(), ...]}
        We need to convert these to NormalizedEventCreate.
        """
        normalized = []
        raw_data = raw_event.raw_data
        
        # Handle GA4 format: {"events": [VisitEvent dicts]}
        if raw_event.source == SourceType.GOOGLE_ANALYTICS:
            events = raw_data.get("events", [])
            
            for event_dict in events:
                try:
                    # VisitEvent already has normalized format, just convert to NormalizedEventCreate
                    normalized_event = NormalizedEventCreate(
                        raw_event_id=raw_event.id,
                        source=SourceType.GOOGLE_ANALYTICS,
                        session_id=event_dict.get("session_id"),
                        user_id=event_dict.get("user_id"),
                        client_id=event_dict.get("client_id"),
                        occurred_at=self._parse_datetime(event_dict.get("occurred_at")),
                        url=event_dict.get("url"),
                        landing_page=event_dict.get("landing_page"),
                        exit_page=event_dict.get("exit_page"),
                        referrer=event_dict.get("referrer"),
                        utm_source=event_dict.get("utm_source"),
                        utm_medium=event_dict.get("utm_medium"),
                        utm_campaign=event_dict.get("utm_campaign"),
                        utm_term=event_dict.get("utm_term"),
                        utm_content=event_dict.get("utm_content"),
                        traffic_source_type=self._parse_traffic_type(event_dict.get("traffic_source_type")),
                        device_type=event_dict.get("device_type"),
                        browser=event_dict.get("browser"),
                        os=event_dict.get("os"),
                        screen_resolution=event_dict.get("screen_resolution"),
                        country=event_dict.get("country"),
                        region=event_dict.get("region"),
                        city=event_dict.get("city"),
                        page_views=event_dict.get("page_views"),
                        raw_visit_duration=event_dict.get("raw_visit_duration"),
                        events_count=event_dict.get("events_count"),
                        is_new_visitor=event_dict.get("is_new_visitor"),
                        is_bounce=event_dict.get("is_bounce"),
                        search_phrase=event_dict.get("search_phrase"),
                        internal_search_query=event_dict.get("internal_search_query"),
                        goals_reached=event_dict.get("goals_reached"),
                    )
                    normalized.append(normalized_event)
                except Exception as e:
                    logger.warning(f"Failed to normalize GA4 event: {e}")
                    continue
        
        return normalized
    
    def _parse_datetime(self, value: Any) -> datetime:
        """Parse datetime from various formats."""
        if value is None:
            return datetime.utcnow()
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try ISO format
                if 'T' in value or ' ' in value:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                # Try date only
                return datetime.combine(datetime.fromisoformat(value).date(), datetime.min.time())
            except Exception:
                pass
        
        return datetime.utcnow()
    
    def _parse_traffic_type(self, value: Any) -> Optional[TrafficSourceType]:
        """Parse traffic source type."""
        if value is None:
            return None
        
        if isinstance(value, TrafficSourceType):
            return value
        
        if isinstance(value, str):
            try:
                return TrafficSourceType(value.lower())
            except ValueError:
                pass
        
        return None

    def _determine_traffic_type(
        self,
        referrer: Optional[str],
        utm_source: Optional[str],
        utm_medium: Optional[str],
    ) -> Optional[TrafficSourceType]:
        """Determine traffic source type from UTM and referrer."""
        if utm_medium:
            medium_lower = utm_medium.lower()
            if medium_lower in ("cpc", "ppc", "paid", "cpm"):
                return TrafficSourceType.PAID
            elif medium_lower in ("email", "newsletter"):
                return TrafficSourceType.EMAIL
            elif medium_lower in ("social", "smm"):
                return TrafficSourceType.SOCIAL
            elif medium_lower == "organic":
                return TrafficSourceType.ORGANIC
            elif medium_lower == "referral":
                return TrafficSourceType.REFERRAL

        if referrer:
            ref_lower = referrer.lower()
            if any(s in ref_lower for s in ["google", "yandex", "bing", "duckduckgo"]):
                return TrafficSourceType.ORGANIC
            elif any(s in ref_lower for s in ["facebook", "instagram", "vk.com", "twitter", "tiktok"]):
                return TrafficSourceType.SOCIAL
            elif referrer:
                return TrafficSourceType.REFERRAL

        if not referrer and not utm_source:
            return TrafficSourceType.DIRECT

        return TrafficSourceType.OTHER

    async def _calculate_and_save_features(
        self,
        normalized_events: list[NormalizedEvent],
    ) -> int:
        """Calculate features and save to L3 (Feature Store)."""
        features_list = []

        for event in normalized_events:
            try:
                # TODO: Fetch user history for better feature calculation
                # user_history = await self._get_user_history(event.user_id or event.client_id)

                features = self.calculator.calculate_features(event, user_history=None)
                features_list.append(features)

            except Exception as e:
                logger.warning(f"Failed to calculate features for {event.id}: {e}")
                continue

        if features_list:
            await self.storage.save_features_batch(features_list)

        return len(features_list)

    async def process_pending_raw_events(
        self,
        source: Optional[SourceType] = None,
        limit: int = 100,
    ) -> PipelineStatus:
        """
        Process pending raw events that weren't fully processed.

        Useful for retry logic or batch processing.
        """
        batch_id = f"retry_{uuid4().hex[:8]}"
        started_at = datetime.utcnow()
        start_time = time.time()

        status = PipelineStatus(
            batch_id=batch_id,
            status="running",
            started_at=started_at,
        )

        try:
            pending = await self.storage.get_pending_raw_events(source, limit)
            status.raw_count = len(pending)

            if not pending:
                status.status = "completed"
                status.completed_at = datetime.utcnow()
                return status

            # Normalize and save
            normalized = await self._normalize_and_save(pending)
            status.normalized_count = len(normalized)

            # Calculate features
            features_count = await self._calculate_and_save_features(normalized)
            status.features_count = features_count

            status.status = "completed"
            status.completed_at = datetime.utcnow()
            status.duration_ms = int((time.time() - start_time) * 1000)

        except Exception as e:
            status.status = "failed"
            status.errors.append(str(e))

        return status


# Singleton instance
_pipeline_instance: Optional[DataIntakePipeline] = None


def get_pipeline() -> DataIntakePipeline:
    """Get or create the pipeline instance."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DataIntakePipeline()
    return _pipeline_instance


def reset_pipeline() -> None:
    """Reset pipeline instance (for testing)."""
    global _pipeline_instance
    _pipeline_instance = None
