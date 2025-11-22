#!/usr/bin/env python3
"""
Скрипт для применения схемы базы данных Visitor Tracking
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.database.supabase_client import get_admin_client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_schema():
    """Применить схему базы данных для Visitor Tracking"""
    
    schema_file = root_dir / "core" / "database" / "schema_visitor_tracking.sql"
    
    if not schema_file.exists():
        logger.error(f"❌ Schema file not found: {schema_file}")
        return False
    
    try:
        # Читаем SQL файл
        with open(schema_file, "r", encoding="utf-8") as f:
            sql = f.read()
        
        logger.info("📄 Reading schema file...")
        
        # Получаем admin клиент
        client = get_admin_client()
        
        # Выполняем SQL
        logger.info("🔧 Applying schema to Supabase...")
        result = client.rpc("exec_sql", {"sql": sql}).execute()
        
        logger.info("✅ Schema applied successfully!")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error applying schema: {e}")
        logger.info("\n💡 Alternative: Apply schema manually via Supabase Dashboard:")
        logger.info(f"   1. Open Supabase Dashboard → SQL Editor")
        logger.info(f"   2. Copy contents of: {schema_file}")
        logger.info(f"   3. Paste and execute")
        return False


if __name__ == "__main__":
    print("🚀 Applying Visitor Tracking schema...")
    success = apply_schema()
    sys.exit(0 if success else 1)

