#!/usr/bin/env python3
"""
Скрипт для применения схемы таблицы telegram_bot_subscribers

Usage:
    python scripts/apply_telegram_bots_schema.py
"""

import sys
from pathlib import Path

# Добавить корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.database.supabase_client import get_supabase_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_schema():
    """Применить схему таблицы telegram_bot_subscribers"""
    try:
        # Читаем SQL файл
        schema_file = root_dir / "core" / "database" / "schema_telegram_bots.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        
        logger.info("📄 Reading schema file...")
        logger.info(f"📁 File: {schema_file}")
        
        # Подключаемся к Supabase
        supabase = get_supabase_client()
        
        logger.info("🔌 Connecting to Supabase...")
        
        # Выполняем SQL через Supabase RPC или напрямую
        # Supabase Python client не поддерживает прямой SQL, используем REST API
        from supabase import create_client, Client
        import os
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL and SUPABASE_KEY must be set in .env")
            return False
        
        # Создаем клиент с service role key для выполнения SQL
        client: Client = create_client(supabase_url, supabase_key)
        
        # Разбиваем SQL на отдельные команды (упрощенная версия)
        # В реальности лучше использовать psycopg2 или asyncpg для прямого выполнения
        logger.warning("⚠️  Supabase Python client doesn't support direct SQL execution.")
        logger.warning("⚠️  Please apply schema manually through Supabase Dashboard:")
        logger.warning(f"   1. Go to SQL Editor in Supabase Dashboard")
        logger.warning(f"   2. Copy contents of: {schema_file}")
        logger.warning(f"   3. Paste and execute")
        
        # Альтернатива: можно использовать Supabase REST API для выполнения SQL
        # Но это требует специальных прав
        
        logger.info("✅ Schema file ready for manual application")
        logger.info(f"📄 File location: {schema_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Error applying schema: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 Applying Telegram Bots Schema")
    print("="*60 + "\n")
    
    success = apply_schema()
    
    if success:
        print("\n✅ Schema file is ready!")
        print("\n📝 Next steps:")
        print("   1. Open Supabase Dashboard → SQL Editor")
        print("   2. Copy contents of: core/database/schema_telegram_bots.sql")
        print("   3. Paste and execute")
        print("\n   Or use psql directly:")
        print("   psql $DATABASE_URL -f core/database/schema_telegram_bots.sql")
    else:
        print("\n❌ Failed to prepare schema")
        sys.exit(1)


