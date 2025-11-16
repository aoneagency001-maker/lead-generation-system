"""
Shared Utilities
Общие вспомогательные функции
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json


# ===================================
# Логирование
# ===================================

def get_logger(name: str) -> logging.Logger:
    """Получить настроенный логгер"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ===================================
# Работа с датами
# ===================================

def format_datetime(dt: datetime) -> str:
    """Форматировать datetime в строку"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(dt_str: str) -> datetime:
    """Парсить строку в datetime"""
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


# ===================================
# Работа с JSON
# ===================================

def load_json(filepath: str) -> Dict:
    """Загрузить JSON файл"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict, filepath: str) -> None:
    """Сохранить данные в JSON файл"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===================================
# Валидация
# ===================================

def validate_phone(phone: str) -> bool:
    """
    Проверить корректность телефона (Казахстан)
    
    Форматы: +77001234567, 87001234567, 77001234567
    """
    import re
    pattern = r'^(\+7|8|7)?[0-9]{10}$'
    return bool(re.match(pattern, phone.replace(" ", "").replace("-", "")))


def normalize_phone(phone: str) -> str:
    """
    Нормализовать телефон к формату +77XXXXXXXXX
    
    Args:
        phone: Телефон в любом формате
        
    Returns:
        str: Нормализованный телефон
    """
    # Убираем все кроме цифр
    digits = ''.join(filter(str.isdigit, phone))
    
    # Если начинается с 8, меняем на 7
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    
    # Если не начинается с 7, добавляем
    if not digits.startswith('7'):
        digits = '7' + digits
    
    return '+' + digits


# ===================================
# Форматирование данных
# ===================================

def format_price(price: float) -> str:
    """Форматировать цену для отображения"""
    return f"{int(price):,} тг".replace(",", " ")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезать текст до максимальной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


# ===================================
# Безопасность
# ===================================

def sanitize_input(text: str) -> str:
    """
    Очистить пользовательский ввод от опасных символов
    
    Args:
        text: Входной текст
        
    Returns:
        str: Очищенный текст
    """
    # Удаляем HTML теги
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Удаляем SQL инъекции (базовая защита)
    dangerous_patterns = [
        r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b)',
        r'(--|\;|\/\*|\*\/)',
    ]
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


# ===================================
# Retry логика
# ===================================

def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Декоратор для повторения функции при ошибке
    
    Args:
        max_attempts: Максимальное количество попыток
        delay: Задержка между попытками (секунды)
    """
    import time
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise last_exception
        return wrapper
    return decorator


# ===================================
# Экспорт
# ===================================

__all__ = [
    "get_logger",
    "format_datetime",
    "parse_datetime",
    "load_json",
    "save_json",
    "validate_phone",
    "normalize_phone",
    "format_price",
    "truncate_text",
    "sanitize_input",
    "retry"
]

