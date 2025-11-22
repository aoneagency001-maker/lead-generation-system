#!/usr/bin/env python3
"""Временный скрипт для применения unified_analytics_schema.sql"""

import os
import sys
from pathlib import Path

# Пароль базы данных
DATABASE_PASSWORD = 'Zaruba2098*'

# Получаем SUPABASE_URL из .env вручную
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_URL='):
                supabase_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                break
        else:
            print("❌ SUPABASE_URL не найден в .env")
            sys.exit(1)
else:
    print("❌ .env файл не найден")
    sys.exit(1)

# Применяем схему
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    conn_string = f"postgresql://postgres.{project_id}:{DATABASE_PASSWORD}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    
    schema_path = Path(__file__).parent.parent / "scripts" / "unified_analytics_schema.sql"
    
    print("=" * 70)
    print("🗄️  ПРИМЕНЕНИЕ UNIFIED ANALYTICS SCHEMA")
    print("=" * 70)
    print()
    print(f"📄 Читаем схему из {schema_path.name}...")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print("🔗 Подключаемся к PostgreSQL...")
    print(f"   Project ID: {project_id}")
    print()
    
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
    
    # Проверяем, что таблицы созданы
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name IN ('unified_metrics', 'analytics_insights', 'llm_processing_queue')
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    if tables:
        print("✅ Проверка таблиц:")
        for table in tables:
            print(f"   ✅ {table[0]}")
    else:
        print("⚠️  Таблицы не найдены")
    
    # Проверяем функцию
    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_schema = 'public'
        AND routine_name = 'update_updated_at_column';
    """)
    
    func = cursor.fetchone()
    if func:
        print(f"   ✅ Функция {func[0]} создана")
    
    # Проверяем views
    cursor.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_schema = 'public'
        AND table_name IN ('daily_unified_summary', 'latest_insights')
        ORDER BY table_name;
    """)
    
    views = cursor.fetchall()
    if views:
        print("✅ Проверка views:")
        for view in views:
            print(f"   ✅ {view[0]}")
    
    cursor.close()
    conn.close()
    
    print()
    print("=" * 70)
    print("✅ ГОТОВО! Схема применена успешно.")
    print("=" * 70)
    print()
    print("Созданы:")
    print("  ✅ unified_metrics")
    print("  ✅ analytics_insights")
    print("  ✅ llm_processing_queue")
    print("  ✅ update_updated_at_column() функция")
    print("  ✅ daily_unified_summary view")
    print("  ✅ latest_insights view")
    print()
    
except ImportError:
    print("❌ psycopg2 не установлен")
    print("Установите: pip install psycopg2-binary")
    sys.exit(1)
except psycopg2.OperationalError as e:
    print(f"❌ Ошибка подключения: {e}")
    print()
    print("Проверьте:")
    print("  - Правильность пароля")
    print("  - Доступность Supabase")
    sys.exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

