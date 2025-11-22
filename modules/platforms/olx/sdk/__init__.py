"""
OLX Module SDK
Python клиент для интеграции с OLX модулем
"""

import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class OLXClient:
    """
    Python SDK для OLX модуля
    
    Example:
        ```python
        from modules.platforms.olx.sdk import OLXClient
        
        client = OLXClient("http://localhost:8001")
        
        # Авторизация
        result = await client.auth.oauth_login(email, password)
        
        # Парсинг
        task = await client.parser.search("iphone 15", city="almaty")
        results = await client.parser.get_results(task["task_id"])
        
        # Публикация
        ad = await client.ads.create(
            title="iPhone 15 Pro",
            description="Отличное состояние",
            price=450000,
            account_id="..."
        )
        ```
    """
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Инициализация клиента
        
        Args:
            base_url: URL OLX модуля API
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
        # Подмодули
        self.auth = AuthAPI(self.client)
        self.parser = ParserAPI(self.client)
        self.ads = AdsAPI(self.client)
    
    async def close(self):
        """Закрыть HTTP клиент"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class AuthAPI:
    """API для авторизации"""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def oauth_login(
        self,
        email: str,
        password: str
    ) -> Dict[str, Any]:
        """
        OAuth авторизация
        
        Args:
            email: Email OLX аккаунта
            password: Пароль
        
        Returns:
            dict: Данные аккаунта с токенами
        """
        response = await self.client.post("/auth/oauth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        return response.json()
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """Получить список аккаунтов"""
        response = await self.client.get("/auth/accounts")
        response.raise_for_status()
        return response.json()
    
    async def get_account(self, account_id: str) -> Dict[str, Any]:
        """Получить аккаунт по ID"""
        response = await self.client.get(f"/auth/accounts/{account_id}")
        response.raise_for_status()
        return response.json()
    
    async def delete_account(self, account_id: str) -> Dict[str, Any]:
        """Удалить аккаунт"""
        response = await self.client.delete(f"/auth/accounts/{account_id}")
        response.raise_for_status()
        return response.json()


class ParserAPI:
    """API для парсинга"""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def search(
        self,
        search_query: str,
        city: str = "almaty",
        category: Optional[str] = None,
        max_pages: int = 1,
        parser_method: str = "lerdem"
    ) -> Dict[str, Any]:
        """
        Запустить парсинг поиска
        
        Args:
            search_query: Поисковый запрос
            city: Город (по умолчанию: almaty)
            category: Категория (опционально)
            max_pages: Максимальное количество страниц (1-10)
            parser_method: Метод парсинга (lerdem, playwright, api)
        
        Returns:
            dict: Результат с task_id
        """
        response = await self.client.post("/parser/search", json={
            "search_query": search_query,
            "city": city,
            "category": category,
            "max_pages": max_pages,
            "parser_method": parser_method
        })
        response.raise_for_status()
        return response.json()
    
    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Получить статус задачи парсинга"""
        response = await self.client.get(f"/parser/tasks/{task_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_results(self, result_id: str) -> Dict[str, Any]:
        """Получить результаты парсинга"""
        response = await self.client.get(f"/parser/results/{result_id}")
        response.raise_for_status()
        return response.json()
    
    async def wait_for_results(
        self,
        task_id: str,
        timeout: int = 60,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Дождаться завершения парсинга и получить результаты
        
        Args:
            task_id: ID задачи
            timeout: Максимальное время ожидания (секунды)
            poll_interval: Интервал проверки (секунды)
        
        Returns:
            dict: Результаты парсинга
        """
        import asyncio
        
        elapsed = 0
        while elapsed < timeout:
            task = await self.get_task(task_id)
            
            if task["status"] == "completed":
                return await self.get_results(task["result_id"])
            elif task["status"] == "failed":
                raise Exception(f"Parsing failed: {task.get('error_message')}")
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        raise TimeoutError(f"Parsing timeout after {timeout} seconds")


class AdsAPI:
    """API для работы с объявлениями"""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def create(
        self,
        title: str,
        description: str,
        price: Optional[float],
        category: str,
        city: str,
        account_id: str,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создать объявление
        
        Args:
            title: Заголовок
            description: Описание
            price: Цена (опционально)
            category: Категория
            city: Город
            account_id: ID аккаунта
            images: Список URLs изображений
            metadata: Дополнительные поля
        
        Returns:
            dict: Результат публикации
        """
        response = await self.client.post(f"/ads?account_id={account_id}", json={
            "title": title,
            "description": description,
            "price": price,
            "category": category,
            "city": city,
            "images": images or [],
            "metadata": metadata or {}
        })
        response.raise_for_status()
        return response.json()
    
    async def get(self, ad_id: str) -> Dict[str, Any]:
        """Получить объявление по ID"""
        response = await self.client.get(f"/ads/{ad_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_status(
        self,
        ad_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Обновить статус объявления
        
        Args:
            ad_id: ID объявления
            status: Новый статус (draft, published, paused, expired, deleted)
        """
        response = await self.client.patch(f"/ads/{ad_id}/status", json={"status": status})
        response.raise_for_status()
        return response.json()


__all__ = ["OLXClient"]



