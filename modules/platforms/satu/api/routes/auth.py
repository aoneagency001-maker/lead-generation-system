"""
Satu Auth Routes
API endpoints для авторизации
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...models import (
    APITokenCredentials,
    AuthResult,
    SatuAccount
)
from ...services.auth_service import SatuAuthService

router = APIRouter()


def get_auth_service():
    """Dependency для auth service"""
    return SatuAuthService()


@router.post("/token", response_model=AuthResult)
async def add_api_token(
    credentials: APITokenCredentials,
    auth_service: SatuAuthService = Depends(get_auth_service)
):
    """
    Добавить/проверить API токен Satu.kz
    
    - **company_name**: Название компании
    - **api_token**: API токен из настроек Satu.kz
    
    **Как получить API токен:**
    1. Войдите в свой аккаунт на satu.kz
    2. Перейдите в Настройки → Управление API-токенами
    3. Создайте новый токен с правами: Orders, Products, Groups, Clients
    4. Скопируйте токен
    """
    result = await auth_service.authenticate_api_token(credentials)
    
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error)
    
    return result


@router.get("/accounts", response_model=List[SatuAccount])
async def list_accounts(
    limit: int = 100,
    auth_service: SatuAuthService = Depends(get_auth_service)
):
    """
    Получить список всех аккаунтов Satu
    
    - **limit**: Максимальное количество записей
    """
    accounts = await auth_service.list_accounts(limit=limit)
    return accounts


@router.get("/accounts/{account_id}", response_model=SatuAccount)
async def get_account(
    account_id: str,
    auth_service: SatuAuthService = Depends(get_auth_service)
):
    """
    Получить информацию об аккаунте
    
    - **account_id**: UUID аккаунта
    """
    account = await auth_service.get_account(account_id)
    
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return account


@router.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str,
    auth_service: SatuAuthService = Depends(get_auth_service)
):
    """
    Удалить аккаунт
    
    - **account_id**: UUID аккаунта
    """
    success = await auth_service.delete_account(account_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete account")
    
    return {"success": True, "message": "Account deleted"}



