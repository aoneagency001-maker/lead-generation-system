"""
Satu Products Routes
API endpoints для работы с товарами
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...models import SatuProduct, SatuProductCreate, SatuProductStatus, PublishResult
from ...services.publisher_service import SatuPublisherService

router = APIRouter()


def get_publisher_service():
    """Dependency для publisher service"""
    return SatuPublisherService()


@router.post("/", response_model=PublishResult)
async def create_product(
    product_data: SatuProductCreate,
    account_id: str,
    publisher_service: SatuPublisherService = Depends(get_publisher_service)
):
    """
    Создать товар на Satu.kz через API
    
    - **title**: Название товара (макс 255 символов)
    - **description**: Описание
    - **price**: Цена в тенге
    - **quantity**: Количество (по умолчанию: 1)
    - **category**: Категория
    - **images**: Список URLs изображений
    - **metadata**: Дополнительные поля (опционально)
    - **account_id**: ID аккаунта Satu
    
    **Возвращает**: Результат публикации с URL товара
    """
    result = await publisher_service.create_product(product_data, account_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result


@router.get("/{product_id}", response_model=SatuProduct)
async def get_product(
    product_id: str,
    publisher_service: SatuPublisherService = Depends(get_publisher_service)
):
    """
    Получить товар по ID
    
    - **product_id**: UUID товара
    """
    product = await publisher_service.get_product(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@router.patch("/{product_id}/status")
async def update_product_status(
    product_id: str,
    status: SatuProductStatus,
    publisher_service: SatuPublisherService = Depends(get_publisher_service)
):
    """
    Обновить статус товара
    
    - **product_id**: UUID товара
    - **status**: Новый статус (draft, published, paused, out_of_stock, deleted)
    """
    success = await publisher_service.update_product_status(product_id, status)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update status")
    
    return {"success": True, "status": status.value}


@router.patch("/{product_id}/quantity")
async def update_quantity(
    product_id: str,
    quantity: int,
    publisher_service: SatuPublisherService = Depends(get_publisher_service)
):
    """
    Обновить количество товара
    
    - **product_id**: UUID товара
    - **quantity**: Новое количество
    """
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity must be >= 0")
    
    success = await publisher_service.update_quantity(product_id, quantity)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update quantity")
    
    return {"success": True, "quantity": quantity}


