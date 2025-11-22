#!/usr/bin/env python3
"""
Скрипт для проверки переменных окружения для Data Intake провайдеров
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env файл
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def check_yandex_metrika():
    """Проверка переменных для Yandex.Metrika"""
    print("\n🔍 Проверка Yandex.Metrika:")
    print("=" * 50)
    
    token = os.getenv("YANDEX_METRIKA_TOKEN")
    counter_id = os.getenv("YANDEX_METRIKA_COUNTER_ID")
    
    if token:
        print(f"✅ YANDEX_METRIKA_TOKEN: установлен ({len(token)} символов)")
    else:
        print("❌ YANDEX_METRIKA_TOKEN: НЕ установлен")
        print("   📝 Инструкция: https://oauth.yandex.ru/")
    
    if counter_id:
        print(f"✅ YANDEX_METRIKA_COUNTER_ID: {counter_id}")
    else:
        print("❌ YANDEX_METRIKA_COUNTER_ID: НЕ установлен")
        print("   📝 Как найти: https://metrika.yandex.ru/ → Настройки → Код счетчика")
    
    return bool(token and counter_id)

def check_google_analytics():
    """Проверка переменных для Google Analytics 4"""
    print("\n🔍 Проверка Google Analytics 4:")
    print("=" * 50)
    
    credentials_path = os.getenv("GOOGLE_ANALYTICS_CREDENTIALS_PATH")
    property_id = os.getenv("GOOGLE_ANALYTICS_PROPERTY_ID")
    
    if credentials_path:
        creds_file = Path(__file__).parent.parent / credentials_path
        if creds_file.exists():
            print(f"✅ GOOGLE_ANALYTICS_CREDENTIALS_PATH: {credentials_path} (файл существует)")
        else:
            print(f"❌ GOOGLE_ANALYTICS_CREDENTIALS_PATH: {credentials_path} (файл НЕ найден)")
            print(f"   📁 Ожидаемый путь: {creds_file.absolute()}")
    else:
        print("❌ GOOGLE_ANALYTICS_CREDENTIALS_PATH: НЕ установлен")
        print("   📝 Инструкция: https://console.cloud.google.com/ → Service Accounts")
    
    if property_id:
        print(f"✅ GOOGLE_ANALYTICS_PROPERTY_ID: {property_id}")
    else:
        print("❌ GOOGLE_ANALYTICS_PROPERTY_ID: НЕ установлен")
        print("   📝 Как найти: https://analytics.google.com/ → Admin → Property Settings")
    
    return bool(credentials_path and property_id and Path(credentials_path).exists())

def main():
    print("\n" + "=" * 60)
    print("🔐 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ДЛЯ DATA INTAKE")
    print("=" * 60)
    
    yandex_ok = check_yandex_metrika()
    ga4_ok = check_google_analytics()
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ СТАТУС:")
    print("=" * 60)
    
    if yandex_ok:
        print("✅ Yandex.Metrika: готов к использованию")
    else:
        print("❌ Yandex.Metrika: требует настройки")
    
    if ga4_ok:
        print("✅ Google Analytics 4: готов к использованию")
    else:
        print("❌ Google Analytics 4: требует настройки")
    
    if yandex_ok and ga4_ok:
        print("\n🎉 Все провайдеры настроены!")
    elif yandex_ok or ga4_ok:
        print("\n⚠️  Частично настроено. Некоторые провайдеры недоступны.")
    else:
        print("\n❌ Ни один провайдер не настроен.")
        print("\n📖 Инструкции:")
        print("   - Yandex.Metrika: MD/v0.3/22.11.2025_00:01_ИНСТРУКЦИЯ_ПО_НАСТРОЙКЕ_ЯНДЕКС_МЕТРИКИ.md")
        print("   - Google Analytics: MD/v0.3/22.11.2025_18:05_ОТЧЕТ_О_ГОТОВНОСТИ_МОДУЛЯ_GA4.md")
        print("   - Общий план: MD/v0.3/23.11.2025_03:00_ПЛАН_НАСТРОЙКИ_ТЕСТОВЫХ_ДАННЫХ_АВТОРИЗАЦИИ.md")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

