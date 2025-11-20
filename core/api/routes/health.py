"""
Health Check Routes
Проверка работоспособности системы
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import logging
from datetime import datetime

from core.database.supabase_client import get_supabase_client
from core.api.config import settings, is_telegram_configured, is_whatsapp_configured
from shared.telegram_notifier import telegram_notifier

router = APIRouter()
logger = logging.getLogger(__name__)

# Для отслеживания состояния здоровья (чтобы не спамить)
_last_health_issues: Dict[str, datetime] = {}
_notification_cooldown = 300  # 5 минут между уведомлениями об одной проблеме


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
    issues: List[str] = []
    
    # Проверка Supabase
    try:
        supabase = get_supabase_client()
        # Простой запрос для проверки
        result = supabase.table("niches").select("id").limit(1).execute()
        services["supabase"] = "ok"
    except Exception as e:
        logger.error(f"Supabase error: {e}")
        services["supabase"] = "error"
        issues.append("Database (Supabase) unreachable")
        
        # Уведомление в Telegram (с защитой от спама)
        await _notify_if_needed(
            "supabase_error",
            f"⚠️ Database connection lost!\nError: {str(e)[:100]}"
        )
    
    # Проверка Telegram
    services["telegram"] = "configured" if is_telegram_configured() else "not_configured"
    
    # Проверка WhatsApp
    services["whatsapp"] = "configured" if is_whatsapp_configured() else "not_configured"
    
    # Проверка Redis (опционально)
    services["redis"] = "not_checked"
    
    # Определяем общий статус
    overall_status = "healthy" if services["supabase"] == "ok" else "degraded"
    
    # Если есть критические проблемы - отправляем в Telegram
    if overall_status == "degraded" and issues:
        await _notify_if_needed(
            "system_degraded",
            f"🚨 System Health Check Failed!\n\nIssues:\n" + "\n".join(f"• {issue}" for issue in issues)
        )
    
    return HealthResponse(
        status=overall_status,
        services=services,
        version="0.1.0"
    )


async def _notify_if_needed(issue_key: str, message: str) -> None:
    """
    Отправить уведомление в Telegram с защитой от спама
    
    Args:
        issue_key: Ключ проблемы (для защиты от дубликатов)
        message: Сообщение для отправки
    """
    now = datetime.now()
    
    # Проверяем не отправляли ли мы уведомление недавно
    if issue_key in _last_health_issues:
        last_sent = _last_health_issues[issue_key]
        elapsed = (now - last_sent).total_seconds()
        
        if elapsed < _notification_cooldown:
            # Слишком рано - не отправляем
            return
    
    # Отправляем
    await telegram_notifier.send_warning(
        message=message,
        module="HealthCheck"
    )
    
    # Запоминаем
    _last_health_issues[issue_key] = now


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

