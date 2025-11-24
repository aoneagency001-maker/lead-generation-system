"""
Yandex.Metrika API Routes
Роуты для работы с Яндекс.Метрикой
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
import logging

from library.integrations.yandex_metrika import (
    YandexMetrikaClient,
    YandexMetrikaError,
    YandexMetrikaAuthError,
    YandexMetrikaAPIError
)
from core.utils.cache import get_cached, set_cached, cache_key
from core.utils.validation import (
    validate_counter_id,
    validate_days,
    validate_limit,
    validate_date_range
)
from core.utils.export import export_to_csv, export_to_excel, format_filename
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter()

# TTL для кэширования summary (10 минут)
SUMMARY_CACHE_TTL = 600


def get_metrika_client() -> YandexMetrikaClient:
    """
    Dependency для получения клиента Яндекс.Метрики
    
    Returns:
        YandexMetrikaClient instance
    """
    try:
        return YandexMetrikaClient()
    except YandexMetrikaAuthError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Yandex Metrika authentication failed",
                "message": str(e),
                "code": 401
            }
        )


@router.get("/yandex-metrika/counters")
async def get_counters(
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить список всех доступных счетчиков Яндекс.Метрики
    
    Returns:
        {
            "counters": [
                {
                    "id": 12345678,
                    "name": "VesselGroup",
                    "site": "https://example.com",
                    ...
                },
                ...
            ]
        }
    
    Raises:
        401: Если токен не установлен или невалидный
        500: Если произошла ошибка API
    """
    # Проверяем кэш (1 час для списка счетчиков)
    cache_key_str = cache_key("ym", "counters")
    cached = await get_cached(cache_key_str)
    if cached:
        logger.info("✅ Использован кэш для списка счетчиков")
        return cached
    
    try:
        counters = await client.get_counters()
        
        # Форматируем ответ - оставляем только нужные поля
        formatted_counters = []
        for counter in counters:
            # Получаем значения, обрабатывая возможные проблемы с кодировкой
            name = counter.get("name", "Без названия")
            site = counter.get("site", "")
            
            # Если это строка в байтах или неправильной кодировке, пытаемся исправить
            if isinstance(name, bytes):
                try:
                    name = name.decode('utf-8')
                except:
                    name = name.decode('latin-1', errors='ignore')
            if isinstance(site, bytes):
                try:
                    site = site.decode('utf-8')
                except:
                    site = site.decode('latin-1', errors='ignore')
            
            formatted_counters.append({
                "id": counter.get("id"),
                "name": str(name) if name else "Без названия",
                "site": str(site) if site else "",
                "status": counter.get("status", "unknown"),
                "type": counter.get("type", "simple"),
            })
        
        from fastapi.responses import JSONResponse
        
        result = {"counters": formatted_counters}
        
        # Сохраняем в кэш (1 час для списка счетчиков)
        await set_cached(cache_key_str, result, ttl=3600)
        
        return JSONResponse(
            content=result,
            media_type="application/json; charset=utf-8"
        )
        
    except YandexMetrikaAuthError as e:
        logger.error(f"Ошибка авторизации Яндекс.Метрики: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Yandex Metrika authentication failed",
                "message": str(e),
                "code": 401
            }
        )
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка API Яндекс.Метрики: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении счетчиков: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Произошла неожиданная ошибка"
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/visitors-by-date")
async def get_visitors_by_date(
    counter_id: int,
    days: int = 30,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить уникальных посетителей по дням
    
    Args:
        counter_id: ID счетчика
        days: Количество дней назад (по умолчанию 30)
    """
    from datetime import datetime, timedelta
    
    # Валидация параметров
    counter_id = validate_counter_id(counter_id)
    days = validate_days(days)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    # Проверяем кэш
    cache_key_str = cache_key("ym", "visitors-by-date", counter_id, days)
    cached = await get_cached(cache_key_str)
    if cached:
        logger.info(f"✅ Использован кэш для visitors-by-date: counter_id={counter_id}, days={days}")
        return cached
    
    try:
        report = await client.get_visitors_by_date(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        
        # Сохраняем в кэш (5 минут)
        await set_cached(cache_key_str, report, ttl=300)
        
        return report
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения данных по дням: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/traffic-sources")
async def get_traffic_sources(
    counter_id: int,
    days: int = 30,
    limit: int = 20,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить распределение по источникам трафика
    """
    from datetime import datetime, timedelta
    
    # Валидация параметров
    counter_id = validate_counter_id(counter_id)
    days = validate_days(days)
    limit = validate_limit(limit, max_limit=100)
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    # Проверяем кэш
    cache_key_str = cache_key("ym", "traffic-sources", counter_id, days, limit)
    cached = await get_cached(cache_key_str)
    if cached:
        logger.info(f"✅ Использован кэш для traffic-sources: counter_id={counter_id}, days={days}, limit={limit}")
        return cached
    
    try:
        report = await client.get_traffic_sources(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        
        # Сохраняем в кэш (5 минут)
        await set_cached(cache_key_str, report, ttl=300)
        
        return report
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения источников трафика: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/search-queries")
async def get_search_queries(
    counter_id: int,
    days: int = 30,
    limit: int = 50,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить ТОП поисковых запросов
    """
    from datetime import datetime, timedelta
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_search_queries(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            limit=limit
        )
        return report
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения поисковых запросов: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/search-queries-detailed")
async def get_search_queries_detailed(
    counter_id: int,
    days: int = 30,
    limit: int = 50,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> List[Dict[str, Any]]:
    """
    Получить поисковые запросы с сегментацией, страницами входа и временем визитов
    
    Возвращает обогащенные данные:
    - Сегментация (Бренд, Продукт, Проблема, Решение, и т.д.)
    - Оценка "горячести" (heat score)
    - Страницы входа (landing pages)
    - Время первого и последнего визита
    """
    from datetime import datetime, timedelta
    from library.utils.search_segmentation import SearchSegmentationEngine
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    segmentation = SearchSegmentationEngine()
    
    logger.info(f"📊 Запрос детальных поисковых запросов: counter_id={counter_id}, days={days}, limit={limit}")
    
    try:
        # КЛЮЧЕВОЙ МОМЕНТ: Получаем данные с dimensions searchPhrase + landingPage вместе
        # Это позволяет получить связку "запрос → страница входа" напрямую из API
        logger.info("🔍 Пытаюсь получить данные с landing pages...")
        try:
            landing_report = await client.get_search_queries_with_landing_pages(
                counter_id=counter_id,
                date1=date_from.isoformat(),
                date2=date_to.isoformat(),
                limit=10000  # Метрика позволяет до 10k строк
            )
            if landing_report.get("data"):
                logger.info(f"✅ Успешно получены данные с landing pages: {len(landing_report['data'])} строк")
            else:
                logger.warning("⚠️ Данные с landing pages пусты")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить данные с landing pages: {e}. Используем базовый запрос.")
            # Fallback: используем базовый запрос без landing pages
            landing_report = {"data": []}
        
        if not landing_report.get("data"):
            logger.info("📋 Нет данных с landing pages, используем базовый запрос")
            # Fallback: получаем базовые данные о запросах
            basic_report = await client.get_search_queries(
                counter_id=counter_id,
                date1=date_from.isoformat(),
                date2=date_to.isoformat(),
                limit=limit
            )
            
            if not basic_report.get("data"):
                return []
            
            # Обрабатываем базовые данные без landing pages
            enriched_queries = []
            for row in basic_report["data"][:limit]:
                dimensions = row.get("dimensions", [])
                metrics = row.get("metrics", [])
                
                if not dimensions or not metrics:
                    continue
                
                query_text = dimensions[0].get("name") if isinstance(dimensions[0], dict) else dimensions[0]
                if not query_text:
                    continue
                
                visits = int(metrics[0]) if metrics else 0
                segments = segmentation.classify_query(query_text)
                primary_segment = segments[0]
                heat_data = segmentation.get_segment_heat_score(primary_segment, visits)
                
                enriched_queries.append({
                    "query": query_text,
                    "visits": visits,
                    "segment": primary_segment.value,
                    "segments": [s.value for s in segments],
                    "heat_score": round(heat_data["heat_visits"], 1),
                    "color": heat_data["color"],
                    "priority": heat_data["priority"],
                    "landing_pages": [],  # Нет данных
                    "first_visit": None,
                    "last_visit": None,
                })
            
            enriched_queries.sort(key=lambda x: x["heat_score"], reverse=True)
            return enriched_queries
        
        # Агрегируем данные по уникальным запросам
        # Один запрос может вести на разные страницы - группируем их
        queries_map = {}
        
        for row in landing_report["data"]:
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            
            if len(dimensions) < 2 or not metrics:
                continue
            
            # Извлекаем запрос и URL
            query_dim = dimensions[0]
            url_dim = dimensions[1]
            
            query_text = query_dim.get("name") if isinstance(query_dim, dict) else query_dim
            landing_url = url_dim.get("name") if isinstance(url_dim, dict) else url_dim
            
            if not query_text:
                continue
            
            visits = int(metrics[0]) if metrics else 0
            
            # Группируем по запросам
            if query_text not in queries_map:
                queries_map[query_text] = {
                    "query": query_text,
                    "total_visits": 0,
                    "landing_pages": [],
                    "visits_by_page": {}  # Для сортировки страниц по популярности
                }
            
            queries_map[query_text]["total_visits"] += visits
            
            # Сохраняем landing page с количеством визитов
            if landing_url:
                if landing_url not in queries_map[query_text]["visits_by_page"]:
                    queries_map[query_text]["visits_by_page"][landing_url] = 0
                    queries_map[query_text]["landing_pages"].append(landing_url)
                queries_map[query_text]["visits_by_page"][landing_url] += visits
        
        # Обогащаем каждый запрос сегментацией
        enriched_queries = []
        
        for query_text, query_data in queries_map.items():
            # Сортируем landing pages по количеству визитов
            sorted_pages = sorted(
                query_data["landing_pages"],
                key=lambda url: query_data["visits_by_page"].get(url, 0),
                reverse=True
            )[:5]  # Максимум 5 страниц
            
            visits = query_data["total_visits"]
            
            # Классифицируем запрос
            segments = segmentation.classify_query(query_text)
            primary_segment = segments[0]  # Главный сегмент
            heat_data = segmentation.get_segment_heat_score(primary_segment, visits)
            
            enriched_queries.append({
                "query": query_text,
                "visits": visits,
                "segment": primary_segment.value,
                "segments": [s.value for s in segments],  # Все найденные сегменты
                "heat_score": round(heat_data["heat_visits"], 1),
                "color": heat_data["color"],
                "priority": heat_data["priority"],
                "landing_pages": sorted_pages,  # Отсортированы по популярности
                "first_visit": None,  # TODO: добавить из логов если нужно
                "last_visit": None,  # TODO: добавить из логов если нужно
            })
        
        # Сортируем по горячести
        enriched_queries.sort(key=lambda x: x["heat_score"], reverse=True)
        
        # Ограничиваем лимитом
        result = enriched_queries[:limit]
        logger.info(f"✅ Возвращаю {len(result)} обогащенных запросов")
        return result
        
    except YandexMetrikaAPIError as e:
        logger.error(f"❌ Ошибка получения детальных поисковых запросов: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении детальных запросов: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e)
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/search-queries-by-segment")
async def get_search_queries_by_segment(
    counter_id: int,
    days: int = 30,
    limit: int = 200,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Группировка поисковых запросов по сегментам
    
    Возвращает данные, сгруппированные по типам сегментов:
    - Бренд
    - Продукт
    - Проблема/Боль
    - Решение
    - Сравнение
    - Высокая спешка
    - Информационный
    - Географический
    """
    from datetime import datetime, timedelta
    
    # Используем детальный endpoint для получения данных
    detailed_queries = await get_search_queries_detailed(
        counter_id=counter_id,
        days=days,
        limit=limit,
        client=client
    )
    
    # Группируем по сегментам
    segmented = {}
    
    for q in detailed_queries:
        segment = q["segment"]
        
        if segment not in segmented:
            segmented[segment] = {
                "total_visits": 0,
                "queries": [],
                "color": q["color"],
                "priority": q["priority"]
            }
        
        segmented[segment]["total_visits"] += q["visits"]
        segmented[segment]["queries"].append(q)
    
    # Сортируем сегменты по приоритету
    sorted_segments = dict(sorted(
        segmented.items(),
        key=lambda x: x[1]["priority"],
        reverse=True
    ))
    
    return sorted_segments


@router.get("/yandex-metrika/counters/{counter_id}/geography")
async def get_geography(
    counter_id: int,
    days: int = 30,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить географию посетителей
    """
    from datetime import datetime, timedelta
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_geography(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        return report
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения географии: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/utm-path")
async def get_utm_path(
    counter_id: int,
    days: int = 30,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить канальный путь utm_source → utm_medium → utm_campaign
    """
    from datetime import datetime, timedelta
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    try:
        report = await client.get_utm_path(
            counter_id=counter_id,
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        return report
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения UTM пути: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/report")
async def get_counter_report(
    counter_id: int,
    metrics: str,
    date1: str,
    date2: str,
    dimensions: Optional[str] = None,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить отчет по счетчику
    
    Args:
        counter_id: ID счетчика
        metrics: Список метрик через запятую (например: "ym:s:visits,ym:s:pageviews")
        date1: Начальная дата (YYYY-MM-DD)
        date2: Конечная дата (YYYY-MM-DD)
        dimensions: Опциональные измерения через запятую
    
    Returns:
        Данные отчета от API Яндекс.Метрики
    """
    try:
        metrics_list = [m.strip() for m in metrics.split(",")]
        dimensions_list = None
        if dimensions:
            dimensions_list = [d.strip() for d in dimensions.split(",")]
        
        report = await client.get_report(
            counter_id=counter_id,
            metrics=metrics_list,
            date1=date1,
            date2=date2,
            dimensions=dimensions_list
        )
        
        return report
        
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения отчета: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении отчета: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Произошла неожиданная ошибка"
            }
        )


@router.get("/yandex-metrika/counters/{counter_id}/recent-visits")
async def get_recent_visits(
    counter_id: int,
    days: int = 7,
    limit: int = 50,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить последние посещения с детальной информацией
    
    Возвращает ТОП 50 последних посещений с полной информацией:
    - Дата и время посещения
    - IP адрес (если доступен через Logs API)
    - Устройство (desktop/mobile/tablet)
    - Браузер и ОС
    - География (страна, город)
    - Страница входа
    - Реферрер
    - Количество просмотренных страниц
    - Длительность визита
    - Новый/возвращающийся посетитель
    
    Args:
        counter_id: ID счетчика
        days: Количество дней назад (по умолчанию 7)
        limit: Лимит результатов (по умолчанию 50, максимум 100)
    
    Returns:
        {
            "visits": [
                {
                    "date": "2025-11-22",
                    "time": "14:30:25",
                    "ip_address": "N/A",
                    "device": "desktop",
                    "browser": "Chrome",
                    "os": "Windows",
                    "country": "Казахстан",
                    "city": "Алматы",
                    "start_url": "https://example.com/page",
                    "referer": "https://google.com",
                    "pageviews": 5,
                    "duration": 120,
                    "is_new_user": true
                },
                ...
            ],
            "count": 50,
            "period": {
                "from": "2025-11-15",
                "to": "2025-11-22"
            }
        }
    """
    from datetime import datetime, timedelta
    
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=days)
    
    logger.info(f"📊 Запрос последних посещений: counter_id={counter_id}, days={days}, limit={limit}")
    
    try:
        visits = await client.get_recent_visits(
            counter_id=counter_id,
            days=days,
            limit=min(limit, 100)  # Максимум 100
        )
        
        logger.info(f"✅ Получено {len(visits)} посещений")
        
        return {
            "visits": visits,
            "count": len(visits),
            "period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat()
            }
        }
        
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка получения последних посещений: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении последних посещений: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e)
            }
        )


@router.get("/yandex-metrika/summary")
async def get_counter_summary(
    counter_id: int,
    client: YandexMetrikaClient = Depends(get_metrika_client)
) -> Dict[str, Any]:
    """
    Получить полную сводку по счетчику:
    - Информация о счетчике
    - Базовые метрики за последние 7 дней
    - Статистика синхронизации из базы данных
    - Топ источников трафика
    
    Данные кэшируются на 10 минут для снижения нагрузки на API Яндекс.Метрики.
    
    Args:
        counter_id: ID счетчика
    
    Returns:
        {
            "counter": {
                "id": 12345678,
                "name": "VesselGroup",
                "domain": "vesselgroup.kz",
                "code_status": "CS_OK",
                "permission": "view"
            },
            "stats": {
                "last_7_days": {
                    "visits": 2345,
                    "users": 1980,
                    "pageviews": 7650,
                    "bounce_rate": 42.1,
                    "avg_duration": 92,
                    "top_sources": [...]
                }
            },
            "sync": {
                "visits_in_db": 55400,
                "hits_in_db": 214500,
                "last_sync": "2025-11-23 03:15"
            }
        }
    """
    from datetime import datetime, timedelta
    from core.database.supabase_client import get_supabase_client
    
    # Проверяем кэш
    cache_key_str = cache_key("metrika:summary", counter_id)
    cached_data = await get_cached(cache_key_str)
    if cached_data:
        logger.debug(f"✅ Summary для счетчика {counter_id} получен из кэша")
        return cached_data
    
    try:
        # 1. Получить информацию о счетчике
        counter_info = await client.get_counter_info(counter_id)
        
        # 2. Получить метрики за последние 7 дней
        date_to = datetime.now().date()
        date_from = date_to - timedelta(days=7)
        
        # Базовые метрики
        basic_metrics = await client.get_report(
            counter_id=counter_id,
            metrics=[
                "ym:s:visits",
                "ym:s:users",
                "ym:s:pageviews",
                "ym:s:bounceRate",
                "ym:s:avgVisitDurationSeconds"
            ],
            date1=date_from.isoformat(),
            date2=date_to.isoformat()
        )
        
        # Метрики по источникам трафика
        traffic_sources = await client.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits"],
            date1=date_from.isoformat(),
            date2=date_to.isoformat(),
            dimensions=["ym:s:trafficSource"]
        )
        
        # Обработка базовых метрик
        totals = basic_metrics.get("totals", [0, 0, 0, 0, 0])
        visits = int(totals[0]) if len(totals) > 0 else 0
        users = int(totals[1]) if len(totals) > 1 else 0
        pageviews = int(totals[2]) if len(totals) > 2 else 0
        # bounceRate уже приходит в процентах (0-100), не нужно умножать на 100
        bounce_rate = float(totals[3]) if len(totals) > 3 and totals[3] is not None else 0.0
        avg_duration = int(totals[4]) if len(totals) > 4 else 0
        
        # Обработка источников трафика
        top_sources = []
        traffic_data = traffic_sources.get("data", [])
        for row in traffic_data[:10]:  # Топ 10
            dimensions = row.get("dimensions", [])
            metrics = row.get("metrics", [])
            if dimensions and metrics:
                source_name = dimensions[0].get("name", "unknown")
                source_visits = int(metrics[0]) if metrics else 0
                if source_name and source_visits > 0:
                    top_sources.append({
                        "source": source_name,
                        "visits": source_visits
                    })
        
        # Сортировка по количеству визитов
        top_sources.sort(key=lambda x: x["visits"], reverse=True)
        
        # 3. Получить статистику из базы данных
        supabase = get_supabase_client()
        counter_id_str = str(counter_id)
        
        visits_in_db = 0
        hits_in_db = 0
        last_sync = None
        
        try:
            # Подсчет visits (из normalized_events где source = YANDEX_METRIKA)
            visits_result = supabase.table("normalized_events")\
                .select("id", count="exact")\
                .eq("source", "YANDEX_METRIKA")\
                .execute()
            visits_in_db = visits_result.count if hasattr(visits_result, 'count') else len(visits_result.data) if visits_result.data else 0
        except Exception as e:
            logger.warning(f"Ошибка подсчета visits из БД: {e}")
            visits_in_db = 0
        
        try:
            # Подсчет hits (из raw_events где source = YANDEX_METRIKA и counter_id совпадает)
            hits_result = supabase.table("raw_events")\
                .select("id", count="exact")\
                .eq("source", "YANDEX_METRIKA")\
                .eq("counter_id", counter_id_str)\
                .execute()
            hits_in_db = hits_result.count if hasattr(hits_result, 'count') else len(hits_result.data) if hits_result.data else 0
        except Exception as e:
            logger.warning(f"Ошибка подсчета hits из БД: {e}")
            hits_in_db = 0
        
        try:
            # Получить последнюю синхронизацию (последний fetched_at из raw_events)
            last_sync_result = supabase.table("raw_events")\
                .select("fetched_at")\
                .eq("source", "YANDEX_METRIKA")\
                .eq("counter_id", counter_id_str)\
                .order("fetched_at", desc=True)\
                .limit(1)\
                .execute()
            
            if last_sync_result.data and len(last_sync_result.data) > 0:
                last_sync_str = last_sync_result.data[0].get("fetched_at")
                if last_sync_str:
                    try:
                        # Парсим ISO формат и форматируем
                        if isinstance(last_sync_str, str):
                            # Убираем Z и парсим
                            last_sync_str_clean = last_sync_str.replace('Z', '+00:00')
                            last_sync_dt = datetime.fromisoformat(last_sync_str_clean)
                            last_sync = last_sync_dt.strftime("%Y-%m-%d %H:%M")
                        else:
                            last_sync = str(last_sync_str)
                    except Exception as e:
                        logger.warning(f"Ошибка парсинга даты синхронизации: {e}")
                        last_sync = str(last_sync_str)
        except Exception as e:
            logger.warning(f"Ошибка получения последней синхронизации: {e}")
            last_sync = None
        
        # Формируем ответ
        result = {
            "counter": {
                "id": counter_info.get("id"),
                "name": counter_info.get("name", "Без названия"),
                "domain": counter_info.get("site", ""),
                "code_status": counter_info.get("code_status", "unknown"),
                "permission": counter_info.get("permission", "unknown")
            },
            "stats": {
                "last_7_days": {
                    "visits": visits,
                    "users": users,
                    "pageviews": pageviews,
                    "bounce_rate": round(bounce_rate, 2),
                    "avg_duration": avg_duration,
                    "top_sources": top_sources
                }
            },
            "sync": {
                "visits_in_db": visits_in_db,
                "hits_in_db": hits_in_db,
                "last_sync": last_sync
            }
        }
        
        # Сохраняем в кэш
        await set_cached(cache_key_str, result, ttl=SUMMARY_CACHE_TTL)
        logger.debug(f"✅ Summary для счетчика {counter_id} сохранен в кэш")
        
        return result
        
    except YandexMetrikaAuthError as e:
        logger.error(f"Ошибка авторизации Яндекс.Метрики: {e}")
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Yandex Metrika authentication failed",
                "message": str(e),
                "code": 401
            }
        )
    except YandexMetrikaAPIError as e:
        logger.error(f"Ошибка API Яндекс.Метрики: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Yandex Metrika API error",
                "message": str(e),
                "code": e.code
            }
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении сводки: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Произошла неожиданная ошибка"
            }
        )

