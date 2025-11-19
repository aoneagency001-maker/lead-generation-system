"""
Universal Parser
Универсальный парсер с авто-детекцией структуры через Playwright
"""

import logging
import json
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup
import asyncio

from .base_parser import BaseParser
from ..models import (
    ParsedProduct,
    ParserConfig,
    ProductPrice,
    ProductImage,
    ProductAttribute,
    SEOData,
    ParserType
)
from ..config import parser_settings

logger = logging.getLogger(__name__)


class UniversalParser(BaseParser):
    """
    Универсальный парсер с использованием Playwright
    Авто-детекция структуры через schema.org, Open Graph, мета-теги
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Инициализация универсального парсера
        
        Args:
            config: Конфигурация парсера (если None, используется default)
        """
        if config is None:
            config = self._get_default_config()
        
        super().__init__(config)
        self.browser: Optional[Browser] = None
        self.context = None
        self.playwright = None
    
    async def __aenter__(self):
        """Контекстный менеджер: вход"""
        self.playwright = await async_playwright().start()
        
        # Запускаем браузер с anti-detect
        self.browser = await self.playwright.chromium.launch(
            headless=parser_settings.playwright_headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu"
            ]
        )
        
        # Выбираем случайный User-Agent
        user_agent = parser_settings.user_agents[0]
        
        # Создаем контекст с кастомными headers
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            extra_http_headers=self.config.custom_headers,
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU"
        )
        
        logger.info("Playwright browser started")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Playwright browser stopped")
    
    # ===================================
    # Main Parsing Methods
    # ===================================
    
    async def parse_product_page(self, url: str) -> Optional[ParsedProduct]:
        """
        Парсинг одной страницы товара
        
        Args:
            url: URL страницы товара
        
        Returns:
            ParsedProduct или None
        """
        try:
            page = await self.context.new_page()
            
            # Переходим на страницу
            logger.info(f"Loading page: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Ждем загрузки контента (если указан селектор)
            if self.config.wait_for_selector:
                try:
                    await page.wait_for_selector(
                        self.config.wait_for_selector,
                        timeout=10000
                    )
                except Exception as e:
                    logger.warning(f"Wait for selector failed: {e}")
            else:
                # Ждем немного для загрузки JS
                await asyncio.sleep(2)
            
            # Получаем HTML
            html = await page.content()
            soup = BeautifulSoup(html, 'lxml')
            
            # Извлекаем данные
            product = await self._extract_product_data(soup, url, page)
            
            await page.close()
            
            # Rate limiting
            await self.rate_limit_wait()
            
            if product:
                logger.info(f"✅ Product parsed: {product.title}")
            else:
                logger.warning(f"⚠️ Failed to parse product from {url}")
            
            return product
            
        except Exception as e:
            logger.error(f"Failed to parse product page {url}: {e}", exc_info=True)
            return None
    
    async def parse_category_page(self, url: str, max_pages: int = 1) -> List[ParsedProduct]:
        """
        Парсинг категории товаров
        
        Args:
            url: URL категории
            max_pages: Максимальное количество страниц
        
        Returns:
            Список товаров
        """
        products = []
        
        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            for page_num in range(max_pages):
                logger.info(f"Parsing category page {page_num + 1}/{max_pages}")
                
                # Получаем ссылки на товары
                product_links = await self._extract_product_links(page)
                
                logger.info(f"Found {len(product_links)} products on page {page_num + 1}")
                
                # Парсим каждый товар
                for product_url in product_links[:10]:  # Лимит 10 на страницу для MVP
                    product = await self.parse_product_page(product_url)
                    if product:
                        products.append(product)
                
                # Переход на следующую страницу (если есть)
                if page_num < max_pages - 1:
                    has_next = await self._go_to_next_page(page)
                    if not has_next:
                        logger.info("No more pages")
                        break
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Failed to parse category {url}: {e}", exc_info=True)
        
        logger.info(f"Total products parsed: {len(products)}")
        return products
    
    # ===================================
    # Data Extraction Methods
    # ===================================
    
    async def _extract_product_data(
        self,
        soup: BeautifulSoup,
        url: str,
        page: Page
    ) -> Optional[ParsedProduct]:
        """Извлечь данные товара из HTML"""
        try:
            # 1. Пытаемся извлечь через schema.org (JSON-LD)
            schema_data = self._extract_schema_org(soup)
            
            # 2. Пытаемся извлечь через Open Graph
            og_data = self._extract_open_graph(soup)
            
            # 3. Извлекаем через селекторы
            selector_data = self._extract_via_selectors(soup)
            
            # 4. Объединяем данные (приоритет: schema > og > selectors)
            merged_data = self._merge_data(schema_data, og_data, selector_data)
            
            # Название обязательно
            title = merged_data.get('title')
            if not title:
                logger.warning(f"No title found for {url}")
                return None
            
            # Создаем SEO данные
            seo_data = self._extract_seo_data(soup)
            
            # Создаем объект товара
            product = ParsedProduct(
                title=title,
                description=merged_data.get('description'),
                short_description=merged_data.get('short_description'),
                sku=merged_data.get('sku'),
                external_id=self.extract_external_id(url),
                price=merged_data.get('price'),
                category=merged_data.get('category'),
                breadcrumbs=merged_data.get('breadcrumbs', []),
                brand=merged_data.get('brand'),
                attributes=merged_data.get('attributes', []),
                images=merged_data.get('images', []),
                rating=merged_data.get('rating'),
                reviews_count=merged_data.get('reviews_count'),
                stock_status=merged_data.get('stock_status'),
                in_stock=merged_data.get('in_stock'),
                seo_data=seo_data,
                source_url=url,
                source_site=self.extract_domain(url),
                parser_type=ParserType.UNIVERSAL,
                raw_html=str(soup)[:5000] if parser_settings.save_raw_html else None
            )
            
            return product
            
        except Exception as e:
            logger.error(f"Failed to extract product data: {e}", exc_info=True)
            return None
    
    def _extract_schema_org(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлечь данные через schema.org (JSON-LD)"""
        data = {}
        
        try:
            # Ищем script с JSON-LD
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    
                    # Может быть массив
                    if isinstance(json_data, list):
                        json_data = next(
                            (item for item in json_data if item.get('@type') == 'Product'),
                            json_data[0] if json_data else {}
                        )
                    
                    # Проверяем тип
                    if json_data.get('@type') == 'Product':
                        data['title'] = json_data.get('name')
                        data['description'] = json_data.get('description')
                        data['sku'] = json_data.get('sku')
                        data['brand'] = json_data.get('brand', {}).get('name')
                        
                        # Цена
                        offers = json_data.get('offers', {})
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        
                        price_value = offers.get('price')
                        if price_value:
                            try:
                                data['price'] = ProductPrice(
                                    amount=float(price_value),
                                    currency=offers.get('priceCurrency', 'KZT')
                                )
                            except:
                                pass
                        
                        # Изображения
                        images = json_data.get('image', [])
                        if isinstance(images, str):
                            images = [images]
                        
                        data['images'] = [
                            ProductImage(url=img, is_primary=(i == 0), order=i)
                            for i, img in enumerate(images)
                        ]
                        
                        # Рейтинг
                        rating_data = json_data.get('aggregateRating', {})
                        if rating_data:
                            data['rating'] = rating_data.get('ratingValue')
                            data['reviews_count'] = rating_data.get('reviewCount')
                        
                        logger.info("✅ Extracted data via schema.org")
                        break
                
                except json.JSONDecodeError:
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to extract schema.org: {e}")
        
        return data
    
    def _extract_open_graph(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлечь данные через Open Graph meta tags"""
        data = {}
        
        try:
            # og:title
            og_title = soup.find('meta', property='og:title')
            if og_title:
                data['title'] = og_title.get('content')
            
            # og:description
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                data['description'] = og_desc.get('content')
            
            # og:image
            og_image = soup.find('meta', property='og:image')
            if og_image:
                data['images'] = [ProductImage(
                    url=og_image.get('content'),
                    is_primary=True,
                    order=0
                )]
            
            # og:price:amount
            og_price = soup.find('meta', property='og:price:amount')
            og_currency = soup.find('meta', property='og:price:currency')
            if og_price:
                try:
                    data['price'] = ProductPrice(
                        amount=float(og_price.get('content')),
                        currency=og_currency.get('content') if og_currency else 'KZT'
                    )
                except:
                    pass
            
            if data:
                logger.info("✅ Extracted data via Open Graph")
        
        except Exception as e:
            logger.warning(f"Failed to extract Open Graph: {e}")
        
        return data
    
    def _extract_via_selectors(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлечь данные через CSS селекторы"""
        data = {}
        selectors = self.config.selectors
        
        try:
            # Title
            if selectors.get('title'):
                title_elem = soup.select_one(selectors['title'])
                if title_elem:
                    data['title'] = self.clean_text(title_elem.text)
            
            # SKU
            if selectors.get('sku'):
                sku_elem = soup.select_one(selectors['sku'])
                if sku_elem:
                    data['sku'] = self.clean_text(sku_elem.text)
            
            # Description
            if selectors.get('description'):
                desc_elem = soup.select_one(selectors['description'])
                if desc_elem:
                    data['description'] = self.clean_text(desc_elem.text)
            
            # Price
            if selectors.get('price'):
                price_elem = soup.select_one(selectors['price'])
                if price_elem:
                    price_amount = self.extract_price(price_elem.text)
                    if price_amount:
                        data['price'] = ProductPrice(amount=price_amount)
                        
                        # Old price
                        if selectors.get('old_price'):
                            old_price_elem = soup.select_one(selectors['old_price'])
                            if old_price_elem:
                                old_price = self.extract_price(old_price_elem.text)
                                if old_price and old_price > price_amount:
                                    data['price'].old_price = old_price
                                    data['price'].calculate_discount()
            
            # Images
            if selectors.get('images'):
                img_elements = soup.select(selectors['images'])
                images = []
                for idx, img_elem in enumerate(img_elements[:10]):  # Максимум 10 изображений
                    img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                    alt_text = img_elem.get('alt')
                    
                    if img_url:
                        # Нормализуем URL
                        img_url = self.normalize_url(img_url)
                        images.append(ProductImage(
                            url=img_url,
                            alt_text=alt_text,
                            is_primary=(idx == 0),
                            order=idx
                        ))
                
                if images:
                    data['images'] = images
            
            # Category
            if selectors.get('category'):
                cat_elem = soup.select_one(selectors['category'])
                if cat_elem:
                    data['category'] = self.clean_text(cat_elem.text)
            
            # Brand
            if selectors.get('brand'):
                brand_elem = soup.select_one(selectors['brand'])
                if brand_elem:
                    data['brand'] = self.clean_text(brand_elem.text)
            
            # Breadcrumbs
            breadcrumb_elem = soup.select_one('.breadcrumb, .breadcrumbs, [itemtype*="BreadcrumbList"]')
            if breadcrumb_elem:
                breadcrumb_text = self.clean_text(breadcrumb_elem.text)
                if breadcrumb_text:
                    data['breadcrumbs'] = self.extract_breadcrumbs_from_text(breadcrumb_text)
            
            if data:
                logger.info("✅ Extracted data via selectors")
        
        except Exception as e:
            logger.warning(f"Failed to extract via selectors: {e}")
        
        return data
    
    def _extract_seo_data(self, soup: BeautifulSoup) -> SEOData:
        """Извлечь SEO метаданные"""
        seo_data = SEOData()
        
        try:
            # Meta title
            title_tag = soup.find('title')
            if title_tag:
                seo_data.meta_title = self.clean_text(title_tag.text)
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                seo_data.meta_description = meta_desc.get('content')
            
            # Meta keywords
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            if meta_keywords:
                keywords_str = meta_keywords.get('content', '')
                seo_data.meta_keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            
            # Open Graph
            og_title = soup.find('meta', property='og:title')
            if og_title:
                seo_data.og_title = og_title.get('content')
            
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                seo_data.og_description = og_desc.get('content')
            
            og_image = soup.find('meta', property='og:image')
            if og_image:
                seo_data.og_image = og_image.get('content')
            
            og_type = soup.find('meta', property='og:type')
            if og_type:
                seo_data.og_type = og_type.get('content')
            
            # Headings
            h1_tags = soup.find_all('h1')
            seo_data.h1 = [self.clean_text(h.text) for h in h1_tags if h.text.strip()][:5]
            
            h2_tags = soup.find_all('h2')
            seo_data.h2 = [self.clean_text(h.text) for h in h2_tags if h.text.strip()][:10]
            
            h3_tags = soup.find_all('h3')
            seo_data.h3 = [self.clean_text(h.text) for h in h3_tags if h.text.strip()][:10]
            
            # Canonical
            canonical = soup.find('link', rel='canonical')
            if canonical:
                seo_data.canonical_url = canonical.get('href')
            
            # Language
            html_tag = soup.find('html')
            if html_tag:
                seo_data.lang = html_tag.get('lang')
            
            # Robots
            meta_robots = soup.find('meta', attrs={'name': 'robots'})
            if meta_robots:
                seo_data.robots = meta_robots.get('content')
        
        except Exception as e:
            logger.warning(f"Failed to extract SEO data: {e}")
        
        return seo_data
    
    def _merge_data(self, *data_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """Объединить данные из разных источников (приоритет: первый > последний)"""
        merged = {}
        
        for data_dict in reversed(data_dicts):
            for key, value in data_dict.items():
                if value is not None:
                    merged[key] = value
        
        return merged
    
    async def _extract_product_links(self, page: Page) -> List[str]:
        """Извлечь ссылки на товары со страницы категории"""
        try:
            # Универсальные селекторы для ссылок на товары
            links = await page.eval_on_selector_all(
                'a[href*="/product"], a[href*="/item"], a[href*="/p/"], a.product-link, .product-card a, .item-card a',
                'elements => elements.map(e => e.href)'
            )
            
            # Убираем дубликаты и фильтруем
            unique_links = list(set(links))
            
            # Фильтруем только ссылки на товары (не категории)
            product_links = [
                link for link in unique_links
                if not self.is_category_page(link)
            ]
            
            return product_links[:50]  # Максимум 50 товаров
            
        except Exception as e:
            logger.warning(f"Failed to extract product links: {e}")
            return []
    
    async def _go_to_next_page(self, page: Page) -> bool:
        """Перейти на следующую страницу пагинации"""
        try:
            # Ищем кнопку "Следующая страница"
            next_selectors = [
                'a.next', 'a[rel="next"]', 'button.pagination-next',
                '[aria-label="Next"]', '.pagination a:last-child',
                'a:contains("Следующая")', 'a:contains("Next")'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = await page.query_selector(selector)
                    if next_button:
                        await next_button.click()
                        await page.wait_for_load_state("domcontentloaded")
                        await self.rate_limit_wait()
                        logger.info("Navigated to next page")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to go to next page: {e}")
            return False
    
    # ===================================
    # Static Methods
    # ===================================
    
    @staticmethod
    def _get_default_config() -> ParserConfig:
        """Получить конфигурацию по умолчанию"""
        return ParserConfig(
            site_name="universal",
            base_url="",
            parser_type=ParserType.UNIVERSAL,
            use_playwright=True,
            selectors={
                "title": "h1, .product-title, .item-title, [itemprop='name']",
                "sku": "[itemprop='sku'], .sku, .article, .product-code",
                "description": "[itemprop='description'], .description, .product-description, .item-description",
                "price": "[itemprop='price'], .price, .product-price, .current-price",
                "old_price": ".old-price, .price-old, .regular-price",
                "images": "img[itemprop='image'], .product-image img, .gallery img, .item-image img",
                "category": "[itemprop='category'], .breadcrumb li:last-child, .category",
                "brand": "[itemprop='brand'], .brand, .manufacturer"
            },
            rate_limit=parser_settings.default_rate_limit,
            timeout=parser_settings.default_timeout
        )

