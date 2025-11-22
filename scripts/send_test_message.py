#!/usr/bin/env python3
"""
Скрипт для отправки тестового сообщения в Telegram бот

Usage:
    python3 scripts/send_test_message.py
"""

import asyncio
import os
import httpx
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()


def get_chat_id_from_env() -> Optional[int]:
    """Получить chat_id из переменных окружения"""
    chat_id_str = (
        os.getenv("TELEGRAM_MONITOR_CHAT_ID") 
        or os.getenv("TELEGRAM_NOTIFICATION_CHAT_ID") 
        or os.getenv("TELEGRAM_CHAT_ID")
    )
    
    if chat_id_str:
        try:
            return int(chat_id_str)
        except ValueError:
            print(f"⚠️  Invalid chat_id in env: {chat_id_str}")
    
    return None


def get_bot_token() -> Optional[str]:
    """Получить токен бота из переменных окружения"""
    return (
        os.getenv("TELEGRAM_MONITOR_BOT_TOKEN") 
        or os.getenv("TELEGRAM_BOT_TOKEN")
    )


async def send_test_message():
    """Отправить тестовое сообщение"""
    # Получить токен и chat_id
    bot_token = get_bot_token()
    chat_id = get_chat_id_from_env()
    
    if not bot_token:
        print("\n❌ Ошибка: TELEGRAM_MONITOR_BOT_TOKEN (или TELEGRAM_BOT_TOKEN) не установлен")
        print("💡 Установи токен в .env файле")
        return
    
    if not chat_id:
        print("\n❌ Ошибка: Chat ID не найден")
        print("💡 Установи TELEGRAM_MONITOR_CHAT_ID в .env файле")
        print("   Или отправь /start боту - он сохранит твой chat_id в БД")
        return
    
    # Тестовое сообщение
    test_message = f"""🧪 <b>Тестовое сообщение от бота</b>

Привет! Это тестовое сообщение для проверки работы Telegram бота.

✅ Бот работает корректно!
📱 Сообщение отправлено успешно
🤖 Система лид-генерации готова к работе

<i>Время отправки:</i> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    # Отправить через Telegram API
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    try:
        print(f"\n📤 Отправляю тестовое сообщение...")
        print(f"   Chat ID: {chat_id}")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": test_message,
                    "parse_mode": "HTML"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print("\n✅ Тестовое сообщение отправлено успешно!")
                    print("💡 Проверь свой Telegram!")
                else:
                    print(f"\n❌ Ошибка Telegram API: {result.get('description', 'Unknown error')}")
            else:
                print(f"\n❌ HTTP ошибка: {response.status_code}")
                print(f"   Ответ: {response.text}")
    
    except Exception as e:
        print(f"\n❌ Ошибка при отправке: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(send_test_message())

