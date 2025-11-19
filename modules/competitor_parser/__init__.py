"""
Competitor Parser Module
Модуль парсинга сайтов конкурентов для извлечения товаров и SEO данных
"""

__version__ = "0.1.0"
__author__ = "Lead Generation System"

# Экспорт основных классов
from .models import (
    ParsedProduct,
    ParserTask,
    ParserConfig,
    SEOData,
    ProductPrice,
    ProductImage,
    ProductAttribute
)

__all__ = [
    "ParsedProduct",
    "ParserTask",
    "ParserConfig",
    "SEOData",
    "ProductPrice",
    "ProductImage",
    "ProductAttribute"
]

