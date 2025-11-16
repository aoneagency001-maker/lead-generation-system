"""
Configuration Management
Управление настройками приложения через переменные окружения
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    api_secret_key: str = "change-me-in-production"
    
    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # n8n
    n8n_url: str = "http://localhost:5678"
    n8n_api_key: Optional[str] = None
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_notification_chat_id: Optional[str] = None
    
    # WhatsApp (WAHA)
    whatsapp_api_url: str = "http://localhost:3001"
    whatsapp_api_key: Optional[str] = None
    
    # Proxy
    use_proxy: bool = False
    proxy_type: str = "http"
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_list: Optional[str] = None
    
    # Captcha
    captcha_api_key: Optional[str] = None
    captcha_enabled: bool = False
    
    # AI/LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    use_local_llm: bool = False
    ollama_base_url: str = "http://localhost:11434"
    
    # OLX
    olx_email_1: Optional[str] = None
    olx_password_1: Optional[str] = None
    olx_phone_1: Optional[str] = None
    
    # Kaspi
    kaspi_merchant_id: Optional[str] = None
    kaspi_api_key: Optional[str] = None
    
    # Application Settings
    max_ads_per_day: int = 10
    max_concurrent_parsers: int = 3
    lead_qualification_timeout: int = 300
    
    # Notifications
    enable_notifications: bool = True
    notification_channels: str = "telegram,email"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Создаем глобальный экземпляр настроек
settings = Settings()


# ===================================
# Helper функции
# ===================================

def get_proxy_config() -> Optional[dict]:
    """
    Получить конфигурацию прокси
    
    Returns:
        dict или None если прокси не используется
    """
    if not settings.use_proxy:
        return None
    
    if settings.proxy_list:
        # Если есть список прокси, возвращаем первый
        proxies = settings.proxy_list.split(",")
        return {"http": proxies[0], "https": proxies[0]}
    
    if settings.proxy_host and settings.proxy_port:
        auth = ""
        if settings.proxy_username and settings.proxy_password:
            auth = f"{settings.proxy_username}:{settings.proxy_password}@"
        
        proxy_url = f"{settings.proxy_type}://{auth}{settings.proxy_host}:{settings.proxy_port}"
        return {"http": proxy_url, "https": proxy_url}
    
    return None


def get_notification_channels() -> list:
    """Получить список активных каналов уведомлений"""
    if not settings.enable_notifications:
        return []
    return [ch.strip() for ch in settings.notification_channels.split(",")]


def is_telegram_configured() -> bool:
    """Проверить, настроен ли Telegram бот"""
    return bool(settings.telegram_bot_token)


def is_whatsapp_configured() -> bool:
    """Проверить, настроен ли WhatsApp"""
    return bool(settings.whatsapp_api_url and settings.whatsapp_api_key)


def is_ai_configured() -> bool:
    """Проверить, настроен ли AI"""
    return bool(settings.openai_api_key or settings.use_local_llm)


# Экспорт
__all__ = [
    "settings",
    "get_proxy_config",
    "get_notification_channels",
    "is_telegram_configured",
    "is_whatsapp_configured",
    "is_ai_configured"
]

