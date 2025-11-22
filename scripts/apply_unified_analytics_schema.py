#!/usr/bin/env python3
"""
Применить unified_analytics_schema.sql к Supabase

Создает таблицы:
- unified_metrics
- analytics_insights
- llm_processing_queue

Использование:
    python scripts/apply_unified_analytics_schema.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Загружаем .env
load_dotenv()


def get_connection_string():
    """Получить connection string для PostgreSQL из Supabase URL"""
    supabase_url = os.getenv("SUPABASE_URL")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL не найден в .env")
    
    # Извлекаем project ID из URL
    # https://upgowxrbwjgyoqbjcegc.supabase.co -> upgowxrbwjgyoqbjcegc
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    print(f"📊 Project ID: {project_id}")
    print(f"🔗 Supabase URL: {supabase_url}")
    print()
    
    # Пробуем получить пароль из переменной окружения
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not db_password:
        print("⚠️  SUPABASE_DB_PASSWORD не найден в .env")
        print()
        print("Для прямого подключения к PostgreSQL нужен Database Password.")
        print("Получить можно в Supabase Dashboard:")
        print("  Settings → Database → Connection string → Direct connection")
        print()
        print("Или используйте Supabase Dashboard SQL Editor:")
        print(f"  https://supabase.com/dashboard/project/{project_id}/sql/new")
        print()
        return None
    
    # Connection string для Supabase PostgreSQL
    # Используем pooler для лучшей производительности
    conn_string = f"postgresql://postgres.{project_id}:{db_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    return conn_string


def apply_schema_via_psycopg2(conn_string: str, schema_path: Path) -> bool:
    """Применить schema.sql через psycopg2"""
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("❌ psycopg2 не установлен. Установите: pip install psycopg2-binary")
        return False
    
    print(f"📄 Читаем схему из {schema_path}...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print("🔗 Подключаемся к PostgreSQL...")
    try:
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Подключение установлено")
        print("📊 Применяем схему...")
        print()
        
        # Выполняем SQL
        cursor.execute(schema_sql)
        
        print("✅ Схема успешно применена!")
        print()
        print("Созданы таблицы:")
        print("  ✅ unified_metrics")
        print("  ✅ analytics_insights")
        print("  ✅ llm_processing_queue")
        print()
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка при применении схемы: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def print_manual_instructions(schema_path: Path):
    """Вывести инструкции для ручного применения схемы"""
    supabase_url = os.getenv("SUPABASE_URL")
    if supabase_url:
        project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
        sql_editor_url = f"https://supabase.com/dashboard/project/{project_id}/sql/new"
    else:
        sql_editor_url = "https://supabase.com/dashboard"
    
    print("=" * 70)
    print("📋 ИНСТРУКЦИИ ДЛЯ РУЧНОГО ПРИМЕНЕНИЯ СХЕМЫ")
    print("=" * 70)
    print()
    print("1. Откройте Supabase Dashboard:")
    print(f"   {sql_editor_url}")
    print()
    print("2. Перейдите в SQL Editor (левое меню → SQL Editor)")
    print()
    print("3. Скопируйте содержимое файла:")
    print(f"   {schema_path}")
    print()
    print("4. Вставьте SQL в редактор и нажмите 'Run'")
    print()
    print("5. Проверьте, что таблицы созданы:")
    print("   - unified_metrics")
    print("   - analytics_insights")
    print("   - llm_processing_queue")
    print()
    print("=" * 70)
    print()
    print("📄 СОДЕРЖИМОЕ SQL СХЕМЫ:")
    print("=" * 70)
    print()
    with open(schema_path, 'r', encoding='utf-8') as f:
        print(f.read())
    print()
    print("=" * 70)


def main():
    """Главная функция"""
    print("=" * 70)
    print("🗄️  ПРИМЕНЕНИЕ UNIFIED ANALYTICS SCHEMA")
    print("=" * 70)
    print()
    
    schema_path = project_root / "scripts" / "unified_analytics_schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Файл схемы не найден: {schema_path}")
        sys.exit(1)
    
    # Пробуем получить connection string
    conn_string = get_connection_string()
    
    if conn_string:
        # Пробуем применить через psycopg2
        print("🔄 Пробуем применить схему через прямое подключение к PostgreSQL...")
        print()
        
        if apply_schema_via_psycopg2(conn_string, schema_path):
            print("✅ Готово! Схема применена успешно.")
            return
        else:
            print()
            print("⚠️  Не удалось применить через прямое подключение.")
            print("Используйте ручной метод ниже.")
            print()
    
    # Если не получилось, выводим инструкции
    print_manual_instructions(schema_path)


if __name__ == "__main__":
    main()

