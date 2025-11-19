"""
Configuration для Satu.kz парсера
Точные селекторы для Satu.kz
"""

from ...models import ParserConfig, ParserType


SATU_CONFIG = ParserConfig(
    site_name="satu.kz",
    base_url="https://satu.kz",
    parser_type=ParserType.SATU,
    use_playwright=True,  # Satu.kz использует JS для загрузки данных
    
    wait_for_selector=".b-product-title",  # Ждем загрузки заголовка товара
    
    selectors={
        # Basic Info
        "title": ".b-product-title h1, h1[itemprop='name']",
        "sku": ".b-article-code, .product-article",
        "description": ".b-product-description, [itemprop='description']",
        "short_description": ".b-product-short-desc",
        
        # Price
        "price": ".b-price-amount, .b-product-price [itemprop='price']",
        "old_price": ".b-price-old, .old-price",
        "currency": ".b-price-currency",
        
        # Classification
        "category": ".b-breadcrumbs li:last-child, .breadcrumb-item:last-child",
        "breadcrumbs": ".b-breadcrumbs, .breadcrumb",
        "brand": ".b-product-brand, [itemprop='brand']",
        "manufacturer": ".b-product-manufacturer",
        
        # Images
        "images": ".b-product-gallery img, .product-images img, img[itemprop='image']",
        "main_image": ".b-product-main-image img",
        
        # Attributes/Characteristics
        "attributes": {
            "container": ".b-characteristics, .product-attributes",
            "name_selector": ".b-char-name, .attr-name",
            "value_selector": ".b-char-value, .attr-value"
        },
        
        # Stock & Availability
        "stock_status": ".b-stock-status, .availability",
        "in_stock": ".b-in-stock",
        
        # Rating & Reviews
        "rating": "[itemprop='ratingValue'], .rating-value",
        "reviews_count": "[itemprop='reviewCount'], .reviews-count",
        
        # SEO
        "meta_title": "meta[property='og:title'], meta[name='title']",
        "meta_description": "meta[name='description'], meta[property='og:description']",
        "canonical": "link[rel='canonical']",
        "h1": "h1",
        "h2": "h2"
    },
    
    # Anti-detect settings
    custom_headers={
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br"
    },
    
    rate_limit=2.0,  # 2 секунды между запросами
    max_retries=3,
    timeout=30,
    
    rotate_user_agent=True,
    respect_robots_txt=False  # Для конкурентного анализа
)


# Дополнительные паттерны для Satu.kz
SATU_PATTERNS = {
    # URL patterns
    "product_url_pattern": r"satu\.kz/.+/p\d+",
    "category_url_pattern": r"satu\.kz/catalog/",
    
    # ID extraction
    "product_id_pattern": r"/p(\d+)",
    
    # Price patterns (если в тексте)
    "price_pattern": r"(\d+(?:\s+\d+)*)\s*₸",
    
    # Phone patterns (если парсим контакты)
    "phone_pattern": r"\+?7[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}"
}

