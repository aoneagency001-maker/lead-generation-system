"""
Validation Utilities
Утилиты для валидации параметров API
"""

from datetime import date, datetime, timedelta
from typing import Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def validate_date_range(date_from: Optional[str], date_to: Optional[str]) -> tuple[date, date]:
    """
    Валидация диапазона дат
    
    Args:
        date_from: Начальная дата (ISO format: YYYY-MM-DD)
        date_to: Конечная дата (ISO format: YYYY-MM-DD)
    
    Returns:
        tuple[date, date]: Валидированные даты
    
    Raises:
        HTTPException: Если даты невалидны
    """
    try:
        if date_from:
            parsed_from = datetime.fromisoformat(date_from).date()
        else:
            parsed_from = date.today() - timedelta(days=7)
        
        if date_to:
            parsed_to = datetime.fromisoformat(date_to).date()
        else:
            parsed_to = date.today()
        
        # Проверка что date_from <= date_to
        if parsed_from > parsed_to:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid date range",
                    "message": "date_from must be <= date_to",
                    "date_from": str(parsed_from),
                    "date_to": str(parsed_to)
                }
            )
        
        # Проверка что даты не в будущем
        today = date.today()
        if parsed_from > today or parsed_to > today:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid date range",
                    "message": "Dates cannot be in the future",
                    "date_from": str(parsed_from),
                    "date_to": str(parsed_to),
                    "today": str(today)
                }
            )
        
        # Проверка что диапазон не слишком большой (макс 365 дней)
        days_diff = (parsed_to - parsed_from).days
        if days_diff > 365:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid date range",
                    "message": "Date range cannot exceed 365 days",
                    "days": days_diff,
                    "max_days": 365
                }
            )
        
        return parsed_from, parsed_to
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid date format",
                "message": "Dates must be in ISO format (YYYY-MM-DD)",
                "example": "2025-11-22"
            }
        )


def validate_counter_id(counter_id: int) -> int:
    """
    Валидация ID счетчика Яндекс.Метрики
    
    Args:
        counter_id: ID счетчика
    
    Returns:
        int: Валидированный ID
    
    Raises:
        HTTPException: Если ID невалиден
    """
    if counter_id <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid counter_id",
                "message": "counter_id must be a positive integer",
                "counter_id": counter_id
            }
        )
    
    # Яндекс.Метрика счетчики обычно 8-9 цифр
    if counter_id < 1000000 or counter_id > 999999999:
        logger.warning(f"Counter ID {counter_id} seems unusual (expected 7-9 digits)")
    
    return counter_id


def validate_property_id(property_id: str) -> str:
    """
    Валидация ID Property Google Analytics 4
    
    Args:
        property_id: ID Property (формат: "123456789" или "properties/123456789")
    
    Returns:
        str: Валидированный ID в формате "properties/XXXXX"
    
    Raises:
        HTTPException: Если ID невалиден
    """
    if not property_id:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid property_id",
                "message": "property_id is required",
                "property_id": property_id
            }
        )
    
    # Убираем префикс "properties/" если есть
    clean_id = property_id.replace("properties/", "")
    
    # Проверяем что это число
    try:
        int(clean_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid property_id",
                "message": "property_id must be numeric",
                "property_id": property_id,
                "example": "123456789"
            }
        )
    
    # Возвращаем в формате "properties/XXXXX"
    return f"properties/{clean_id}"


def validate_limit(limit: int, max_limit: int = 10000, min_limit: int = 1) -> int:
    """
    Валидация лимита записей
    
    Args:
        limit: Лимит записей
        max_limit: Максимальный лимит
        min_limit: Минимальный лимит
    
    Returns:
        int: Валидированный лимит
    
    Raises:
        HTTPException: Если лимит невалиден
    """
    if limit < min_limit:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid limit",
                "message": f"limit must be >= {min_limit}",
                "limit": limit,
                "min_limit": min_limit
            }
        )
    
    if limit > max_limit:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid limit",
                "message": f"limit must be <= {max_limit}",
                "limit": limit,
                "max_limit": max_limit
            }
        )
    
    return limit


def validate_days(days: int, max_days: int = 365, min_days: int = 1) -> int:
    """
    Валидация количества дней
    
    Args:
        days: Количество дней
        max_days: Максимальное количество дней
        min_days: Минимальное количество дней
    
    Returns:
        int: Валидированное количество дней
    
    Raises:
        HTTPException: Если количество дней невалидно
    """
    if days < min_days:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid days",
                "message": f"days must be >= {min_days}",
                "days": days,
                "min_days": min_days
            }
        )
    
    if days > max_days:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid days",
                "message": f"days must be <= {max_days}",
                "days": days,
                "max_days": max_days
            }
        )
    
    return days

