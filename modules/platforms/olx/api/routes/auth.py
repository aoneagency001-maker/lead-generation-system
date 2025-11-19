"""
OLX Auth Routes
API endpoints для авторизации
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ...models import (
    OAuthCredentials,
    BrowserCredentials,
    AuthResult,
    OLXAccount
)
from ...services.auth_service import OLXAuthService

router = APIRouter()


def get_auth_service():
    """Dependency для auth service"""
    return OLXAuthService()


@router.post("/oauth/login", response_model=AuthResult)
async def oauth_login(
    credentials: OAuthCredentials,
    auth_service: OLXAuthService = Depends(get_auth_service)
):
    """
    OAuth 2.0 авторизация через официальный OLX Partner API
    
    - **email**: Email аккаунта OLX
    - **password**: Пароль
    - **client_id**: OLX API Client ID
    - **client_secret**: OLX API Client Secret
    """
    result = await auth_service.authenticate_oauth(credentials)
    
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error)
    
    return result


@router.post("/browser/login", response_model=AuthResult)
async def browser_login(
    credentials: BrowserCredentials,
    auth_service: OLXAuthService = Depends(get_auth_service)
):
    """
    Browser авторизация через Playwright
    
    - **email**: Email аккаунта OLX
    - **password**: Пароль
    - **proxy_url**: (Optional) URL прокси
    
    **Note**: Пока не реализовано. Требует установки Playwright.
    """
    result = await auth_service.authenticate_browser(credentials)
    
    if not result.success:
        raise HTTPException(status_code=401, detail=result.error)
    
    return result


@router.get("/accounts", response_model=List[OLXAccount])
async def list_accounts(
    limit: int = 100,
    auth_service: OLXAuthService = Depends(get_auth_service)
):
    """
    Получить список всех аккаунтов OLX
    
    - **limit**: Максимальное количество записей
    """
    accounts = await auth_service.list_accounts(limit=limit)
    return accounts


@router.get("/accounts/{account_id}", response_model=OLXAccount)
async def get_account(
    account_id: str,
    auth_service: OLXAuthService = Depends(get_auth_service)
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
    auth_service: OLXAuthService = Depends(get_auth_service)
):
    """
    Удалить аккаунт
    
    - **account_id**: UUID аккаунта
    """
    success = await auth_service.delete_account(account_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete account")
    
    return {"success": True, "message": "Account deleted"}


@router.post("/accounts/{account_id}/refresh-token")
async def refresh_token(
    account_id: str,
    auth_service: OLXAuthService = Depends(get_auth_service)
):
    """
    Обновить access token
    
    - **account_id**: UUID аккаунта
    """
    new_token = await auth_service.refresh_token(account_id)
    
    if not new_token:
        raise HTTPException(status_code=401, detail="Failed to refresh token")
    
    return {"success": True, "access_token": new_token}


