"""
Satu.kz Module - Pydantic Models
Модели данных для Satu модуля
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ===================================
# Enums
# ===================================

class SatuAccountStatus(str, Enum):
    """Статусы аккаунта Satu"""
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SatuProductStatus(str, Enum):
    """Статусы товара"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class SatuPublishMethod(str, Enum):
    """Методы публикации"""
    API = "api"
    BROWSER = "browser"


class SatuParserMethod(str, Enum):
    """Методы парсинга"""
    PLAYWRIGHT = "playwright"
    API = "api"


class SatuOrderStatus(str, Enum):
    """Статусы заказа"""
    NEW = "new"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class SatuPaymentStatus(str, Enum):
    """Статусы оплаты"""
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"


class SatuMessageStatus(str, Enum):
    """Статусы сообщения"""
    NEW = "new"
    READ = "read"
    REPLIED = "replied"
    ARCHIVED = "archived"


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

class SatuAccountBase(BaseModel):
    """Базовая модель аккаунта"""
    company_name: str
    company_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class SatuAccountCreate(SatuAccountBase):
    """Создание аккаунта"""
    api_token: str
    token_permissions: Dict = Field(default_factory=dict)


class SatuAccount(BaseDBModel, SatuAccountBase):
    """Полная модель аккаунта"""
    api_token: str
    token_permissions: Dict = Field(default_factory=dict)
    token_expires_at: Optional[datetime] = None
    cookies: Optional[Dict] = None
    user_agent: Optional[str] = None
    proxy_url: Optional[str] = None
    status: SatuAccountStatus = SatuAccountStatus.ACTIVE
    last_api_call_at: Optional[datetime] = None


class APITokenCredentials(BaseModel):
    """Credentials для API авторизации"""
    company_name: str
    api_token: str


# ===================================
# Product Models
# ===================================

class SatuProductBase(BaseModel):
    """Базовая модель товара"""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=10000)
    price: Optional[float] = Field(None, gt=0)
    currency: str = "KZT"
    category: Optional[str] = None
    attributes: Dict = Field(default_factory=dict)


class SatuProductCreate(SatuProductBase):
    """Создание товара"""
    account_id: str
    images: List[str] = Field(default_factory=list)
    stock_quantity: int = Field(default=0, ge=0)
    sku: Optional[str] = None
    publish_method: SatuPublishMethod = SatuPublishMethod.API
    metadata: Dict = Field(default_factory=dict)


class SatuProduct(BaseDBModel, SatuProductBase):
    """Полная модель товара"""
    account_id: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    category_id: Optional[str] = None
    group_id: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    stock_quantity: int = 0
    sku: Optional[str] = None
    status: SatuProductStatus = SatuProductStatus.DRAFT
    publish_method: Optional[SatuPublishMethod] = None
    views_count: int = 0
    orders_count: int = 0
    published_at: Optional[datetime] = None
    metadata: Dict = Field(default_factory=dict)


# ===================================
# Order Models
# ===================================

class SatuOrderProduct(BaseModel):
    """Товар в заказе"""
    product_id: str
    product_name: str
    quantity: int
    price: float


class SatuOrder(BaseDBModel):
    """Модель заказа"""
    account_id: str
    external_id: str
    order_number: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    products: List[SatuOrderProduct] = Field(default_factory=list)
    total_amount: Optional[float] = None
    currency: str = "KZT"
    delivery_method: Optional[str] = None
    delivery_address: Optional[str] = None
    delivery_city: Optional[str] = None
    status: SatuOrderStatus = SatuOrderStatus.NEW
    payment_status: SatuPaymentStatus = SatuPaymentStatus.PENDING
    order_date: datetime = Field(default_factory=datetime.now)
    metadata: Dict = Field(default_factory=dict)


# ===================================
# Message Models
# ===================================

class SatuMessage(BaseDBModel):
    """Модель сообщения"""
    account_id: str
    order_id: Optional[str] = None
    external_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    message_text: str
    status: SatuMessageStatus = SatuMessageStatus.NEW
    replied_at: Optional[datetime] = None
    received_at: datetime = Field(default_factory=datetime.now)


# ===================================
# Parser Models
# ===================================

class SearchQuery(BaseModel):
    """Запрос на парсинг"""
    search_query: str = Field(..., min_length=1)
    category: Optional[str] = None
    parser_method: SatuParserMethod = SatuParserMethod.PLAYWRIGHT
    max_pages: int = Field(default=1, ge=1, le=10)


class SatuListing(BaseModel):
    """Один товар из парсинга"""
    title: str
    price: Optional[float] = None
    url: str
    external_id: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    seller_name: Optional[str] = None
    seller_rating: Optional[float] = None


class SatuParsedData(BaseDBModel):
    """Результаты парсинга"""
    search_query: str
    search_url: Optional[str] = None
    category: Optional[str] = None
    parser_method: SatuParserMethod
    data: List[SatuListing] = Field(default_factory=list)
    items_count: int = 0
    parse_duration_seconds: Optional[float] = None
    pages_parsed: int = 1
    parsed_at: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    status: str = "success"


class SatuParserTask(BaseDBModel):
    """Задача парсинга"""
    search_query: str
    category: Optional[str] = None
    parser_method: SatuParserMethod
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
    account: Optional[SatuAccount] = None
    error: Optional[str] = None


class PublishResult(BaseModel):
    """Результат публикации"""
    success: bool
    product: Optional[SatuProduct] = None
    error: Optional[str] = None
    method: SatuPublishMethod


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
    "SatuAccountStatus",
    "SatuProductStatus",
    "SatuPublishMethod",
    "SatuParserMethod",
    "SatuOrderStatus",
    "SatuPaymentStatus",
    "SatuMessageStatus",
    "TaskStatus",
    # Account Models
    "SatuAccountBase",
    "SatuAccountCreate",
    "SatuAccount",
    "APITokenCredentials",
    # Product Models
    "SatuProductBase",
    "SatuProductCreate",
    "SatuProduct",
    # Order Models
    "SatuOrderProduct",
    "SatuOrder",
    # Message Models
    "SatuMessage",
    # Parser Models
    "SearchQuery",
    "SatuListing",
    "SatuParsedData",
    "SatuParserTask",
    # Response Models
    "AuthResult",
    "PublishResult",
    "ParserResult",
]


