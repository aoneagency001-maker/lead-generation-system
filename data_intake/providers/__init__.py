"""
Data Intake Providers

Analytics data providers for different external sources.

Available providers:
- YandexMetrikaProvider: Yandex.Metrika API integration
- (future) GoogleAnalyticsProvider: Google Analytics integration
- (future) YandexMapsProvider: Yandex.Maps/Business integration

Creating a new provider:
    1. Create a new file in this directory (e.g., google_analytics.py)
    2. Inherit from BaseAnalyticsProvider
    3. Implement fetch_visits() and optionally health_check()
    4. Register in DataIntakeService._auto_register_providers()

Example:
    from data_intake.providers.base import BaseAnalyticsProvider
    from data_intake.models import SourceType, VisitEvent

    class MyProvider(BaseAnalyticsProvider):
        source_type = SourceType.OTHER

        async def fetch_visits(self, date_from, date_to, limit=None):
            # Fetch and transform data
            return [VisitEvent(...)]
"""

from data_intake.providers.base import (
    BaseAnalyticsProvider,
    ProviderAPIError,
    ProviderAuthError,
    ProviderConfigError,
    ProviderError,
)
from data_intake.providers.yandex_metrika import YandexMetrikaProvider
from data_intake.providers.google_analytics import GoogleAnalyticsProvider

__all__ = [
    # Base
    "BaseAnalyticsProvider",
    "ProviderError",
    "ProviderAPIError",
    "ProviderAuthError",
    "ProviderConfigError",
    # Providers
    "YandexMetrikaProvider",
    "GoogleAnalyticsProvider",
]
