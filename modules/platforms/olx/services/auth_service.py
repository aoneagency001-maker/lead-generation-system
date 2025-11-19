"""
OLX Auth Service
Сервис авторизации через OAuth 2.0 и Playwright
"""

import httpx
import json
import bcrypt
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

from ..models import (
    OLXAccount,
    OLXAccountCreate,
    OAuthCredentials,
    BrowserCredentials,
    AuthResult,
    OLXAccountStatus,
    OLXLoginMethod
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class OLXAuthService:
    """Сервис авторизации OLX"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.oauth_url = settings.olx_oauth_url
        
    # ===================================
    # OAuth 2.0 Authentication
    # ===================================
    
    async def authenticate_oauth(
        self,
        credentials: OAuthCredentials
    ) -> AuthResult:
        """
        Авторизация через OAuth 2.0 (Official OLX Partner API)
        
        Args:
            credentials: OAuth credentials (email, password, client_id, client_secret)
        
        Returns:
            AuthResult: Результат авторизации
        """
        try:
            logger.info(f"Attempting OAuth login for {credentials.email}")
            
            # Подготовка данных для OAuth запроса
            oauth_data = {
                "grant_type": "password",
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "username": credentials.email,
                "password": credentials.password
            }
            
            # Запрос токена
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.oauth_url,
                    data=oauth_data,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    }
                )
                
                if response.status_code != 200:
                    error_msg = f"OAuth failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return AuthResult(
                        success=False,
                        error=error_msg,
                        method=OLXLoginMethod.OAUTH
                    )
                
                token_data = response.json()
                
            # Хэшируем пароль для безопасного хранения
            password_hash = bcrypt.hashpw(
                credentials.password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Создаем/обновляем аккаунт в БД
            account_data = {
                "email": credentials.email,
                "password_hash": password_hash,
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_expires_at": (
                    datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
                ).isoformat(),
                "client_id": credentials.client_id,
                "status": OLXAccountStatus.ACTIVE.value,
                "last_login_at": datetime.now().isoformat(),
                "login_method": OLXLoginMethod.OAUTH.value
            }
            
            # Проверяем существует ли аккаунт
            existing = self.db.table("olx_accounts").select("*").eq("email", credentials.email).execute()
            
            if existing.data:
                # Обновляем существующий
                result = self.db.table("olx_accounts").update(account_data).eq("email", credentials.email).execute()
                account_dict = result.data[0] if result.data else None
            else:
                # Создаем новый
                result = self.db.table("olx_accounts").insert(account_data).execute()
                account_dict = result.data[0] if result.data else None
            
            if not account_dict:
                return AuthResult(
                    success=False,
                    error="Failed to save account to database",
                    method=OLXLoginMethod.OAUTH
                )
            
            account = OLXAccount(**account_dict)
            logger.info(f"OAuth login successful for {credentials.email}")
            
            return AuthResult(
                success=True,
                account=account,
                method=OLXLoginMethod.OAUTH
            )
            
        except Exception as e:
            logger.error(f"OAuth authentication error: {e}", exc_info=True)
            return AuthResult(
                success=False,
                error=str(e),
                method=OLXLoginMethod.OAUTH
            )
    
    # ===================================
    # Token Refresh
    # ===================================
    
    async def refresh_token(self, account_id: str) -> Optional[str]:
        """
        Обновить access token используя refresh token
        
        Args:
            account_id: ID аккаунта
        
        Returns:
            Optional[str]: Новый access token или None
        """
        try:
            # Получаем аккаунт из БД
            result = self.db.table("olx_accounts").select("*").eq("id", account_id).execute()
            
            if not result.data:
                logger.error(f"Account {account_id} not found")
                return None
            
            account_data = result.data[0]
            refresh_token = account_data.get("refresh_token")
            client_id = account_data.get("client_id")
            
            if not refresh_token or not client_id:
                logger.error("Missing refresh_token or client_id")
                return None
            
            # Запрос нового токена
            oauth_data = {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": refresh_token
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.oauth_url,
                    data=oauth_data
                )
                
                if response.status_code != 200:
                    logger.error(f"Token refresh failed: {response.status_code}")
                    return None
                
                token_data = response.json()
            
            # Обновляем токен в БД
            new_token = token_data.get("access_token")
            expires_at = (
                datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
            ).isoformat()
            
            self.db.table("olx_accounts").update({
                "access_token": new_token,
                "token_expires_at": expires_at
            }).eq("id", account_id).execute()
            
            logger.info(f"Token refreshed for account {account_id}")
            return new_token
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}", exc_info=True)
            return None
    
    # ===================================
    # Account Management
    # ===================================
    
    async def get_account(self, account_id: str) -> Optional[OLXAccount]:
        """
        Получить аккаунт по ID
        
        Args:
            account_id: ID аккаунта
        
        Returns:
            Optional[OLXAccount]: Аккаунт или None
        """
        try:
            result = self.db.table("olx_accounts").select("*").eq("id", account_id).execute()
            
            if not result.data:
                return None
            
            return OLXAccount(**result.data[0])
            
        except Exception as e:
            logger.error(f"Get account error: {e}", exc_info=True)
            return None
    
    async def list_accounts(self, limit: int = 100) -> list[OLXAccount]:
        """
        Получить список всех аккаунтов
        
        Args:
            limit: Лимит записей
        
        Returns:
            list[OLXAccount]: Список аккаунтов
        """
        try:
            result = self.db.table("olx_accounts").select("*").limit(limit).execute()
            
            return [OLXAccount(**item) for item in result.data]
            
        except Exception as e:
            logger.error(f"List accounts error: {e}", exc_info=True)
            return []
    
    async def delete_account(self, account_id: str) -> bool:
        """
        Удалить аккаунт
        
        Args:
            account_id: ID аккаунта
        
        Returns:
            bool: True если успешно
        """
        try:
            self.db.table("olx_accounts").delete().eq("id", account_id).execute()
            logger.info(f"Account {account_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Delete account error: {e}", exc_info=True)
            return False
    
    # ===================================
    # Browser Authentication (будет реализовано с Playwright)
    # ===================================
    
    async def authenticate_browser(
        self,
        credentials: BrowserCredentials
    ) -> AuthResult:
        """
        Авторизация через браузер (Playwright)
        TODO: Реализовать после добавления Playwright
        
        Args:
            credentials: Browser credentials
        
        Returns:
            AuthResult: Результат авторизации
        """
        # Placeholder - будет реализовано позже
        return AuthResult(
            success=False,
            error="Browser authentication not implemented yet",
            method=OLXLoginMethod.BROWSER
        )


