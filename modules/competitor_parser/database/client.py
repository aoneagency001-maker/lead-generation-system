"""
Database Client для Competitor Parser
Работа с Supabase для модуля парсера
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from supabase import Client

from core.database.supabase_client import get_supabase_client
from ..models import ParsedProduct, ParserTask, TaskStatus

logger = logging.getLogger(__name__)


class ParserDatabaseClient:
    """Клиент для работы с БД парсера"""
    
    def __init__(self, supabase_client: Optional[Client] = None):
        """
        Инициализация клиента
        
        Args:
            supabase_client: Supabase клиент (если None, создается новый)
        """
        self.db = supabase_client or get_supabase_client()
    
    # ===================================
    # Parser Tasks
    # ===================================
    
    async def create_task(self, task: ParserTask) -> Dict[str, Any]:
        """Создать задачу парсинга"""
        try:
            data = {
                "id": task.id,
                "url": task.url,
                "parser_type": task.parser_type.value if hasattr(task.parser_type, 'value') else task.parser_type,
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "progress": task.progress,
                "max_pages": task.max_pages,
                "rate_limit": float(task.rate_limit),
                "max_retries": task.max_retries
            }
            
            result = self.db.table("parser_tasks").insert(data).execute()
            
            if result.data:
                logger.info(f"Task created: {task.id}")
                return result.data[0]
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}", exc_info=True)
            raise
    
    async def get_task(self, task_id: str) -> Optional[ParserTask]:
        """Получить задачу по ID"""
        try:
            result = self.db.table("parser_tasks").select("*").eq("id", task_id).execute()
            
            if not result.data:
                return None
            
            data = result.data[0]
            return ParserTask(**data)
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[int] = None,
        error_message: Optional[str] = None,
        products_found: Optional[int] = None
    ) -> bool:
        """Обновить статус задачи"""
        try:
            data: Dict[str, Any] = {
                "status": status.value if hasattr(status, 'value') else status
            }
            
            if progress is not None:
                data["progress"] = progress
            
            if error_message:
                data["error_message"] = error_message
            
            if products_found is not None:
                data["products_found"] = products_found
            
            # Обновляем timestamps
            if status == TaskStatus.RUNNING:
                data["started_at"] = datetime.now().isoformat()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                data["completed_at"] = datetime.now().isoformat()
            
            result = self.db.table("parser_tasks").update(data).eq("id", task_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False
    
    async def get_recent_tasks(self, limit: int = 20) -> List[ParserTask]:
        """Получить последние задачи"""
        try:
            result = self.db.table("parser_tasks")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return [ParserTask(**task) for task in result.data]
            
        except Exception as e:
            logger.error(f"Failed to get recent tasks: {e}")
            return []
    
    # ===================================
    # Parsed Products
    # ===================================
    
    async def save_product(self, product: ParsedProduct) -> Optional[str]:
        """Сохранить товар"""
        try:
            data = {
                "task_id": product.task_id,
                "sku": product.sku,
                "external_id": product.external_id,
                "title": product.title,
                "description": product.description,
                "short_description": product.short_description,
                
                # Price
                "price_amount": product.price.amount if product.price else None,
                "price_currency": product.price.currency if product.price else "KZT",
                "old_price": product.price.old_price if product.price else None,
                "discount_percent": product.price.discount_percent if product.price else None,
                
                # Classification
                "category": product.category,
                "breadcrumbs": product.breadcrumbs or [],
                "brand": product.brand,
                "manufacturer": product.manufacturer,
                
                # Stock & Rating
                "stock_status": product.stock_status,
                "in_stock": product.in_stock,
                "rating": float(product.rating) if product.rating else None,
                "reviews_count": product.reviews_count,
                
                # JSON fields
                "attributes": [attr.dict() for attr in product.attributes],
                "images": [img.dict() for img in product.images],
                "seo_data": product.seo_data.dict() if product.seo_data else {},
                
                # Source
                "source_url": product.source_url,
                "source_site": product.source_site,
                "parser_type": product.parser_type.value if hasattr(product.parser_type, 'value') else product.parser_type,
                
                # Metadata
                "parsed_at": product.parsed_at.isoformat(),
                "parser_version": product.parser_version,
                "raw_html": product.raw_html if product.raw_html else None
            }
            
            result = self.db.table("parsed_products").insert(data).execute()
            
            if result.data:
                product_id = result.data[0]["id"]
                logger.info(f"Product saved: {product.title} ({product_id})")
                return product_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to save product: {e}", exc_info=True)
            return None
    
    async def save_products_batch(self, products: List[ParsedProduct]) -> int:
        """Сохранить несколько товаров"""
        saved_count = 0
        
        for product in products:
            product_id = await self.save_product(product)
            if product_id:
                saved_count += 1
        
        logger.info(f"Saved {saved_count}/{len(products)} products")
        return saved_count
    
    async def get_products(
        self,
        task_id: Optional[str] = None,
        source_site: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ParsedProduct]:
        """Получить товары с фильтрацией"""
        try:
            query = self.db.table("parsed_products").select("*")
            
            if task_id:
                query = query.eq("task_id", task_id)
            
            if source_site:
                query = query.eq("source_site", source_site)
            
            result = query.order("parsed_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            products = []
            for data in result.data:
                try:
                    # Преобразуем JSON поля обратно в модели
                    products.append(ParsedProduct(**data))
                except Exception as e:
                    logger.warning(f"Failed to parse product: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            return []
    
    async def get_product_by_id(self, product_id: str) -> Optional[ParsedProduct]:
        """Получить товар по ID"""
        try:
            result = self.db.table("parsed_products")\
                .select("*")\
                .eq("id", product_id)\
                .execute()
            
            if not result.data:
                return None
            
            return ParsedProduct(**result.data[0])
            
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None
    
    # ===================================
    # Sites Management
    # ===================================
    
    async def update_site_stats(self, domain: str, site_name: Optional[str] = None):
        """Обновить статистику сайта"""
        try:
            # Подсчитываем товары
            result = self.db.table("parsed_products")\
                .select("id", count="exact")\
                .eq("source_site", domain)\
                .execute()
            
            total_products = result.count or 0
            
            # Обновляем или создаем запись
            site_data = {
                "site_domain": domain,
                "total_products": total_products,
                "last_parsed_at": datetime.now().isoformat()
            }
            
            if site_name:
                site_data["site_name"] = site_name
            
            # Upsert
            self.db.table("parsed_sites")\
                .upsert(site_data, on_conflict="site_domain")\
                .execute()
            
            logger.info(f"Updated stats for {domain}: {total_products} products")
            
        except Exception as e:
            logger.error(f"Failed to update site stats: {e}")
    
    # ===================================
    # Statistics & Analytics
    # ===================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Получить общую статистику"""
        try:
            # Всего задач
            tasks_result = self.db.table("parser_tasks")\
                .select("id", count="exact")\
                .execute()
            
            # Всего товаров
            products_result = self.db.table("parsed_products")\
                .select("id", count="exact")\
                .execute()
            
            # Товаров по сайтам
            sites_result = self.db.table("parsed_products")\
                .select("source_site")\
                .execute()
            
            sites_count = len(set(p["source_site"] for p in sites_result.data))
            
            return {
                "total_tasks": tasks_result.count or 0,
                "total_products": products_result.count or 0,
                "total_sites": sites_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_tasks": 0,
                "total_products": 0,
                "total_sites": 0
            }


# ===================================
# Singleton для использования в модуле
# ===================================

_db_client: Optional[ParserDatabaseClient] = None


def get_parser_db_client() -> ParserDatabaseClient:
    """
    Получить singleton клиент БД парсера
    
    Returns:
        ParserDatabaseClient instance
    """
    global _db_client
    
    if _db_client is None:
        _db_client = ParserDatabaseClient()
    
    return _db_client

