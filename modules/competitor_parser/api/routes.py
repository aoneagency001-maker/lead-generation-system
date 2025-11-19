"""
API Routes для Competitor Parser
FastAPI endpoints для парсинга конкурентов
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import Response
from typing import List, Optional
import logging

from ..models import (
    ParseRequest,
    ParseResponse,
    ParsedProduct,
    ParserTask,
    TaskStatus,
    ParserType,
    ExportFormat
)
from ..services.parser_service import get_parser_service
from ..services.export_service import get_export_service
from ..database.client import get_parser_db_client

logger = logging.getLogger(__name__)

# Создаем router
router = APIRouter(
    prefix="/parser",
    tags=["Competitor Parser"]
)


@router.post("/parse", response_model=ParseResponse)
async def parse_competitor_site(
    request: ParseRequest,
    background_tasks: BackgroundTasks
):
    """
    Запустить парсинг сайта конкурента
    
    Args:
        request: Параметры парсинга
        background_tasks: FastAPI background tasks
    
    Returns:
        ParseResponse с task_id
    """
    try:
        service = get_parser_service()
        
        # Создаем задачу
        task = await service.create_parse_task(request)
        
        # Запускаем парсинг в фоне
        background_tasks.add_task(service.start_parsing, task.id)
        
        return ParseResponse(
            success=True,
            task_id=task.id,
            status=TaskStatus.PENDING,
            message=f"Parsing task created. Type: {task.parser_type}"
        )
    
    except Exception as e:
        logger.error(f"Failed to create parse task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=ParserTask)
async def get_task_status(task_id: str):
    """
    Получить статус задачи парсинга
    
    Args:
        task_id: ID задачи
    
    Returns:
        ParserTask
    """
    try:
        db = get_parser_db_client()
        task = await db.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[ParserTask])
async def get_recent_tasks(limit: int = Query(default=20, le=100)):
    """
    Получить последние задачи парсинга
    
    Args:
        limit: Максимальное количество задач
    
    Returns:
        Список задач
    """
    try:
        db = get_parser_db_client()
        tasks = await db.get_recent_tasks(limit=limit)
        return tasks
    
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products", response_model=List[ParsedProduct])
async def get_products(
    task_id: Optional[str] = None,
    source_site: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """
    Получить распарсенные товары
    
    Args:
        task_id: Фильтр по задаче
        source_site: Фильтр по сайту
        limit: Лимит записей
        offset: Смещение
    
    Returns:
        Список товаров
    """
    try:
        db = get_parser_db_client()
        
        products = await db.get_products(
            task_id=task_id,
            source_site=source_site,
            limit=limit,
            offset=offset
        )
        
        return products
    
    except Exception as e:
        logger.error(f"Failed to get products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{product_id}", response_model=ParsedProduct)
async def get_product(product_id: str):
    """
    Получить товар по ID
    
    Args:
        product_id: ID товара
    
    Returns:
        ParsedProduct
    """
    try:
        db = get_parser_db_client()
        product = await db.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_statistics():
    """
    Получить общую статистику парсинга
    
    Returns:
        Статистика
    """
    try:
        db = get_parser_db_client()
        stats = await db.get_statistics()
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Проверка здоровья парсера
    
    Returns:
        Статус
    """
    return {
        "status": "healthy",
        "module": "competitor-parser",
        "version": "0.1.0"
    }


# ===================================
# Export Endpoints
# ===================================

@router.get("/export/{format}")
async def export_products(
    format: str,
    task_id: Optional[str] = None,
    source_site: Optional[str] = None,
    limit: Optional[int] = Query(default=None, le=10000)
):
    """
    Экспорт товаров в различных форматах
    
    Args:
        format: Формат экспорта (json, csv, sql, wordpress_xml, schema_org)
        task_id: Фильтр по задаче
        source_site: Фильтр по сайту
        limit: Лимит записей
    
    Returns:
        Файл для скачивания
    """
    try:
        # Валидация формата
        try:
            export_format = ExportFormat(format)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Supported: {[f.value for f in ExportFormat]}"
            )
        
        # Экспорт
        export_service = get_export_service()
        data_bytes, filename, content_type = await export_service.export_products(
            format=export_format,
            task_id=task_id,
            source_site=source_site,
            limit=limit
        )
        
        # Возвращаем файл
        return Response(
            content=data_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

