"""
Pydantic Models для Competitor Parser
Модели данных для парсинга товаров с SEO метаданными
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ParserType(str, Enum):
    """Типы парсеров"""
    UNIVERSAL = "universal"
    SATU = "satu"
    KASPI = "kaspi"
    CUSTOM = "custom"


class TaskStatus(str, Enum):
    """Статусы задач парсинга"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Форматы экспорта"""
    JSON = "json"
    CSV = "csv"
    SQL = "sql"
    WORDPRESS_XML = "wordpress_xml"
    SCHEMA_ORG = "schema_org"


# ===================================
# Product Related Models
# ===================================

class ProductAttribute(BaseModel):
    """Атрибут/характеристика товара"""
    name: str
    value: str
    unit: Optional[str] = None


class ProductImage(BaseModel):
    """Изображение товара"""
    url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    order: int = 0
    width: Optional[int] = None
    height: Optional[int] = None


class ProductPrice(BaseModel):
    """Цена товара"""
    amount: float
    currency: str = "KZT"
    old_price: Optional[float] = None
    discount_percent: Optional[float] = None
    
    def calculate_discount(self):
        """Рассчитать процент скидки"""
        if self.old_price and self.old_price > self.amount:
            self.discount_percent = round(
                ((self.old_price - self.amount) / self.old_price) * 100, 2
            )


# ===================================
# SEO Data Models
# ===================================

class SEOData(BaseModel):
    """SEO метаданные страницы"""
    # Meta tags
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[List[str]] = None
    
    # Open Graph
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    og_type: Optional[str] = None
    
    # Headings
    h1: Optional[List[str]] = None
    h2: Optional[List[str]] = None
    h3: Optional[List[str]] = None
    
    # URLs
    canonical_url: Optional[str] = None
    
    # Schema.org
    schema_org: Optional[Dict[str, Any]] = None
    
    # Additional
    lang: Optional[str] = None
    robots: Optional[str] = None


# ===================================
# Main Product Model
# ===================================

class ParsedProduct(BaseModel):
    """Распарсенный товар с полными данными"""
    
    # Primary ID
    id: Optional[str] = None
    
    # Basic Info
    sku: Optional[str] = None
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    
    # Price
    price: Optional[ProductPrice] = None
    
    # Category & Classification
    category: Optional[str] = None
    breadcrumbs: Optional[List[str]] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    
    # Attributes & Images
    attributes: List[ProductAttribute] = []
    images: List[ProductImage] = []
    
    # Stock & Rating
    stock_status: Optional[str] = None
    in_stock: Optional[bool] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    
    # SEO Data
    seo_data: Optional[SEOData] = None
    
    # Source
    source_url: str
    source_site: str
    parser_type: ParserType = ParserType.UNIVERSAL
    
    # Metadata
    parsed_at: datetime = Field(default_factory=datetime.now)
    parser_version: str = "0.1.0"
    task_id: Optional[str] = None
    
    # Optional: raw HTML for debugging
    raw_html: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ===================================
# Parser Task Models
# ===================================

class ParserTask(BaseModel):
    """Задача парсинга"""
    id: str
    url: str
    parser_type: ParserType
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    
    # Results
    products_found: int = 0
    products_saved: int = 0
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Settings
    max_pages: int = 1
    rate_limit: float = 2.0
    
    class Config:
        use_enum_values = True


# ===================================
# Parser Config Models
# ===================================

class ParserConfig(BaseModel):
    """Конфигурация парсера для конкретного сайта"""
    site_name: str
    base_url: str
    parser_type: ParserType = ParserType.UNIVERSAL
    
    # Селекторы для извлечения данных
    selectors: Dict[str, Any] = {
        "title": "h1, .product-title, [itemprop='name']",
        "sku": "[itemprop='sku'], .sku, .article",
        "description": "[itemprop='description'], .description, .product-description",
        "price": "[itemprop='price'], .price, .product-price",
        "old_price": ".old-price, .price-old",
        "images": "img[itemprop='image'], .product-image img",
        "attributes": {},
        "category": "[itemprop='category'], .breadcrumb li:last-child",
        "brand": "[itemprop='brand'], .brand",
        # SEO selectors
        "meta_title": "meta[property='og:title'], meta[name='title']",
        "meta_description": "meta[name='description'], meta[property='og:description']",
        "h1": "h1",
        "h2": "h2",
        "canonical": "link[rel='canonical']"
    }
    
    # Настройки парсера
    use_playwright: bool = False
    wait_for_selector: Optional[str] = None
    custom_headers: Dict[str, str] = {}
    rate_limit: float = 2.0
    max_retries: int = 3
    timeout: int = 30
    
    # Anti-detect
    rotate_user_agent: bool = True
    respect_robots_txt: bool = False
    
    class Config:
        use_enum_values = True


# ===================================
# Request/Response Models
# ===================================

class ParseRequest(BaseModel):
    """Запрос на парсинг"""
    url: str
    parser_type: ParserType = ParserType.UNIVERSAL
    max_pages: int = 1
    custom_config: Optional[ParserConfig] = None


class ParseResponse(BaseModel):
    """Ответ на запрос парсинга"""
    success: bool
    task_id: str
    status: TaskStatus
    message: str
    
    class Config:
        use_enum_values = True


class ExportRequest(BaseModel):
    """Запрос на экспорт"""
    format: ExportFormat
    task_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    
    class Config:
        use_enum_values = True

