"""
Satu Module SDK
Python клиент для интеграции с Satu модулем
"""

import httpx
from typing import List, Optional, Dict, Any


class SatuClient:
    """
    Python SDK для Satu модуля
    
    Example:
        ```python
        from modules.platforms.satu.sdk import SatuClient
        
        client = SatuClient("http://localhost:8002")
        
        # Авторизация
        account = await client.auth.login(api_token="your_token")
        
        # Парсинг
        task = await client.parser.search("сварочный аппарат")
        results = await client.parser.get_results(task["task_id"])
        
        # Публикация товара
        product = await client.products.create(
            title="Сварочный аппарат Ресанта",
            description="Инверторный",
            price=85000,
            quantity=5,
            account_id="..."
        )
        ```
    """
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Инициализация клиента
        
        Args:
            base_url: URL Satu модуля API
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)
        
        # Подмодули
        self.auth = AuthAPI(self.client)
        self.parser = ParserAPI(self.client)
        self.products = ProductsAPI(self.client)
    
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
    
    async def login(
        self,
        api_token: str,
        company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Авторизация через API токен
        
        Args:
            api_token: API токен Satu.kz
            company_id: ID компании (опционально)
        
        Returns:
            dict: Данные аккаунта
        """
        response = await self.client.post("/auth/token", json={
            "api_token": api_token,
            "company_id": company_id
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


class ParserAPI:
    """API для парсинга"""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def search(
        self,
        search_query: str,
        category: Optional[str] = None,
        max_pages: int = 1,
        parser_method: str = "playwright"
    ) -> Dict[str, Any]:
        """
        Запустить парсинг поиска
        
        Args:
            search_query: Поисковый запрос
            category: Категория (опционально)
            max_pages: Максимальное количество страниц (1-10)
            parser_method: Метод парсинга (playwright, api)
        
        Returns:
            dict: Результат с task_id
        """
        response = await self.client.post("/parser/search", json={
            "search_query": search_query,
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


class ProductsAPI:
    """API для работы с товарами"""
    
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
    
    async def create(
        self,
        title: str,
        description: str,
        price: float,
        quantity: int,
        category: str,
        account_id: str,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Создать товар
        
        Args:
            title: Название
            description: Описание
            price: Цена
            quantity: Количество
            category: Категория
            account_id: ID аккаунта
            images: Список URLs изображений
            metadata: Дополнительные поля
        
        Returns:
            dict: Результат публикации
        """
        response = await self.client.post(f"/products?account_id={account_id}", json={
            "title": title,
            "description": description,
            "price": price,
            "quantity": quantity,
            "category": category,
            "images": images or [],
            "metadata": metadata or {}
        })
        response.raise_for_status()
        return response.json()
    
    async def get(self, product_id: str) -> Dict[str, Any]:
        """Получить товар по ID"""
        response = await self.client.get(f"/products/{product_id}")
        response.raise_for_status()
        return response.json()
    
    async def update_status(
        self,
        product_id: str,
        status: str
    ) -> Dict[str, Any]:
        """
        Обновить статус товара
        
        Args:
            product_id: ID товара
            status: Новый статус (draft, published, paused, out_of_stock, deleted)
        """
        response = await self.client.patch(f"/products/{product_id}/status", json={"status": status})
        response.raise_for_status()
        return response.json()
    
    async def update_quantity(
        self,
        product_id: str,
        quantity: int
    ) -> Dict[str, Any]:
        """
        Обновить количество товара
        
        Args:
            product_id: ID товара
            quantity: Новое количество
        """
        response = await self.client.patch(f"/products/{product_id}/quantity", json={"quantity": quantity})
        response.raise_for_status()
        return response.json()


__all__ = ["SatuClient"]



