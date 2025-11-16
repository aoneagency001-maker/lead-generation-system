"""
Leads Routes
API для управления лидами
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from core.database.supabase_client import (
    create_lead,
    get_record,
    get_records,
    update_lead_status,
    get_lead_conversations,
    add_conversation_message
)

router = APIRouter()


class LeadCreate(BaseModel):
    ad_id: Optional[str] = None
    name: Optional[str] = None
    phone: str
    source: str  # whatsapp, telegram, olx, kaspi
    platform_user_id: Optional[str] = None
    budget: Optional[float] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    name: Optional[str]
    phone: str
    source: str
    status: str
    quality_score: Optional[int]
    created_at: datetime


class ConversationMessage(BaseModel):
    message: str
    sender: str  # bot, lead, human
    platform: str


@router.post("/", response_model=LeadResponse)
async def create_lead_endpoint(lead: LeadCreate):
    """Создать нового лида"""
    try:
        result = create_lead(
            ad_id=lead.ad_id or "",
            name=lead.name or "Неизвестно",
            phone=lead.phone,
            source=lead.source,
            platform_user_id=lead.platform_user_id,
            budget=lead.budget,
            notes=lead.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[LeadResponse])
async def list_leads(
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100
):
    """Получить список лидов"""
    filters = {}
    if status:
        filters["status"] = status
    if source:
        filters["source"] = source
    
    leads = get_records("leads", limit=limit, filters=filters if filters else None)
    return leads


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    """Получить лида с историей общения"""
    lead = get_record("leads", lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Лид не найден")
    
    # Добавляем историю общения
    conversations = get_lead_conversations(lead_id)
    lead["conversations"] = conversations
    
    return lead


@router.patch("/{lead_id}/status")
async def update_lead_status_endpoint(lead_id: str, status: str):
    """Обновить статус лида"""
    valid_statuses = ["new", "contacted", "qualified", "hot", "won", "lost", "spam"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Статус должен быть одним из: {', '.join(valid_statuses)}"
        )
    
    result = update_lead_status(lead_id, status)
    return result


@router.post("/{lead_id}/messages")
async def add_message(lead_id: str, message: ConversationMessage):
    """Добавить сообщение в историю общения с лидом"""
    try:
        result = add_conversation_message(
            lead_id=lead_id,
            message=message.message,
            sender=message.sender,
            platform=message.platform
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{lead_id}/messages")
async def get_messages(lead_id: str):
    """Получить все сообщения лида"""
    conversations = get_lead_conversations(lead_id)
    return {"lead_id": lead_id, "messages": conversations}

