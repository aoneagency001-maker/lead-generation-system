"""
Google Analytics 4 API Routes
Роуты для работы с GA4
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from library.integrations.google_analytics import (
    GoogleAnalyticsClient,
    GoogleAnalyticsError,
    GoogleAnalyticsAuthError,
    GoogleAnalyticsAPIError
)
from core.utils.cache import get_cached, set_cached, cache_key

logger = logging.getLogger(__name__)

router = APIRouter()

# TTL для кэширования summary (10 минут)
SUMMARY_CACHE_TTL = 600


def get_ga_client() -> GoogleAnalyticsClient:
    """
    Dependency для получения клиента Google Analytics 4
    
    Returns:
        GoogleAnalyticsClient instance
    """
    try:
        return GoogleAnalyticsClient()
    except GoogleAnalyticsAuthError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Google Analytics authentication failed",
                "message": str(e),
                "code": 401
            }
        )


@router.get("/google-analytics/properties")
async def get_properties(
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить список всех доступных Properties Google Analytics 4
    
    Returns:
        {
            "properties": [
                {
                    "id": "123456789",
                    "name": "Default Property",
                    "property": "properties/123456789"
                },
                ...
            ]
        }
    
    Raises:
        401: Если credentials не установлены или невалидные
        500: Если произошла ошибка API
    """
    try:
        properties = await client.get_properties()
        
        from fastapi.responses import JSONResponse
        
        return JSONResponse(
            content={"properties": properties},
            media_type="application/json; charset=utf-8"
        )
        
    except GoogleAnalyticsAuthError as e:
        logger.error(f"Ошибка авторизации Google Analytics: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Google Analytics authentication failed",
                "message": str(e),
                "code": 401
            }
        )
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка API Google Analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении Properties: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Произошла неожиданная ошибка"
            }
        )


@router.get("/google-analytics/properties/{property_id}/visitors-by-date")
async def get_visitors_by_date(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить посетителей по дням
    
    Args:
        property_id: ID Property (формат: "123456789" или "properties/123456789")
        days: Количество дней назад (по умолчанию 30)
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_visitors_by_date(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения данных по дням: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/traffic-sources")
async def get_traffic_sources(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить распределение по источникам трафика
    
    Args:
        property_id: ID Property
        days: Количество дней назад
        limit: Лимит результатов
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_traffic_sources(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения источников трафика: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/search-queries")
async def get_search_queries(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=1000),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить поисковые запросы/события
    
    Примечание: В GA4 нет прямого аналога поисковых запросов из Метрики.
    Возвращаем события и landing pages для определения поискового трафика.
    
    Args:
        property_id: ID Property
        days: Количество дней назад
        limit: Лимит результатов
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_search_queries(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения поисковых запросов: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/geography")
async def get_geography(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить географию посетителей
    
    Args:
        property_id: ID Property
        days: Количество дней назад
        limit: Лимит результатов
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_geography(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения географии: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/online-visitors")
async def get_online_visitors(
    property_id: str,
    limit: int = Query(100, ge=1, le=1000),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить онлайн посетителей (real-time, последние 30 минут)
    
    Args:
        property_id: ID Property
        limit: Лимит результатов
    """
    try:
        report = await client.get_online_visitors(
            property_id=property_id,
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения онлайн посетителей: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/recent-visits")
async def get_recent_visits(
    property_id: str,
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(100, ge=1, le=1000),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить последние посещения
    
    Args:
        property_id: ID Property
        days: Количество дней назад
        limit: Лимит результатов
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_recent_visits(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения последних посещений: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/properties/{property_id}/report")
async def get_property_report(
    property_id: str,
    metrics: str = Query(..., description="Список метрик через запятую (например: sessions,activeUsers)"),
    date1: str = Query(..., description="Начальная дата (YYYY-MM-DD)"),
    date2: str = Query(..., description="Конечная дата (YYYY-MM-DD)"),
    dimensions: Optional[str] = Query(None, description="Список измерений через запятую (например: country,city)"),
    limit: Optional[int] = Query(None, ge=1, le=10000),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Универсальный endpoint для получения отчетов GA4
    
    Args:
        property_id: ID Property
        metrics: Список метрик через запятую
        date1: Начальная дата
        date2: Конечная дата
        dimensions: Опциональные измерения через запятую
        limit: Лимит результатов
    """
    try:
        metrics_list = [m.strip() for m in metrics.split(",")]
        dimensions_list = [d.strip() for d in dimensions.split(",")] if dimensions else None
        
        report = await client.get_report(
            property_id=property_id,
            metrics=metrics_list,
            date1=date1,
            date2=date2,
            dimensions=dimensions_list,
            limit=limit
        )
        return report
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения отчета: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/google-analytics/summary")
async def get_summary(
    property_id: str = Query(..., description="ID Property"),
    days: int = Query(7, ge=1, le=365),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Dict[str, Any]:
    """
    Получить сводку по Property (аналог summary для Метрики)
    
    Args:
        property_id: ID Property
        days: Количество дней назад
    """
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    # Проверяем кэш
    cache_key_str = cache_key("ga4", "summary", property_id, days)
    cached = await get_cached(cache_key_str)
    if cached:
        logger.info(f"✅ Использован кэш для summary GA4: {property_id}")
        return cached
    
    try:
        # Получаем основные метрики
        visitors_report = await client.get_visitors_by_date(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        
        # Получаем источники трафика
        sources_report = await client.get_traffic_sources(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=10
        )
        
        # Получаем онлайн посетителей
        online_report = await client.get_online_visitors(
            property_id=property_id,
            limit=100
        )
        
        # Формируем сводку
        total_sessions = sum(row["metrics"][0] for row in visitors_report.get("data", []))
        total_users = sum(row["metrics"][1] for row in visitors_report.get("data", []))
        total_pageviews = sum(row["metrics"][2] for row in visitors_report.get("data", []))
        
        online_users = sum(row["metrics"][0] for row in online_report.get("data", []))
        
        # Функция классификации типа трафика с детализацией
        def classify_traffic_type(source: str, medium: str) -> tuple[str, str]:
            """
            Классифицирует трафик: (основной_тип, детальный_тип)
            Возвращает кортеж: (основной тип, детальный подтип)
            """
            source_lower = (source or "").lower()
            medium_lower = (medium or "").lower()
            
            # Реклама - детализация по источникам
            paid_mediums = ["cpc", "cpm", "cpv", "cpa", "cpp", "affiliate"]
            if medium_lower in paid_mediums:
                # Детализация рекламы по источникам
                if "google" in source_lower or "gclid" in source_lower:
                    return ("Реклама", "Google Ads")
                elif "yandex" in source_lower or "yclid" in source_lower:
                    return ("Реклама", "Yandex Direct")
                elif "facebook" in source_lower or "fb" in source_lower:
                    return ("Реклама", "Facebook Ads")
                elif "instagram" in source_lower:
                    return ("Реклама", "Instagram Ads")
                elif "vk" in source_lower or "vkontakte" in source_lower:
                    return ("Реклама", "VK Ads")
                elif "mytarget" in source_lower or "target" in source_lower:
                    return ("Реклама", "MyTarget")
                elif "ok" in source_lower or "odnoklassniki" in source_lower:
                    return ("Реклама", "OK Ads")
                else:
                    return ("Реклама", "Другая реклама")
            
            # Проверка рекламных источников напрямую
            paid_sources = ["google", "yandex", "facebook", "instagram", "vk", "ok", "mytarget", "vkontakte"]
            if any(ps in source_lower for ps in paid_sources):
                if "google" in source_lower:
                    return ("Реклама", "Google Ads")
                elif "yandex" in source_lower:
                    return ("Реклама", "Yandex Direct")
                elif "facebook" in source_lower or "fb" in source_lower:
                    return ("Реклама", "Facebook Ads")
                elif "instagram" in source_lower:
                    return ("Реклама", "Instagram Ads")
                elif "vk" in source_lower or "vkontakte" in source_lower:
                    return ("Реклама", "VK Ads")
                elif "mytarget" in source_lower:
                    return ("Реклама", "MyTarget")
                elif "ok" in source_lower or "odnoklassniki" in source_lower:
                    return ("Реклама", "OK Ads")
                else:
                    return ("Реклама", "Другая реклама")
            
            # Соцсети (органический трафик из соцсетей, не реклама)
            social_sources = ["facebook", "instagram", "vk", "vkontakte", "ok", "odnoklassniki", "telegram", "whatsapp", "twitter", "linkedin"]
            if any(ss in source_lower for ss in social_sources) and medium_lower not in paid_mediums:
                if "telegram" in source_lower:
                    return ("Соцсети", "Telegram")
                elif "whatsapp" in source_lower:
                    return ("Соцсети", "WhatsApp")
                elif "vk" in source_lower or "vkontakte" in source_lower:
                    return ("Соцсети", "VK")
                elif "facebook" in source_lower:
                    return ("Соцсети", "Facebook")
                elif "instagram" in source_lower:
                    return ("Соцсети", "Instagram")
                elif "ok" in source_lower or "odnoklassniki" in source_lower:
                    return ("Соцсети", "Одноклассники")
                else:
                    return ("Соцсети", "Другие соцсети")
            
            # Органика (поисковики) - детализация
            organic_sources = ["google", "yandex", "bing", "yahoo", "duckduckgo"]
            if medium_lower == "organic" or any(os in source_lower for os in organic_sources):
                if "google" in source_lower:
                    return ("Органика", "Google")
                elif "yandex" in source_lower:
                    return ("Органика", "Yandex")
                elif "bing" in source_lower:
                    return ("Органика", "Bing")
                elif "yahoo" in source_lower:
                    return ("Органика", "Yahoo")
                else:
                    return ("Органика", "Другие поисковики")
            
            # Прямой трафик
            if not source or source_lower in ["(direct)", "direct", "прямой"]:
                return ("Прямой", "Прямой")
            
            # Реферальный (переименовываем в "С других сайтов")
            # Используем название источника как детализацию
            detail_name = source if source and source.lower() not in ["(direct)", "direct", "прямой"] else "Неизвестный источник"
            return ("С других сайтов", detail_name)
        
        # Преобразуем источники трафика в удобный формат с классификацией
        top_sources_formatted = []
        traffic_by_type = {
            "Реклама": {"visits": 0, "users": 0, "subtypes": {}},
            "Органика": {"visits": 0, "users": 0, "subtypes": {}},
            "Прямой": {"visits": 0, "users": 0, "subtypes": {}},
            "Соцсети": {"visits": 0, "users": 0, "subtypes": {}},
            "С других сайтов": {"visits": 0, "users": 0, "subtypes": {}},
        }
        
        for row in sources_report.get("data", []):
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            source_name = dimensions[0] if len(dimensions) > 0 else "Прямой трафик"
            medium = dimensions[1] if len(dimensions) > 1 else None
            visits = int(metrics[0]) if len(metrics) > 0 else 0
            users = int(metrics[1]) if len(metrics) > 1 else 0
            
            main_type, detail_type = classify_traffic_type(source_name, medium)
            
            # Обновляем основной тип
            if main_type in traffic_by_type:
                traffic_by_type[main_type]["visits"] += visits
                traffic_by_type[main_type]["users"] += users
                
                # Обновляем подтипы
                if detail_type not in traffic_by_type[main_type]["subtypes"]:
                    traffic_by_type[main_type]["subtypes"][detail_type] = {"visits": 0, "users": 0}
                traffic_by_type[main_type]["subtypes"][detail_type]["visits"] += visits
                traffic_by_type[main_type]["subtypes"][detail_type]["users"] += users
            
            # Добавляем в топ источников (первые 10)
            if len(top_sources_formatted) < 10:
                top_sources_formatted.append({
                    "source": source_name,
                    "medium": medium,
                    "campaign": dimensions[2] if len(dimensions) > 2 else None,
                    "visits": visits,
                    "users": users,
                    "traffic_type": main_type,
                    "traffic_detail": detail_type,
                    "bounce_rate": float(metrics[2]) if len(metrics) > 2 else None,
                })
        
        summary = {
            "property_id": property_id,
            "period": {
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat(),
                "days": days
            },
            "metrics": {
                "sessions": int(total_sessions),
                "users": int(total_users),
                "pageviews": int(total_pageviews),
                "online_users": int(online_users)
            },
            "top_sources": top_sources_formatted,
            "traffic_by_type": traffic_by_type,
            "sync_status": {
                "last_sync": datetime.now().isoformat(),
                "status": "ok"
            }
        }
        
        # Кэшируем результат
        await set_cached(cache_key_str, summary, SUMMARY_CACHE_TTL)
        
        return summary
        
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка получения сводки: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e),
                "code": e.code
            }
        )

