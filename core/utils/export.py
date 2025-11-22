"""
Export Utilities
Утилиты для экспорта данных в различные форматы (CSV, Excel)
"""

import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("⚠️ pandas не установлен. Экспорт в Excel недоступен.")


def export_to_csv(data: List[Dict[str, Any]], filename: Optional[str] = None) -> bytes:
    """
    Экспортировать данные в CSV формат.
    
    Args:
        data: Список словарей с данными
        filename: Имя файла (опционально, для логирования)
    
    Returns:
        bytes: CSV данные в байтах
    """
    if not data:
        return b""
    
    # Получаем все ключи из первого элемента
    fieldnames = list(data[0].keys())
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    # Записываем заголовки
    writer.writeheader()
    
    # Записываем данные
    for row in data:
        # Преобразуем значения в строки
        clean_row = {}
        for key, value in row.items():
            if value is None:
                clean_row[key] = ""
            elif isinstance(value, (dict, list)):
                clean_row[key] = str(value)
            else:
                clean_row[key] = str(value)
        writer.writerow(clean_row)
    
    # Возвращаем в байтах (UTF-8 с BOM для Excel)
    csv_bytes = output.getvalue().encode('utf-8-sig')
    output.close()
    
    logger.info(f"✅ Экспортировано {len(data)} записей в CSV")
    return csv_bytes


def export_to_excel(
    data: List[Dict[str, Any]],
    sheet_name: str = "Data",
    filename: Optional[str] = None
) -> bytes:
    """
    Экспортировать данные в Excel формат (.xlsx).
    
    Args:
        data: Список словарей с данными
        sheet_name: Имя листа
        filename: Имя файла (опционально, для логирования)
    
    Returns:
        bytes: Excel данные в байтах
    
    Raises:
        ImportError: Если pandas не установлен
    """
    if not PANDAS_AVAILABLE:
        raise ImportError(
            "pandas не установлен. Установите: pip install pandas openpyxl"
        )
    
    if not data:
        # Создаем пустой DataFrame
        df = pd.DataFrame()
    else:
        # Создаем DataFrame из данных
        df = pd.DataFrame(data)
    
    # Создаем Excel файл в памяти
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    excel_bytes = output.getvalue()
    output.close()
    
    logger.info(f"✅ Экспортировано {len(data)} записей в Excel")
    return excel_bytes


def export_to_json(data: List[Dict[str, Any]]) -> bytes:
    """
    Экспортировать данные в JSON формат.
    
    Args:
        data: Список словарей с данными
    
    Returns:
        bytes: JSON данные в байтах
    """
    import json
    
    json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    json_bytes = json_str.encode('utf-8')
    
    logger.info(f"✅ Экспортировано {len(data)} записей в JSON")
    return json_bytes


def format_filename(prefix: str, source: str, extension: str = "csv") -> str:
    """
    Сформировать имя файла для экспорта.
    
    Args:
        prefix: Префикс (например, "analytics", "visits")
        source: Источник данных (например, "yandex-metrika", "ga4")
        extension: Расширение файла (csv, xlsx, json)
    
    Returns:
        str: Имя файла
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{source}_{timestamp}.{extension}"

