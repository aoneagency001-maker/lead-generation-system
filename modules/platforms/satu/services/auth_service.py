"""
Satu Auth Service
Сервис авторизации через API токены
"""

import httpx
from typing import Optional
from datetime import datetime
import logging

from ..models import (
    SatuAccount,
    SatuAccountCreate,
    APITokenCredentials,
    AuthResult,
    SatuAccountStatus
)
from ..database.client import get_supabase_client
from ..api.config import settings

logger = logging.getLogger(__name__)


class SatuAuthService:
    """Сервис авторизации Satu"""
    
    def __init__(self):
        self.db = get_supabase_client()
        self.api_base_url = settings.satu_api_base_url
    
    # ===================================
    # API Token Authentication
    # ===================================
    
    async def authenticate_api_token(
        self,
        credentials: APITokenCredentials
    ) -> AuthResult:
        """
        Добавление/проверка API токена Satu.kz
        
        Args:
            credentials: API token credentials (company_name, api_token)
        
        Returns:
            AuthResult: Результат авторизации
        """
        try:
            logger.info(f"Adding Satu API token for {credentials.company_name}")
            
            # Проверяем валидность токена через test запрос
            is_valid = await self._validate_token(credentials.api_token)
            
            if not is_valid:
                return AuthResult(
                    success=False,
                    error="Invalid API token or token expired"
                )
            
            # Получаем права доступа токена
            permissions = await self._get_token_permissions(credentials.api_token)
            
            # Создаем/обновляем аккаунт в БД
            account_data = {
                "company_name": credentials.company_name,
                "api_token": credentials.api_token,
                "token_permissions": permissions,
                "status": SatuAccountStatus.ACTIVE.value,
                "last_api_call_at": datetime.now().isoformat()
            }
            
            # Проверяем существует ли аккаунт с таким токеном
            existing = self.db.table("satu_accounts").select("*").eq(
                "company_name", credentials.company_name
            ).execute()
            
            if existing.data:
                # Обновляем существующий
                result = self.db.table("satu_accounts").update(account_data).eq(
                    "company_name", credentials.company_name
                ).execute()
                account_dict = result.data[0] if result.data else None
            else:
                # Создаем новый
                result = self.db.table("satu_accounts").insert(account_data).execute()
                account_dict = result.data[0] if result.data else None
            
            if not account_dict:
                return AuthResult(
                    success=False,
                    error="Failed to save account to database"
                )
            
            account = SatuAccount(**account_dict)
            logger.info(f"API token added for {credentials.company_name}")
            
            return AuthResult(
                success=True,
                account=account
            )
            
        except Exception as e:
            logger.error(f"API token authentication error: {e}", exc_info=True)
            return AuthResult(
                success=False,
                error=str(e)
            )
    
    # ===================================
    # Token Validation
    # ===================================
    
    async def _validate_token(self, api_token: str) -> bool:
        """
        Проверить валидность API токена
        
        Args:
            api_token: API токен
        
        Returns:
            bool: True если токен валидный
        """
        try:
            # Пробуем сделать GET запрос к API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.api_base_url}/api/products",
                    headers={
                        "Authorization": f"Bearer {api_token}",
                        "Content-Type": "application/json"
                    },
                    params={"limit": 1}  # Минимальный запрос
                )
                
                # 200 или 403 (forbidden) - токен валидный, но может не быть прав
                # 401 - токен невалидный или истек
                return response.status_code in [200, 403]
                
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False
    
    async def _get_token_permissions(self, api_token: str) -> dict:
        """
        Получить права доступа токена
        
        Args:
            api_token: API токен
        
        Returns:
            dict: Права доступа
        """
        permissions = {
            "products": "unknown",
            "orders": "unknown",
            "clients": "unknown",
            "messages": "unknown"
        }
        
        try:
            # Проверяем доступ к разным endpoints
            endpoints_to_check = [
                ("products", "/api/products"),
                ("orders", "/api/orders"),
                ("clients", "/api/clients"),
            ]
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                for perm_name, endpoint in endpoints_to_check:
                    try:
                        response = await client.get(
                            f"{self.api_base_url}{endpoint}",
                            headers={
                                "Authorization": f"Bearer {api_token}",
                                "Content-Type": "application/json"
                            },
                            params={"limit": 1}
                        )
                        
                        if response.status_code == 200:
                            permissions[perm_name] = "read_write"
                        elif response.status_code == 403:
                            permissions[perm_name] = "no_access"
                        else:
                            permissions[perm_name] = "unknown"
                    except:
                        permissions[perm_name] = "unknown"
            
            return permissions
            
        except Exception as e:
            logger.error(f"Get permissions error: {e}")
            return permissions
    
    # ===================================
    # Account Management
    # ===================================
    
    async def get_account(self, account_id: str) -> Optional[SatuAccount]:
        """
        Получить аккаунт по ID
        
        Args:
            account_id: ID аккаунта
        
        Returns:
            Optional[SatuAccount]: Аккаунт или None
        """
        try:
            result = self.db.table("satu_accounts").select("*").eq("id", account_id).execute()
            
            if not result.data:
                return None
            
            return SatuAccount(**result.data[0])
            
        except Exception as e:
            logger.error(f"Get account error: {e}", exc_info=True)
            return None
    
    async def list_accounts(self, limit: int = 100) -> list[SatuAccount]:
        """
        Получить список всех аккаунтов
        
        Args:
            limit: Лимит записей
        
        Returns:
            list[SatuAccount]: Список аккаунтов
        """
        try:
            result = self.db.table("satu_accounts").select("*").limit(limit).execute()
            
            return [SatuAccount(**item) for item in result.data]
            
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
            self.db.table("satu_accounts").delete().eq("id", account_id).execute()
            logger.info(f"Account {account_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Delete account error: {e}", exc_info=True)
            return False
    
    async def update_last_api_call(self, account_id: str):
        """
        Обновить время последнего API вызова
        
        Args:
            account_id: ID аккаунта
        """
        try:
            self.db.table("satu_accounts").update({
                "last_api_call_at": datetime.now().isoformat()
            }).eq("id", account_id).execute()
        except Exception as e:
            logger.error(f"Update last API call error: {e}")



