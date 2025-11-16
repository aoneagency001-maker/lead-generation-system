"""
Niches Routes
API для управления нишами
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from core.database.supabase_client import (
    get_supabase_client,
    create_record,
    get_record,
    get_records,
    update_record,
    delete_record
)

router = APIRouter()


# Pydantic модели
class NicheCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    cpl_target: Optional[float] = None
    roi_target: Optional[float] = None


class NicheUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    cpl_target: Optional[float] = None
    roi_target: Optional[float] = None


class NicheResponse(BaseModel):
    id: str
    name: str
    category: Optional[str]
    status: str
    cpl_target: Optional[float]
    roi_target: Optional[float]
    created_at: datetime


@router.post("/", response_model=NicheResponse)
async def create_niche(niche: NicheCreate):
    """
    Создать новую нишу
    
    Args:
        niche: Данные ниши
        
    Returns:
        NicheResponse: Созданная ниша
    """
    try:
        result = create_record("niches", niche.model_dump(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[NicheResponse])
async def list_niches(status: Optional[str] = None, limit: int = 100):
    """
    Получить список ниш
    
    Args:
        status: Фильтр по статусу (research, active, paused, completed, rejected)
        limit: Количество записей
        
    Returns:
        List[NicheResponse]: Список ниш
    """
    try:
        filters = {"status": status} if status else None
        niches = get_records("niches", limit=limit, filters=filters)
        return niches
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{niche_id}", response_model=NicheResponse)
async def get_niche(niche_id: str):
    """
    Получить нишу по ID
    
    Args:
        niche_id: UUID ниши
        
    Returns:
        NicheResponse: Ниша
    """
    niche = get_record("niches", niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Ниша не найдена")
    return niche


@router.patch("/{niche_id}", response_model=NicheResponse)
async def update_niche(niche_id: str, niche: NicheUpdate):
    """
    Обновить нишу
    
    Args:
        niche_id: UUID ниши
        niche: Данные для обновления
        
    Returns:
        NicheResponse: Обновленная ниша
    """
    try:
        result = update_record(
            "niches", 
            niche_id, 
            niche.model_dump(exclude_none=True)
        )
        if not result:
            raise HTTPException(status_code=404, detail="Ниша не найдена")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{niche_id}")
async def delete_niche(niche_id: str):
    """
    Удалить нишу
    
    Args:
        niche_id: UUID ниши
        
    Returns:
        dict: Сообщение об успехе
    """
    success = delete_record("niches", niche_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ниша не найдена")
    return {"message": "Ниша удалена", "id": niche_id}

