"""
OLX Parser Routes
API endpoints для парсинга
"""

from fastapi import APIRouter, HTTPException, Depends

from ...models import SearchQuery, ParserResult, OLXParsedData
from ...services.parser_service import OLXParserService

router = APIRouter()


def get_parser_service():
    """Dependency для parser service"""
    return OLXParserService()


@router.post("/search", response_model=ParserResult)
async def parse_search(
    query: SearchQuery,
    parser_service: OLXParserService = Depends(get_parser_service)
):
    """
    Запустить парсинг поиска на OLX.kz
    
    - **search_query**: Поисковый запрос (например: "iphone 15")
    - **city**: Город (по умолчанию: "almaty")
    - **category**: Категория (опционально)
    - **parser_method**: Метод парсинга (lerdem, playwright, api)
    - **max_pages**: Максимальное количество страниц (1-10)
    
    **Возвращает**: Task ID для отслеживания прогресса
    """
    result = await parser_service.parse_search(query)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return result


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    parser_service: OLXParserService = Depends(get_parser_service)
):
    """
    Получить статус задачи парсинга
    
    - **task_id**: UUID задачи
    
    **Статусы**:
    - pending: В очереди
    - running: Выполняется
    - completed: Завершено
    - failed: Ошибка
    """
    task = await parser_service.get_task_status(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.get("/results/{result_id}", response_model=OLXParsedData)
async def get_parse_results(
    result_id: str,
    parser_service: OLXParserService = Depends(get_parser_service)
):
    """
    Получить результаты парсинга
    
    - **result_id**: UUID результата (из task.result_id)
    
    **Возвращает**: Список найденных объявлений с метаданными
    """
    results = await parser_service.get_parse_results(result_id)
    
    if not results:
        raise HTTPException(status_code=404, detail="Results not found")
    
    return results


