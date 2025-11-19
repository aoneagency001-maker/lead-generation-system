"""
OLX Publisher Service
Публикация объявлений на OLX.kz
"""

from playwright.async_api import async_playwright, Browser, Page
from typing import Optional
import logging
import uuid
from datetime import datetime
import asyncio

from ..models import (
    OLXAd,
    OLXAdCreate,
    OLXAdStatus,
    PublishResult
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class OLXPublisherService:
    """Сервис публикации объявлений на OLX.kz"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.base_url = "https://www.olx.kz"
    
    # ===================================
    # Public Methods
    # ===================================
    
    async def create_ad(
        self,
        ad_data: OLXAdCreate,
        account_id: str
    ) -> PublishResult:
        """
        Создать объявление на OLX
        
        Args:
            ad_data: Данные объявления
            account_id: ID аккаунта OLX
        
        Returns:
            PublishResult: Результат публикации
        """
        try:
            # Получаем аккаунт
            account_result = self.db.table("olx_accounts").select("*").eq("id", account_id).execute()
            
            if not account_result.data:
                return PublishResult(
                    success=False,
                    error="Account not found"
                )
            
            account = account_result.data[0]
            
            # Проверяем статус аккаунта
            if account.get("status") != "active":
                return PublishResult(
                    success=False,
                    error=f"Account is {account.get('status')}, must be active"
                )
            
            # Публикуем через Playwright
            result = await self._publish_via_playwright(ad_data, account)
            
            if result.success:
                # Сохраняем объявление в БД
                ad_id = str(uuid.uuid4())
                ad_db_data = {
                    "id": ad_id,
                    "account_id": account_id,
                    "title": ad_data.title,
                    "description": ad_data.description,
                    "price": ad_data.price,
                    "category": ad_data.category,
                    "city": ad_data.city,
                    "status": OLXAdStatus.PUBLISHED.value,
                    "external_id": result.external_id,
                    "external_url": result.ad_url,
                    "images": ad_data.images,
                    "metadata": ad_data.metadata
                }
                
                self.db.table("olx_ads").insert(ad_db_data).execute()
                
                result.ad_id = ad_id
            
            return result
            
        except Exception as e:
            logger.error(f"Create ad error: {e}", exc_info=True)
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    async def get_ad(self, ad_id: str) -> Optional[OLXAd]:
        """Получить объявление по ID"""
        try:
            result = self.db.table("olx_ads").select("*").eq("id", ad_id).execute()
            
            if not result.data:
                return None
            
            return OLXAd(**result.data[0])
            
        except Exception as e:
            logger.error(f"Get ad error: {e}")
            return None
    
    async def update_ad_status(
        self,
        ad_id: str,
        status: OLXAdStatus
    ) -> bool:
        """Обновить статус объявления"""
        try:
            self.db.table("olx_ads").update({
                "status": status.value
            }).eq("id", ad_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Update ad status error: {e}")
            return False
    
    # ===================================
    # Internal Methods
    # ===================================
    
    async def _publish_via_playwright(
        self,
        ad_data: OLXAdCreate,
        account: dict
    ) -> PublishResult:
        """
        Публикация через Playwright (браузерная автоматизация)
        
        Args:
            ad_data: Данные объявления
            account: Аккаунт OLX
        
        Returns:
            PublishResult: Результат публикации
        """
        try:
            async with async_playwright() as p:
                # Запускаем браузер
                browser = await p.chromium.launch(
                    headless=settings.browser_headless,
                    slow_mo=settings.browser_slow_mo
                )
                
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=account.get("user_agent") or "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                )
                
                # Загружаем cookies если есть
                if account.get("cookies"):
                    await context.add_cookies(account["cookies"])
                
                page = await context.new_page()
                
                # Переходим на страницу добавления объявления
                await page.goto(f"{self.base_url}/post", wait_until="networkidle")
                
                # Проверяем авторизацию
                is_logged_in = await self._check_login(page)
                
                if not is_logged_in:
                    # Нужна авторизация
                    login_success = await self._login(page, account)
                    if not login_success:
                        await browser.close()
                        return PublishResult(
                            success=False,
                            error="Login failed"
                        )
                
                # Заполняем форму объявления
                await self._fill_ad_form(page, ad_data)
                
                # Загружаем изображения
                if ad_data.images:
                    await self._upload_images(page, ad_data.images)
                
                # Публикуем
                await page.click('button[type="submit"]')
                
                # Ждем редиректа на страницу объявления
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)
                
                # Получаем URL опубликованного объявления
                ad_url = page.url
                external_id = self._extract_external_id(ad_url)
                
                # Сохраняем обновленные cookies
                cookies = await context.cookies()
                self.db.table("olx_accounts").update({
                    "cookies": cookies
                }).eq("id", account["id"]).execute()
                
                await browser.close()
                
                logger.info(f"Ad published successfully: {ad_url}")
                
                return PublishResult(
                    success=True,
                    ad_url=ad_url,
                    external_id=external_id
                )
            
        except Exception as e:
            logger.error(f"Publish via Playwright error: {e}", exc_info=True)
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    async def _check_login(self, page: Page) -> bool:
        """Проверить авторизован ли пользователь"""
        try:
            # Ищем элемент, который указывает на авторизацию
            profile_elem = await page.query_selector('[data-testid="user-menu"]')
            return profile_elem is not None
        except:
            return False
    
    async def _login(self, page: Page, account: dict) -> bool:
        """
        Авторизация на OLX.kz
        
        Args:
            page: Playwright Page
            account: Данные аккаунта
        
        Returns:
            bool: True если успешно
        """
        try:
            # Кликаем на кнопку входа
            await page.click('[data-testid="login-button"]')
            await asyncio.sleep(2)
            
            # Заполняем email
            email_input = await page.query_selector('input[type="email"]')
            if not email_input:
                return False
            
            await email_input.fill(account["email"])
            await asyncio.sleep(1)
            
            # Кликаем "Продолжить"
            await page.click('button[type="submit"]')
            await asyncio.sleep(2)
            
            # Заполняем пароль
            password_input = await page.query_selector('input[type="password"]')
            if not password_input:
                return False
            
            await password_input.fill(account["password"])
            await asyncio.sleep(1)
            
            # Кликаем "Войти"
            await page.click('button[type="submit"]')
            await asyncio.sleep(3)
            
            # Проверяем успешность
            return await self._check_login(page)
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    async def _fill_ad_form(self, page: Page, ad_data: OLXAdCreate):
        """Заполнить форму объявления"""
        try:
            # Заголовок
            title_input = await page.query_selector('input[name="title"]')
            if title_input:
                await title_input.fill(ad_data.title)
                await asyncio.sleep(1)
            
            # Описание
            desc_textarea = await page.query_selector('textarea[name="description"]')
            if desc_textarea:
                await desc_textarea.fill(ad_data.description)
                await asyncio.sleep(1)
            
            # Цена
            if ad_data.price:
                price_input = await page.query_selector('input[name="price"]')
                if price_input:
                    await price_input.fill(str(int(ad_data.price)))
                    await asyncio.sleep(1)
            
            # Категория (TODO: выбор из dropdown)
            
            # Город (TODO: выбор из dropdown)
            
            # Дополнительные поля из metadata
            if ad_data.metadata:
                for key, value in ad_data.metadata.items():
                    # TODO: заполнение дополнительных полей
                    pass
            
        except Exception as e:
            logger.error(f"Fill ad form error: {e}")
            raise
    
    async def _upload_images(self, page: Page, images: list[str]):
        """
        Загрузить изображения
        
        Args:
            page: Playwright Page
            images: Список путей к изображениям или URLs
        """
        try:
            # TODO: Реализовать загрузку изображений
            # Нужно:
            # 1. Если URL - скачать локально
            # 2. Найти input[type="file"]
            # 3. Загрузить файлы
            pass
        except Exception as e:
            logger.error(f"Upload images error: {e}")
            raise
    
    def _extract_external_id(self, url: str) -> Optional[str]:
        """Извлечь ID объявления из URL"""
        try:
            if "-ID" in url:
                parts = url.split("-ID")
                if len(parts) > 1:
                    id_part = parts[1].split(".")[0]
                    return id_part
        except:
            pass
        
        return None


