"""
Примеры использования Telegram Notifier
Показывает как использовать уведомления в модулях
"""

from shared.telegram_notifier import telegram_notifier, notify_error, notify_success, notify_warning
from typing import Optional


# ============================================================================
# ПРИМЕР 1: Уведомление об ошибке в сервисе
# ============================================================================

class WhatsAppService:
    """Пример сервиса отправки WhatsApp сообщений"""
    
    async def send_message(self, phone: str, text: str) -> bool:
        """Отправить сообщение через WhatsApp"""
        try:
            # Твоя логика отправки
            # response = await whatsapp_api.send(phone, text)
            
            # Успех - можно уведомить (опционально)
            await notify_success(
                f"Message sent to {phone}",
                module="WhatsAppService"
            )
            
            return True
            
        except ConnectionError as e:
            # Критическая ошибка - уведомляем
            await telegram_notifier.send_error(
                error=e,
                module="WhatsAppService.send_message",
                user_context={
                    "phone": phone,
                    "message_length": len(text)
                },
                severity="CRITICAL"  # Это критично!
            )
            raise
        
        except ValueError as e:
            # Некритическая ошибка - просто WARNING
            await telegram_notifier.send_error(
                error=e,
                module="WhatsAppService.send_message",
                user_context={"phone": phone},
                severity="WARNING"
            )
            return False


# ============================================================================
# ПРИМЕР 2: Мониторинг долгих операций
# ============================================================================

import time
from datetime import datetime

class OLXParser:
    """Пример парсера OLX"""
    
    async def parse_ads(self, category: str, max_pages: int = 10):
        """Парсить объявления с OLX"""
        start_time = time.time()
        
        try:
            # Уведомление о старте (опционально)
            await notify_success(
                f"Started parsing OLX: {category} ({max_pages} pages)",
                module="OLXParser"
            )
            
            ads = []
            for page in range(max_pages):
                # Твоя логика парсинга
                # page_ads = await self._parse_page(page)
                # ads.extend(page_ads)
                pass
            
            # Успех - отчет
            elapsed = time.time() - start_time
            await notify_success(
                f"✅ OLX parsing completed!\n"
                f"Category: {category}\n"
                f"Ads found: {len(ads)}\n"
                f"Time: {elapsed:.1f}s",
                module="OLXParser"
            )
            
            return ads
        
        except Exception as e:
            # Ошибка - детальный отчет
            elapsed = time.time() - start_time
            await telegram_notifier.send_error(
                error=e,
                module="OLXParser.parse_ads",
                user_context={
                    "category": category,
                    "max_pages": max_pages,
                    "elapsed_time": f"{elapsed:.1f}s"
                },
                extra_info={
                    "ads_collected": len(ads) if 'ads' in locals() else 0
                }
            )
            raise


# ============================================================================
# ПРИМЕР 3: Критические события системы
# ============================================================================

class DatabaseService:
    """Пример сервиса для работы с БД"""
    
    async def check_disk_space(self):
        """Проверить место на диске"""
        # Твоя логика проверки
        disk_usage_percent = 85  # Пример
        
        if disk_usage_percent > 90:
            # КРИТИЧНО! Немедленное уведомление
            await telegram_notifier.send_critical(
                message="Disk space critical!",
                module="DatabaseService",
                details={
                    "disk_usage": f"{disk_usage_percent}%",
                    "action_required": "Clean up old data or expand disk",
                    "estimated_time_left": "~2 hours"
                }
            )
        
        elif disk_usage_percent > 80:
            # Предупреждение
            await notify_warning(
                f"⚠️ Disk usage high: {disk_usage_percent}%\n"
                f"Consider cleanup soon.",
                module="DatabaseService"
            )


# ============================================================================
# ПРИМЕР 4: Мониторинг производительности
# ============================================================================

class PerformanceMonitor:
    """Пример мониторинга производительности"""
    
    async def check_api_response_time(self, endpoint: str, response_time: float):
        """Проверить время ответа API"""
        
        # Если медленно - уведомляем
        if response_time > 2.0:
            await notify_warning(
                f"🐌 Slow API response detected!\n"
                f"Endpoint: {endpoint}\n"
                f"Response time: {response_time:.2f}s\n"
                f"Threshold: 2.0s",
                module="PerformanceMonitor"
            )
        
        # Если очень медленно - критично
        if response_time > 5.0:
            await telegram_notifier.send_critical(
                message=f"API endpoint extremely slow: {endpoint}",
                module="PerformanceMonitor",
                details={
                    "response_time": f"{response_time:.2f}s",
                    "threshold": "5.0s",
                    "action": "Check server load and database queries"
                }
            )


# ============================================================================
# ПРИМЕР 5: Периодические отчеты
# ============================================================================

class DailyReporter:
    """Пример ежедневного отчета"""
    
    async def send_daily_report(
        self,
        leads_created: int,
        messages_sent: int,
        errors_count: int
    ):
        """Отправить ежедневный отчет"""
        
        report = f"""
📊 <b>Daily Report</b> - {datetime.now().strftime('%Y-%m-%d')}

📈 <b>Metrics:</b>
  • Leads created: {leads_created}
  • Messages sent: {messages_sent}
  • Errors: {errors_count}

{'✅ <b>Status: Good</b>' if errors_count < 10 else '⚠️ <b>Status: Issues detected</b>'}
"""
        
        await telegram_notifier._send_message(report, parse_mode="HTML")


# ============================================================================
# ПРИМЕР 6: Обработка ошибок в декораторе
# ============================================================================

from functools import wraps

def with_telegram_error_handling(module_name: str):
    """
    Декоратор для автоматической отправки ошибок в Telegram
    
    Usage:
        @with_telegram_error_handling("MyService")
        async def my_function():
            # Your code here
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                await telegram_notifier.send_error(
                    error=e,
                    module=f"{module_name}.{func.__name__}",
                    extra_info={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs": str(kwargs)[:100]
                    }
                )
                raise
        return wrapper
    return decorator


# Пример использования декоратора
@with_telegram_error_handling("LeadService")
async def create_lead(phone: str, name: str):
    """Создать нового лида"""
    # Если здесь будет ошибка - автоматически уведомит в Telegram
    # ...
    pass


# ============================================================================
# ПРИМЕР 7: Интеграция с Celery tasks
# ============================================================================

# from celery import Task
# 
# class TelegramNotifyTask(Task):
#     """Базовая Celery task с уведомлениями в Telegram"""
#     
#     def on_failure(self, exc, task_id, args, kwargs, einfo):
#         """Автоматически уведомлять при провале задачи"""
#         import asyncio
#         
#         asyncio.run(
#             telegram_notifier.send_error(
#                 error=exc,
#                 module=f"CeleryTask.{self.name}",
#                 extra_info={
#                     "task_id": task_id,
#                     "args": str(args)[:100],
#                     "kwargs": str(kwargs)[:100]
#                 }
#             )
#         )
# 
# # Использование
# @app.task(base=TelegramNotifyTask)
# def my_background_task():
#     # Если упадет - автоматически уведомит
#     pass


