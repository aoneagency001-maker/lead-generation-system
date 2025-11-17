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
    telegram_sales_chat_id: Optional[str] = None
    
    # WhatsApp (WAHA)
    whatsapp_api_url: str = "http://localhost:3001"
    whatsapp_api_key: Optional[str] = None
    whatsapp_session_name: str = "leadgen"
    
    # Proxy
    use_proxy: bool = False
    proxy_type: str = "http"
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_list: Optional[str] = None
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    proxy_rotation_interval: int = 300
    
    # Captcha
    captcha_api_key: Optional[str] = None
    captcha_enabled: bool = False
    
    # AI/LLM
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 500
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
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
    
    # Module 1: Market Research
    max_scraping_workers: int = 3
    scraping_rate_limit: int = 1
    scraping_timeout: int = 30
    
    # Module 2: Traffic Generation
    max_ads_per_campaign: int = 10
    ad_posting_delay_min: int = 2
    ad_posting_delay_max: int = 5
    
    # Module 3: Lead Qualification
    min_qualification_score: int = 60
    
    # Module 4: Sales Handoff
    auto_handoff_threshold: int = 80
    handoff_notification_channels: str = "telegram"
    
    # Module 5: Analytics
    metrics_cache_ttl: int = 3600
    daily_report_time: str = "09:00"
    enable_daily_reports: bool = True
    
    # Notifications
    enable_notifications: bool = True
    notification_channels: str = "telegram,email"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    # Email
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_password: Optional[str] = None
    
    # SMS
    sms_provider: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # Analytics
    ga_tracking_id: Optional[str] = None
    sentry_dsn: Optional[str] = None
    
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

