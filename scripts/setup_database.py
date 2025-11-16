"""
Setup Database Script
Скрипт для создания таблиц в Supabase
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from dotenv import load_dotenv
from core.database.supabase_client import get_admin_client

# Загружаем переменные окружения
load_dotenv()


def setup_database():
    """Создать таблицы в Supabase"""
    
    print("🗄️  Настройка базы данных Supabase...")
    
    try:
        # Читаем SQL схему
        schema_path = root_dir / "core" / "database" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_schema = f.read()
        
        # Получаем клиент с правами администратора
        supabase = get_admin_client()
        
        print("📊 Применяем схему базы данных...")
        
        # Supabase Python SDK не поддерживает прямое выполнение SQL
        # Нужно либо использовать REST API, либо применить схему через UI
        print("\n⚠️  Внимание!")
        print("Supabase Python SDK не поддерживает выполнение произвольного SQL.")
        print("\nВам нужно выполнить один из вариантов:")
        print("\n1. Через Supabase Dashboard:")
        print("   - Откройте https://supabase.com/dashboard")
        print("   - Выберите ваш проект")
        print("   - Перейдите в SQL Editor")
        print(f"   - Скопируйте содержимое файла: {schema_path}")
        print("   - Вставьте и выполните SQL")
        
        print("\n2. Через psql (если есть доступ):")
        print("   psql -h <your-host> -U postgres -d postgres -f core/database/schema.sql")
        
        print("\n3. Через Python с psycopg2:")
        print("   pip install psycopg2-binary")
        print("   python scripts/setup_database_psql.py")
        
        # Проверяем подключение
        print("\n✅ Проверка подключения к Supabase...")
        result = supabase.table("niches").select("id").limit(1).execute()
        print("✅ Подключение успешно! Таблицы должны быть созданы через UI.")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nУбедитесь, что:")
        print("1. Создан проект на https://supabase.com")
        print("2. В .env заполнены SUPABASE_URL и SUPABASE_SERVICE_KEY")
        print("3. SQL схема применена через Supabase Dashboard (SQL Editor)")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()

