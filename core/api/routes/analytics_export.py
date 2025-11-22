"""
Analytics Export Routes
Роуты для экспорта данных аналитики в CSV/Excel
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from fastapi.responses import Response
import logging

from library.integrations.yandex_metrika import (
    YandexMetrikaClient,
    YandexMetrikaAuthError,
    YandexMetrikaAPIError
)
from library.integrations.google_analytics import (
    GoogleAnalyticsClient,
    GoogleAnalyticsAuthError,
    GoogleAnalyticsAPIError
)
from core.utils.export import export_to_csv, export_to_excel, format_filename
from core.utils.validation import (
    validate_counter_id,
    validate_property_id,
    validate_days,
    validate_limit
)
from core.api.routes.yandex_metrika import get_metrika_client
from core.api.routes.google_analytics import get_ga_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Yandex Metrika Export
# ============================================================================

@router.get("/yandex-metrika/counters/{counter_id}/export/visitors-by-date")
async def export_visitors_by_date(
    counter_id: int,
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Response:
    """
    Экспортировать посетителей по дням в CSV или Excel
    
    Args:
        counter_id: ID счетчика
        days: Количество дней назад
        format: Формат экспорта (csv или xlsx)
    """
    from datetime import datetime, timedelta
    
    # Валидация
    counter_id = validate_counter_id(counter_id)
    days = validate_days(days)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_visitors_by_date(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        
        # Преобразуем данные в список словарей
        data = []
        for row in report.get("data", []):
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            data.append({
                "Дата": dimensions[0] if len(dimensions) > 0 else "",
                "Визиты": int(metrics[0]) if len(metrics) > 0 else 0,
                "Посетители": int(metrics[1]) if len(metrics) > 1 else 0,
                "Просмотры": int(metrics[2]) if len(metrics) > 2 else 0,
            })
        
        # Экспортируем
        if format == "csv":
            content = export_to_csv(data)
            media_type = "text/csv; charset=utf-8"
            extension = "csv"
        else:
            content = export_to_excel(data, sheet_name="Посетители по дням")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = format_filename("visitors", "yandex-metrika", extension)
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка экспорта: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e)
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/export/traffic-sources")
async def export_traffic_sources(
    counter_id: int,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Response:
    """
    Экспортировать источники трафика в CSV или Excel
    """
    from datetime import datetime, timedelta
    
    # Валидация
    counter_id = validate_counter_id(counter_id)
    days = validate_days(days)
    limit = validate_limit(limit, max_limit=1000)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_traffic_sources(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        
        # Преобразуем данные
        data = []
        for row in report.get("data", []):
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            data.append({
                "Источник": dimensions[0] if len(dimensions) > 0 else "",
                "Medium": dimensions[1] if len(dimensions) > 1 else "",
                "Визиты": int(metrics[0]) if len(metrics) > 0 else 0,
                "Посетители": int(metrics[1]) if len(metrics) > 1 else 0,
            })
        
        # Экспортируем
        if format == "csv":
            content = export_to_csv(data)
            media_type = "text/csv; charset=utf-8"
            extension = "csv"
        else:
            content = export_to_excel(data, sheet_name="Источники трафика")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = format_filename("traffic-sources", "yandex-metrika", extension)
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка экспорта: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e)
            }
        )


# ============================================================================
# Google Analytics 4 Export
# ============================================================================

@router.get("/google-analytics/properties/{property_id}/export/visitors-by-date")
async def export_ga4_visitors_by_date(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Response:
    """
    Экспортировать посетителей по дням из GA4 в CSV или Excel
    """
    from datetime import datetime, timedelta
    
    # Валидация
    property_id = validate_property_id(property_id)
    days = validate_days(days)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_visitors_by_date(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        
        # Преобразуем данные
        data = []
        for row in report.get("data", []):
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            data.append({
                "Дата": dimensions[0] if len(dimensions) > 0 else "",
                "Sessions": int(metrics[0]) if len(metrics) > 0 else 0,
                "Users": int(metrics[1]) if len(metrics) > 1 else 0,
                "Pageviews": int(metrics[2]) if len(metrics) > 2 else 0,
            })
        
        # Экспортируем
        if format == "csv":
            content = export_to_csv(data)
            media_type = "text/csv; charset=utf-8"
            extension = "csv"
        else:
            content = export_to_excel(data, sheet_name="Visitors by Date")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = format_filename("visitors", "ga4", extension)
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка экспорта GA4: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e)
            }
        )


@router.get("/google-analytics/properties/{property_id}/export/traffic-sources")
async def export_ga4_traffic_sources(
    property_id: str,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    format: str = Query("csv", regex="^(csv|xlsx)$"),
    client: GoogleAnalyticsClient = Depends(get_ga_client)
) -> Response:
    """
    Экспортировать источники трафика из GA4 в CSV или Excel
    """
    from datetime import datetime, timedelta
    
    # Валидация
    property_id = validate_property_id(property_id)
    days = validate_days(days)
    limit = validate_limit(limit, max_limit=1000)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_traffic_sources(
            property_id=property_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        
        # Преобразуем данные
        data = []
        for row in report.get("data", []):
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            data.append({
                "Source": dimensions[0] if len(dimensions) > 0 else "",
                "Medium": dimensions[1] if len(dimensions) > 1 else "",
                "Sessions": int(metrics[0]) if len(metrics) > 0 else 0,
                "Users": int(metrics[1]) if len(metrics) > 1 else 0,
            })
        
        # Экспортируем
        if format == "csv":
            content = export_to_csv(data)
            media_type = "text/csv; charset=utf-8"
            extension = "csv"
        else:
            content = export_to_excel(data, sheet_name="Traffic Sources")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        
        filename = format_filename("traffic-sources", "ga4", extension)
        
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except GoogleAnalyticsAPIError as e:
        logger.error(f"Ошибка экспорта GA4: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Google Analytics API error",
                "message": str(e)
            }
        )

