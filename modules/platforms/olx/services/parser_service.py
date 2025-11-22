"""
OLX Parser Service
Парсинг объявлений с OLX.kz (адаптировано из lerdem/olx-parser)
"""

import httpx
from lxml import etree
from typing import List, Optional
from datetime import datetime
import logging
import uuid
import asyncio

from ..models import (
    SearchQuery,
    OLXListing,
    OLXParsedData,
    OLXParserTask,
    TaskStatus,
    OLXParserMethod,
    ParserResult
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class OLXParserService:
    """Сервис парсинга OLX.kz"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.base_url = "https://www.olx.kz"
    
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
                "city": query.city,
                "category": query.category,
                "parser_method": query.parser_method.value,
                "status": TaskStatus.PENDING.value,
                "progress": 0
            }
            
            self.db.table("olx_parser_tasks").insert(task_data).execute()
            
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
            result = self.db.table("olx_parser_tasks").select("*").eq("id", task_id).execute()
            
            if not result.data:
                return None
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Get task status error: {e}")
            return None
    
    async def get_parse_results(self, result_id: str) -> Optional[OLXParsedData]:
        """Получить результаты парсинга"""
        try:
            result = self.db.table("olx_parsed_data").select("*").eq("id", result_id).execute()
            
            if not result.data:
                return None
            
            data = result.data[0]
            # Преобразуем JSONB data в список OLXListing
            listings = [OLXListing(**item) for item in data.get("data", [])]
            data["data"] = listings
            
            return OLXParsedData(**data)
            
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
            self.db.table("olx_parser_tasks").update({
                "status": TaskStatus.RUNNING.value,
                "started_at": start_time.isoformat(),
                "progress": 10
            }).eq("id", task_id).execute()
            
            # Строим URL для поиска
            search_url = self._build_search_url(query)
            logger.info(f"Parsing URL: {search_url}")
            
            # Парсим
            listings = await self._parse_olx_search(search_url, query.max_pages)
            
            # Сохраняем результаты
            parse_duration = (datetime.now() - start_time).total_seconds()
            
            parsed_data = {
                "search_query": query.search_query,
                "search_url": search_url,
                "city": query.city,
                "category": query.category,
                "parser_method": query.parser_method.value,
                "data": [listing.dict() for listing in listings],
                "items_count": len(listings),
                "parse_duration_seconds": parse_duration,
                "pages_parsed": min(query.max_pages, 1),  # TODO: реальное количество
                "status": "success"
            }
            
            result = self.db.table("olx_parsed_data").insert(parsed_data).execute()
            result_id = result.data[0]["id"] if result.data else None
            
            # Обновляем задачу
            self.db.table("olx_parser_tasks").update({
                "status": TaskStatus.COMPLETED.value,
                "progress": 100,
                "result_id": result_id,
                "completed_at": datetime.now().isoformat()
            }).eq("id", task_id).execute()
            
            logger.info(f"Parsing completed: {len(listings)} items found")
            
        except Exception as e:
            logger.error(f"Parsing task error: {e}", exc_info=True)
            
            # Обновляем задачу с ошибкой
            self.db.table("olx_parser_tasks").update({
                "status": TaskStatus.FAILED.value,
                "error_message": str(e),
                "completed_at": datetime.now().isoformat()
            }).eq("id", task_id).execute()
    
    def _build_search_url(self, query: SearchQuery) -> str:
        """Построить URL для поиска"""
        # Базовый URL
        url = f"{self.base_url}/list"
        
        # Добавляем параметры
        params = []
        
        if query.search_query:
            params.append(f"q={query.search_query}")
        
        if query.city and query.city != "almaty":
            # TODO: mapping городов на пути OLX
            pass
        
        if query.category:
            # TODO: категории
            pass
        
        # Сортировка по дате (новые первыми)
        params.append("search[order]=created_at:desc")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    async def _parse_olx_search(
        self,
        search_url: str,
        max_pages: int = 1
    ) -> List[OLXListing]:
        """
        Парсинг поиска OLX.kz (адаптировано из lerdem/olx-parser)
        
        Args:
            search_url: URL поиска
            max_pages: Максимальное количество страниц
        
        Returns:
            List[OLXListing]: Список объявлений
        """
        listings = []
        
        try:
            async with httpx.AsyncClient(timeout=settings.parser_timeout) as client:
                # Получаем HTML
                response = await client.get(
                    search_url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch: {response.status_code}")
                    return listings
                
                html = response.text
                dom = etree.HTML(html)
                
                # Проверяем пустой поиск
                is_empty = len(dom.xpath('//div[contains(@class, "emptynew")]')) == 1
                if is_empty:
                    logger.info("Empty search results")
                    return listings
                
                # Парсим объявления (используем несколько вариантов селекторов)
                # Вариант 1: новый дизайн OLX
                items = dom.xpath('.//div[contains(@data-cy, "l-card")]')
                
                if not items:
                    # Вариант 2: старый дизайн
                    items = dom.xpath('.//div[@class="offer-wrapper"]')
                
                logger.info(f"Found {len(items)} items")
                
                for item in items:
                    try:
                        listing = self._parse_listing_item(item)
                        if listing:
                            listings.append(listing)
                    except Exception as e:
                        logger.warning(f"Failed to parse item: {e}")
                        continue
                
                # TODO: Pagination - парсинг следующих страниц
                
        except Exception as e:
            logger.error(f"Parse OLX search error: {e}", exc_info=True)
        
        return listings
    
    def _parse_listing_item(self, item) -> Optional[OLXListing]:
        """
        Парсинг одного объявления
        
        Args:
            item: lxml element
        
        Returns:
            Optional[OLXListing]: Объявление или None
        """
        try:
            # Вариант 1: новый дизайн
            title_xpath = './/h6/text()'
            price_xpath = './/p[@data-testid="ad-price"]/text()'
            link_xpath = './/a/@href'
            
            title_candidates = item.xpath(title_xpath)
            
            if not title_candidates:
                # Вариант 2: старый дизайн
                title_xpath = './/strong/text()'
                price_xpath = './/p[@class="price"]/strong/text()'
                title_candidates = item.xpath(title_xpath)
            
            if not title_candidates:
                return None
            
            title = title_candidates[0].strip()
            
            # Цена
            price_candidates = item.xpath(price_xpath)
            price_str = price_candidates[0].strip() if price_candidates else None
            price = self._parse_price(price_str)
            
            # Ссылка
            link_candidates = item.xpath(link_xpath)
            if not link_candidates:
                return None
            
            link = link_candidates[0]
            if not link.startswith("http"):
                link = self.base_url + link
            
            # External ID из URL
            external_id = self._extract_external_id(link)
            
            # Создаем объявление
            listing = OLXListing(
                title=title,
                price=price,
                url=link,
                external_id=external_id
            )
            
            return listing
            
        except Exception as e:
            logger.error(f"Parse listing item error: {e}")
            return None
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
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
        """Извлечь ID объявления из URL"""
        try:
            # URL обычно вида: https://www.olx.kz/d/obyavlenie/...-ID123456.html
            if "-ID" in url:
                parts = url.split("-ID")
                if len(parts) > 1:
                    id_part = parts[1].split(".")[0]
                    return id_part
        except:
            pass
        
        return None



