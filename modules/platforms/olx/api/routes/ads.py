"""
OLX Ads Routes
API endpoints для работы с объявлениями
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...models import OLXAd, OLXAdCreate, OLXAdStatus, PublishResult
from ...services.publisher_service import OLXPublisherService

router = APIRouter()


def get_publisher_service():
    """Dependency для publisher service"""
    return OLXPublisherService()


@router.post("/", response_model=PublishResult)
async def create_ad(
    ad_data: OLXAdCreate,
    account_id: str,
    publisher_service: OLXPublisherService = Depends(get_publisher_service)
):
    """
    Создать объявление на OLX.kz
    
    - **title**: Заголовок (макс 70 символов)
    - **description**: Описание (макс 9000 символов)
    - **price**: Цена (опционально)
    - **category**: Категория
    - **city**: Город
    - **images**: Список URLs изображений (макс 8 штук)
    - **metadata**: Дополнительные поля (опционально)
    - **account_id**: ID аккаунта OLX
    
    **Возвращает**: Результат публикации с URL объявления
    """
    result = await publisher_service.create_ad(ad_data, account_id)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return result


@router.get("/{ad_id}", response_model=OLXAd)
async def get_ad(
    ad_id: str,
    publisher_service: OLXPublisherService = Depends(get_publisher_service)
):
    """
    Получить объявление по ID
    
    - **ad_id**: UUID объявления
    """
    ad = await publisher_service.get_ad(ad_id)
    
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    return ad


@router.patch("/{ad_id}/status")
async def update_ad_status(
    ad_id: str,
    status: OLXAdStatus,
    publisher_service: OLXPublisherService = Depends(get_publisher_service)
):
    """
    Обновить статус объявления
    
    - **ad_id**: UUID объявления
    - **status**: Новый статус (draft, published, paused, expired, deleted)
    """
    success = await publisher_service.update_ad_status(ad_id, status)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update status")
    
    return {"success": True, "status": status.value}



