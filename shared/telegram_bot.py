"""
Telegram Bot с командами для мониторинга и управления системой

Команды:
/start - Приветствие и список команд
/status - Статус системы
/health - Health check всех сервисов
/stats - Статистика за последние 24 часа
/logs - Последние логи (опционально)
/help - Справка по командам

Usage:
    python -m shared.telegram_bot
"""

import asyncio
import httpx
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

from shared.telegram_notifier import TelegramErrorNotifier
from core.database.supabase_client import get_supabase_client
from core.api.config import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    """Интерактивный Telegram бот для мониторинга системы"""
    
    def __init__(self, bot_token: Optional[str] = None, bot_type: str = "monitor"):
        """
        Args:
            bot_token: Telegram Bot Token (если None - берет из env)
            bot_type: Тип бота (monitor, leads, sales и т.д.) - используется для идентификации в БД
        """
        # Используем новые переменные с fallback на старые для обратной совместимости
        self.bot_token = bot_token or os.getenv(
            "TELEGRAM_MONITOR_BOT_TOKEN"
        ) or os.getenv("TELEGRAM_BOT_TOKEN")
        
        # Старый chat_id используется только для отправки уведомлений администратору
        self.admin_chat_id = os.getenv(
            "TELEGRAM_MONITOR_CHAT_ID"
        ) or os.getenv("TELEGRAM_NOTIFICATION_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token:
            raise ValueError(
                "TELEGRAM_MONITOR_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) not set in environment"
            )
        
        self.bot_type = bot_type  # monitor, leads, sales и т.д.
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Notifier использует admin_chat_id для уведомлений администратору
        if self.admin_chat_id:
            self.notifier = TelegramErrorNotifier(self.bot_token, self.admin_chat_id)
        else:
            self.notifier = TelegramErrorNotifier(self.bot_token, None)
        
        # Для хранения последних обновлений
        self.last_update_id = 0
        
        logger.info(f"✅ Telegram Bot initialized (type: {bot_type})")
    
    async def start_polling(self):
        """Запустить бота в режиме polling"""
        logger.info("🤖 Starting Telegram bot polling...")
        
        # Отправить приветствие
        await self.notifier.send_success(
            "🤖 Telegram Bot started and ready for commands!",
            module="TelegramBot"
        )
        
        while True:
            try:
                # Получить обновления
                updates = await self._get_updates()
                
                for update in updates:
                    await self._handle_update(update)
                
                # Небольшая задержка между запросами
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in bot polling: {e}", exc_info=True)
                await asyncio.sleep(5)  # Подождать перед повтором
    
    async def _get_updates(self) -> list:
        """Получить новые обновления от Telegram"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/getUpdates",
                    params={
                        "offset": self.last_update_id + 1,
                        "timeout": 30
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        
                        # Обновить last_update_id
                        if updates:
                            self.last_update_id = max(
                                u["update_id"] for u in updates
                            )
                        
                        return updates
                
                return []
        
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Обработать одно обновление"""
        if "message" not in update:
            return
        
        message = update["message"]
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        text = message.get("text", "").strip()
        from_user = message.get("from", {})
        
        # Извлекаем данные пользователя для сохранения в БД
        user_data = {
            "chat_id": chat_id,
            "username": from_user.get("username"),
            "first_name": from_user.get("first_name"),
            "last_name": from_user.get("last_name"),
            "language_code": from_user.get("language_code")
        }
        
        # Обработка команд
        if text.startswith("/"):
            command = text.split()[0] if text else ""
            
            # Если команда /start - сохраняем подписчика в БД
            if command == "/start":
                await self._save_subscriber(user_data)
            
            await self._handle_command(chat_id, command, text, user_data)
        else:
            # Обычное сообщение - обновляем last_activity_at
            await self._update_subscriber_activity(chat_id)
            await self._send_message(
                chat_id,
                "👋 Use /help to see available commands"
            )
    
    async def _handle_command(self, chat_id: int, command: str, full_text: str, user_data: Dict[str, Any]):
        """Обработать команду"""
        try:
            # Обновляем активность пользователя
            await self._update_subscriber_activity(chat_id)
            
            if command == "/start":
                await self._cmd_start(chat_id, user_data)
            
            elif command == "/status":
                await self._cmd_status(chat_id)
            
            elif command == "/health":
                await self._cmd_health(chat_id)
            
            elif command == "/stats":
                await self._cmd_stats(chat_id)
            
            elif command == "/help":
                await self._cmd_help(chat_id)
            
            else:
                await self._send_message(
                    chat_id,
                    f"❓ Unknown command: {command}\n\nUse /help to see available commands"
                )
        
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}", exc_info=True)
            await self._send_message(
                chat_id,
                f"❌ Error executing command: {str(e)}"
            )
    
    async def _cmd_start(self, chat_id: int, user_data: Dict[str, Any]):
        """Команда /start - приветствие и сохранение подписчика"""
        # Подписчик уже сохранен в _handle_update, просто отправляем приветствие
        username = user_data.get("username") or user_data.get("first_name", "there")
        
        message = f"""
🤖 <b>Lead Generation System Bot</b>

Привет, {username}! 👋

Я бот для мониторинга системы лид-генерации.

<b>Доступные команды:</b>
/status - Статус системы
/health - Проверка здоровья
/stats - Статистика (24ч)
/help - Справка

Отправь /help для подробной информации.

✅ Ты успешно подписан на уведомления!
        """
        await self._send_message(chat_id, message, parse_mode="HTML")
        
        # Логируем подписку
        logger.info(
            f"✅ New subscriber: chat_id={chat_id}, "
            f"username=@{user_data.get('username')}, "
            f"bot_type={self.bot_type}"
        )
    
    async def _cmd_status(self, chat_id: int):
        """Команда /status - статус системы"""
        try:
            # Получить базовую информацию
            uptime = self._get_uptime()
            memory = self._get_memory_usage()
            
            # Проверить базу данных
            db_status = "❌ Error"
            try:
                supabase = get_supabase_client()
                supabase.table("niches").select("id").limit(1).execute()
                db_status = "✅ OK"
            except:
                db_status = "❌ Unreachable"
            
            message = f"""
📊 <b>System Status</b>

🟢 <b>Status:</b> Running
⏰ <b>Uptime:</b> {uptime}
💾 <b>Memory:</b> {memory}
🗄️ <b>Database:</b> {db_status}
🌍 <b>Environment:</b> {'Development' if settings.debug else 'Production'}
📦 <b>Version:</b> 0.1.0
            """
            
            await self._send_message(chat_id, message, parse_mode="HTML")
        
        except Exception as e:
            await self._send_message(
                chat_id,
                f"❌ Error getting status: {str(e)}"
            )
    
    async def _cmd_health(self, chat_id: int):
        """Команда /health - детальная проверка здоровья"""
        try:
            services = {}
            issues = []
            
            # Проверка Supabase
            try:
                supabase = get_supabase_client()
                supabase.table("niches").select("id").limit(1).execute()
                services["supabase"] = "✅ OK"
            except Exception as e:
                services["supabase"] = f"❌ Error: {str(e)[:50]}"
                issues.append("Database unreachable")
            
            # Проверка Telegram
            telegram_token = os.getenv("TELEGRAM_MONITOR_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
            services["telegram"] = "✅ Configured" if telegram_token else "⚠️ Not configured"
            
            # Проверка WhatsApp
            services["whatsapp"] = "⚠️ Not checked"
            
            # Проверка Redis
            services["redis"] = "⚠️ Not checked"
            
            # Общий статус
            overall = "✅ Healthy" if not issues else "⚠️ Degraded"
            
            message = f"""
🏥 <b>Health Check</b>

<b>Overall Status:</b> {overall}

<b>Services:</b>
• Database: {services.get("supabase", "❓ Unknown")}
• Telegram: {services.get("telegram", "❓ Unknown")}
• WhatsApp: {services.get("whatsapp", "❓ Unknown")}
• Redis: {services.get("redis", "❓ Unknown")}

{('⚠️ <b>Issues detected:</b>\n' + '\n'.join(f'• {issue}' for issue in issues)) if issues else '✅ All services operational'}
            """
            
            await self._send_message(chat_id, message, parse_mode="HTML")
        
        except Exception as e:
            await self._send_message(
                chat_id,
                f"❌ Error checking health: {str(e)}"
            )
    
    async def _cmd_stats(self, chat_id: int):
        """Команда /stats - статистика за 24 часа"""
        try:
            supabase = get_supabase_client()
            
            # Получить статистику из базы
            stats = {
                "leads_24h": 0,
                "campaigns_active": 0,
                "errors_24h": 0
            }
            
            try:
                # Подсчет лидов за 24 часа
                yesterday = datetime.now() - timedelta(days=1)
                leads_result = supabase.table("leads").select(
                    "id",
                    count="exact"
                ).gte("created_at", yesterday.isoformat()).execute()
                
                stats["leads_24h"] = leads_result.count if hasattr(leads_result, 'count') else 0
                
                # Активные кампании
                campaigns_result = supabase.table("campaigns").select(
                    "id",
                    count="exact"
                ).eq("status", "active").execute()
                
                stats["campaigns_active"] = campaigns_result.count if hasattr(campaigns_result, 'count') else 0
            
            except Exception as e:
                logger.warning(f"Error getting stats from DB: {e}")
            
            message = f"""
📈 <b>Statistics (Last 24h)</b>

👥 <b>Leads created:</b> {stats['leads_24h']}
🚀 <b>Active campaigns:</b> {stats['campaigns_active']}
❌ <b>Errors:</b> {stats['errors_24h']}

⏰ <b>Last updated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            await self._send_message(chat_id, message, parse_mode="HTML")
        
        except Exception as e:
            await self._send_message(
                chat_id,
                f"❌ Error getting stats: {str(e)}"
            )
    
    async def _cmd_help(self, chat_id: int):
        """Команда /help - справка"""
        message = """
📖 <b>Available Commands</b>

<b>/start</b> - Welcome message
<b>/status</b> - System status (uptime, memory, database)
<b>/health</b> - Detailed health check of all services
<b>/stats</b> - Statistics for last 24 hours
<b>/help</b> - This help message

<b>Examples:</b>
• Send <code>/status</code> to check if system is running
• Send <code>/health</code> to verify all services
• Send <code>/stats</code> to see recent activity

<b>Note:</b> This bot also sends automatic notifications about errors and system events.
        """
        await self._send_message(chat_id, message, parse_mode="HTML")
    
    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Отправить сообщение"""
        try:
            payload = {
                "chat_id": chat_id,
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
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def _save_subscriber(self, user_data: Dict[str, Any]) -> bool:
        """
        Сохранить подписчика в базу данных
        
        Args:
            user_data: Данные пользователя (chat_id, username, first_name и т.д.)
        
        Returns:
            True если успешно сохранено
        """
        try:
            supabase = get_supabase_client()
            
            # Подготовка данных для вставки
            subscriber_data = {
                "bot_type": self.bot_type,
                "chat_id": user_data["chat_id"],
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "language_code": user_data.get("language_code"),
                "status": "active",
                "metadata": {}
            }
            
            # Используем upsert (INSERT ... ON CONFLICT UPDATE)
            # Если подписчик уже есть - обновляем данные
            result = supabase.table("telegram_bot_subscribers").upsert(
                subscriber_data,
                on_conflict="bot_type,chat_id"
            ).execute()
            
            logger.info(
                f"✅ Subscriber saved: chat_id={user_data['chat_id']}, "
                f"bot_type={self.bot_type}"
            )
            return True
        
        except Exception as e:
            logger.error(f"Error saving subscriber: {e}", exc_info=True)
            return False
    
    async def _update_subscriber_activity(self, chat_id: int) -> bool:
        """
        Обновить время последней активности подписчика
        
        Args:
            chat_id: Chat ID пользователя
        
        Returns:
            True если успешно обновлено
        """
        try:
            supabase = get_supabase_client()
            
            # Обновляем last_activity_at
            result = supabase.table("telegram_bot_subscribers").update({
                "last_activity_at": datetime.now().isoformat()
            }).eq("bot_type", self.bot_type).eq("chat_id", chat_id).execute()
            
            return True
        
        except Exception as e:
            # Не критично если не удалось обновить
            logger.debug(f"Could not update subscriber activity: {e}")
            return False
    
    def _get_uptime(self) -> str:
        """Получить uptime системы (упрощенная версия)"""
        # В реальности можно использовать psutil или системные команды
        return "N/A"
    
    def _get_memory_usage(self) -> str:
        """Получить использование памяти (упрощенная версия)"""
        # В реальности можно использовать psutil
        return "N/A"


# ============================================================================
# Запуск бота
# ============================================================================

async def main():
    """Главная функция для запуска бота"""
    try:
        bot = TelegramBot()
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

