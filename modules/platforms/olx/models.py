"""
OLX Module - Pydantic Models
Модели данных для OLX модуля
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ===================================
# Enums
# ===================================

class OLXAccountStatus(str, Enum):
    """Статусы аккаунта OLX"""
    ACTIVE = "active"
    BANNED = "banned"
    SUSPENDED = "suspended"
    EXPIRED = "expired"


class OLXLoginMethod(str, Enum):
    """Методы авторизации"""
    OAUTH = "oauth"
    BROWSER = "browser"


class OLXAdStatus(str, Enum):
    """Статусы объявления"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    EXPIRED = "expired"
    DELETED = "deleted"
    MODERATION = "moderation"


class OLXPublishMethod(str, Enum):
    """Методы публикации"""
    API = "api"
    BROWSER = "browser"


class OLXParserMethod(str, Enum):
    """Методы парсинга"""
    LERDEM = "lerdem"
    PLAYWRIGHT = "playwright"
    API = "api"


class TaskStatus(str, Enum):
    """Статусы задач"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


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
# Account Models
# ===================================

class OLXAccountBase(BaseModel):
    """Базовая модель аккаунта"""
    email: str
    phone: Optional[str] = None


class OLXAccountCreate(OLXAccountBase):
    """Создание аккаунта"""
    password: Optional[str] = None
    client_id: Optional[str] = None


class OLXAccount(BaseDBModel, OLXAccountBase):
    """Полная модель аккаунта"""
    password_hash: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    client_id: Optional[str] = None
    cookies: Optional[Dict] = None
    user_agent: Optional[str] = None
    proxy_url: Optional[str] = None
    status: OLXAccountStatus = OLXAccountStatus.ACTIVE
    last_login_at: Optional[datetime] = None
    login_method: OLXLoginMethod = OLXLoginMethod.OAUTH


class OAuthCredentials(BaseModel):
    """Credentials для OAuth авторизации"""
    email: str
    password: str
    client_id: str
    client_secret: str


class BrowserCredentials(BaseModel):
    """Credentials для Browser авторизации"""
    email: str
    password: str
    proxy_url: Optional[str] = None


# ===================================
# Ad Models
# ===================================

class OLXAdBase(BaseModel):
    """Базовая модель объявления"""
    title: str = Field(..., min_length=10, max_length=70)
    description: Optional[str] = Field(None, max_length=9000)
    price: Optional[float] = Field(None, gt=0)
    currency: str = "KZT"
    category: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None


class OLXAdCreate(OLXAdBase):
    """Создание объявления"""
    account_id: str
    images: List[str] = Field(default_factory=list, max_items=8)
    publish_method: OLXPublishMethod = OLXPublishMethod.API
    metadata: Dict = Field(default_factory=dict)


class OLXAd(BaseDBModel, OLXAdBase):
    """Полная модель объявления"""
    account_id: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    status: OLXAdStatus = OLXAdStatus.DRAFT
    publish_method: Optional[OLXPublishMethod] = None
    views_count: int = 0
    favorites_count: int = 0
    messages_count: int = 0
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)


# ===================================
# Parser Models
# ===================================

class SearchQuery(BaseModel):
    """Запрос на парсинг"""
    search_query: str = Field(..., min_length=1)
    city: Optional[str] = "almaty"
    category: Optional[str] = None
    parser_method: OLXParserMethod = OLXParserMethod.PLAYWRIGHT
    max_pages: int = Field(default=1, ge=1, le=10)


class OLXListing(BaseModel):
    """Одно объявление из парсинга"""
    title: str
    price: Optional[float] = None
    url: str
    external_id: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    city: Optional[str] = None
    published_date: Optional[str] = None
    seller_name: Optional[str] = None


class OLXParsedData(BaseDBModel):
    """Результаты парсинга"""
    search_query: str
    search_url: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    parser_method: OLXParserMethod
    data: List[OLXListing] = Field(default_factory=list)
    items_count: int = 0
    parse_duration_seconds: Optional[float] = None
    pages_parsed: int = 1
    parsed_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    status: str = "success"


class OLXParserTask(BaseDBModel):
    """Задача парсинга"""
    search_query: str
    city: Optional[str] = None
    category: Optional[str] = None
    parser_method: OLXParserMethod
    status: TaskStatus = TaskStatus.PENDING
    progress: int = Field(default=0, ge=0, le=100)
    result_id: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ===================================
# Response Models
# ===================================

class AuthResult(BaseModel):
    """Результат авторизации"""
    success: bool
    account: Optional[OLXAccount] = None
    error: Optional[str] = None
    method: OLXLoginMethod


class PublishResult(BaseModel):
    """Результат публикации"""
    success: bool
    ad: Optional[OLXAd] = None
    error: Optional[str] = None
    method: OLXPublishMethod


class ParserResult(BaseModel):
    """Результат парсинга"""
    success: bool
    task_id: str
    status: TaskStatus
    items_found: int = 0
    error: Optional[str] = None


# ===================================
# Экспорт
# ===================================

__all__ = [
    # Enums
    "OLXAccountStatus",
    "OLXLoginMethod",
    "OLXAdStatus",
    "OLXPublishMethod",
    "OLXParserMethod",
    "TaskStatus",
    # Account Models
    "OLXAccountBase",
    "OLXAccountCreate",
    "OLXAccount",
    "OAuthCredentials",
    "BrowserCredentials",
    # Ad Models
    "OLXAdBase",
    "OLXAdCreate",
    "OLXAd",
    # Parser Models
    "SearchQuery",
    "OLXListing",
    "OLXParsedData",
    "OLXParserTask",
    # Response Models
    "AuthResult",
    "PublishResult",
    "ParserResult",
]



