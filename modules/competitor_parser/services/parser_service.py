"""
Parser Service
Бизнес-логика парсинга
"""

import logging
import uuid
from typing import Optional, List
from datetime import datetime
import asyncio

from ..models import (
    ParsedProduct,
    ParserTask,
    ParserType,
    TaskStatus,
    ParseRequest
)
from ..parsers.universal_parser import UniversalParser
from ..parsers.satu_parser import SatuParser
from ..database.client import get_parser_db_client
from shared.event_bus import emit_event

logger = logging.getLogger(__name__)


class ParserService:
    """Сервис для управления парсингом"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self.db = get_parser_db_client()
    
    async def create_parse_task(self, request: ParseRequest) -> ParserTask:
        """
        Создать задачу парсинга
        
        Args:
            request: Запрос на парсинг
        
        Returns:
            ParserTask
        """
        # Определяем тип парсера если не указан
        parser_type = request.parser_type
        if parser_type == ParserType.UNIVERSAL:
            parser_type = self._detect_parser_type(request.url)
        
        # Создаем задачу
        task = ParserTask(
            id=str(uuid.uuid4()),
            url=request.url,
            parser_type=parser_type,
            status=TaskStatus.PENDING,
            max_pages=request.max_pages,
            created_at=datetime.now()
        )
        
        # Сохраняем в БД
        await self.db.create_task(task)
        
        logger.info(f"Created parse task: {task.id} ({parser_type})")
        
        return task
    
    async def start_parsing(self, task_id: str) -> bool:
        """
        Запустить парсинг в фоне
        
        Args:
            task_id: ID задачи
        
        Returns:
            True если запущено успешно
        """
        try:
            # Запускаем в фоновом task
            asyncio.create_task(self._run_parsing_task(task_id))
            return True
        except Exception as e:
            logger.error(f"Failed to start parsing task {task_id}: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[ParserTask]:
        """
        Получить статус задачи
        
        Args:
            task_id: ID задачи
        
        Returns:
            ParserTask или None
        """
        return await self.db.get_task(task_id)
    
    async def get_task_products(self, task_id: str) -> List[ParsedProduct]:
        """
        Получить товары по задаче
        
        Args:
            task_id: ID задачи
        
        Returns:
            Список товаров
        """
        return await self.db.get_products(task_id=task_id)
    
    async def get_all_products(
        self,
        source_site: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ParsedProduct]:
        """
        Получить все товары с фильтрацией
        
        Args:
            source_site: Фильтр по сайту
            limit: Лимит записей
            offset: Смещение
        
        Returns:
            Список товаров
        """
        return await self.db.get_products(
            source_site=source_site,
            limit=limit,
            offset=offset
        )
    
    # ===================================
    # Internal Methods
    # ===================================
    
    async def _run_parsing_task(self, task_id: str):
        """
        Выполнить задачу парсинга
        
        Args:
            task_id: ID задачи
        """
        start_time = datetime.now()
        
        try:
            # Получаем задачу
            task = await self.db.get_task(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            # Обновляем статус на RUNNING
            await self.db.update_task_status(
                task_id,
                TaskStatus.RUNNING,
                progress=10
            )
            
            logger.info(f"🚀 Starting parsing task {task_id}: {task.url}")
            
            # Создаем парсер
            parser = self._create_parser(task.parser_type)
            
            # Парсим
            products = []
            
            async with parser:
                # Обновляем прогресс
                await self.db.update_task_status(task_id, TaskStatus.RUNNING, progress=30)
                
                # Определяем: категория или товар
                if self._is_category_url(task.url):
                    logger.info("Parsing category page")
                    products = await parser.parse_category_page(task.url, task.max_pages)
                else:
                    logger.info("Parsing product page")
                    product = await parser.parse_product_page(task.url)
                    if product:
                        products = [product]
                
                # Обновляем прогресс
                await self.db.update_task_status(
                    task_id,
                    TaskStatus.RUNNING,
                    progress=70,
                    products_found=len(products)
                )
            
            # Сохраняем товары в БД
            if products:
                # Добавляем task_id к каждому товару
                for product in products:
                    product.task_id = task_id
                
                saved_count = await self.db.save_products_batch(products)
                
                logger.info(f"Saved {saved_count}/{len(products)} products")
            
            # Обновляем статистику сайта
            if products:
                domain = products[0].source_site
                await self.db.update_site_stats(domain)
            
            # Завершаем задачу
            duration = (datetime.now() - start_time).total_seconds()
            
            await self.db.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                progress=100,
                products_found=len(products)
            )
            
            logger.info(f"✅ Task {task_id} completed in {duration:.2f}s: {len(products)} products")
            
            # Emit event для будущих модулей
            try:
                emit_event("parser.completed", {
                    "task_id": task_id,
                    "url": task.url,
                    "products_count": len(products),
                    "duration": duration
                })
            except Exception as e:
                logger.warning(f"Failed to emit event: {e}")
        
        except Exception as e:
            logger.error(f"❌ Parsing task {task_id} failed: {e}", exc_info=True)
            
            # Обновляем задачу с ошибкой
            await self.db.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=str(e)
            )
    
    def _create_parser(self, parser_type: ParserType):
        """
        Создать парсер по типу
        
        Args:
            parser_type: Тип парсера
        
        Returns:
            Parser instance
        """
        if parser_type == ParserType.SATU:
            return SatuParser()
        else:
            return UniversalParser()
    
    def _detect_parser_type(self, url: str) -> ParserType:
        """
        Определить тип парсера по URL
        
        Args:
            url: URL
        
        Returns:
            ParserType
        """
        url_lower = url.lower()
        
        if "satu.kz" in url_lower:
            return ParserType.SATU
        elif "kaspi.kz" in url_lower:
            return ParserType.KASPI
        else:
            return ParserType.UNIVERSAL
    
    def _is_category_url(self, url: str) -> bool:
        """
        Определить, это категория или товар
        
        Args:
            url: URL
        
        Returns:
            True если категория
        """
        category_indicators = [
            '/catalog', '/category', '/products', '/list',
            '/c/', '/cat/', '/shop/'
        ]
        
        return any(indicator in url.lower() for indicator in category_indicators)


# ===================================
# Singleton
# ===================================

_parser_service: Optional[ParserService] = None


def get_parser_service() -> ParserService:
    """
    Получить singleton ParserService
    
    Returns:
        ParserService instance
    """
    global _parser_service
    
    if _parser_service is None:
        _parser_service = ParserService()
    
    return _parser_service

