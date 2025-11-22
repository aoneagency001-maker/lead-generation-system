"""
Satu Parser Service
Парсинг товаров с Satu.kz через Playwright
"""

from playwright.async_api import async_playwright, Browser, Page
from typing import List, Optional
import logging
import asyncio
import uuid
from datetime import datetime

from ..models import (
    SearchQuery,
    SatuListing,
    SatuParsedData,
    SatuParserTask,
    TaskStatus,
    SatuParserMethod,
    ParserResult
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class SatuParserService:
    """Сервис парсинга Satu.kz"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.base_url = "https://satu.kz"
    
    # ===================================
    # Public Methods
    # ===================================
    
    async def parse_search(
        self,
        query: SearchQuery
    ) -> ParserResult:
        """
        Запустить парсинг поиска
        
        Args:
            query: Параметры поиска
        
        Returns:
            ParserResult: Результат с task_id
        """
        try:
            # Создаем задачу парсинга
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "search_query": query.search_query,
                "category": query.category,
                "parser_method": query.parser_method.value,
                "status": TaskStatus.PENDING.value,
                "progress": 0
            }
            
            self.db.table("satu_parser_tasks").insert(task_data).execute()
            
            # Запускаем парсинг асинхронно (в фоне)
            asyncio.create_task(self._run_parsing_task(task_id, query))
            
            return ParserResult(
                success=True,
                task_id=task_id,
                status=TaskStatus.PENDING,
                items_found=0
            )
            
        except Exception as e:
            logger.error(f"Parse search error: {e}", exc_info=True)
            return ParserResult(
                success=False,
                task_id="",
                status=TaskStatus.FAILED,
                error=str(e)
            )
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Получить статус задачи парсинга"""
        try:
            result = self.db.table("satu_parser_tasks").select("*").eq("id", task_id).execute()
            
            if not result.data:
                return None
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Get task status error: {e}")
            return None
    
    async def get_parse_results(self, result_id: str) -> Optional[SatuParsedData]:
        """Получить результаты парсинга"""
        try:
            result = self.db.table("satu_parsed_data").select("*").eq("id", result_id).execute()
            
            if not result.data:
                return None
            
            data = result.data[0]
            # Преобразуем JSONB data в список SatuListing
            listings = [SatuListing(**item) for item in data.get("data", [])]
            data["data"] = listings
            
            return SatuParsedData(**data)
            
        except Exception as e:
            logger.error(f"Get parse results error: {e}")
            return None
    
    # ===================================
    # Internal Methods
    # ===================================
    
    async def _run_parsing_task(self, task_id: str, query: SearchQuery):
        """Выполнить задачу парсинга"""
        start_time = datetime.now()
        
        try:
            # Обновляем статус на RUNNING
            self.db.table("satu_parser_tasks").update({
                "status": TaskStatus.RUNNING.value,
                "started_at": start_time.isoformat(),
                "progress": 10
            }).eq("id", task_id).execute()
            
            # Парсим через Playwright
            listings = await self._parse_satu_playwright(query.search_query, query.max_pages)
            
            # Сохраняем результаты
            parse_duration = (datetime.now() - start_time).total_seconds()
            
            search_url = f"{self.base_url}/search?query={query.search_query}"
            
            parsed_data = {
                "search_query": query.search_query,
                "search_url": search_url,
                "category": query.category,
                "parser_method": query.parser_method.value,
                "data": [listing.dict() for listing in listings],
                "items_count": len(listings),
                "parse_duration_seconds": parse_duration,
                "pages_parsed": min(query.max_pages, 1),
                "status": "success"
            }
            
            result = self.db.table("satu_parsed_data").insert(parsed_data).execute()
            result_id = result.data[0]["id"] if result.data else None
            
            # Обновляем задачу
            self.db.table("satu_parser_tasks").update({
                "status": TaskStatus.COMPLETED.value,
                "progress": 100,
                "result_id": result_id,
                "completed_at": datetime.now().isoformat()
            }).eq("id", task_id).execute()
            
            logger.info(f"Parsing completed: {len(listings)} items found")
            
        except Exception as e:
            logger.error(f"Parsing task error: {e}", exc_info=True)
            
            # Обновляем задачу с ошибкой
            self.db.table("satu_parser_tasks").update({
                "status": TaskStatus.FAILED.value,
                "error_message": str(e),
                "completed_at": datetime.now().isoformat()
            }).eq("id", task_id).execute()
    
    async def _parse_satu_playwright(
        self,
        search_query: str,
        max_pages: int = 1
    ) -> List[SatuListing]:
        """
        Парсинг Satu.kz через Playwright
        
        Args:
            search_query: Поисковый запрос
            max_pages: Максимальное количество страниц
        
        Returns:
            List[SatuListing]: Список товаров
        """
        listings = []
        
        try:
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(
                    headless=settings.browser_headless,
                    slow_mo=settings.browser_slow_mo
                )
                
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                
                page = await context.new_page()
                
                # Строим URL поиска
                search_url = f"{self.base_url}/search?query={search_query}"
                
                logger.info(f"Navigating to: {search_url}")
                
                # Переходим на страницу
                await page.goto(search_url, wait_until="networkidle")
                
                # Ждем загрузки товаров
                try:
                    await page.wait_for_selector('.product-card', timeout=10000)
                except:
                    logger.warning("No products found")
                    await browser.close()
                    return listings
                
                # Парсим товары
                page_listings = await self._parse_page(page)
                listings.extend(page_listings)
                
                logger.info(f"Found {len(page_listings)} products on page 1")
                
                # TODO: Pagination
                
                await browser.close()
            
        except Exception as e:
            logger.error(f"Playwright parsing error: {e}", exc_info=True)
        
        return listings
    
    async def _parse_page(self, page: Page) -> List[SatuListing]:
        """Парсинг одной страницы результатов"""
        listings = []
        
        try:
            # Получаем все карточки товаров
            cards = await page.query_selector_all('.product-card')
            
            logger.info(f"Found {len(cards)} product cards")
            
            for card in cards:
                try:
                    listing = await self._parse_card(card)
                    if listing:
                        listings.append(listing)
                except Exception as e:
                    logger.warning(f"Failed to parse card: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Parse page error: {e}")
        
        return listings
    
    async def _parse_card(self, card) -> Optional[SatuListing]:
        """Парсинг одной карточки товара"""
        try:
            # Заголовок
            title_elem = await card.query_selector('.product-title, .product-name, h3, h2')
            if not title_elem:
                return None
            
            title = await title_elem.inner_text()
            title = title.strip()
            
            # Цена
            price = None
            price_elem = await card.query_selector('.product-price, .price, [data-test="price"]')
            if price_elem:
                price_text = await price_elem.inner_text()
                price = self._parse_price(price_text)
            
            # Ссылка
            link_elem = await card.query_selector('a')
            if not link_elem:
                return None
            
            link = await link_elem.get_attribute('href')
            if not link:
                return None
            
            if not link.startswith('http'):
                link = self.base_url + link
            
            # External ID из URL
            external_id = self._extract_external_id(link)
            
            # Продавец
            seller_name = None
            seller_elem = await card.query_selector('.seller-name, .company-name')
            if seller_elem:
                seller_name = await seller_elem.inner_text()
                seller_name = seller_name.strip()
            
            # Создаем товар
            listing = SatuListing(
                title=title,
                price=price,
                url=link,
                external_id=external_id,
                seller_name=seller_name
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Parse card error: {e}")
            return None
    
    def _parse_price(self, price_str: str) -> Optional[float]:
        """Парсинг цены из строки"""
        if not price_str:
            return None
        
        try:
            # Убираем все кроме цифр
            price_digits = ''.join(filter(str.isdigit, price_str))
            if price_digits:
                return float(price_digits)
        except:
            pass
        
        return None
    
    def _extract_external_id(self, url: str) -> Optional[str]:
        """Извлечь ID товара из URL"""
        try:
            # URL обычно вида: https://satu.kz/product/product-name-123456
            parts = url.rstrip('/').split('/')
            if parts:
                last_part = parts[-1]
                # Пробуем извлечь числовой ID
                if '-' in last_part:
                    potential_id = last_part.split('-')[-1]
                    if potential_id.isdigit():
                        return potential_id
                elif last_part.isdigit():
                    return last_part
        except:
            pass
        
        return None



