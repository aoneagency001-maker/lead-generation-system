"""
Yandex.Metrika Analytics Provider

Fetches analytics data from Yandex.Metrika API and transforms it
into normalized VisitEvent format.

Environment Variables:
    YANDEX_METRIKA_TOKEN: OAuth token for API access
    YANDEX_METRIKA_COUNTER_ID: Counter ID to fetch data from

API Documentation:
    https://yandex.ru/dev/metrika/doc/api2/api_v1/intro.html
"""

import logging
import os
from datetime import date, datetime
from typing import Any, Optional

import httpx

from data_intake.models import SourceType, VisitEvent
from data_intake.providers.base import (
    BaseAnalyticsProvider,
    ProviderAPIError,
    ProviderAuthError,
    ProviderConfigError,
)

logger = logging.getLogger(__name__)

# API Configuration
METRIKA_API_BASE = "https://api-metrika.yandex.net"
REPORTING_API_URL = f"{METRIKA_API_BASE}/stat/v1/data"
DEFAULT_LIMIT = 10000
REQUEST_TIMEOUT = 30.0


class YandexMetrikaProvider(BaseAnalyticsProvider):
    """
    Yandex.Metrika provider implementation.

    Uses Reporting API (stat/v1/data) for fetching aggregated visit data.

    Note on active_time_sec:
        Currently uses visitDuration from Reporting API which includes
        total time (including AFK). For accurate "active time" calculation,
        we would need to use Logs API with detailed hit-level data.
        TODO: Implement Logs API integration for precise active time tracking.
    """

    source_type = SourceType.YANDEX_METRIKA

    def __init__(
        self,
        token: Optional[str] = None,
        counter_id: Optional[str] = None,
    ):
        """
        Initialize Yandex.Metrika provider.

        Args:
            token: OAuth token (defaults to YANDEX_METRIKA_TOKEN env var)
            counter_id: Counter ID (defaults to YANDEX_METRIKA_COUNTER_ID env var)

        Raises:
            ProviderConfigError: If required configuration is missing
        """
        self.token = token or os.getenv("YANDEX_METRIKA_TOKEN")
        self.counter_id = counter_id or os.getenv("YANDEX_METRIKA_COUNTER_ID")

        if not self.token:
            raise ProviderConfigError(
                "YANDEX_METRIKA_TOKEN is not set",
                source=self.source_type,
            )
        if not self.counter_id:
            raise ProviderConfigError(
                "YANDEX_METRIKA_COUNTER_ID is not set",
                source=self.source_type,
            )

    async def fetch_visits(
        self,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visit data from Yandex.Metrika Reporting API.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit: Maximum number of records (default: 10000)

        Returns:
            List of normalized VisitEvent objects

        Raises:
            ProviderAuthError: If OAuth token is invalid
            ProviderAPIError: If API request fails
        """
        effective_limit = limit or DEFAULT_LIMIT

        # Build request parameters
        # Using dimensions to get per-visit breakdown
        params = {
            "ids": self.counter_id,
            "date1": date_from.isoformat(),
            "date2": date_to.isoformat(),
            "metrics": "ym:s:visits",
            "dimensions": ",".join([
                "ym:s:date",
                "ym:s:startURL",
                "ym:s:referer",
                "ym:s:UTMSource",
                "ym:s:UTMMedium",
                "ym:s:UTMCampaign",
                "ym:s:isNewUser",
            ]),
            "limit": str(effective_limit),
            "accuracy": "full",
        }

        headers = {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json",
        }

        logger.info(
            f"Fetching visits from Yandex.Metrika: "
            f"counter={self.counter_id}, period={date_from} to {date_to}"
        )

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    REPORTING_API_URL,
                    params=params,
                    headers=headers,
                )
            except httpx.TimeoutException as e:
                logger.error(f"Yandex.Metrika API timeout: {e}")
                raise ProviderAPIError(
                    "API request timed out",
                    source=self.source_type,
                )
            except httpx.RequestError as e:
                logger.error(f"Yandex.Metrika API request error: {e}")
                raise ProviderAPIError(
                    f"API request failed: {e}",
                    source=self.source_type,
                )

        # Handle response
        if response.status_code == 401:
            logger.error("Yandex.Metrika authentication failed")
            raise ProviderAuthError(
                "Invalid OAuth token",
                source=self.source_type,
            )

        if response.status_code == 403:
            logger.error("Yandex.Metrika access denied")
            raise ProviderAuthError(
                "Access denied - check token permissions",
                source=self.source_type,
            )

        if response.status_code != 200:
            logger.error(
                f"Yandex.Metrika API error: status={response.status_code}, "
                f"body={response.text[:500]}"
            )
            raise ProviderAPIError(
                f"API returned status {response.status_code}",
                source=self.source_type,
                status_code=response.status_code,
                response_body=response.text[:1000],
            )

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Failed to parse Yandex.Metrika response: {e}")
            raise ProviderAPIError(
                "Failed to parse API response",
                source=self.source_type,
            )

        # Transform to normalized events
        events = self._transform_response(data)

        logger.info(f"Fetched {len(events)} visits from Yandex.Metrika")
        return events

    def _transform_response(self, data: dict[str, Any]) -> list[VisitEvent]:
        """
        Transform Yandex.Metrika API response to normalized VisitEvent list.

        Response structure:
        {
            "data": [
                {
                    "dimensions": [
                        {"name": "2025-11-22"},  # date
                        {"name": "https://..."},  # startURL
                        {"name": "https://..."},  # referer
                        {"name": "google"},  # UTMSource
                        {"name": "cpc"},  # UTMMedium
                        {"name": "campaign1"},  # UTMCampaign
                        {"name": "Да"/"Нет"},  # isNewUser
                    ],
                    "metrics": [5.0]  # visits count
                },
                ...
            ],
            "query": {...},
            "totals": [...]
        }
        """
        events: list[VisitEvent] = []

        rows = data.get("data", [])
        if not rows:
            logger.warning("No data returned from Yandex.Metrika")
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

        if len(dimensions) < 7:
            logger.warning(f"Row {idx} has incomplete dimensions: {len(dimensions)}")
            return None

        # Extract dimension values (they come as {"name": "value"} or {"id": X, "name": "..."})
        def get_dim_value(dim: dict) -> Optional[str]:
            val = dim.get("name", "")
            if val in ("", "null", "(not set)", "(прямой трафик)"):
                return None
            return val

        date_str = get_dim_value(dimensions[0])
        start_url = get_dim_value(dimensions[1])
        referer = get_dim_value(dimensions[2])
        utm_source = get_dim_value(dimensions[3])
        utm_medium = get_dim_value(dimensions[4])
        utm_campaign = get_dim_value(dimensions[5])
        is_new_user_str = get_dim_value(dimensions[6])

        # Parse date
        try:
            occurred_at = datetime.strptime(date_str, "%Y-%m-%d") if date_str else datetime.now()
        except ValueError:
            occurred_at = datetime.now()

        # Parse isNewUser ("Да" = Yes, "Нет" = No in Russian)
        is_new_visitor = None
        if is_new_user_str:
            is_new_visitor = is_new_user_str.lower() in ("да", "yes", "1", "true")

        # Get visits count from metrics
        visits_count = int(metrics[0]) if metrics else 1

        # Generate unique event ID
        event_id = f"ym_{self.counter_id}_{date_str}_{idx}"

        return VisitEvent(
            event_id=event_id,
            source=self.source_type,
            session_id=None,  # Not available in Reporting API aggregated data
            occurred_at=occurred_at,
            url=start_url,
            referrer=referer,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            is_new_visitor=is_new_visitor,
            page_views=visits_count,  # Using visits count as aggregation
            # TODO: active_time_sec requires Logs API for accurate calculation
            # Currently not available in this aggregated endpoint
            active_time_sec=None,
            visit_number=None,
            user_id=None,
            user_agent=None,
            ip=None,
        )

    async def health_check(self) -> bool:
        """
        Check if provider can connect to Yandex.Metrika API.

        Returns:
            True if API is accessible and token is valid
        """
        headers = {"Authorization": f"OAuth {self.token}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{METRIKA_API_BASE}/management/v1/counters",
                    headers=headers,
                    params={"per_page": 1},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Yandex.Metrika health check failed: {e}")
            return False

    async def get_counter_info(self) -> Optional[dict[str, Any]]:
        """
        Get information about the configured counter.

        Returns:
            Counter info dict or None if failed
        """
        headers = {"Authorization": f"OAuth {self.token}"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{METRIKA_API_BASE}/management/v1/counter/{self.counter_id}",
                    headers=headers,
                )
                if response.status_code == 200:
                    return response.json().get("counter")
                return None
        except Exception as e:
            logger.error(f"Failed to get counter info: {e}")
            return None
