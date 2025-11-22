"""
Unified Analytics Interface
Унифицированный интерфейс для работы с разными источниками аналитики

Предоставляет единый API для работы с Яндекс.Метрикой и Google Analytics 4
"""

from typing import Dict, Any, Optional, List
from datetime import date, datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AnalyticsSource(str, Enum):
    """Источники аналитики"""
    YANDEX_METRIKA = "yandex_metrika"
    GOOGLE_ANALYTICS = "google_analytics"


class UnifiedAnalyticsResponse:
    """
    Унифицированный формат ответа для всех источников аналитики
    """
    
    def __init__(
        self,
        source: AnalyticsSource,
        data: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.source = source
        self.data = data
        self.metadata = metadata or {}
        self.count = len(data)
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            "source": self.source.value,
            "count": self.count,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


def normalize_visitors_data(
    source: AnalyticsSource,
    raw_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Нормализовать данные посетителей из разных источников в единый формат
    
    Args:
        source: Источник данных
        raw_data: Сырые данные из API
    
    Returns:
        Список нормализованных записей
    """
    normalized = []
    
    if source == AnalyticsSource.YANDEX_METRIKA:
        # Формат Яндекс.Метрики
        rows = raw_data.get("data", [])
        for row in rows:
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            normalized.append({
                "date": dimensions[0] if len(dimensions) > 0 else "",
                "visits": int(metrics[0]) if len(metrics) > 0 else 0,
                "users": int(metrics[1]) if len(metrics) > 1 else 0,
                "pageviews": int(metrics[2]) if len(metrics) > 2 else 0,
            })
    
    elif source == AnalyticsSource.GOOGLE_ANALYTICS:
        # Формат Google Analytics 4
        rows = raw_data.get("data", [])
        for row in rows:
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            # GA4 использует формат YYYYMMDD для даты
            date_str = dimensions[0] if len(dimensions) > 0 else ""
            if date_str and len(date_str) == 8:
                # Преобразуем YYYYMMDD в YYYY-MM-DD
                date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date_formatted = date_str
            
            normalized.append({
                "date": date_formatted,
                "visits": int(metrics[0]) if len(metrics) > 0 else 0,  # sessions
                "users": int(metrics[1]) if len(metrics) > 1 else 0,  # activeUsers
                "pageviews": int(metrics[2]) if len(metrics) > 2 else 0,  # screenPageViews
            })
    
    return normalized


def normalize_traffic_sources_data(
    source: AnalyticsSource,
    raw_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Нормализовать данные источников трафика из разных источников в единый формат
    
    Args:
        source: Источник данных
        raw_data: Сырые данные из API
    
    Returns:
        Список нормализованных записей
    """
    normalized = []
    
    if source == AnalyticsSource.YANDEX_METRIKA:
        # Формат Яндекс.Метрики
        rows = raw_data.get("data", [])
        for row in rows:
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            normalized.append({
                "source": dimensions[0] if len(dimensions) > 0 else "",
                "medium": dimensions[1] if len(dimensions) > 1 else "",
                "visits": int(metrics[0]) if len(metrics) > 0 else 0,
                "users": int(metrics[1]) if len(metrics) > 1 else 0,
            })
    
    elif source == AnalyticsSource.GOOGLE_ANALYTICS:
        # Формат Google Analytics 4
        rows = raw_data.get("data", [])
        for row in rows:
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            normalized.append({
                "source": dimensions[0] if len(dimensions) > 0 else "",
                "medium": dimensions[1] if len(dimensions) > 1 else "",
                "visits": int(metrics[0]) if len(metrics) > 0 else 0,  # sessions
                "users": int(metrics[1]) if len(metrics) > 1 else 0,  # activeUsers
            })
    
    return normalized


def create_unified_response(
    source: AnalyticsSource,
    raw_data: Dict[str, Any],
    data_type: str = "visitors"
) -> UnifiedAnalyticsResponse:
    """
    Создать унифицированный ответ из сырых данных
    
    Args:
        source: Источник данных
        raw_data: Сырые данные из API
        data_type: Тип данных ("visitors" или "traffic_sources")
    
    Returns:
        UnifiedAnalyticsResponse
    """
    if data_type == "visitors":
        normalized_data = normalize_visitors_data(source, raw_data)
    elif data_type == "traffic_sources":
        normalized_data = normalize_traffic_sources_data(source, raw_data)
    else:
        normalized_data = []
    
    return UnifiedAnalyticsResponse(
        source=source,
        data=normalized_data,
        metadata={
            "data_type": data_type,
            "raw_count": len(raw_data.get("data", []))
        }
    )

