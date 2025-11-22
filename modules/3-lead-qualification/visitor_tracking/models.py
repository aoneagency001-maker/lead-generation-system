"""
Visitor Tracking Models
Pydantic модели для отслеживания посетителей
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VisitorTrackRequest(BaseModel):
    """Запрос на отслеживание посетителя"""
    page: Optional[str] = Field(None, description="Текущая страница")
    landingPage: Optional[str] = Field(None, description="Лендинг")
    referrer: Optional[str] = Field(None, description="Реферер")
    screenResolution: Optional[str] = Field(None, description="Разрешение экрана")
    sessionId: Optional[str] = Field(None, description="ID сессии")
    utmSource: Optional[str] = Field(None, alias="utmSource", description="UTM source")
    utmMedium: Optional[str] = Field(None, alias="utmMedium", description="UTM medium")
    utmCampaign: Optional[str] = Field(None, alias="utmCampaign", description="UTM campaign")
    utmTerm: Optional[str] = Field(None, alias="utmTerm", description="UTM term")
    utmContent: Optional[str] = Field(None, alias="utmContent", description="UTM content")
    isFirstVisit: Optional[bool] = Field(None, alias="isFirstVisit", description="Первый визит")
    
    class Config:
        allow_population_by_field_name = True


class VisitorTrackResponse(BaseModel):
    """Ответ на запрос отслеживания"""
    tracked: bool
    visitorId: Optional[str] = None
    requestId: Optional[str] = None
    message: Optional[str] = None


class TildaWebhookRequest(BaseModel):
    """Webhook запрос от Tilda"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    message: Optional[str] = None
    form_name: Optional[str] = Field(None, alias="formName", description="Название формы")
    page_url: Optional[str] = Field(None, alias="pageUrl", description="URL страницы")
    
    class Config:
        allow_population_by_field_name = True


class TildaWebhookResponse(BaseModel):
    """Ответ на Tilda webhook"""
    success: bool
    message: str
    requestId: Optional[str] = None


class VisitorData(BaseModel):
    """Данные посетителя для хранения в БД"""
    id: Optional[str] = None
    session_id: Optional[str] = None
    page: Optional[str] = None
    landing_page: Optional[str] = None
    referrer: Optional[str] = None
    screen_resolution: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    device_type: Optional[str] = None  # mobile, tablet, desktop
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_term: Optional[str] = None
    utm_content: Optional[str] = None
    is_first_visit: Optional[bool] = None
    is_bot: Optional[bool] = None
    created_at: Optional[datetime] = None

