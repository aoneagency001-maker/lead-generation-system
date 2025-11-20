"""
Telegram Error Notifier
Модуль для отправки уведомлений об ошибках и событиях в Telegram

Usage:
    from shared.telegram_notifier import telegram_notifier
    
    await telegram_notifier.send_error(
        error=exception,
        module="ModuleName",
        user_context={"user_id": 123}
    )
"""

import httpx
import traceback
import os
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TelegramErrorNotifier:
    """Отправка уведомлений в Telegram о ошибках и событиях системы"""
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        Args:
            bot_token: Telegram Bot Token (если None - берет из env)
            chat_id: Telegram Chat ID (если None - берет из env)
        """
        # Используем новые переменные с fallback на старые для обратной совместимости
        self.bot_token = bot_token or os.getenv(
            "TELEGRAM_MONITOR_BOT_TOKEN"
        ) or os.getenv("TELEGRAM_BOT_TOKEN")
        
        self.chat_id = chat_id or os.getenv(
            "TELEGRAM_MONITOR_CHAT_ID"
        ) or os.getenv("TELEGRAM_NOTIFICATION_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
        
        # Если нет токена или chat_id - просто логируем
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning(
                "⚠️  Telegram notifier disabled: "
                "TELEGRAM_MONITOR_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) or "
                "TELEGRAM_MONITOR_CHAT_ID (or TELEGRAM_NOTIFICATION_CHAT_ID) not set"
            )
        else:
            logger.info("✅ Telegram notifier enabled")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
        # Для защиты от спама - кэш последних ошибок
        self._error_cache: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 минут
    
    async def send_error(
        self,
        error: Exception,
        module: str,
        user_context: Optional[Dict[str, Any]] = None,
        extra_info: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> bool:
        """
        Отправить ошибку в Telegram
        
        Args:
            error: Exception объект
            module: Название модуля (например, "WhatsAppService")
            user_context: Контекст пользователя (user_id, phone, etc.)
            extra_info: Дополнительная информация
            severity: Уровень важности (ERROR, WARNING, CRITICAL)
        
        Returns:
            True если отправлено успешно, False если нет
        """
        if not self.enabled:
            logger.error(f"❌ {module}: {type(error).__name__}: {str(error)}")
            return False
        
        # Защита от спама - не отправляем одинаковые ошибки чаще раза в 5 минут
        error_key = f"{module}:{type(error).__name__}:{str(error)[:50]}"
        if self._is_duplicate_error(error_key):
            logger.debug(f"Skipping duplicate error: {error_key}")
            return False
        
        # Форматировать сообщение
        message = self._format_error_message(
            error=error,
            module=module,
            user_context=user_context,
            extra_info=extra_info,
            severity=severity
        )
        
        # Отправить
        success = await self._send_message(message, parse_mode="HTML")
        
        if success:
            # Запомнить что отправили
            self._error_cache[error_key] = datetime.now()
            logger.info(f"📤 Error sent to Telegram: {module}")
        
        return success
    
    async def send_success(self, message: str, module: Optional[str] = None) -> bool:
        """
        Отправить успешное уведомление
        
        Args:
            message: Текст сообщения
            module: Название модуля (optional)
        
        Returns:
            True если отправлено
        """
        if not self.enabled:
            return False
        
        text = f"✅ {message}"
        if module:
            text = f"✅ **{module}**\n{message}"
        
        return await self._send_message(text)
    
    async def send_warning(self, message: str, module: Optional[str] = None) -> bool:
        """
        Отправить предупреждение
        
        Args:
            message: Текст сообщения
            module: Название модуля (optional)
        
        Returns:
            True если отправлено
        """
        if not self.enabled:
            return False
        
        text = f"⚠️ {message}"
        if module:
            text = f"⚠️ **{module}**\n{message}"
        
        return await self._send_message(text)
    
    async def send_info(self, message: str, module: Optional[str] = None) -> bool:
        """
        Отправить информационное сообщение
        
        Args:
            message: Текст сообщения
            module: Название модуля (optional)
        
        Returns:
            True если отправлено
        """
        if not self.enabled:
            return False
        
        text = f"ℹ️ {message}"
        if module:
            text = f"ℹ️ **{module}**\n{message}"
        
        return await self._send_message(text)
    
    async def send_critical(
        self,
        message: str,
        module: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Отправить критическое уведомление (требует немедленного внимания)
        
        Args:
            message: Текст сообщения
            module: Название модуля
            details: Дополнительные детали
        
        Returns:
            True если отправлено
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        text = f"""
🚨🚨🚨 <b>CRITICAL ALERT!</b> 🚨🚨🚨

⏰ <b>Time:</b> {timestamp}
🔥 <b>Module:</b> {module}
💥 <b>Message:</b> {message}
"""
        
        if details:
            text += "\n📋 <b>Details:</b>\n"
            for key, value in details.items():
                text += f"  • {key}: {value}\n"
        
        text += "\n⚡ <b>ACTION REQUIRED IMMEDIATELY!</b>"
        
        return await self._send_message(text, parse_mode="HTML")
    
    def _format_error_message(
        self,
        error: Exception,
        module: str,
        user_context: Optional[Dict[str, Any]],
        extra_info: Optional[Dict[str, Any]],
        severity: str
    ) -> str:
        """Форматировать красивое сообщение об ошибке"""
        
        # Эмодзи по severity
        emoji_map = {
            "ERROR": "❌",
            "WARNING": "⚠️",
            "CRITICAL": "🚨"
        }
        emoji = emoji_map.get(severity, "❌")
        
        # Время
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Stack trace (последние 5 строк)
        stack = ''.join(traceback.format_tb(error.__traceback__))
        stack_lines = [line.strip() for line in stack.split('\n') if line.strip()]
        stack_preview = '\n'.join(stack_lines[-5:]) if stack_lines else "No stack trace"
        
        # Собрать сообщение
        message = f"""
{emoji} <b>{severity} in Production!</b>

⏰ <b>Time:</b> {timestamp}
📦 <b>Module:</b> {module}
❌ <b>Error Type:</b> {type(error).__name__}
💬 <b>Message:</b> {str(error)[:200]}
"""
        
        # Контекст пользователя
        if user_context:
            message += f"\n👤 <b>User Context:</b>\n"
            for key, value in list(user_context.items())[:5]:  # Макс 5 полей
                message += f"  • {key}: {value}\n"
        
        # Доп. инфо
        if extra_info:
            message += f"\n📋 <b>Extra Info:</b>\n"
            for key, value in list(extra_info.items())[:5]:  # Макс 5 полей
                message += f"  • {key}: {value}\n"
        
        # Stack trace
        message += f"\n📍 <b>Stack Trace:</b>\n<code>{stack_preview[:500]}</code>"
        
        # Telegram лимит 4096 символов
        return message[:4000]
    
    async def _send_message(
        self,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """
        Отправить сообщение в Telegram
        
        Args:
            text: Текст сообщения
            parse_mode: "HTML" или "Markdown" (optional)
        
        Returns:
            True если успешно
        """
        if not self.enabled:
            return False
        
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(
                        f"Telegram API error: {response.status_code} - {response.text}"
                    )
                    return False
        
        except Exception as e:
            # Если Telegram недоступен - просто логируем
            logger.error(f"Failed to send Telegram notification: {e}")
            return False
    
    def _is_duplicate_error(self, error_key: str) -> bool:
        """Проверить, не отправляли ли мы эту ошибку недавно"""
        if error_key not in self._error_cache:
            return False
        
        # Проверить не истек ли TTL
        last_sent = self._error_cache[error_key]
        elapsed = (datetime.now() - last_sent).total_seconds()
        
        if elapsed > self._cache_ttl:
            # TTL истек - можем отправить снова
            del self._error_cache[error_key]
            return False
        
        return True
    
    def clear_cache(self):
        """Очистить кэш ошибок (для тестирования)"""
        self._error_cache.clear()


# Глобальный singleton инстанс
telegram_notifier = TelegramErrorNotifier()


# Convenience functions для быстрого использования
async def notify_error(
    error: Exception,
    module: str,
    **kwargs
) -> bool:
    """Shortcut для отправки ошибки"""
    return await telegram_notifier.send_error(error, module, **kwargs)


async def notify_success(message: str, module: Optional[str] = None) -> bool:
    """Shortcut для успеха"""
    return await telegram_notifier.send_success(message, module)


async def notify_warning(message: str, module: Optional[str] = None) -> bool:
    """Shortcut для предупреждения"""
    return await telegram_notifier.send_warning(message, module)


async def notify_critical(message: str, module: str, details: Optional[Dict] = None) -> bool:
    """Shortcut для критического события"""
    return await telegram_notifier.send_critical(message, module, details)

