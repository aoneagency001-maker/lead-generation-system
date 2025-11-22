"""
Base Analytics Provider Interface

Defines the abstract interface that all analytics providers must implement.
New providers (Google Analytics, Yandex.Maps, etc.) should inherit from
BaseAnalyticsProvider and implement all abstract methods.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from data_intake.models import SourceType, VisitEvent


class ProviderError(Exception):
    """Base exception for provider errors."""

    def __init__(self, message: str, source: Optional[SourceType] = None):
        self.message = message
        self.source = source
        super().__init__(self.message)


class ProviderAuthError(ProviderError):
    """Authentication/authorization error."""
    pass


class ProviderAPIError(ProviderError):
    """API request error."""

    def __init__(
        self,
        message: str,
        source: Optional[SourceType] = None,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ):
        super().__init__(message, source)
        self.status_code = status_code
        self.response_body = response_body


class ProviderConfigError(ProviderError):
    """Configuration error (missing env vars, etc.)."""
    pass


class BaseAnalyticsProvider(ABC):
    """
    Abstract base class for analytics data providers.

    Each provider implementation is responsible for:
    1. Fetching raw data from external API
    2. Transforming data into normalized VisitEvent/PageViewEvent models
    3. Handling provider-specific authentication and errors

    Usage:
        class MyProvider(BaseAnalyticsProvider):
            source_type = SourceType.MY_SOURCE

            async def fetch_visits(self, date_from, date_to):
                # Implementation
                ...

    Note:
        Providers should NOT depend on FastAPI or any web framework.
        They only interact with external APIs and return normalized data.
    """

    source_type: SourceType = SourceType.OTHER

    @abstractmethod
    async def fetch_visits(
        self,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visit/session data for the specified date range.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit: Maximum number of records to return (optional)

        Returns:
            List of normalized VisitEvent objects

        Raises:
            ProviderAuthError: If authentication fails
            ProviderAPIError: If API request fails
            ProviderConfigError: If provider is not properly configured
        """
        raise NotImplementedError("Subclasses must implement fetch_visits()")

    async def health_check(self) -> bool:
        """
        Check if provider is properly configured and can connect to API.

        Returns:
            True if provider is healthy, False otherwise
        """
        # Default implementation - can be overridden
        return True

    def get_source_type(self) -> SourceType:
        """Return the source type for this provider."""
        return self.source_type
