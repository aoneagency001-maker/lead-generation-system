"""
Script для применения схемы БД к Supabase
"""

import os
import sys
from pathlib import Path

# Добавляем root в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.database.supabase_client import get_supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_schema():
    """Применить SQL схему к Supabase"""
    try:
        # Читаем schema.sql
        schema_path = Path(__file__).parent / "schema.sql"
        
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        logger.info("📖 Читаем schema.sql...")
        
        # Получаем клиент Supabase
        supabase = get_supabase_client()
        
        logger.info("🔌 Подключились к Supabase")
        
        # Применяем схему через RPC
        # Примечание: Supabase Python SDK не поддерживает прямой SQL
        # Нужно использовать Supabase SQL Editor или psycopg2
        
        logger.info("⚠️  Для применения схемы используйте один из способов:")
        logger.info("1. Скопируйте schema.sql в Supabase SQL Editor")
        logger.info("2. Используйте psql напрямую:")
        logger.info(f"   psql 'postgresql://...' < {schema_path}")
        
        # Выводим schema для копирования
        print("\n" + "="*50)
        print("SQL SCHEMA (скопируйте в Supabase SQL Editor):")
        print("="*50)
        print(schema_sql)
        print("="*50 + "\n")
        
        # Проверяем существование таблиц
        try:
            result = supabase.table("parser_tasks").select("id").limit(1).execute()
            logger.info("✅ Таблица parser_tasks существует!")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Таблица parser_tasks не найдена: {e}")
            logger.info("Примените SQL схему вручную через Supabase Dashboard")
            return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка при применении схемы: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("🚀 Применение schema для Competitor Parser Module\n")
    success = apply_schema()
    
    if success:
        print("\n✅ Схема успешно применена!")
    else:
        print("\n⚠️  Примените схему вручную")
        print("Откройте Supabase Dashboard → SQL Editor")
        print(f"И выполните содержимое: {Path(__file__).parent / 'schema.sql'}")

