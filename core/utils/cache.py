"""
Redis Cache Utility
Утилита для кэширования данных в Redis
"""

import json
import redis
from typing import Optional, Any
from functools import wraps
import logging
from core.api.config import settings

logger = logging.getLogger(__name__)

# Глобальный клиент Redis (singleton)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """
    Получить Redis клиент (singleton)
    
    Returns:
        redis.Redis: Redis клиент
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Проверяем подключение
            _redis_client.ping()
            logger.info(f"✅ Redis подключен: {settings.redis_url}")
        except Exception as e:
            logger.warning(f"⚠️  Redis недоступен: {e}. Кэширование отключено.")
            _redis_client = None
    
    return _redis_client


async def get_cached(key: str) -> Optional[Any]:
    """
    Получить значение из кэша
    
    Args:
        key: Ключ кэша
    
    Returns:
        Значение из кэша или None если не найдено
    """
    try:
        client = get_redis_client()
        if client is None:
            return None
        
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.warning(f"Ошибка получения из кэша {key}: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Сохранить значение в кэш
    
    Args:
        key: Ключ кэша
        value: Значение для сохранения
        ttl: Время жизни в секундах (по умолчанию 5 минут)
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        client = get_redis_client()
        if client is None:
            return False
        
        client.setex(
            key,
            ttl,
            json.dumps(value, default=str)  # default=str для дат и других объектов
        )
        return True
    except Exception as e:
        logger.warning(f"Ошибка сохранения в кэш {key}: {e}")
        return False


def cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Создать ключ кэша из префикса и параметров
    
    Args:
        prefix: Префикс ключа
        *args: Позиционные аргументы
        **kwargs: Именованные аргументы
    
    Returns:
        Строка ключа кэша
    """
    parts = [prefix]
    
    # Добавляем позиционные аргументы
    for arg in args:
        parts.append(str(arg))
    
    # Добавляем именованные аргументы (сортируем для консистентности)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        for key, value in sorted_kwargs:
            parts.append(f"{key}:{value}")
    
    return ":".join(parts)

