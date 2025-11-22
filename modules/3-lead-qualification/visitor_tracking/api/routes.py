"""
Visitor Tracking API Routes
FastAPI роуты для отслеживания посетителей и обработки Tilda webhook'ов
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import logging

# Импорты с обработкой относительных путей
try:
    # Попытка относительного импорта (когда модуль загружается как пакет)
    from ..models import (
        VisitorTrackRequest,
        VisitorTrackResponse,
        TildaWebhookRequest,
        TildaWebhookResponse
    )
    from ..services.visitor_tracker import VisitorTracker
    from ..services.tilda_webhook import TildaWebhookHandler
except (ImportError, ValueError):
    # Fallback для случаев, когда модуль загружается напрямую через importlib
    import sys
    from pathlib import Path
    
    # Добавляем путь к модулю в sys.path
    module_dir = Path(__file__).parent.parent
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))
    
    # Абсолютные импорты
    from models import (
        VisitorTrackRequest,
        VisitorTrackResponse,
        TildaWebhookRequest,
        TildaWebhookResponse
    )
    from services.visitor_tracker import VisitorTracker
    from services.tilda_webhook import TildaWebhookHandler

logger = logging.getLogger(__name__)

router = APIRouter()

# Инициализируем сервисы
visitor_tracker = VisitorTracker()
tilda_handler = TildaWebhookHandler()


@router.post("/track-visitor", response_model=VisitorTrackResponse)
async def track_visitor(
    request: VisitorTrackRequest,
    http_request: Request
):
    """
    Отследить посетителя и отправить уведомление в Telegram
    
    Использование:
        POST /api/visitor-tracking/track-visitor
        {
            "page": "/ru",
            "referrer": "https://google.com",
            "screenResolution": "1920x1080",
            "utmSource": "yandex",
            "utmMedium": "cpc"
        }
    """
    try:
        # Получаем IP адрес и User-Agent из запроса
        client_ip = None
        if http_request.client:
            # Проверяем заголовок X-Forwarded-For (для прокси)
            forwarded_for = http_request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = http_request.client.host
        
        user_agent = http_request.headers.get("User-Agent")
        
        # Конвертируем Pydantic модель в dict
        request_data = request.dict(exclude_none=True)
        
        # Отслеживаем посетителя
        result = await visitor_tracker.track_visitor(
            request_data=request_data,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        return VisitorTrackResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in track-visitor endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tilda-webhook", response_model=TildaWebhookResponse)
async def tilda_webhook(
    request: TildaWebhookRequest,
    http_request: Request
):
    """
    Обработать webhook от Tilda и отправить уведомление в Telegram
    
    Использование:
        POST /api/visitor-tracking/tilda-webhook
        {
            "name": "Иван Иванов",
            "phone": "+7 777 123 45 67",
            "email": "ivan@example.com",
            "message": "Хочу заказать разработку сайта"
        }
    """
    try:
        # Получаем IP адрес
        client_ip = None
        if http_request.client:
            forwarded_for = http_request.headers.get("X-Forwarded-For")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            else:
                client_ip = http_request.client.host
        
        # Конвертируем Pydantic модель в dict
        webhook_data = request.dict(exclude_none=True)
        
        # Обрабатываем webhook
        result = await tilda_handler.handle_webhook(
            webhook_data=webhook_data,
            ip_address=client_ip
        )
        
        return TildaWebhookResponse(**result)
    
    except Exception as e:
        logger.error(f"Error in tilda-webhook endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/online-visitors")
async def get_online_visitors(minutes: int = 15, limit: int = 50):
    """
    Получить список онлайн-посетителей (за последние N минут)
    
    Args:
        minutes: Количество минут для определения "онлайн" (по умолчанию 15)
        limit: Максимальное количество посетителей (по умолчанию 50)
    
    Returns:
        Список посетителей с информацией: IP, устройство, браузер, город, страница
    """
    from core.database.supabase_client import get_supabase_client
    
    try:
        supabase = get_supabase_client()
        
        # Вычисляем время "онлайн" (последние N минут)
        time_threshold = datetime.now() - timedelta(minutes=minutes)
        
        # Получаем посетителей за последние N минут, исключая ботов
        query = supabase.table("visitors")\
            .select("*")\
            .eq("is_bot", False)\
            .gte("created_at", time_threshold.isoformat())
        
        # Supabase использует другой синтаксис для сортировки
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        visitors = result.data if result.data else []
        
        # Форматируем данные для фронтенда
        formatted_visitors = []
        for visitor in visitors:
            # Парсим user_agent для определения браузера и ОС
            user_agent = visitor.get("user_agent", "") or ""
            browser = _parse_browser(user_agent)
            os = _parse_os(user_agent)
            
            formatted_visitors.append({
                "id": visitor.get("id"),
                "ip_address": visitor.get("ip_address") or "Неизвестно",
                "city": visitor.get("city") or "Неизвестно",
                "country": visitor.get("country") or "Неизвестно",
                "device_type": visitor.get("device_type") or "unknown",
                "browser": browser,
                "os": os,
                "page": visitor.get("page") or visitor.get("landing_page") or "/",
                "referrer": visitor.get("referrer") or "Прямой переход",
                "utm_source": visitor.get("utm_source"),
                "utm_medium": visitor.get("utm_medium"),
                "utm_campaign": visitor.get("utm_campaign"),
                "screen_resolution": visitor.get("screen_resolution") or "Неизвестно",
                "is_first_visit": visitor.get("is_first_visit", False),
                "created_at": visitor.get("created_at"),
            })
        
        return {
            "visitors": formatted_visitors,
            "count": len(formatted_visitors),
            "time_threshold_minutes": minutes
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting online visitors: {e}", exc_info=True)
        
        # Если таблица не найдена - возвращаем пустой список с информацией
        if "Could not find the table" in error_msg or "visitors" in error_msg.lower():
            logger.warning("Table 'visitors' not found. Returning empty list.")
            return {
                "visitors": [],
                "count": 0,
                "time_threshold_minutes": minutes,
                "error": "Таблица visitors не найдена в базе данных. Примените схему из core/database/schema_visitor_tracking.sql"
            }
        
        raise HTTPException(status_code=500, detail=error_msg)


def _parse_browser(user_agent: str) -> str:
    """Простой парсер браузера из User-Agent"""
    ua_lower = user_agent.lower()
    
    if "chrome" in ua_lower and "edg" not in ua_lower:
        return "Chrome"
    elif "firefox" in ua_lower:
        return "Firefox"
    elif "safari" in ua_lower and "chrome" not in ua_lower:
        return "Safari"
    elif "edg" in ua_lower:
        return "Edge"
    elif "opera" in ua_lower or "opr" in ua_lower:
        return "Opera"
    elif "yandex" in ua_lower:
        return "Yandex Browser"
    elif "msie" in ua_lower or "trident" in ua_lower:
        return "Internet Explorer"
    
    return "Неизвестно"


def _parse_os(user_agent: str) -> str:
    """Простой парсер ОС из User-Agent"""
    ua_lower = user_agent.lower()
    
    if "windows" in ua_lower:
        if "windows nt 10" in ua_lower:
            return "Windows 10/11"
        elif "windows nt 6.3" in ua_lower:
            return "Windows 8.1"
        elif "windows nt 6.2" in ua_lower:
            return "Windows 8"
        elif "windows nt 6.1" in ua_lower:
            return "Windows 7"
        return "Windows"
    elif "mac os x" in ua_lower or "macintosh" in ua_lower:
        return "macOS"
    elif "linux" in ua_lower:
        return "Linux"
    elif "android" in ua_lower:
        return "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower or "ipod" in ua_lower:
        return "iOS"
    
    return "Неизвестно"


@router.get("/health")
async def health_check():
    """Проверка работоспособности модуля"""
    return {
        "status": "ok",
        "service": "visitor-tracking",
        "timestamp": datetime.now().isoformat()
    }

