"""
Data Intake Service Layer

Provides a unified interface for fetching analytics data from multiple sources.
Handles provider registration and orchestrates data collection.
"""

import asyncio
import logging
from datetime import date
from typing import Optional

from data_intake.models import SourceType, VisitEvent
from data_intake.providers.base import (
    BaseAnalyticsProvider,
    ProviderConfigError,
    ProviderError,
)
from data_intake.providers.yandex_metrika import YandexMetrikaProvider
from data_intake.providers.google_analytics import GoogleAnalyticsProvider

logger = logging.getLogger(__name__)


class DataIntakeService:
    """
    Main service for data intake operations.

    Manages multiple analytics providers and provides unified interface
    for fetching normalized data from different sources.

    Usage:
        service = DataIntakeService()
        visits = await service.fetch_visits_from_source(
            SourceType.YANDEX_METRIKA,
            date(2025, 11, 1),
            date(2025, 11, 22)
        )

    To add new providers:
        service.register_provider(SourceType.GOOGLE_ANALYTICS, GoogleAnalyticsProvider())
    """

    def __init__(self, auto_register: bool = True):
        """
        Initialize DataIntakeService.

        Args:
            auto_register: If True, automatically register available providers
                          based on environment configuration
        """
        self.providers: dict[SourceType, BaseAnalyticsProvider] = {}

        if auto_register:
            self._auto_register_providers()

    def _auto_register_providers(self) -> None:
        """
        Auto-register providers based on available configuration.

        Attempts to create and register each provider. If configuration
        is missing (env vars), the provider is skipped with a warning.
        """
        # Try to register Yandex.Metrika
        try:
            yandex_provider = YandexMetrikaProvider()
            self.register_provider(SourceType.YANDEX_METRIKA, yandex_provider)
            logger.info("Registered Yandex.Metrika provider")
        except ProviderConfigError as e:
            logger.warning(f"Yandex.Metrika provider not configured: {e.message}")

        # Try to register Google Analytics 4
        try:
            ga_provider = GoogleAnalyticsProvider()
            self.register_provider(SourceType.GOOGLE_ANALYTICS, ga_provider)
            logger.info("Registered Google Analytics 4 provider")
        except ProviderConfigError as e:
            logger.warning(f"Google Analytics provider not configured: {e.message}")

    def register_provider(
        self,
        source: SourceType,
        provider: BaseAnalyticsProvider,
    ) -> None:
        """
        Register an analytics provider.

        Args:
            source: Source type identifier
            provider: Provider instance

        Raises:
            ValueError: If provider is already registered for this source
        """
        if source in self.providers:
            logger.warning(f"Overwriting existing provider for {source}")

        self.providers[source] = provider
        logger.debug(f"Registered provider for {source}")

    def unregister_provider(self, source: SourceType) -> bool:
        """
        Unregister a provider.

        Args:
            source: Source type to unregister

        Returns:
            True if provider was unregistered, False if not found
        """
        if source in self.providers:
            del self.providers[source]
            logger.debug(f"Unregistered provider for {source}")
            return True
        return False

    def get_registered_sources(self) -> list[SourceType]:
        """Return list of registered source types."""
        return list(self.providers.keys())

    def is_source_available(self, source: SourceType) -> bool:
        """Check if a source is registered and available."""
        return source in self.providers

    async def fetch_visits_from_source(
        self,
        source: SourceType,
        date_from: date,
        date_to: date,
        limit: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visits from a specific source.

        Args:
            source: Source type to fetch from
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit: Maximum number of records

        Returns:
            List of normalized VisitEvent objects

        Raises:
            ValueError: If source is not registered
            ProviderError: If provider fails to fetch data
        """
        if source not in self.providers:
            available = ", ".join(s.value for s in self.providers.keys())
            raise ValueError(
                f"Source '{source.value}' is not registered. "
                f"Available sources: {available or 'none'}"
            )

        provider = self.providers[source]
        logger.info(f"Fetching visits from {source.value}: {date_from} to {date_to}")

        try:
            events = await provider.fetch_visits(date_from, date_to, limit)
            logger.info(f"Fetched {len(events)} visits from {source.value}")
            return events
        except ProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching from {source.value}: {e}")
            raise ProviderError(
                f"Unexpected error: {e}",
                source=source,
            )

    async def fetch_all_visits(
        self,
        date_from: date,
        date_to: date,
        limit_per_source: Optional[int] = None,
    ) -> list[VisitEvent]:
        """
        Fetch visits from all registered sources.

        Runs all provider fetches concurrently and aggregates results.

        Args:
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            limit_per_source: Maximum records per source

        Returns:
            Combined list of VisitEvent from all sources

        Note:
            If a provider fails, its errors are logged but other
            providers continue. Partial results may be returned.
        """
        if not self.providers:
            logger.warning("No providers registered")
            return []

        async def fetch_with_error_handling(
            source: SourceType,
            provider: BaseAnalyticsProvider,
        ) -> list[VisitEvent]:
            try:
                return await provider.fetch_visits(date_from, date_to, limit_per_source)
            except Exception as e:
                logger.error(f"Failed to fetch from {source.value}: {e}")
                return []

        # Run all fetches concurrently
        tasks = [
            fetch_with_error_handling(source, provider)
            for source, provider in self.providers.items()
        ]

        results = await asyncio.gather(*tasks)

        # Flatten results
        all_events: list[VisitEvent] = []
        for events in results:
            all_events.extend(events)

        logger.info(
            f"Fetched {len(all_events)} total visits from "
            f"{len(self.providers)} sources"
        )
        return all_events

    async def health_check_all(self) -> dict[SourceType, bool]:
        """
        Run health checks on all registered providers.

        Returns:
            Dict mapping source type to health status
        """
        results: dict[SourceType, bool] = {}

        for source, provider in self.providers.items():
            try:
                results[source] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {source.value}: {e}")
                results[source] = False

        return results


# Singleton instance for convenience
_default_service: Optional[DataIntakeService] = None


def get_data_intake_service() -> DataIntakeService:
    """
    Get or create the default DataIntakeService instance.

    Returns:
        Shared DataIntakeService instance
    """
    global _default_service
    if _default_service is None:
        _default_service = DataIntakeService()
    return _default_service


def reset_data_intake_service() -> None:
    """Reset the default service instance (useful for testing)."""
    global _default_service
    _default_service = None
