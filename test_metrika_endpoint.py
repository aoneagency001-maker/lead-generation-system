#!/usr/bin/env python3
"""
Тестовый скрипт для проверки endpoint Яндекс.Метрики
"""

import os
import sys
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Проверяем токен
token = os.getenv("YANDEX_METRIKA_TOKEN")
if not token:
    print("❌ ОШИБКА: YANDEX_METRIKA_TOKEN не найден в .env")
    print("Добавьте в .env:")
    print("YANDEX_METRIKA_TOKEN=y0__xDRn5OABBir2zsgqO_EnxUezT_ln_UKWnGz2duHNjE8tQQzfA")
    sys.exit(1)

print(f"✅ Токен найден: {token[:20]}...")

# Проверяем импорт
try:
    from library.integrations.yandex_metrika import YandexMetrikaClient
    print("✅ Импорт YandexMetrikaClient успешен")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)

# Проверяем создание клиента
try:
    client = YandexMetrikaClient()
    print("✅ Клиент создан успешно")
except Exception as e:
    print(f"❌ Ошибка создания клиента: {e}")
    sys.exit(1)

# Проверяем импорт роутов
try:
    from core.api.routes import yandex_metrika
    print("✅ Импорт роутов успешен")
    print(f"✅ Роутер создан: {yandex_metrika.router}")
except Exception as e:
    print(f"❌ Ошибка импорта роутов: {e}")
    sys.exit(1)

print("\n✅ Все проверки пройдены! Сервер должен работать.")
print("\nДля запуска сервера:")
print("  uvicorn core.api.main:app --reload")
print("\nДля проверки endpoint:")
print("  curl http://localhost:8000/api/yandex-metrika/counters")

