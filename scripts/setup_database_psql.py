"""
Setup Database using psycopg2 (direct PostgreSQL connection)
Применяет schema.sql к Supabase PostgreSQL
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

# Загружаем .env
load_dotenv()

def get_connection_string():
    """Получить connection string для PostgreSQL из Supabase URL"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url:
        raise ValueError("SUPABASE_URL not found in .env")
    
    # Извлекаем project ID из URL
    # https://upgowxrbwjgyoqbjcegc.supabase.co -> upgowxrbwjgyoqbjcegc
    project_id = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    # Supabase PostgreSQL connection string
    # Формат: postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres
    # Для service_role используем service_key как пароль
    
    print(f"📊 Project ID: {project_id}")
    print(f"🔗 Supabase URL: {supabase_url}")
    print()
    print("⚠️  ВАЖНО: Для прямого подключения к PostgreSQL нужен database password")
    print("Получить можно в Supabase Dashboard → Settings → Database → Connection string")
    print()
    
    db_password = input("Введите Database Password (или Enter для использования через Supabase Dashboard): ").strip()
    
    if not db_password:
        return None
    
    conn_string = f"postgresql://postgres.{project_id}:{db_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
    return conn_string

def apply_schema_via_psycopg2(conn_string):
    """Применить schema.sql через psycopg2"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 не установлен")
        print("Установите: pip install psycopg2-binary")
        return False
    
    schema_path = Path(__file__).parent.parent / "core" / "database" / "schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Файл schema.sql не найден: {schema_path}")
        return False
    
    print(f"📄 Читаем schema.sql...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    print(f"🔗 Подключаемся к PostgreSQL...")
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        print(f"✅ Подключение установлено")
        print(f"📊 Применяем схему...")
        
        # Выполняем SQL
        cursor.execute(schema_sql)
        conn.commit()
        
        print(f"✅ Схема успешно применена!")
        
        # Проверяем что таблицы созданы
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Созданные таблицы:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при применении схемы: {e}")
        return False

def apply_schema_via_dashboard():
    """Инструкция по применению через Dashboard"""
    schema_path = Path(__file__).parent.parent / "core" / "database" / "schema.sql"
    
    print("=" * 70)
    print("📋 ИНСТРУКЦИЯ: Применение схемы через Supabase Dashboard")
    print("=" * 70)
    print()
    print("1. Откройте https://supabase.com/dashboard")
    print("2. Выберите ваш проект")
    print("3. В левом меню: SQL Editor")
    print("4. Нажмите 'New query'")
    print("5. Скопируйте содержимое файла:")
    print(f"   {schema_path}")
    print()
    print("6. Вставьте в SQL Editor и нажмите 'Run' (или Ctrl+Enter)")
    print()
    print("=" * 70)
    print()
    
    # Показываем путь к файлу для копирования
    print(f"💡 Быстрая команда для копирования в буфер (macOS):")
    print(f"   cat {schema_path} | pbcopy")
    print()

def main():
    print("=" * 70)
    print("🗄️  Setup Database - Lead Generation System")
    print("=" * 70)
    print()
    
    # Проверяем что .env существует
    if not Path(".env").exists():
        print("❌ Файл .env не найден!")
        print("Создайте .env файл с SUPABASE_URL и SUPABASE_SERVICE_KEY")
        return
    
    print("Выберите метод применения схемы:")
    print()
    print("1. Через psycopg2 (прямое подключение к PostgreSQL)")
    print("2. Через Supabase Dashboard (SQL Editor) - РЕКОМЕНДУЕТСЯ")
    print()
    
    choice = input("Ваш выбор (1 или 2): ").strip()
    
    if choice == "1":
        conn_string = get_connection_string()
        if conn_string:
            success = apply_schema_via_psycopg2(conn_string)
            if success:
                print()
                print("🎉 База данных успешно настроена!")
                print("Теперь можно запустить: python scripts/test_connection.py")
        else:
            print()
            print("⚠️  Переключаемся на метод через Dashboard...")
            apply_schema_via_dashboard()
    else:
        apply_schema_via_dashboard()

if __name__ == "__main__":
    main()

