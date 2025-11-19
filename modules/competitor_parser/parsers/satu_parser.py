"""
Satu.kz Parser
Специфичный парсер для Satu.kz с оптимизированными селекторами
"""

import logging
import re
from typing import List, Optional
from bs4 import BeautifulSoup

from .universal_parser import UniversalParser
from .configs.satu_config import SATU_CONFIG, SATU_PATTERNS
from ..models import ParsedProduct, ProductAttribute

logger = logging.getLogger(__name__)


class SatuParser(UniversalParser):
    """
    Специфичный парсер для Satu.kz
    Наследует UniversalParser но использует оптимизированные селекторы
    """
    
    def __init__(self):
        """Инициализация парсера Satu.kz"""
        super().__init__(config=SATU_CONFIG)
        self.patterns = SATU_PATTERNS
        logger.info("Satu.kz parser initialized")
    
    async def parse_product_page(self, url: str) -> Optional[ParsedProduct]:
        """
        Парсинг страницы товара с Satu.kz
        Переопределяем для специфичной логики
        
        Args:
            url: URL товара на Satu.kz
        
        Returns:
            ParsedProduct или None
        """
        # Проверяем что это действительно Satu.kz
        if "satu.kz" not in url:
            logger.warning(f"URL не принадлежит Satu.kz: {url}")
            return None
        
        # Используем базовый метод из UniversalParser
        product = await super().parse_product_page(url)
        
        if not product:
            return None
        
        # Дополнительная обработка специфичная для Satu.kz
        product = self._enhance_satu_product(product)
        
        return product
    
    def _enhance_satu_product(self, product: ParsedProduct) -> ParsedProduct:
        """
        Улучшить данные товара специфичной логикой для Satu.kz
        
        Args:
            product: Базовый распарсенный товар
        
        Returns:
            Улучшенный товар
        """
        try:
            # Извлечь ID из URL если не нашли
            if not product.external_id:
                match = re.search(self.patterns['product_id_pattern'], product.source_url)
                if match:
                    product.external_id = match.group(1)
            
            # Нормализовать SKU (убрать префиксы типа "Артикул: ")
            if product.sku:
                product.sku = re.sub(r'^(Артикул|SKU|Код):\s*', '', product.sku, flags=re.IGNORECASE)
            
            # Дополнить breadcrumbs если категория есть но breadcrumbs нет
            if product.category and not product.breadcrumbs:
                product.breadcrumbs = [product.category]
            
            # Нормализовать статус наличия
            if product.stock_status:
                status_lower = product.stock_status.lower()
                if any(word in status_lower for word in ['в наличии', 'available', 'есть']):
                    product.in_stock = True
                    product.stock_status = "В наличии"
                elif any(word in status_lower for word in ['нет', 'unavailable', 'out of stock']):
                    product.in_stock = False
                    product.stock_status = "Нет в наличии"
                elif any(word in status_lower for word in ['под заказ', 'на заказ', 'preorder']):
                    product.in_stock = False
                    product.stock_status = "Под заказ"
            
            logger.info(f"✅ Enhanced Satu.kz product: {product.title}")
        
        except Exception as e:
            logger.warning(f"Failed to enhance Satu product: {e}")
        
        return product
    
    def _extract_via_selectors(self, soup: BeautifulSoup) -> dict:
        """
        Переопределяем извлечение через селекторы для Satu.kz
        Добавляем специфичную логику извлечения атрибутов
        """
        # Получаем базовые данные
        data = super()._extract_via_selectors(soup)
        
        # Дополнительно извлекаем атрибуты по специфичной структуре Satu.kz
        try:
            attributes = []
            
            # Вариант 1: Таблица характеристик
            char_table = soup.select_one('.b-characteristics, .product-attributes, .characteristics-table')
            if char_table:
                # Ищем строки с характеристиками
                rows = char_table.select('tr, .char-row, .attribute-row')
                
                for row in rows:
                    name_elem = row.select_one('.b-char-name, .attr-name, td:first-child, .name')
                    value_elem = row.select_one('.b-char-value, .attr-value, td:last-child, .value')
                    
                    if name_elem and value_elem:
                        name = self.clean_text(name_elem.text)
                        value = self.clean_text(value_elem.text)
                        
                        if name and value:
                            # Извлекаем единицу измерения если есть
                            unit = None
                            unit_match = re.search(r'\(([^)]+)\)$', name)
                            if unit_match:
                                unit = unit_match.group(1)
                                name = name.replace(f'({unit})', '').strip()
                            
                            attributes.append(ProductAttribute(
                                name=name,
                                value=value,
                                unit=unit
                            ))
            
            # Вариант 2: Список DL/DT/DD
            dl_elem = soup.select_one('dl.characteristics, dl.attributes')
            if dl_elem:
                dt_elements = dl_elem.select('dt')
                dd_elements = dl_elem.select('dd')
                
                for dt, dd in zip(dt_elements, dd_elements):
                    name = self.clean_text(dt.text)
                    value = self.clean_text(dd.text)
                    
                    if name and value:
                        attributes.append(ProductAttribute(name=name, value=value))
            
            if attributes:
                data['attributes'] = attributes
                logger.info(f"Extracted {len(attributes)} attributes for Satu.kz")
        
        except Exception as e:
            logger.warning(f"Failed to extract Satu.kz attributes: {e}")
        
        return data
    
    async def _extract_product_links(self, page) -> List[str]:
        """
        Извлечь ссылки на товары со страницы категории Satu.kz
        Переопределяем для специфичных селекторов
        """
        try:
            # Специфичные селекторы для Satu.kz
            links = await page.eval_on_selector_all(
                '.b-product-card a, .product-item a, a[href*="/p"]',
                'elements => elements.map(e => e.href)'
            )
            
            # Фильтруем только ссылки на товары (с /p\d+ в URL)
            product_links = [
                link for link in links
                if re.search(self.patterns['product_url_pattern'], link)
            ]
            
            # Убираем дубликаты
            product_links = list(set(product_links))
            
            logger.info(f"Found {len(product_links)} Satu.kz product links")
            return product_links[:50]  # Лимит 50
            
        except Exception as e:
            logger.warning(f"Failed to extract Satu.kz product links: {e}")
            # Fallback на базовый метод
            return await super()._extract_product_links(page)
    
    def is_satu_product_url(self, url: str) -> bool:
        """
        Проверить, является ли URL ссылкой на товар Satu.kz
        
        Args:
            url: URL для проверки
        
        Returns:
            True если это товар Satu.kz
        """
        return bool(re.search(self.patterns['product_url_pattern'], url))
    
    def is_satu_category_url(self, url: str) -> bool:
        """
        Проверить, является ли URL ссылкой на категорию Satu.kz
        
        Args:
            url: URL для проверки
        
        Returns:
            True если это категория Satu.kz
        """
        return bool(re.search(self.patterns['category_url_pattern'], url))

