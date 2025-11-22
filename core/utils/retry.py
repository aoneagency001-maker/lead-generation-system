"""
Retry Utilities
Утилиты для повторных попыток при временных ошибках
"""

import asyncio
import logging
from typing import Callable, TypeVar, Optional, List
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_async(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> T:
    """
    Повторить асинхронную функцию при ошибке.
    
    Args:
        func: Асинхронная функция для выполнения
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками (секунды)
        backoff: Множитель для увеличения задержки
        exceptions: Кортеж исключений, при которых нужно повторять
        on_retry: Функция, вызываемая при каждой попытке
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Последнее исключение, если все попытки исчерпаны
    """
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func()
            else:
                return func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_attempts:
                wait_time = delay * (backoff ** (attempt - 1))
                logger.warning(
                    f"⚠️ Попытка {attempt}/{max_attempts} не удалась: {e}. "
                    f"Повтор через {wait_time:.1f}с..."
                )
                
                if on_retry:
                    try:
                        await on_retry(attempt, e) if asyncio.iscoroutinefunction(on_retry) else on_retry(attempt, e)
                    except Exception:
                        pass
                
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Все {max_attempts} попыток исчерпаны. Последняя ошибка: {e}")
    
    # Если дошли сюда, все попытки исчерпаны
    raise last_exception


def retry_sync(
    func: Callable,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> T:
    """
    Повторить синхронную функцию при ошибке.
    
    Args:
        func: Синхронная функция для выполнения
        max_attempts: Максимальное количество попыток
        delay: Начальная задержка между попытками (секунды)
        backoff: Множитель для увеличения задержки
        exceptions: Кортеж исключений, при которых нужно повторять
        on_retry: Функция, вызываемая при каждой попытке
    
    Returns:
        Результат выполнения функции
    
    Raises:
        Последнее исключение, если все попытки исчерпаны
    """
    import time
    
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_attempts:
                wait_time = delay * (backoff ** (attempt - 1))
                logger.warning(
                    f"⚠️ Попытка {attempt}/{max_attempts} не удалась: {e}. "
                    f"Повтор через {wait_time:.1f}с..."
                )
                
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception:
                        pass
                
                time.sleep(wait_time)
            else:
                logger.error(f"❌ Все {max_attempts} попыток исчерпаны. Последняя ошибка: {e}")
    
    # Если дошли сюда, все попытки исчерпаны
    raise last_exception


def retry_decorator(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Декоратор для автоматического повтора функции при ошибке.
    
    Usage:
        @retry_decorator(max_attempts=3, delay=1.0)
        async def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await retry_async(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions
            )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return retry_sync(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions
            )
        
        # Определяем, асинхронная ли функция
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

