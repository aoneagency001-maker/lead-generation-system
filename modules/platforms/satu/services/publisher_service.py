"""
Satu Publisher Service
Публикация товаров на Satu.kz
"""

import httpx
from typing import Optional
import logging
import uuid
from datetime import datetime

from ..models import (
    SatuProduct,
    SatuProductCreate,
    SatuProductStatus,
    PublishResult
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class SatuPublisherService:
    """Сервис публикации товаров на Satu.kz"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.api_url = "https://api.satu.kz/api/v2"
    
    # ===================================
    # Public Methods
    # ===================================
    
    async def create_product(
        self,
        product_data: SatuProductCreate,
        account_id: str
    ) -> PublishResult:
        """
        Создать товар на Satu.kz через API
        
        Args:
            product_data: Данные товара
            account_id: ID аккаунта Satu
        
        Returns:
            PublishResult: Результат публикации
        """
        try:
            # Получаем аккаунт
            account_result = self.db.table("satu_accounts").select("*").eq("id", account_id).execute()
            
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
            
            # Публикуем через API
            result = await self._publish_via_api(product_data, account)
            
            if result.success:
                # Сохраняем товар в БД
                product_id = str(uuid.uuid4())
                product_db_data = {
                    "id": product_id,
                    "account_id": account_id,
                    "title": product_data.title,
                    "description": product_data.description,
                    "price": product_data.price,
                    "quantity": product_data.quantity,
                    "category": product_data.category,
                    "status": SatuProductStatus.PUBLISHED.value,
                    "external_id": result.external_id,
                    "external_url": result.ad_url,
                    "images": product_data.images,
                    "metadata": product_data.metadata
                }
                
                self.db.table("satu_products").insert(product_db_data).execute()
                
                result.ad_id = product_id
            
            return result
            
        except Exception as e:
            logger.error(f"Create product error: {e}", exc_info=True)
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    async def get_product(self, product_id: str) -> Optional[SatuProduct]:
        """Получить товар по ID"""
        try:
            result = self.db.table("satu_products").select("*").eq("id", product_id).execute()
            
            if not result.data:
                return None
            
            return SatuProduct(**result.data[0])
            
        except Exception as e:
            logger.error(f"Get product error: {e}")
            return None
    
    async def update_product_status(
        self,
        product_id: str,
        status: SatuProductStatus
    ) -> bool:
        """Обновить статус товара"""
        try:
            self.db.table("satu_products").update({
                "status": status.value
            }).eq("id", product_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Update product status error: {e}")
            return False
    
    async def update_quantity(
        self,
        product_id: str,
        quantity: int
    ) -> bool:
        """Обновить количество товара"""
        try:
            self.db.table("satu_products").update({
                "quantity": quantity
            }).eq("id", product_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Update quantity error: {e}")
            return False
    
    # ===================================
    # Internal Methods
    # ===================================
    
    async def _publish_via_api(
        self,
        product_data: SatuProductCreate,
        account: dict
    ) -> PublishResult:
        """
        Публикация через Satu.kz API
        
        Args:
            product_data: Данные товара
            account: Аккаунт Satu
        
        Returns:
            PublishResult: Результат публикации
        """
        try:
            api_token = account.get("api_token")
            company_id = account.get("company_id")
            
            if not api_token:
                return PublishResult(
                    success=False,
                    error="API token not found"
                )
            
            # Подготавливаем данные для API
            api_data = {
                "name": product_data.title,
                "description": product_data.description,
                "price": product_data.price,
                "quantity": product_data.quantity or 1,
                "company_id": company_id,
                # TODO: добавить category_id, images и другие поля
            }
            
            if product_data.metadata:
                api_data.update(product_data.metadata)
            
            # Отправляем POST запрос
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/products",
                    json=api_data,
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code not in [200, 201]:
                    logger.error(f"API error: {response.status_code} - {response.text}")
                    return PublishResult(
                        success=False,
                        error=f"API error: {response.status_code}"
                    )
                
                result_data = response.json()
                
                # Извлекаем ID и URL
                external_id = str(result_data.get("id", ""))
                ad_url = result_data.get("url") or f"https://satu.kz/product/{external_id}"
                
                logger.info(f"Product published successfully: {ad_url}")
                
                return PublishResult(
                    success=True,
                    ad_url=ad_url,
                    external_id=external_id
                )
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}", exc_info=True)
            return PublishResult(
                success=False,
                error=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Publish via API error: {e}", exc_info=True)
            return PublishResult(
                success=False,
                error=str(e)
            )
    
    async def _upload_images_api(
        self,
        images: list[str],
        api_token: str
    ) -> list[str]:
        """
        Загрузить изображения через API
        
        Args:
            images: Список путей к изображениям или URLs
            api_token: API токен
        
        Returns:
            list[str]: Список ID загруженных изображений
        """
        uploaded_ids = []
        
        try:
            # TODO: Реализовать загрузку изображений
            # Нужно:
            # 1. Если URL - скачать локально
            # 2. Отправить POST /api/v2/images с multipart/form-data
            # 3. Получить ID изображений
            pass
        except Exception as e:
            logger.error(f"Upload images error: {e}")
        
        return uploaded_ids


