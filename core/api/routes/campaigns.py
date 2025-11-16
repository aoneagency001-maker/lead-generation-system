"""
Campaigns Routes
API для управления кампаниями
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

from core.database.supabase_client import (
    create_record,
    get_record,
    get_records,
    update_record,
    get_campaign_stats
)

router = APIRouter()


class CampaignCreate(BaseModel):
    niche_id: str
    name: str
    platform: str  # olx, kaspi, telegram
    budget: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CampaignResponse(BaseModel):
    id: str
    niche_id: str
    name: str
    platform: str
    status: str
    budget: Optional[float]
    spent: float
    ads_count: int
    leads_count: int
    created_at: datetime


@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate):
    """Создать новую кампанию"""
    try:
        result = create_record("campaigns", campaign.model_dump(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(niche_id: Optional[str] = None, platform: Optional[str] = None):
    """Получить список кампаний"""
    filters = {}
    if niche_id:
        filters["niche_id"] = niche_id
    if platform:
        filters["platform"] = platform
    
    campaigns = get_records("campaigns", filters=filters if filters else None)
    return campaigns


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Получить кампанию с детальной статистикой"""
    campaign = get_record("campaigns", campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    # Добавляем статистику
    stats = get_campaign_stats(campaign_id)
    campaign["stats"] = stats
    
    return campaign


@router.patch("/{campaign_id}/status")
async def update_campaign_status(campaign_id: str, status: str):
    """Обновить статус кампании"""
    valid_statuses = ["draft", "active", "paused", "completed", "failed"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Статус должен быть одним из: {', '.join(valid_statuses)}"
        )
    
    result = update_record("campaigns", campaign_id, {"status": status})
    if not result:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    return result

