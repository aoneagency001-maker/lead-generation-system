"""
API Routes для управления модулями платформ
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
import httpx

from shared.models import PlatformModule, ModuleStatus, PipelineStage, Platform
from core.database.supabase_client import get_supabase_client

router = APIRouter(prefix="/modules", tags=["modules"])


# ===================================
# Хелперы
# ===================================

async def check_module_health(module: PlatformModule) -> bool:
    """Проверка здоровья модуля"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{module.api_url}{module.health_endpoint}")
            return response.status_code == 200
    except Exception:
        return False


# ===================================
# GET Routes
# ===================================

@router.get("/", response_model=List[PlatformModule])
async def get_modules(
    status: Optional[ModuleStatus] = None,
    platform: Optional[Platform] = None
):
    """
    Получить список всех модулей

    Query params:
    - status: фильтр по статусу (active, testing, inactive, archived)
    - platform: фильтр по платформе (olx, satu, kaspi и т.д.)
    """
    supabase = get_supabase_client()

    query = supabase.table("platform_modules").select("*")

    if status:
        query = query.eq("status", status.value)
    if platform:
        query = query.eq("platform", platform.value)

    query = query.order("order", desc=False)

    response = query.execute()

    return response.data


@router.get("/{module_id}", response_model=PlatformModule)
async def get_module(module_id: str):
    """Получить модуль по ID"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").select("*").eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


@router.get("/{module_id}/health")
async def check_health(module_id: str):
    """Проверить здоровье модуля"""
    module = await get_module(module_id)
    is_healthy = await check_module_health(module)

    # Обновить статус здоровья
    supabase = get_supabase_client()
    supabase.table("platform_modules").update({
        "is_healthy": is_healthy,
        "last_health_check": datetime.utcnow().isoformat()
    }).eq("id", module_id).execute()

    return {
        "module_id": module_id,
        "is_healthy": is_healthy,
        "checked_at": datetime.utcnow().isoformat()
    }


# ===================================
# POST Routes
# ===================================

@router.post("/", response_model=PlatformModule)
async def create_module(module: PlatformModule):
    """Создать новый модуль"""
    supabase = get_supabase_client()

    module_dict = module.model_dump(exclude={'id', 'created_at', 'updated_at'})

    response = supabase.table("platform_modules").insert(module_dict).execute()

    return response.data[0]


# ===================================
# PATCH Routes
# ===================================

@router.patch("/{module_id}/status", response_model=PlatformModule)
async def update_status(module_id: str, status: ModuleStatus):
    """Обновить статус модуля"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").update({
        "status": status.value,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


@router.patch("/{module_id}/pipeline-stage", response_model=PlatformModule)
async def update_pipeline_stage(module_id: str, pipeline_stage: PipelineStage):
    """Обновить стратегический этап модуля"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").update({
        "pipeline_stage": pipeline_stage.value,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


@router.patch("/{module_id}/order", response_model=PlatformModule)
async def update_order(module_id: str, order: int):
    """Обновить порядок отображения модуля в статусном Kanban"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").update({
        "order": order,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


@router.patch("/{module_id}/pipeline-order", response_model=PlatformModule)
async def update_pipeline_order(module_id: str, pipeline_order: int):
    """Обновить порядок отображения модуля в стратегическом Kanban"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").update({
        "pipeline_order": pipeline_order,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


@router.patch("/{module_id}", response_model=PlatformModule)
async def update_module(module_id: str, updates: dict):
    """Обновить модуль"""
    supabase = get_supabase_client()

    updates["updated_at"] = datetime.utcnow().isoformat()

    response = supabase.table("platform_modules").update(updates).eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return response.data[0]


# ===================================
# DELETE Routes
# ===================================

@router.delete("/{module_id}")
async def delete_module(module_id: str):
    """Удалить модуль"""
    supabase = get_supabase_client()

    response = supabase.table("platform_modules").delete().eq("id", module_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Module not found")

    return {"message": "Module deleted successfully", "id": module_id}


# ===================================
# Batch Operations
# ===================================

@router.post("/batch/reorder")
async def batch_reorder(module_orders: List[dict]):
    """
    Массовое изменение порядка модулей

    Body: [{"id": "uuid1", "order": 0}, {"id": "uuid2", "order": 1}, ...]
    """
    supabase = get_supabase_client()

    for item in module_orders:
        supabase.table("platform_modules").update({
            "order": item["order"],
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", item["id"]).execute()

    return {"message": "Modules reordered successfully", "count": len(module_orders)}


@router.post("/batch/health-check")
async def batch_health_check():
    """Проверить здоровье всех активных модулей"""
    modules = await get_modules(status=ModuleStatus.ACTIVE)

    results = []
    for module in modules:
        is_healthy = await check_module_health(module)

        # Обновить статус
        supabase = get_supabase_client()
        supabase.table("platform_modules").update({
            "is_healthy": is_healthy,
            "last_health_check": datetime.utcnow().isoformat()
        }).eq("id", module.id).execute()

        results.append({
            "module_id": module.id,
            "name": module.name,
            "is_healthy": is_healthy
        })

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "total": len(results),
        "healthy": sum(1 for r in results if r["is_healthy"]),
        "unhealthy": sum(1 for r in results if not r["is_healthy"]),
        "results": results
    }
