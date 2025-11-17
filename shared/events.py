"""
Event Definitions
Определения всех событий системы для Event-Driven Architecture
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


# =============================================================================
# Module 1: Market Research Events
# =============================================================================

@dataclass
class NicheAnalyzedEvent:
    """Событие: Ниша проанализирована"""
    niche_id: str
    niche_name: str
    profitability_score: int
    market: str
    analyzed_at: datetime
    data: Dict[str, Any]  # Детали анализа


# =============================================================================
# Module 2: Traffic Generation Events
# =============================================================================

@dataclass
class CampaignCreatedEvent:
    """Событие: Кампания создана"""
    campaign_id: str
    niche_id: str
    platform: str  # olx, kaspi, telegram
    budget: float
    created_at: datetime


@dataclass
class AdPostedEvent:
    """Событие: Объявление размещено"""
    ad_id: str
    campaign_id: str
    platform: str
    title: str
    posted_at: datetime


@dataclass
class LeadCreatedEvent:
    """Событие: Новый лид создан"""
    lead_id: str
    campaign_id: str
    source: str  # olx, kaspi, telegram, whatsapp
    phone: Optional[str]
    email: Optional[str]
    name: Optional[str]
    created_at: datetime


# =============================================================================
# Module 3: Lead Qualification Events
# =============================================================================

@dataclass
class LeadContactedEvent:
    """Событие: Лид контактирован (начат диалог)"""
    lead_id: str
    platform: str  # telegram, whatsapp
    first_message: str
    contacted_at: datetime


@dataclass
class ConversationMessageEvent:
    """Событие: Сообщение в разговоре"""
    conversation_id: str
    lead_id: str
    message: str
    sender: str  # bot, lead, human
    timestamp: datetime


@dataclass
class LeadQualifiedEvent:
    """Событие: Лид квалифицирован (прошел отбор)"""
    lead_id: str
    qualification_score: int
    qualification_data: Dict[str, Any]  # Ответы на вопросы
    qualified_at: datetime


@dataclass
class LeadDisqualifiedEvent:
    """Событие: Лид дисквалифицирован (не подходит)"""
    lead_id: str
    qualification_score: int
    reason: str
    disqualified_at: datetime


# =============================================================================
# Module 4: Sales Handoff Events
# =============================================================================

@dataclass
class LeadHandedOffEvent:
    """Событие: Лид передан в продажи"""
    lead_id: str
    assigned_to: Optional[str]  # ID sales rep
    lead_package: Dict[str, Any]  # Пакет с данными лида
    handed_off_at: datetime


@dataclass
class LeadAcceptedEvent:
    """Событие: Лид принят sales rep"""
    lead_id: str
    accepted_by: str
    accepted_at: datetime


@dataclass
class LeadClosedEvent:
    """Событие: Сделка закрыта (успешно)"""
    lead_id: str
    closed_by: str
    deal_amount: float
    closed_at: datetime


@dataclass
class LeadLostEvent:
    """Событие: Лид потерян (не закрыли сделку)"""
    lead_id: str
    reason: str
    lost_at: datetime


# =============================================================================
# Module 5: Analytics Events
# =============================================================================

@dataclass
class MetricsCalculatedEvent:
    """Событие: Метрики рассчитаны"""
    campaign_id: str
    metrics: Dict[str, Any]  # CPL, ROI, conversion_rate, etc.
    calculated_at: datetime


@dataclass
class DailyReportGeneratedEvent:
    """Событие: Ежедневный отчет сгенерирован"""
    report_date: str
    total_leads: int
    qualified_leads: int
    closed_deals: int
    total_revenue: float
    generated_at: datetime


# =============================================================================
# System Events
# =============================================================================

@dataclass
class SystemErrorEvent:
    """Событие: Системная ошибка"""
    module: str
    error_type: str
    error_message: str
    traceback: Optional[str]
    occurred_at: datetime


@dataclass
class NotificationSentEvent:
    """Событие: Уведомление отправлено"""
    notification_type: str  # telegram, email, sms
    recipient: str
    message: str
    sent_at: datetime


# =============================================================================
# Event Type Registry
# =============================================================================

EVENT_TYPES = {
    # Module 1
    "NicheAnalyzed": NicheAnalyzedEvent,
    
    # Module 2
    "CampaignCreated": CampaignCreatedEvent,
    "AdPosted": AdPostedEvent,
    "LeadCreated": LeadCreatedEvent,
    
    # Module 3
    "LeadContacted": LeadContactedEvent,
    "ConversationMessage": ConversationMessageEvent,
    "LeadQualified": LeadQualifiedEvent,
    "LeadDisqualified": LeadDisqualifiedEvent,
    
    # Module 4
    "LeadHandedOff": LeadHandedOffEvent,
    "LeadAccepted": LeadAcceptedEvent,
    "LeadClosed": LeadClosedEvent,
    "LeadLost": LeadLostEvent,
    
    # Module 5
    "MetricsCalculated": MetricsCalculatedEvent,
    "DailyReportGenerated": DailyReportGeneratedEvent,
    
    # System
    "SystemError": SystemErrorEvent,
    "NotificationSent": NotificationSentEvent,
}


def get_event_class(event_type: str):
    """
    Получить класс события по его типу
    
    Args:
        event_type: Тип события (например, "LeadCreated")
    
    Returns:
        Класс события или None
    """
    return EVENT_TYPES.get(event_type)


# Экспорт
__all__ = [
    # Module 1
    "NicheAnalyzedEvent",
    
    # Module 2
    "CampaignCreatedEvent",
    "AdPostedEvent",
    "LeadCreatedEvent",
    
    # Module 3
    "LeadContactedEvent",
    "ConversationMessageEvent",
    "LeadQualifiedEvent",
    "LeadDisqualifiedEvent",
    
    # Module 4
    "LeadHandedOffEvent",
    "LeadAcceptedEvent",
    "LeadClosedEvent",
    "LeadLostEvent",
    
    # Module 5
    "MetricsCalculatedEvent",
    "DailyReportGeneratedEvent",
    
    # System
    "SystemErrorEvent",
    "NotificationSentEvent",
    
    # Utility
    "EVENT_TYPES",
    "get_event_class",
]

