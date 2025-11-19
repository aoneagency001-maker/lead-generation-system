"""
Export Service
Экспорт данных товаров в различные форматы (JSON, CSV, SQL, WordPress XML)
"""

import logging
import json
import csv
from io import StringIO, BytesIO
from typing import List, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

from ..models import ParsedProduct, ExportFormat
from ..database.client import get_parser_db_client

logger = logging.getLogger(__name__)


class ExportService:
    """Сервис экспорта данных"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.db = get_parser_db_client()
    
    async def export_products(
        self,
        format: ExportFormat,
        task_id: Optional[str] = None,
        source_site: Optional[str] = None,
        limit: Optional[int] = None
    ) -> tuple[bytes, str, str]:
        """
        Экспорт товаров в указанном формате
        
        Args:
            format: Формат экспорта
            task_id: Фильтр по задаче
            source_site: Фильтр по сайту
            limit: Лимит записей
        
        Returns:
            Tuple (data_bytes, filename, content_type)
        """
        # Получаем товары
        products = await self.db.get_products(
            task_id=task_id,
            source_site=source_site,
            limit=limit or 1000
        )
        
        if not products:
            logger.warning("No products to export")
            return b"", "empty.txt", "text/plain"
        
        # Экспортируем в нужном формате
        if format == ExportFormat.JSON:
            return self._export_json(products)
        elif format == ExportFormat.CSV:
            return self._export_csv(products)
        elif format == ExportFormat.SQL:
            return self._export_sql(products)
        elif format == ExportFormat.WORDPRESS_XML:
            return self._export_wordpress_xml(products)
        elif format == ExportFormat.SCHEMA_ORG:
            return self._export_schema_org(products)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    # ===================================
    # Export Formats
    # ===================================
    
    def _export_json(self, products: List[ParsedProduct]) -> tuple[bytes, str, str]:
        """Экспорт в JSON"""
        try:
            # Преобразуем в dict
            data = [product.dict() for product in products]
            
            # Сериализуем в JSON
            json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            json_bytes = json_str.encode('utf-8')
            
            filename = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            logger.info(f"Exported {len(products)} products to JSON")
            
            return json_bytes, filename, "application/json"
        
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise
    
    def _export_csv(self, products: List[ParsedProduct]) -> tuple[bytes, str, str]:
        """Экспорт в CSV"""
        try:
            output = StringIO()
            
            # Определяем поля для CSV
            fieldnames = [
                'id', 'sku', 'external_id', 'title', 'description',
                'price_amount', 'price_currency', 'old_price', 'discount_percent',
                'category', 'brand', 'manufacturer',
                'stock_status', 'in_stock', 'rating', 'reviews_count',
                'source_url', 'source_site', 'parsed_at'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            
            # Пишем строки
            for product in products:
                row = {
                    'id': product.id,
                    'sku': product.sku,
                    'external_id': product.external_id,
                    'title': product.title,
                    'description': product.description,
                    'price_amount': product.price.amount if product.price else None,
                    'price_currency': product.price.currency if product.price else 'KZT',
                    'old_price': product.price.old_price if product.price else None,
                    'discount_percent': product.price.discount_percent if product.price else None,
                    'category': product.category,
                    'brand': product.brand,
                    'manufacturer': product.manufacturer,
                    'stock_status': product.stock_status,
                    'in_stock': product.in_stock,
                    'rating': product.rating,
                    'reviews_count': product.reviews_count,
                    'source_url': product.source_url,
                    'source_site': product.source_site,
                    'parsed_at': product.parsed_at.isoformat() if product.parsed_at else None
                }
                writer.writerow(row)
            
            csv_bytes = output.getvalue().encode('utf-8')
            filename = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            logger.info(f"Exported {len(products)} products to CSV")
            
            return csv_bytes, filename, "text/csv"
        
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def _export_sql(self, products: List[ParsedProduct]) -> tuple[bytes, str, str]:
        """Экспорт в SQL INSERT statements"""
        try:
            sql_statements = []
            
            # Заголовок
            sql_statements.append("-- SQL Export of Products")
            sql_statements.append(f"-- Generated: {datetime.now().isoformat()}")
            sql_statements.append(f"-- Total products: {len(products)}")
            sql_statements.append("")
            
            # CREATE TABLE statement
            sql_statements.append("CREATE TABLE IF NOT EXISTS products (")
            sql_statements.append("    id VARCHAR(36) PRIMARY KEY,")
            sql_statements.append("    sku VARCHAR(255),")
            sql_statements.append("    external_id VARCHAR(255),")
            sql_statements.append("    title TEXT NOT NULL,")
            sql_statements.append("    description TEXT,")
            sql_statements.append("    price_amount DECIMAL(10, 2),")
            sql_statements.append("    price_currency VARCHAR(10),")
            sql_statements.append("    old_price DECIMAL(10, 2),")
            sql_statements.append("    discount_percent DECIMAL(5, 2),")
            sql_statements.append("    category TEXT,")
            sql_statements.append("    brand VARCHAR(255),")
            sql_statements.append("    manufacturer VARCHAR(255),")
            sql_statements.append("    stock_status VARCHAR(50),")
            sql_statements.append("    in_stock BOOLEAN,")
            sql_statements.append("    rating DECIMAL(3, 2),")
            sql_statements.append("    reviews_count INTEGER,")
            sql_statements.append("    source_url TEXT,")
            sql_statements.append("    source_site VARCHAR(255),")
            sql_statements.append("    parsed_at TIMESTAMP")
            sql_statements.append(");")
            sql_statements.append("")
            
            # INSERT statements
            for product in products:
                values = [
                    self._sql_escape(str(product.id)),
                    self._sql_escape(product.sku),
                    self._sql_escape(product.external_id),
                    self._sql_escape(product.title),
                    self._sql_escape(product.description),
                    str(product.price.amount) if product.price else 'NULL',
                    self._sql_escape(product.price.currency) if product.price else "'KZT'",
                    str(product.price.old_price) if (product.price and product.price.old_price) else 'NULL',
                    str(product.price.discount_percent) if (product.price and product.price.discount_percent) else 'NULL',
                    self._sql_escape(product.category),
                    self._sql_escape(product.brand),
                    self._sql_escape(product.manufacturer),
                    self._sql_escape(product.stock_status),
                    'TRUE' if product.in_stock else 'FALSE',
                    str(product.rating) if product.rating else 'NULL',
                    str(product.reviews_count) if product.reviews_count else 'NULL',
                    self._sql_escape(product.source_url),
                    self._sql_escape(product.source_site),
                    self._sql_escape(product.parsed_at.isoformat()) if product.parsed_at else 'NULL'
                ]
                
                sql = f"INSERT INTO products VALUES ({', '.join(values)});"
                sql_statements.append(sql)
            
            sql_str = "\n".join(sql_statements)
            sql_bytes = sql_str.encode('utf-8')
            
            filename = f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            logger.info(f"Exported {len(products)} products to SQL")
            
            return sql_bytes, filename, "application/sql"
        
        except Exception as e:
            logger.error(f"Failed to export SQL: {e}")
            raise
    
    def _export_wordpress_xml(self, products: List[ParsedProduct]) -> tuple[bytes, str, str]:
        """
        Экспорт в WordPress WXR (WordPress eXtended RSS) формат
        Для импорта на ПБН сайты
        """
        try:
            # Создаем корневой элемент RSS
            rss = ET.Element('rss', {
                'version': '2.0',
                'xmlns:excerpt': 'http://wordpress.org/export/1.2/excerpt/',
                'xmlns:content': 'http://purl.org/rss/1.0/modules/content/',
                'xmlns:wfw': 'http://wellformedweb.org/CommentAPI/',
                'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
                'xmlns:wp': 'http://wordpress.org/export/1.2/'
            })
            
            channel = ET.SubElement(rss, 'channel')
            
            # Метаданные канала
            ET.SubElement(channel, 'title').text = "Products Export"
            ET.SubElement(channel, 'link').text = "https://example.com"
            ET.SubElement(channel, 'description').text = f"Exported {len(products)} products"
            ET.SubElement(channel, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
            ET.SubElement(channel, 'language').text = "ru-RU"
            ET.SubElement(channel, 'wp:wxr_version').text = "1.2"
            
            # Добавляем товары как посты
            for idx, product in enumerate(products):
                item = ET.SubElement(channel, 'item')
                
                # Основные поля
                ET.SubElement(item, 'title').text = product.title
                ET.SubElement(item, 'link').text = product.source_url
                ET.SubElement(item, 'pubDate').text = product.parsed_at.strftime('%a, %d %b %Y %H:%M:%S +0000') if product.parsed_at else datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
                ET.SubElement(item, 'dc:creator').text = "admin"
                ET.SubElement(item, 'guid', isPermaLink="false").text = f"product-{product.id}"
                ET.SubElement(item, 'description').text = product.short_description or ""
                
                # Контент
                content = self._build_wordpress_content(product)
                ET.SubElement(item, 'content:encoded').text = f"<![CDATA[{content}]]>"
                ET.SubElement(item, 'excerpt:encoded').text = f"<![CDATA[{product.short_description or ''}]]>"
                
                # WordPress мета
                ET.SubElement(item, 'wp:post_id').text = str(idx + 1)
                ET.SubElement(item, 'wp:post_date').text = product.parsed_at.strftime('%Y-%m-%d %H:%M:%S') if product.parsed_at else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ET.SubElement(item, 'wp:post_type').text = "post"
                ET.SubElement(item, 'wp:status').text = "publish"
                
                # Категория
                if product.category:
                    cat = ET.SubElement(item, 'category', domain="category", nicename=product.category.lower().replace(' ', '-'))
                    cat.text = f"<![CDATA[{product.category}]]>"
                
                # Custom fields для товарных данных
                if product.price:
                    postmeta = ET.SubElement(item, 'wp:postmeta')
                    ET.SubElement(postmeta, 'wp:meta_key').text = "price"
                    ET.SubElement(postmeta, 'wp:meta_value').text = f"<![CDATA[{product.price.amount}]]>"
                
                if product.sku:
                    postmeta = ET.SubElement(item, 'wp:postmeta')
                    ET.SubElement(postmeta, 'wp:meta_key').text = "sku"
                    ET.SubElement(postmeta, 'wp:meta_value').text = f"<![CDATA[{product.sku}]]>"
            
            # Красиво форматируем XML
            xml_str = self._prettify_xml(rss)
            xml_bytes = xml_str.encode('utf-8')
            
            filename = f"wordpress_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            logger.info(f"Exported {len(products)} products to WordPress XML")
            
            return xml_bytes, filename, "application/xml"
        
        except Exception as e:
            logger.error(f"Failed to export WordPress XML: {e}")
            raise
    
    def _export_schema_org(self, products: List[ParsedProduct]) -> tuple[bytes, str, str]:
        """Экспорт в Schema.org JSON-LD формат"""
        try:
            schema_products = []
            
            for product in products:
                schema_product = {
                    "@context": "https://schema.org/",
                    "@type": "Product",
                    "name": product.title,
                    "description": product.description,
                    "sku": product.sku,
                    "brand": {
                        "@type": "Brand",
                        "name": product.brand
                    } if product.brand else None,
                    "image": [img.url for img in product.images] if product.images else [],
                    "offers": {
                        "@type": "Offer",
                        "url": product.source_url,
                        "priceCurrency": product.price.currency if product.price else "KZT",
                        "price": product.price.amount if product.price else None,
                        "availability": "https://schema.org/InStock" if product.in_stock else "https://schema.org/OutOfStock"
                    } if product.price else None
                }
                
                # Удаляем None значения
                schema_product = {k: v for k, v in schema_product.items() if v is not None}
                schema_products.append(schema_product)
            
            json_str = json.dumps(schema_products, ensure_ascii=False, indent=2, default=str)
            json_bytes = json_str.encode('utf-8')
            
            filename = f"schema_org_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            logger.info(f"Exported {len(products)} products to Schema.org JSON-LD")
            
            return json_bytes, filename, "application/ld+json"
        
        except Exception as e:
            logger.error(f"Failed to export Schema.org: {e}")
            raise
    
    # ===================================
    # Helper Methods
    # ===================================
    
    def _sql_escape(self, value: Optional[str]) -> str:
        """Экранирование значения для SQL"""
        if value is None:
            return "NULL"
        
        # Экранируем одинарные кавычки
        value = str(value).replace("'", "''")
        return f"'{value}'"
    
    def _build_wordpress_content(self, product: ParsedProduct) -> str:
        """Создать HTML контент для WordPress поста"""
        content_parts = []
        
        # Описание
        if product.description:
            content_parts.append(f"<p>{product.description}</p>")
        
        # Цена
        if product.price:
            price_html = f"<p><strong>Цена:</strong> {product.price.amount} {product.price.currency}</p>"
            if product.price.old_price:
                price_html += f"<p><s>{product.price.old_price} {product.price.currency}</s> (скидка {product.price.discount_percent}%)</p>"
            content_parts.append(price_html)
        
        # Характеристики
        if product.attributes:
            content_parts.append("<h2>Характеристики</h2>")
            content_parts.append("<ul>")
            for attr in product.attributes:
                unit = f" {attr.unit}" if attr.unit else ""
                content_parts.append(f"<li><strong>{attr.name}:</strong> {attr.value}{unit}</li>")
            content_parts.append("</ul>")
        
        # Изображения
        if product.images:
            content_parts.append("<h2>Изображения</h2>")
            for img in product.images[:3]:  # Первые 3 изображения
                alt = img.alt_text or product.title
                content_parts.append(f'<img src="{img.url}" alt="{alt}" />')
        
        # Ссылка на источник
        content_parts.append(f"<p><a href='{product.source_url}' target='_blank'>Оригинал товара</a></p>")
        
        return "\n".join(content_parts)
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """Красиво форматировать XML"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")


# ===================================
# Singleton
# ===================================

_export_service: Optional[ExportService] = None


def get_export_service() -> ExportService:
    """
    Получить singleton ExportService
    
    Returns:
        ExportService instance
    """
    global _export_service
    
    if _export_service is None:
        _export_service = ExportService()
    
    return _export_service

