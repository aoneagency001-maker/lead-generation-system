"""
Google Analytics 4 API Client
Клиент для работы с GA4 Data API v1

Использует Service Account credentials из переменной окружения GOOGLE_ANALYTICS_CREDENTIALS_PATH.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    RunRealtimeReportRequest,
    Dimension,
    Metric,
    DateRange,
    OrderBy,
)
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Timeouts
REQUEST_TIMEOUT = 30.0


class GoogleAnalyticsError(Exception):
    """Базовое исключение для ошибок Google Analytics"""
    pass


class GoogleAnalyticsAuthError(GoogleAnalyticsError):
    """Ошибка авторизации"""
    pass


class GoogleAnalyticsAPIError(GoogleAnalyticsError):
    """Ошибка API запроса"""
    def __init__(self, message: str, code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.response = response


class GoogleAnalyticsClient:
    """
    Клиент для работы с Google Analytics 4 Data API
    
    Использует Service Account credentials из переменной окружения.
    """
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        property_id: Optional[str] = None
    ):
        """
        Инициализация клиента
        
        Args:
            credentials_path: Путь к JSON файлу с credentials (service account)
            property_id: ID Property (формат: "123456789" или "properties/123456789")
        """
        # Пробуем получить из переданных параметров, затем из env, затем из config
        self.credentials_path = credentials_path or os.getenv("GOOGLE_ANALYTICS_CREDENTIALS_PATH")
        self.property_id = property_id or os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID")
        
        # Если не нашли в env, пробуем из config (если доступен)
        if not self.credentials_path:
            try:
                from core.api.config import settings
                self.credentials_path = settings.google_analytics_credentials_path
            except ImportError:
                pass
        
        if not self.property_id:
            try:
                from core.api.config import settings
                self.property_id = settings.google_analytics_property_id
            except ImportError:
                pass
        
        if not self.credentials_path:
            raise GoogleAnalyticsAuthError(
                "GOOGLE_ANALYTICS_CREDENTIALS_PATH не установлен. "
                "Установите переменную окружения GOOGLE_ANALYTICS_CREDENTIALS_PATH"
            )
        
        if not os.path.exists(self.credentials_path):
            raise GoogleAnalyticsAuthError(
                f"Файл credentials не найден: {self.credentials_path}"
            )
        
        try:
            # Загружаем credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"]
            )
            
            # Создаем клиент
            self.client = BetaAnalyticsDataClient(credentials=self.credentials)
            
            logger.info(f"✅ GA4 client initialized (credentials: {self.credentials_path})")
            
        except Exception as e:
            logger.error(f"❌ GA4 initialization failed: {e}")
            raise GoogleAnalyticsAuthError(f"Ошибка загрузки credentials: {e}")
    
    def _format_property_id(self, property_id: Optional[str] = None) -> str:
        """
        Форматирует property_id в правильный формат для API
        
        Args:
            property_id: ID Property (может быть "123456789" или "properties/123456789")
        
        Returns:
            Отформатированный property_id: "properties/123456789"
        """
        prop_id = property_id or self.property_id
        if not prop_id:
            raise GoogleAnalyticsAPIError("property_id не указан")
        
        # Если уже в формате "properties/123456789", возвращаем как есть
        if prop_id.startswith("properties/"):
            return prop_id
        
        # Иначе добавляем префикс
        return f"properties/{prop_id}"
    
    async def get_properties(self) -> List[Dict[str, Any]]:
        """
        Получить список всех доступных Properties
        
        Пробует использовать Admin API для получения списка Properties.
        Если Admin API недоступен, возвращает property_id из env, если он указан.
        
        Returns:
            Список словарей с информацией о Properties
        """
        properties = []
        
        # Пробуем использовать Admin API
        try:
            from google.analytics.admin import AnalyticsAdminServiceClient
            from google.analytics.admin_v1alpha.types import ListPropertiesRequest
            
            # Используем сохраненные credentials с расширенными scopes для Admin API
            admin_credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=[
                    "https://www.googleapis.com/auth/analytics.readonly",
                    "https://www.googleapis.com/auth/analytics.manage"
                ]
            )
            
            admin_client = AnalyticsAdminServiceClient(credentials=admin_credentials)
            
            # Пробуем получить список аккаунтов сначала
            try:
                from google.analytics.admin_v1alpha.types import ListAccountsRequest
                accounts_response = admin_client.list_accounts(request=ListAccountsRequest())
                accounts = list(accounts_response)
                
                if accounts:
                    # Используем первый аккаунт для получения Properties
                    account_name = accounts[0].name
                    request = ListPropertiesRequest(filter=f"parent:{account_name}")
                else:
                    # Если аккаунтов нет, пробуем без фильтра (может не сработать)
                    request = ListPropertiesRequest()
            except Exception as e:
                logger.warning(f"Не удалось получить список аккаунтов: {e}, пробуем без фильтра")
                # Пробуем без фильтра
                request = ListPropertiesRequest()
            
            response = admin_client.list_properties(request=request)
            
            for prop in response:
                property_id = prop.name.split('/')[-1] if '/' in prop.name else prop.name
                properties.append({
                    "id": property_id,
                    "name": prop.display_name or "Unnamed Property",
                    "property": f"properties/{property_id}"
                })
            
            if properties:
                logger.info(f"✅ Получено {len(properties)} Properties через Admin API")
                return properties
        except ImportError:
            logger.warning("Admin API не установлен. Используйте: pip install google-analytics-admin")
        except Exception as e:
            logger.warning(f"Не удалось получить Properties через Admin API: {e}")
        
        # Fallback: возвращаем property_id из env, если он указан
        if self.property_id:
            property_id = self.property_id.replace("properties/", "")
            return [{
                "id": property_id,
                "name": "Default Property",
                "property": self._format_property_id()
            }]
        
        return []
    
    async def get_report(
        self,
        property_id: Optional[str] = None,
        metrics: List[str] = None,
        date1: str = None,
        date2: str = None,
        dimensions: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Получить отчет через Data API v1
        
        Args:
            property_id: ID Property (формат: "123456789" или "properties/123456789")
            metrics: Список метрик (например: ["sessions", "activeUsers"])
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            dimensions: Опциональные измерения
            limit: Лимит результатов
            order_by: Сортировка (например: {"metric": {"metric_name": "sessions"}, "descending": True})
        
        Returns:
            Словарь с данными отчета
        """
        if not metrics:
            raise GoogleAnalyticsAPIError("metrics обязательны")
        
        if not date1 or not date2:
            raise GoogleAnalyticsAPIError("date1 и date2 обязательны")
        
        try:
            request = RunReportRequest(
                property=self._format_property_id(property_id),
                date_ranges=[DateRange(start_date=date1, end_date=date2)],
                metrics=[Metric(name=m) for m in metrics],
                dimensions=[Dimension(name=d) for d in dimensions] if dimensions else [],
                limit=limit,
            )
            
            # Добавляем сортировку, если указана
            if order_by:
                # Правильный формат для GA4 API
                if "metric" in order_by:
                    metric_name = order_by["metric"].get("metric_name", "sessions")
                    desc = order_by.get("descending", True)
                    request.order_bys = [
                        OrderBy(
                            metric=OrderBy.MetricOrderBy(metric_name=metric_name),
                            desc=desc
                        )
                    ]
                elif "dimension" in order_by:
                    dimension_name = order_by["dimension"].get("dimension_name", "date")
                    desc = order_by.get("descending", True)
                    request.order_bys = [
                        OrderBy(
                            dimension=OrderBy.DimensionOrderBy(dimension_name=dimension_name),
                            desc=desc
                        )
                    ]
                else:
                    # Fallback для старого формата
                    request.order_bys = [OrderBy(**order_by)]
            
            response = self.client.run_report(request)
            
            # Преобразуем в формат, аналогичный Метрике
            data = []
            for row in response.rows:
                row_data = {
                    "dimensions": [d.value for d in row.dimension_values],
                    "metrics": [float(m.value) if m.value else 0.0 for m in row.metric_values]
                }
                data.append(row_data)
            
            totals = []
            if response.totals:
                totals = [float(m.value) if m.value else 0.0 for m in response.totals[0].metric_values]
            
            return {
                "data": data,
                "totals": totals,
                "row_count": len(data)
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета GA4: {e}")
            raise GoogleAnalyticsAPIError(f"Ошибка получения отчета: {e}")
    
    async def get_realtime_report(
        self,
        property_id: Optional[str] = None,
        metrics: List[str] = None,
        dimensions: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Получить real-time отчет (последние 30 минут)
        
        Args:
            property_id: ID Property
            metrics: Список метрик
            dimensions: Опциональные измерения
        
        Returns:
            Словарь с real-time данными
        """
        if not metrics:
            raise GoogleAnalyticsAPIError("metrics обязательны")
        
        try:
            request = RunRealtimeReportRequest(
                property=self._format_property_id(property_id),
                metrics=[Metric(name=m) for m in metrics],
                dimensions=[Dimension(name=d) for d in dimensions] if dimensions else [],
                limit=limit,
            )
            
            response = self.client.run_realtime_report(request)
            
            # Преобразуем в формат, аналогичный Метрике
            data = []
            for row in response.rows:
                row_data = {
                    "dimensions": [d.value for d in row.dimension_values],
                    "metrics": [float(m.value) if m.value else 0.0 for m in row.metric_values]
                }
                data.append(row_data)
            
            return {
                "data": data,
                "row_count": len(data),
                "note": "Real-time data (last 30 minutes)"
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения real-time отчета GA4: {e}")
            raise GoogleAnalyticsAPIError(f"Ошибка получения real-time отчета: {e}")
    
    async def get_visitors_by_date(
        self,
        property_id: Optional[str] = None,
        date1: str = None,
        date2: str = None
    ) -> Dict[str, Any]:
        """
        Получить посетителей по дням
        
        Args:
            property_id: ID Property
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
        
        Returns:
            Отчет с данными по дням
        """
        return await self.get_report(
            property_id=property_id,
            metrics=["sessions", "activeUsers", "screenPageViews"],
            date1=date1,
            date2=date2,
            dimensions=["date"]
        )
    
    async def get_traffic_sources(
        self,
        property_id: Optional[str] = None,
        date1: str = None,
        date2: str = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Получить источники трафика
        
        Args:
            property_id: ID Property
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с источниками трафика
        """
        return await self.get_report(
            property_id=property_id,
            metrics=["sessions", "activeUsers", "bounceRate"],
            date1=date1,
            date2=date2,
            dimensions=["sessionSource", "sessionMedium", "sessionCampaignName"],
            limit=limit,
            order_by={"metric": {"metric_name": "sessions"}, "descending": True}
        )
    
    async def get_search_queries(
        self,
        property_id: Optional[str] = None,
        date1: str = None,
        date2: str = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Получить поисковые запросы (через события)
        
        Примечание: В GA4 нет прямого аналога поисковых запросов из Метрики.
        Используем события и landing pages для определения поискового трафика.
        
        Args:
            property_id: ID Property
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с поисковыми запросами/событиями
        """
        return await self.get_report(
            property_id=property_id,
            metrics=["eventCount", "activeUsers"],
            date1=date1,
            date2=date2,
            dimensions=["eventName", "landingPage"],
            limit=limit,
            order_by={"metric": {"metric_name": "eventCount"}, "descending": True}
        )
    
    async def get_geography(
        self,
        property_id: Optional[str] = None,
        date1: str = None,
        date2: str = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Получить географию посетителей
        
        Args:
            property_id: ID Property
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с географией
        """
        return await self.get_report(
            property_id=property_id,
            metrics=["sessions", "activeUsers"],
            date1=date1,
            date2=date2,
            dimensions=["country", "city", "region"],
            limit=limit,
            order_by={"metric": {"metric_name": "sessions"}, "descending": True}
        )
    
    async def get_online_visitors(
        self,
        property_id: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Получить онлайн посетителей (real-time)
        
        Args:
            property_id: ID Property
            limit: Лимит результатов
        
        Returns:
            Real-time данные о посетителях
        """
        # Real-time API имеет ограничения на комбинации dimensions/metrics
        # Используем только совместимые комбинации
        return await self.get_realtime_report(
            property_id=property_id,
            metrics=["activeUsers"],
            dimensions=["country", "deviceCategory"],
            limit=limit
        )
    
    async def get_recent_visits(
        self,
        property_id: Optional[str] = None,
        date1: str = None,
        date2: str = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Получить последние посещения
        
        Args:
            property_id: ID Property
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с последними посещениями
        """
        return await self.get_report(
            property_id=property_id,
            metrics=["sessions", "activeUsers", "screenPageViews"],
            date1=date1,
            date2=date2,
            dimensions=["date", "country", "deviceCategory", "operatingSystem", "browser", "landingPage"],
            limit=limit,
            order_by={"dimension": {"dimension_name": "date"}, "descending": True}
        )

