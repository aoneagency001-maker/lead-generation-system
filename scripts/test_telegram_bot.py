#!/usr/bin/env python3
"""
Скрипт для тестирования Telegram Bot

Тестирует все функции:
1. Уведомления (success, error, warning, critical)
2. Команды бота (/status, /health, /stats)
3. Health check уведомления
4. Error handling

Usage:
    python scripts/test_telegram_bot.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавить корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from shared.telegram_notifier import telegram_notifier
from shared.telegram_bot import TelegramBot
import httpx
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramBotTester:
    """Класс для тестирования Telegram бота"""
    
    def __init__(self):
        # Используем новые переменные с fallback на старые
        self.bot_token = os.getenv("TELEGRAM_MONITOR_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_MONITOR_CHAT_ID") or os.getenv("TELEGRAM_NOTIFICATION_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_MONITOR_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) and "
                "TELEGRAM_MONITOR_CHAT_ID (or TELEGRAM_NOTIFICATION_CHAT_ID) must be set in .env"
            )
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        logger.info("✅ Telegram Bot Tester initialized")
    
    async def test_all(self):
        """Запустить все тесты"""
        print("\n" + "="*60)
        print("🧪 TELEGRAM BOT TESTING SUITE")
        print("="*60 + "\n")
        
        tests = [
            ("1. Success Notification", self.test_success),
            ("2. Warning Notification", self.test_warning),
            ("3. Error Notification", self.test_error),
            ("4. Critical Notification", self.test_critical),
            ("5. Command /start", self.test_start_command),
            ("6. Command /status", self.test_status_command),
            ("7. Command /health", self.test_health_command),
            ("8. Command /stats", self.test_stats_command),
            ("9. Command /help", self.test_help_command),
            ("10. Error Handling", self.test_error_handling),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            print("-" * 60)
            
            try:
                await test_func()
                results.append((test_name, "✅ PASSED"))
                print(f"✅ {test_name} - PASSED")
            except Exception as e:
                results.append((test_name, f"❌ FAILED: {str(e)}"))
                print(f"❌ {test_name} - FAILED: {e}")
            
            # Пауза между тестами
            await asyncio.sleep(2)
        
        # Итоговый отчет
        print("\n" + "="*60)
        print("📊 TEST RESULTS")
        print("="*60)
        
        passed = sum(1 for _, result in results if "PASSED" in result)
        failed = len(results) - passed
        
        for test_name, result in results:
            print(f"{result} - {test_name}")
        
        print("\n" + "="*60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {len(results)}")
        print("="*60 + "\n")
    
    async def test_success(self):
        """Тест успешного уведомления"""
        await telegram_notifier.send_success(
            "✅ Test: Success notification",
            module="TestSuite"
        )
        print("   Sent success notification")
    
    async def test_warning(self):
        """Тест предупреждения"""
        await telegram_notifier.send_warning(
            "⚠️ Test: Warning notification",
            module="TestSuite"
        )
        print("   Sent warning notification")
    
    async def test_error(self):
        """Тест уведомления об ошибке"""
        try:
            raise ValueError("Test error for notification")
        except Exception as e:
            await telegram_notifier.send_error(
                error=e,
                module="TestSuite.test_error",
                user_context={"test": "value"},
                severity="ERROR"
            )
            print("   Sent error notification")
    
    async def test_critical(self):
        """Тест критического уведомления"""
        await telegram_notifier.send_critical(
            message="🚨 Test: Critical notification",
            module="TestSuite",
            details={
                "test_type": "critical",
                "severity": "high"
            }
        )
        print("   Sent critical notification")
    
    async def test_start_command(self):
        """Тест команды /start"""
        await self._send_command("/start")
        print("   Command /start sent")
    
    async def test_status_command(self):
        """Тест команды /status"""
        await self._send_command("/status")
        print("   Command /status sent")
    
    async def test_health_command(self):
        """Тест команды /health"""
        await self._send_command("/health")
        print("   Command /health sent")
    
    async def test_stats_command(self):
        """Тест команды /stats"""
        await self._send_command("/stats")
        print("   Command /stats sent")
    
    async def test_help_command(self):
        """Тест команды /help"""
        await self._send_command("/help")
        print("   Command /help sent")
    
    async def test_error_handling(self):
        """Тест обработки ошибок"""
        # Симуляция ошибки в модуле
        try:
            raise ConnectionError("Test connection error")
        except Exception as e:
            await telegram_notifier.send_error(
                error=e,
                module="TestSuite.error_handling",
                user_context={
                    "test_scenario": "error_handling",
                    "error_type": "ConnectionError"
                },
                extra_info={
                    "recovery_action": "retry",
                    "max_retries": 3
                },
                severity="ERROR"
            )
            print("   Error handling test completed")
    
    async def _send_command(self, command: str):
        """Отправить команду боту через API"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": command
                    }
                )
                
                if response.status_code == 200:
                    print(f"   ✅ Command sent successfully")
                else:
                    raise Exception(f"API error: {response.status_code}")
        
        except Exception as e:
            raise Exception(f"Failed to send command: {e}")


async def main():
    """Главная функция"""
    try:
        tester = TelegramBotTester()
        await tester.test_all()
        
        print("\n💡 Tip: Check your Telegram to see all notifications and responses!")
        print("💡 Note: Bot must be running (python -m shared.telegram_bot) to receive commands\n")
    
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nMake sure you have:")
        print("1. TELEGRAM_MONITOR_BOT_TOKEN (or TELEGRAM_BOT_TOKEN) in .env")
        print("2. TELEGRAM_MONITOR_CHAT_ID (or TELEGRAM_NOTIFICATION_CHAT_ID) in .env")
        print("3. Bot created via @BotFather")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

