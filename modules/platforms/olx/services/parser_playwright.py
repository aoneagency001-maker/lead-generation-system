"""
OLX Playwright Parser
Парсинг через браузерную автоматизацию (более надежный метод)
"""

from playwright.async_api import async_playwright, Browser, Page
from typing import List, Optional
import logging
import asyncio

from ..models import OLXListing
from ..api.config import settings

logger = logging.getLogger(__name__)


class OLXPlaywrightParser:
    """Парсер OLX через Playwright"""
    
    def __init__(self):
        self.base_url = "https://www.olx.kz"
        self.browser: Optional[Browser] = None
    
    async def parse_search(
        self,
        search_query: str,
        city: str = "almaty",
        max_pages: int = 1
    ) -> List[OLXListing]:
        """
        Парсинг поиска через Playwright
        
        Args:
            search_query: Поисковый запрос
            city: Город
            max_pages: Максимальное количество страниц
        
        Returns:
            List[OLXListing]: Список объявлений
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
                search_url = f"{self.base_url}/list?q={search_query}"
                
                logger.info(f"Navigating to: {search_url}")
                
                # Переходим на страницу
                await page.goto(search_url, wait_until="networkidle")
                
                # Ждем загрузки объявлений
                try:
                    await page.wait_for_selector('[data-cy="l-card"]', timeout=10000)
                except:
                    logger.warning("No listings found with data-cy selector")
                    # Пробуем альтернативный селектор
                    try:
                        await page.wait_for_selector('.offer-wrapper', timeout=5000)
                    except:
                        logger.error("No listings found")
                        await browser.close()
                        return listings
                
                # Парсим объявления
                page_listings = await self._parse_page(page)
                listings.extend(page_listings)
                
                logger.info(f"Found {len(page_listings)} listings on page 1")
                
                # TODO: Pagination - переход на следующие страницы
                # for page_num in range(2, max_pages + 1):
                #     has_next = await self._go_to_next_page(page)
                #     if not has_next:
                #         break
                #     page_listings = await self._parse_page(page)
                #     listings.extend(page_listings)
                
                await browser.close()
            
        except Exception as e:
            logger.error(f"Playwright parsing error: {e}", exc_info=True)
        
        return listings
    
    async def _parse_page(self, page: Page) -> List[OLXListing]:
        """
        Парсинг одной страницы результатов
        
        Args:
            page: Playwright Page
        
        Returns:
            List[OLXListing]: Список объявлений
        """
        listings = []
        
        try:
            # Получаем все карточки объявлений
            cards = await page.query_selector_all('[data-cy="l-card"]')
            
            if not cards:
                # Пробуем старый дизайн
                cards = await page.query_selector_all('.offer-wrapper')
            
            logger.info(f"Found {len(cards)} cards")
            
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
    
    async def _parse_card(self, card) -> Optional[OLXListing]:
        """
        Парсинг одной карточки объявления
        
        Args:
            card: Playwright ElementHandle
        
        Returns:
            Optional[OLXListing]: Объявление или None
        """
        try:
            # Заголовок
            title_elem = await card.query_selector('h6')
            if not title_elem:
                title_elem = await card.query_selector('strong')
            
            if not title_elem:
                return None
            
            title = await title_elem.inner_text()
            title = title.strip()
            
            # Цена
            price = None
            price_elem = await card.query_selector('[data-testid="ad-price"]')
            if not price_elem:
                price_elem = await card.query_selector('.price strong')
            
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
            
            # External ID
            external_id = self._extract_external_id(link)
            
            # Город (опционально)
            city = None
            city_elem = await card.query_selector('[data-testid="location-date"]')
            if city_elem:
                city_text = await city_elem.inner_text()
                city = city_text.split('-')[0].strip() if '-' in city_text else None
            
            # Создаем объявление
            listing = OLXListing(
                title=title,
                price=price,
                url=link,
                external_id=external_id,
                city=city
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
    
    async def _go_to_next_page(self, page: Page) -> bool:
        """
        Переход на следующую страницу
        
        Args:
            page: Playwright Page
        
        Returns:
            bool: True если успешно перешли
        """
        try:
            # Ищем кнопку "Следующая страница"
            next_button = await page.query_selector('a[data-cy="pagination-forward"]')
            
            if not next_button:
                logger.info("No next page button found")
                return False
            
            # Кликаем
            await next_button.click()
            
            # Ждем загрузки
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Дополнительная задержка
            
            return True
            
        except Exception as e:
            logger.error(f"Go to next page error: {e}")
            return False



