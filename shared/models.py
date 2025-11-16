"""
Pydantic Models
Общие модели данных для всей системы
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ===================================
# Enums
# ===================================

class NicheStatus(str, Enum):
    """Статусы ниши"""
    RESEARCH = "research"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    REJECTED = "rejected"


class CampaignStatus(str, Enum):
    """Статусы кампании"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class LeadStatus(str, Enum):
    """Статусы лида"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    HOT = "hot"
    WON = "won"
    LOST = "lost"
    SPAM = "spam"


class Platform(str, Enum):
    """Платформы"""
    OLX = "olx"
    KASPI = "kaspi"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"


# ===================================
# Base Models
# ===================================

class BaseDBModel(BaseModel):
    """Базовая модель с общими полями"""
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================================
# Niche Models
# ===================================

class Niche(BaseDBModel):
    """Модель ниши"""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    status: NicheStatus = NicheStatus.RESEARCH
    
    cpl_target: Optional[float] = Field(None, description="Целевой CPL в тенге")
    roi_target: Optional[float] = Field(None, description="Целевой ROI в %")
    
    market_size: Optional[int] = None
    competition_level: Optional[str] = None
    avg_price: Optional[float] = None
    seasonality: Optional[Dict] = None


# ===================================
# Campaign Models
# ===================================

class Campaign(BaseDBModel):
    """Модель кампании"""
    niche_id: str
    name: str
    platform: Platform
    status: CampaignStatus = CampaignStatus.DRAFT
    
    budget: Optional[float] = None
    spent: float = 0
    
    ads_count: int = 0
    leads_count: int = 0
    conversions_count: int = 0
    
    config: Optional[Dict] = Field(None, description="Конфигурация кампании")


# ===================================
# Ad Models
# ===================================

class Ad(BaseDBModel):
    """Модель объявления"""
    campaign_id: str
    platform: Platform
    
    external_id: Optional[str] = Field(None, description="ID на внешней платформе")
    url: Optional[str] = None
    
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    images: Optional[List[str]] = Field(default_factory=list)
    
    status: str = "draft"
    
    views_count: int = 0
    clicks_count: int = 0
    messages_count: int = 0
    
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


# ===================================
# Lead Models
# ===================================

class Lead(BaseDBModel):
    """Модель лида"""
    ad_id: Optional[str] = None
    
    name: Optional[str] = "Неизвестно"
    phone: str
    email: Optional[str] = None
    
    source: Platform
    platform_user_id: Optional[str] = None
    
    status: LeadStatus = LeadStatus.NEW
    quality_score: Optional[int] = Field(None, ge=0, le=100)
    
    budget: Optional[float] = None
    urgency: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict] = Field(default_factory=dict)
    
    contacted_at: Optional[datetime] = None
    qualified_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    @validator('phone')
    def validate_phone(cls, v):
        """Валидация телефона"""
        from shared.utils import validate_phone
        if not validate_phone(v):
            raise ValueError('Некорректный формат телефона')
        return v


# ===================================
# Conversation Models
# ===================================

class ConversationMessage(BaseDBModel):
    """Модель сообщения"""
    lead_id: str
    platform: Platform
    
    message: str
    sender: str  # bot, lead, human
    
    message_type: str = "text"
    metadata: Optional[Dict] = Field(default_factory=dict)


# ===================================
# Analytics Models
# ===================================

class CampaignMetrics(BaseModel):
    """Метрики кампании"""
    campaign_id: str
    ads_count: int
    leads_count: int
    qualified_leads: int
    hot_leads: int
    won_leads: int
    
    spent: float
    cpl: float  # Cost Per Lead
    roi: Optional[float] = None


class NicheMetrics(BaseModel):
    """Метрики ниши"""
    niche_id: str
    name: str
    
    total_campaigns: int
    total_leads: int
    total_spent: float
    
    avg_cpl: float
    avg_roi: Optional[float] = None
    
    best_platform: Optional[str] = None


# ===================================
# Экспорт
# ===================================

__all__ = [
    "NicheStatus",
    "CampaignStatus",
    "LeadStatus",
    "Platform",
    "Niche",
    "Campaign",
    "Ad",
    "Lead",
    "ConversationMessage",
    "CampaignMetrics",
    "NicheMetrics"
]

