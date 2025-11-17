"""
Автоматическое применение schema.sql к Supabase
Использует Supabase REST API для выполнения SQL
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Загружаем .env
load_dotenv()

def apply_schema_via_api():
    """Применить schema.sql через Supabase REST API"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ SUPABASE_URL или SUPABASE_SERVICE_KEY не найдены в .env")
        return False
    
    schema_path = Path(__file__).parent.parent / "core" / "database" / "schema.sql"
    
    if not schema_path.exists():
        print(f"❌ Файл schema.sql не найден: {schema_path}")
        return False
    
    print(f"📄 Читаем schema.sql...")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    # Разбиваем на отдельные команды (по точке с запятой)
    commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]
    
    print(f"📊 Найдено {len(commands)} SQL команд")
    print(f"🔗 Подключаемся к Supabase...")
    
    # Supabase SQL API endpoint
    # Используем PostgREST для выполнения SQL через RPC
    api_url = f"{supabase_url}/rest/v1/rpc"
    
    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json"
    }
    
    print(f"✅ Применяем схему через Supabase API...")
    print()
    print("=" * 70)
    print("⚠️  ВАЖНО: Supabase REST API не поддерживает прямое выполнение DDL SQL")
    print("=" * 70)
    print()
    print("Используйте один из методов:")
    print()
    print("МЕТОД 1 (РЕКОМЕНДУЕТСЯ - 2 минуты):")
    print("1. Откройте: https://supabase.com/dashboard/project/upgowxrbwjgyoqbjcegc")
    print("2. SQL Editor (слева)")
    print("3. New query")
    print("4. Скопируйте содержимое файла:")
    print(f"   {schema_path}")
    print("5. Вставьте и нажмите Run")
    print()
    print("МЕТОД 2 (Через командную строку):")
    print(f"   cat {schema_path} | pbcopy")
    print("   # Затем вставьте в Supabase SQL Editor")
    print()
    print("=" * 70)
    
    return False

def main():
    print("=" * 70)
    print("🗄️  Автоматическое применение schema.sql")
    print("=" * 70)
    print()
    
    apply_schema_via_api()

if __name__ == "__main__":
    main()

