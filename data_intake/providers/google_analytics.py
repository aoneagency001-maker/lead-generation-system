"""
Google Analytics 4 Analytics Provider

Fetches analytics data from GA4 Data API and transforms it
into normalized VisitEvent format.

Environment Variables:
    GOOGLE_ANALYTICS_CREDENTIALS_PATH: Path to Service Account JSON file
    GOOGLE_ANALYTICS_PROPERTY_ID: GA4 Property ID (format: "123456789" or "properties/123456789")

API Documentation:
    https://developers.google.com/analytics/devguides/reporting/data/v1
"""

import logging
import os
from datetime import date, datetime
from typing import Any, Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange,
    OrderBy,
)
from google.oauth2 import service_account

from data_intake.models import SourceType, VisitEvent
from data_intake.providers.base import (
    BaseAnalyticsProvider,
    ProviderAPIError,
    ProviderAuthError,
    ProviderConfigError,
)

logger = logging.getLogger(__name__)

# API Configuration
DEFAULT_LIMIT = 10000
REQUEST_TIMEOUT = 30.0


class GoogleAnalyticsProvider(BaseAnalyticsProvider):
    """
    Google Analytics 4 provider implementation.

    Uses Data API v1beta for fetching aggregated visit data.

    Note on active_time_sec:
        GA4 provides sessionDuration metric which includes total time.
        For accurate "active time" calculation, we would need to use
        event-level data with engagement metrics.
        TODO: Implement event-level data fetching for precise active time tracking.
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
            credentials_path: Path to Service Account JSON (defaults to env var)
            property_id: GA4 Property ID (defaults to env var)

        Raises:
            ProviderConfigError: If required configuration is missing
        """
        self.credentials_path = credentials_path or os.getenv(
            "GOOGLE_ANALYTICS_CREDENTIALS_PATH"
        )
        self.property_id = property_id or os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID")

        # Try to get from config if available
        if not self.credentials_path:
            try:
                from core.api.config import settings

                self.credentials_path = settings.google_analytics_credentials_path
            except (ImportError, AttributeError):
                pass

        if not self.property_id:
            try:
                from core.api.config import settings

                self.property_id = settings.google_analytics_property_id
            except (ImportError, AttributeError):
                pass

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

        # Initialize GA4 client
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            self.client = BetaAnalyticsDataClient(credentials=self.credentials)
            logger.info("Google Analytics 4 client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GA4 client: {e}")
            raise ProviderConfigError(
                f"Failed to initialize GA4 client: {e}",
                source=self.source_type,
            )

        # Format property ID
        self.property_id = self._format_property_id(self.property_id)

    def _format_property_id(self, property_id: Optional[str]) -> str:
        """Format property ID to 'properties/XXXXX' format."""
        if not property_id:
            return ""
        if property_id.startswith("properties/"):
            return property_id
        return f"properties/{property_id}"

    async def fetch_visits(
        self,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visit data from GA4 Data API.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit: Maximum number of records (default: 10000)

        Returns:
            List of normalized VisitEvent objects

        Raises:
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API request fails
        """
        if not self.property_id:
            raise ProviderConfigError(
                "GOOGLE_ANALYTICS_PROPERTY_ID is not set",
                source=self.source_type,
            )

        effective_limit = limit or DEFAULT_LIMIT

        logger.info(
            f"Fetching visits from GA4: "
            f"property={self.property_id}, period={date_from} to {date_to}"
        )

        try:
            # Build request
            request = RunReportRequest(
                property=self.property_id,
                date_ranges=[
                    DateRange(
                        start_date=date_from.isoformat(),
                        end_date=date_to.isoformat(),
                    )
                ],
                dimensions=[
                    Dimension(name="date"),
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                    Dimension(name="sessionCampaignName"),
                    Dimension(name="landingPage"),
                    Dimension(name="firstUserDefaultChannelGroup"),
                ],
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="activeUsers"),
                    Metric(name="newUsers"),
                ],
                limit=effective_limit,
                order_bys=[
                    OrderBy(
                        desc=True,
                        metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                    )
                ],
            )

            # Execute request
            response = self.client.run_report(request)

            # Transform to normalized events
            events = self._transform_response(response, date_from)

            logger.info(f"Fetched {len(events)} visits from GA4")
            return events

        except Exception as e:
            error_msg = str(e)
            logger.error(f"GA4 API error: {error_msg}")

            # Check for authentication errors
            if "authentication" in error_msg.lower() or "credentials" in error_msg.lower():
                raise ProviderAuthError(
                    f"GA4 authentication failed: {error_msg}",
                    source=self.source_type,
                )

            # Check for permission errors
            if "permission" in error_msg.lower() or "403" in error_msg:
                raise ProviderAuthError(
                    f"GA4 access denied: {error_msg}",
                    source=self.source_type,
                )

            # Generic API error
            raise ProviderAPIError(
                f"GA4 API request failed: {error_msg}",
                source=self.source_type,
            )

    def _transform_response(
        self, response: Any, default_date: date
    ) -> list[VisitEvent]:
        """
        Transform GA4 API response to normalized VisitEvent list.

        Response structure:
        {
            "dimension_headers": [...],
            "metric_headers": [...],
            "rows": [
                {
                    "dimension_values": [
                        {"value": "20251122"},  # date
                        {"value": "google"},  # sessionSource
                        {"value": "organic"},  # sessionMedium
                        {"value": "campaign1"},  # sessionCampaignName
                        {"value": "https://..."},  # landingPage
                        {"value": "Organic Search"},  # firstUserDefaultChannelGroup
                    ],
                    "metric_values": [
                        {"value": "5"},  # sessions
                        {"value": "4"},  # activeUsers
                        {"value": "2"},  # newUsers
                    ]
                },
                ...
            ]
        }
        """
        events: list[VisitEvent] = []

        rows = list(response.rows) if response.rows else []
        if not rows:
            logger.warning("No data returned from GA4")
            return events

        for idx, row in enumerate(rows):
            try:
                event = self._parse_row(row, default_date, idx)
                if event:
                    events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse GA4 row {idx}: {e}")
                continue

        return events

    def _parse_row(
        self, row: Any, default_date: date, idx: int
    ) -> Optional[VisitEvent]:
        """Parse a single GA4 data row into VisitEvent."""
        dimension_values = row.dimension_values
        metric_values = row.metric_values

        if len(dimension_values) < 6:
            logger.warning(f"Row {idx} has incomplete dimensions: {len(dimension_values)}")
            return None

        # Extract dimension values
        def get_value(dim_val: Any) -> Optional[str]:
            val = dim_val.value if hasattr(dim_val, "value") else str(dim_val)
            if val in ("", "null", "(not set)", "(not provided)"):
                return None
            return val

        date_str = get_value(dimension_values[0])
        session_source = get_value(dimension_values[1])
        session_medium = get_value(dimension_values[2])
        session_campaign = get_value(dimension_values[3])
        landing_page = get_value(dimension_values[4])
        channel_group = get_value(dimension_values[5])

        # Parse date (format: YYYYMMDD)
        try:
            if date_str and len(date_str) == 8:
                occurred_at = datetime.strptime(date_str, "%Y%m%d")
            else:
                occurred_at = datetime.combine(default_date, datetime.min.time())
        except ValueError:
            occurred_at = datetime.combine(default_date, datetime.min.time())

        # Extract metrics
        sessions_count = int(metric_values[0].value) if len(metric_values) > 0 and hasattr(metric_values[0], "value") else 1
        active_users = int(metric_values[1].value) if len(metric_values) > 1 and hasattr(metric_values[1], "value") else 0
        new_users = int(metric_values[2].value) if len(metric_values) > 2 and hasattr(metric_values[2], "value") else 0

        # Determine if new visitor
        is_new_visitor = new_users > 0 if new_users is not None else None

        # Generate unique event ID
        event_id = f"ga4_{self.property_id.replace('properties/', '')}_{date_str}_{idx}"

        return VisitEvent(
            event_id=event_id,
            source=self.source_type,
            session_id=None,  # Not available in aggregated data
            occurred_at=occurred_at,
            url=landing_page,
            referrer=None,  # Not available in this aggregation
            utm_source=session_source,
            utm_medium=session_medium,
            utm_campaign=session_campaign,
            is_new_visitor=is_new_visitor,
            page_views=sessions_count,  # Using sessions count as aggregation
            # TODO: active_time_sec requires event-level data for accurate calculation
            active_time_sec=None,
            visit_number=None,
            user_id=None,
            user_agent=None,
            ip=None,
        )

    async def health_check(self) -> bool:
        """
        Check if provider can connect to GA4 API.

        Returns:
            True if API is accessible and credentials are valid
        """
        if not self.property_id:
            return False

        try:
            # Try to fetch a minimal report
            request = RunReportRequest(
                property=self.property_id,
                date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
                metrics=[Metric(name="sessions")],
                limit=1,
            )
            self.client.run_report(request)
            return True
        except Exception as e:
            logger.error(f"GA4 health check failed: {e}")
            return False

    async def get_property_info(self) -> Optional[dict[str, Any]]:
        """
        Get information about the configured property.

        Returns:
            Property info dict or None if failed
        """
        # Note: This would require Admin API, which is separate from Data API
        # For now, just return basic info
        return {
            "property_id": self.property_id,
            "source": "GA4",
        }
