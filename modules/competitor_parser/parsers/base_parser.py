"""
Base Parser Class
Базовый класс для всех парсеров
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import asyncio
import re

from ..models import ParsedProduct, ParserConfig, ProductPrice

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Базовый класс парсера"""
    
    def __init__(self, config: ParserConfig):
        """
        Инициализация парсера
        
        Args:
            config: Конфигурация парсера
        """
        self.config = config
        self.products: List[ParsedProduct] = []
        self.base_url = config.base_url
    
    @abstractmethod
    async def parse_product_page(self, url: str) -> Optional[ParsedProduct]:
        """
        Парсинг одной страницы товара
        
        Args:
            url: URL страницы товара
        
        Returns:
            ParsedProduct или None если не удалось распарсить
        """
        pass
    
    @abstractmethod
    async def parse_category_page(self, url: str, max_pages: int = 1) -> List[ParsedProduct]:
        """
        Парсинг страницы категории (списка товаров)
        
        Args:
            url: URL категории
            max_pages: Максимальное количество страниц для парсинга
        
        Returns:
            List[ParsedProduct]: Список товаров
        """
        pass
    
    # ===================================
    # Helper Methods
    # ===================================
    
    def extract_domain(self, url: str) -> str:
        """
        Извлечь домен из URL
        
        Args:
            url: URL
        
        Returns:
            Домен (например: satu.kz)
        """
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    
    async def rate_limit_wait(self):
        """Подождать согласно rate limit"""
        await asyncio.sleep(self.config.rate_limit)
    
    def clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Очистка текста от лишних пробелов и переносов
        
        Args:
            text: Текст для очистки
        
        Returns:
            Очищенный текст или None
        """
        if not text:
            return None
        
        # Убираем лишние пробелы и переносы
        text = " ".join(text.split())
        return text.strip() if text else None
    
    def extract_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Извлечь цену из строки
        
        Args:
            price_str: Строка с ценой (например: "1 250 ₸", "$100.50")
        
        Returns:
            Цена в виде float или None
        """
        if not price_str:
            return None
        
        try:
            # Убираем все кроме цифр, точки и запятой
            price_clean = re.sub(r'[^\d.,]', '', price_str)
            
            # Заменяем запятую на точку
            price_clean = price_clean.replace(',', '.')
            
            # Убираем лишние точки (оставляем только последнюю как разделитель)
            parts = price_clean.split('.')
            if len(parts) > 2:
                # Если несколько точек, считаем последнюю разделителем копеек
                price_clean = ''.join(parts[:-1]) + '.' + parts[-1]
            
            if price_clean:
                return float(price_clean)
        except Exception as e:
            logger.warning(f"Failed to parse price '{price_str}': {e}")
        
        return None
    
    def extract_external_id(self, url: str) -> Optional[str]:
        """
        Извлечь ID товара из URL
        
        Args:
            url: URL товара
        
        Returns:
            ID или None
        """
        try:
            # Пытаемся найти число в конце URL
            # Примеры:
            # /product-12345.html -> 12345
            # /item/12345/ -> 12345
            # /p/name-id-12345 -> 12345
            
            matches = re.findall(r'[-_/](\d+)(?:[.-]html?|/|$)', url)
            if matches:
                return matches[-1]  # Берем последнее найденное число
            
            # Если не нашли, пытаемся найти любое длинное число
            matches = re.findall(r'\b(\d{5,})\b', url)
            if matches:
                return matches[-1]
        
        except Exception as e:
            logger.warning(f"Failed to extract ID from URL '{url}': {e}")
        
        return None
    
    def is_category_page(self, url: str) -> bool:
        """
        Определить, это страница категории или товара
        
        Args:
            url: URL
        
        Returns:
            True если это категория
        """
        # Простая эвристика
        category_indicators = [
            '/catalog', '/category', '/products', '/list',
            '/c/', '/cat/', '/shop/', '/store/'
        ]
        
        return any(indicator in url.lower() for indicator in category_indicators)
    
    def normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        Нормализовать URL (добавить домен если нужно)
        
        Args:
            url: URL
            base_url: Базовый URL для относительных ссылок
        
        Returns:
            Полный URL
        """
        if not url:
            return ""
        
        # Если URL уже полный
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Если URL относительный
        base = base_url or self.base_url
        
        # Убираем trailing slash у base
        base = base.rstrip('/')
        
        # Добавляем leading slash если нет
        if not url.startswith('/'):
            url = '/' + url
        
        return base + url
    
    def calculate_discount_percent(self, old_price: float, new_price: float) -> float:
        """
        Рассчитать процент скидки
        
        Args:
            old_price: Старая цена
            new_price: Новая цена
        
        Returns:
            Процент скидки
        """
        if old_price <= 0 or new_price >= old_price:
            return 0.0
        
        return round(((old_price - new_price) / old_price) * 100, 2)
    
    def create_product_price(
        self,
        amount: float,
        old_amount: Optional[float] = None,
        currency: str = "KZT"
    ) -> ProductPrice:
        """
        Создать объект ProductPrice
        
        Args:
            amount: Текущая цена
            old_amount: Старая цена (если есть скидка)
            currency: Валюта
        
        Returns:
            ProductPrice
        """
        price = ProductPrice(amount=amount, currency=currency)
        
        if old_amount and old_amount > amount:
            price.old_price = old_amount
            price.discount_percent = self.calculate_discount_percent(old_amount, amount)
        
        return price
    
    def extract_breadcrumbs_from_text(self, breadcrumb_text: str) -> List[str]:
        """
        Извлечь breadcrumbs из текста
        
        Args:
            breadcrumb_text: Текст breadcrumbs (например: "Home > Category > Subcategory")
        
        Returns:
            Список категорий
        """
        if not breadcrumb_text:
            return []
        
        # Разделители для breadcrumbs
        separators = [' > ', ' / ', ' → ', ' » ', ' | ']
        
        for sep in separators:
            if sep in breadcrumb_text:
                parts = [p.strip() for p in breadcrumb_text.split(sep)]
                # Убираем "Home", "Главная" и пустые элементы
                return [p for p in parts if p and p.lower() not in ['home', 'главная', 'домой']]
        
        # Если разделителя нет, возвращаем весь текст как один элемент
        return [breadcrumb_text.strip()]

