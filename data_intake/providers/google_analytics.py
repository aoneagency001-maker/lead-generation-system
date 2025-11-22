"""
Google Analytics 4 Provider for Data Intake

Fetches analytics data from GA4 Data API and transforms it
into normalized VisitEvent format for the Data Intake pipeline.

Uses existing GoogleAnalyticsClient from library/integrations/google_analytics.py

Environment Variables:
    GOOGLE_ANALYTICS_CREDENTIALS_PATH: Path to service account JSON
    GOOGLE_ANALYTICS_PROPERTY_ID: Property ID to fetch data from
"""

import logging
import os
from datetime import date, datetime
from typing import Any, Optional

from data_intake.models import SourceType, VisitEvent
from data_intake.providers.base import (
    BaseAnalyticsProvider,
    ProviderAPIError,
    ProviderAuthError,
    ProviderConfigError,
)

logger = logging.getLogger(__name__)

# Default settings
DEFAULT_LIMIT = 10000


class GoogleAnalyticsProvider(BaseAnalyticsProvider):
    """
    Google Analytics 4 provider implementation for Data Intake.

    Uses GA4 Data API v1 for fetching visit data.
    Transforms GA4 reports into normalized VisitEvent format.
    """

    source_type = SourceType.GOOGLE_ANALYTICS

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        property_id: Optional[str] = None,
    ):
        """
        Initialize Google Analytics 4 provider.

        Args:
            credentials_path: Path to service account JSON (defaults to env)
            property_id: Property ID (defaults to env)

        Raises:
            ProviderConfigError: If required configuration is missing
        """
        self.credentials_path = credentials_path or os.getenv("GOOGLE_ANALYTICS_CREDENTIALS_PATH")
        self.property_id = property_id or os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID")

        if not self.credentials_path:
            raise ProviderConfigError(
                "GOOGLE_ANALYTICS_CREDENTIALS_PATH is not set",
                source=self.source_type,
            )

        if not os.path.exists(self.credentials_path):
            raise ProviderConfigError(
                f"Credentials file not found: {self.credentials_path}",
                source=self.source_type,
            )

        if not self.property_id:
            raise ProviderConfigError(
                "GOOGLE_ANALYTICS_PROPERTY_ID is not set",
                source=self.source_type,
            )

        # Initialize the existing GA4 client
        try:
            from library.integrations.google_analytics import GoogleAnalyticsClient
            self._client = GoogleAnalyticsClient(
                credentials_path=self.credentials_path,
                property_id=self.property_id
            )
            logger.info(f"GoogleAnalyticsProvider initialized for property: {self.property_id}")
        except Exception as e:
            logger.error(f"Failed to initialize GA4 client: {e}")
            raise ProviderConfigError(
                f"Failed to initialize GA4 client: {e}",
                source=self.source_type,
            )

    async def fetch_visits(
        self,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visit data from Google Analytics 4 Data API.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit: Maximum number of records (default: 10000)

        Returns:
            List of normalized VisitEvent objects

        Raises:
            ProviderAuthError: If credentials are invalid
            ProviderAPIError: If API request fails
        """
        effective_limit = limit or DEFAULT_LIMIT

        logger.info(
            f"Fetching visits from GA4: "
            f"property={self.property_id}, period={date_from} to {date_to}"
        )

        try:
            # Fetch recent visits with full dimensions
            report = await self._client.get_report(
                property_id=self.property_id,
                metrics=["sessions", "activeUsers", "screenPageViews", "bounceRate", "averageSessionDuration"],
                date1=date_from.isoformat(),
                date2=date_to.isoformat(),
                dimensions=[
                    "date",
                    "sessionSource",
                    "sessionMedium",
                    "sessionCampaignName",
                    "landingPage",
                    "country",
                    "city",
                    "deviceCategory",
                    "newVsReturning",
                ],
                limit=effective_limit,
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                raise ProviderAuthError(
                    "Invalid GA4 credentials",
                    source=self.source_type,
                )
            logger.error(f"GA4 API error: {e}")
            raise ProviderAPIError(
                f"GA4 API request failed: {e}",
                source=self.source_type,
            )

        # Transform to normalized events
        events = self._transform_response(report)

        logger.info(f"Fetched {len(events)} visits from GA4")
        return events

    def _transform_response(self, data: dict[str, Any]) -> list[VisitEvent]:
        """
        Transform GA4 API response to normalized VisitEvent list.

        GA4 report structure:
        {
            "data": [
                {
                    "dimensions": ["2025-11-22", "google", "organic", ...],
                    "metrics": [sessions, users, pageviews, bounceRate, avgDuration]
                },
                ...
            ],
            "totals": [...],
            "row_count": N
        }
        """
        events: list[VisitEvent] = []

        rows = data.get("data", [])
        if not rows:
            logger.warning("No data returned from GA4")
            return events

        for idx, row in enumerate(rows):
            try:
                event = self._parse_row(row, idx)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse row {idx}: {e}")
                continue

        return events

    def _parse_row(self, row: dict[str, Any], idx: int) -> Optional[VisitEvent]:
        """Parse a single data row into VisitEvent."""
        dimensions = row.get("dimensions", [])
        metrics = row.get("metrics", [])

        # Dimensions: date, source, medium, campaign, landingPage, country, city, device, newVsReturning
        if len(dimensions) < 9:
            logger.warning(f"Row {idx} has incomplete dimensions: {len(dimensions)}")
            return None

        def safe_get(lst: list, index: int, default: Any = None) -> Any:
            try:
                val = lst[index]
                if val in ("(not set)", "(none)", "(direct)", ""):
                    return default
                return val
            except IndexError:
                return default

        date_str = safe_get(dimensions, 0)
        source = safe_get(dimensions, 1)
        medium = safe_get(dimensions, 2)
        campaign = safe_get(dimensions, 3)
        landing_page = safe_get(dimensions, 4)
        country = safe_get(dimensions, 5)
        city = safe_get(dimensions, 6)
        device = safe_get(dimensions, 7)
        new_vs_returning = safe_get(dimensions, 8)

        # Parse date
        try:
            # GA4 returns date as YYYYMMDD
            if date_str and len(date_str) == 8:
                occurred_at = datetime.strptime(date_str, "%Y%m%d")
            elif date_str:
                occurred_at = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                occurred_at = datetime.now()
        except ValueError:
            occurred_at = datetime.now()

        # Parse metrics
        sessions = int(metrics[0]) if len(metrics) > 0 and metrics[0] else 1
        users = int(metrics[1]) if len(metrics) > 1 and metrics[1] else 1
        pageviews = int(metrics[2]) if len(metrics) > 2 and metrics[2] else 0
        bounce_rate = float(metrics[3]) if len(metrics) > 3 and metrics[3] else None
        avg_duration = float(metrics[4]) if len(metrics) > 4 and metrics[4] else None

        # Determine if new visitor
        is_new_visitor = None
        if new_vs_returning:
            is_new_visitor = new_vs_returning.lower() == "new"

        # Map medium to utm_medium
        utm_medium = medium
        if medium:
            medium_lower = medium.lower()
            if medium_lower in ["cpc", "ppc", "paid"]:
                utm_medium = "cpc"
            elif medium_lower == "organic":
                utm_medium = "organic"
            elif medium_lower == "referral":
                utm_medium = "referral"
            elif medium_lower in ["social", "social-media"]:
                utm_medium = "social"

        # Generate unique event ID
        event_id = f"ga4_{self.property_id}_{date_str}_{idx}"

        return VisitEvent(
            event_id=event_id,
            source=self.source_type,
            session_id=None,  # Not available in aggregated reports
            occurred_at=occurred_at,
            url=landing_page,
            referrer=None,  # Not directly available
            utm_source=source,
            utm_medium=utm_medium,
            utm_campaign=campaign,
            is_new_visitor=is_new_visitor,
            page_views=pageviews,
            active_time_sec=int(avg_duration) if avg_duration else None,
            visit_number=None,
            user_id=None,
            user_agent=None,
            ip=None,
            # Extended fields
            country=country,
            city=city,
            device_type=device,
            bounce_rate=bounce_rate,
        )

    async def health_check(self) -> bool:
        """
        Check if provider can connect to GA4 API.

        Returns:
            True if API is accessible and credentials are valid
        """
        try:
            properties = await self._client.get_properties()
            return len(properties) > 0
        except Exception as e:
            logger.error(f"GA4 health check failed: {e}")
            return False

    async def get_property_info(self) -> Optional[dict[str, Any]]:
        """
        Get information about the configured property.

        Returns:
            Property info dict or None if failed
        """
        try:
            properties = await self._client.get_properties()
            for prop in properties:
                if prop.get("id") == self.property_id.replace("properties/", ""):
                    return prop
            return None
        except Exception as e:
            logger.error(f"Failed to get property info: {e}")
            return None

    async def fetch_raw_for_storage(
        self,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Fetch raw data from GA4 for storage in L1 (raw_events).

        This method returns the raw API response without transformation,
        suitable for storing in the raw_events table.

        Args:
            date_from: Start date
            date_to: End date
            limit: Maximum records

        Returns:
            Raw API response as dict
        """
        effective_limit = limit or DEFAULT_LIMIT

        try:
            report = await self._client.get_report(
                property_id=self.property_id,
                metrics=["sessions", "activeUsers", "screenPageViews", "bounceRate", "averageSessionDuration"],
                date1=date_from.isoformat(),
                date2=date_to.isoformat(),
                dimensions=[
                    "date",
                    "sessionSource",
                    "sessionMedium",
                    "sessionCampaignName",
                    "landingPage",
                    "country",
                    "city",
                    "deviceCategory",
                    "newVsReturning",
                ],
                limit=effective_limit,
            )
            return {
                "source": "google_analytics",
                "property_id": self.property_id,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "api_version": "v1beta",
                "response": report,
            }
        except Exception as e:
            logger.error(f"Failed to fetch raw GA4 data: {e}")
            raise ProviderAPIError(
                f"Failed to fetch raw data: {e}",
                source=self.source_type,
            )
