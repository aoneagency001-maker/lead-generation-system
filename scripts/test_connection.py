"""
Test Connection Script
Проверка подключения ко всем сервисам
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
from core.database.supabase_client import get_supabase_client
from core.api.config import settings, is_telegram_configured, is_whatsapp_configured

# Загружаем переменные окружения
load_dotenv()


def test_supabase():
    """Тест подключения к Supabase"""
    print("\n📊 Тестирование Supabase...")
    try:
        supabase = get_supabase_client()
        # Простой запрос
        result = supabase.table("niches").select("id").limit(1).execute()
        print("   ✅ Supabase подключен успешно")
        return True
    except Exception as e:
        print(f"   ❌ Ошибка Supabase: {e}")
        return False


def test_telegram():
    """Тест настройки Telegram"""
    print("\n🤖 Проверка Telegram...")
    if is_telegram_configured():
        print(f"   ✅ Telegram настроен (токен: {settings.telegram_bot_token[:10]}...)")
        return True
    else:
        print("   ⚠️  Telegram не настроен (TELEGRAM_BOT_TOKEN не задан)")
        return False


def test_whatsapp():
    """Тест настройки WhatsApp"""
    print("\n💬 Проверка WhatsApp...")
    if is_whatsapp_configured():
        print(f"   ✅ WhatsApp настроен (URL: {settings.whatsapp_api_url})")
        return True
    else:
        print("   ⚠️  WhatsApp не настроен")
        return False


def test_redis():
    """Тест подключения к Redis"""
    print("\n🔴 Проверка Redis...")
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("   ✅ Redis подключен")
        return True
    except ImportError:
        print("   ⚠️  Redis клиент не установлен (pip install redis)")
        return False
    except Exception as e:
        print(f"   ❌ Redis недоступен: {e}")
        print("   💡 Запустите: docker-compose up -d redis")
        return False


def test_n8n():
    """Тест доступности n8n"""
    print("\n🔄 Проверка n8n...")
    try:
        import requests
        response = requests.get(f"{settings.n8n_url}/healthz", timeout=5)
        if response.status_code == 200:
            print("   ✅ n8n доступен")
            return True
        else:
            print(f"   ❌ n8n вернул статус {response.status_code}")
            return False
    except ImportError:
        print("   ⚠️  requests не установлен (pip install requests)")
        return False
    except Exception as e:
        print(f"   ❌ n8n недоступен: {e}")
        print("   💡 Запустите: docker-compose up -d n8n")
        return False


def main():
    """Запустить все тесты"""
    print("=" * 50)
    print("🔍 Проверка подключений Lead Generation System")
    print("=" * 50)
    
    results = {
        "Supabase": test_supabase(),
        "Telegram": test_telegram(),
        "WhatsApp": test_whatsapp(),
        "Redis": test_redis(),
        "n8n": test_n8n()
    }
    
    print("\n" + "=" * 50)
    print("📊 Результаты:")
    print("=" * 50)
    
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "=" * 50)
    print(f"Успешно: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Все сервисы работают!")
    elif results["Supabase"]:
        print("\n⚠️  Основные сервисы работают, но есть предупреждения")
        print("   Система может работать с ограниченным функционалом")
    else:
        print("\n❌ Критические ошибки!")
        print("   Система не может работать без Supabase")
        print("\n💡 Следующие шаги:")
        print("   1. Проверьте .env файл")
        print("   2. Создайте проект на https://supabase.com")
        print("   3. Запустите: docker-compose up -d")
        sys.exit(1)


if __name__ == "__main__":
    main()

