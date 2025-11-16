"""
Health Check Routes
Проверка работоспособности системы
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import logging

from core.database.supabase_client import get_supabase_client
from core.api.config import settings, is_telegram_configured, is_whatsapp_configured

router = APIRouter()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Проверка работоспособности системы
    
    Returns:
        HealthResponse: Статус всех сервисов
    """
    services = {}
    
    # Проверка Supabase
    try:
        supabase = get_supabase_client()
        # Простой запрос для проверки
        result = supabase.table("niches").select("id").limit(1).execute()
        services["supabase"] = "ok"
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        services["supabase"] = "error"
    
    # Проверка Telegram
    services["telegram"] = "configured" if is_telegram_configured() else "not_configured"
    
    # Проверка WhatsApp
    services["whatsapp"] = "configured" if is_whatsapp_configured() else "not_configured"
    
    # Проверка Redis (опционально)
    services["redis"] = "not_checked"
    
    # Определяем общий статус
    overall_status = "healthy" if services["supabase"] == "ok" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        services=services,
        version="0.1.0"
    )


@router.get("/config")
async def get_config():
    """
    Получить текущую конфигурацию (без секретов)
    
    Returns:
        dict: Публичная конфигурация
    """
    return {
        "debug": settings.debug,
        "max_ads_per_day": settings.max_ads_per_day,
        "notification_channels": settings.notification_channels.split(","),
        "features": {
            "telegram": is_telegram_configured(),
            "whatsapp": is_whatsapp_configured(),
            "captcha": settings.captcha_enabled,
            "proxy": settings.use_proxy
        }
    }

