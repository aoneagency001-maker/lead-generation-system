"""
Yandex.Metrika API Client
Клиент для работы с API Яндекс.Метрики

Использует OAuth токен из переменной окружения YANDEX_METRIKA_TOKEN.
Не использует OAuth flow, только готовый токен.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime
import httpx

logger = logging.getLogger(__name__)

# API URLs
MANAGEMENT_API_BASE = "https://api-metrika.yandex.net/management/v1"
REPORTING_API_BASE = "https://api-metrika.yandex.net/stat/v1/data"
LOGS_API_BASE = "https://api-metrika.yandex.net/logs/v1/export"

# Timeouts
REQUEST_TIMEOUT = 30.0
LOGS_TIMEOUT = 60.0


class YandexMetrikaError(Exception):
    """Базовое исключение для ошибок Яндекс.Метрики"""
    pass


class YandexMetrikaAuthError(YandexMetrikaError):
    """Ошибка авторизации"""
    pass


class YandexMetrikaAPIError(YandexMetrikaError):
    """Ошибка API запроса"""
    def __init__(self, message: str, code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.code = code
        self.response = response


class YandexMetrikaClient:
    """
    Клиент для работы с API Яндекс.Метрики
    
    Использует OAuth токен из переменной окружения YANDEX_METRIKA_TOKEN.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            token: OAuth токен. Если не указан, берется из YANDEX_METRIKA_TOKEN
        """
        self.token = token or os.getenv("YANDEX_METRIKA_TOKEN")
        
        if self.token:
            # Убираем лишние пробелы
            self.token = self.token.strip()
        
        if not self.token:
            raise YandexMetrikaAuthError(
                "YANDEX_METRIKA_TOKEN не установлен. "
                "Установите переменную окружения YANDEX_METRIKA_TOKEN"
            )
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запросов"""
        return {
            "Authorization": f"OAuth {self.token}",
            "Content-Type": "application/json"
        }
    
    async def get_counters(self) -> List[Dict[str, Any]]:
        """
        Получить список всех доступных счетчиков
        
        Returns:
            Список словарей с информацией о счетчиках:
            [
                {
                    "id": 12345678,
                    "name": "VesselGroup",
                    "site": "https://example.com",
                    ...
                },
                ...
            ]
        
        Raises:
            YandexMetrikaAuthError: Если токен невалидный
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        url = f"{MANAGEMENT_API_BASE}/counters"
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 401:
                    raise YandexMetrikaAuthError(
                        "Неверный токен авторизации. Проверьте YANDEX_METRIKA_TOKEN"
                    )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка API: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                # Устанавливаем правильную кодировку для ответа
                response.encoding = 'utf-8'
                data = response.json()
                counters = data.get("counters", [])
                
                logger.info(f"Получено счетчиков: {len(counters)}")
                
                return counters
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к API Яндекс.Метрики")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")
    
    async def get_counter_info(self, counter_id: int) -> Dict[str, Any]:
        """
        Получить детальную информацию о счетчике
        
        Args:
            counter_id: ID счетчика
        
        Returns:
            Словарь с информацией о счетчике:
            {
                "id": 12345678,
                "name": "VesselGroup",
                "site": "https://example.com",
                "code_status": "CS_OK",
                "permission": "view",
                ...
            }
        
        Raises:
            YandexMetrikaAuthError: Если токен невалидный
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        url = f"{MANAGEMENT_API_BASE}/counter/{counter_id}"
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                
                if response.status_code == 401:
                    raise YandexMetrikaAuthError(
                        "Неверный токен авторизации. Проверьте YANDEX_METRIKA_TOKEN"
                    )
                
                if response.status_code == 404:
                    raise YandexMetrikaAPIError(
                        f"Счетчик {counter_id} не найден",
                        code=404
                    )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка API: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                response.encoding = 'utf-8'
                data = response.json()
                counter = data.get("counter", {})
                
                logger.info(f"Получена информация о счетчике {counter_id}")
                
                return counter
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к API Яндекс.Метрики")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")
    
    async def get_visitors_by_date(
        self,
        counter_id: int,
        date1: str,
        date2: str
    ) -> Dict[str, Any]:
        """
        Получить уникальных посетителей по дням
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
        
        Returns:
            Отчет с данными по дням
        """
        return await self.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits", "ym:s:users", "ym:s:pageviews"],
            date1=date1,
            date2=date2,
            dimensions=["ym:s:date"]
        )
    
    async def get_traffic_sources(
        self,
        counter_id: int,
        date1: str,
        date2: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Получить источники трафика (utm_source, referrer)
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с источниками трафика
        """
        return await self.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits", "ym:s:users"],
            date1=date1,
            date2=date2,
            dimensions=["ym:s:UTMSource", "ym:s:referer"]
        )
    
    async def get_search_queries(
        self,
        counter_id: int,
        date1: str,
        date2: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Получить поисковые запросы
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Отчет с поисковыми запросами
        """
        return await self.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits"],
            date1=date1,
            date2=date2,
            dimensions=["ym:s:searchPhrase"]
        )
    
    async def get_search_queries_with_landing_pages(
        self,
        counter_id: int,
        date1: str,
        date2: str,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Получить поисковые запросы вместе со страницами входа
        
        Пробует несколько вариантов dimensions для получения связки "запрос → страница входа"
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов (до 10000)
        
        Returns:
            Отчет с данными: запрос, страница входа, визиты
        """
        # Вариант 1: searchPhrase + startURL (страница входа)
        try:
            result = await self.get_report(
                counter_id=counter_id,
                metrics=["ym:s:visits", "ym:s:users"],
                date1=date1,
                date2=date2,
                dimensions=["ym:s:searchPhrase", "ym:s:startURL"]
            )
            if result.get("data"):
                logger.info("✅ Успешно: searchPhrase + startURL")
                return result
        except Exception as e:
            logger.warning(f"⚠️ Вариант 1 не сработал: {e}")
        
        # Вариант 2: searchPhrase + pv:URL (URL просмотра)
        try:
            result = await self.get_report(
                counter_id=counter_id,
                metrics=["ym:s:visits"],
                date1=date1,
                date2=date2,
                dimensions=["ym:s:searchPhrase", "ym:pv:URL"]
            )
            if result.get("data"):
                logger.info("✅ Успешно: searchPhrase + pv:URL")
                return result
        except Exception as e:
            logger.warning(f"⚠️ Вариант 2 не сработал: {e}")
        
        # Вариант 3: searchPhrase + landingPage (если поддерживается)
        try:
            result = await self.get_report(
                counter_id=counter_id,
                metrics=["ym:s:visits"],
                date1=date1,
                date2=date2,
                dimensions=["ym:s:searchPhrase", "ym:s:landingPage"]
            )
            if result.get("data"):
                logger.info("✅ Успешно: searchPhrase + landingPage")
                return result
        except Exception as e:
            logger.warning(f"⚠️ Вариант 3 не сработал: {e}")
        
        # Если ничего не сработало, возвращаем пустой результат
        logger.warning("❌ Не удалось получить landing pages ни одним способом")
        return {"data": []}
    
    async def get_recent_visits(
        self,
        counter_id: int,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Получить последние посещения с детальной информацией
        
        Использует Reporting API с максимальным количеством dimensions для получения
        информации о каждом визите: IP, устройство, время, количество страниц, время окончания
        
        Args:
            counter_id: ID счетчика
            days: Количество дней назад (по умолчанию 7)
            limit: Лимит результатов (по умолчанию 50)
        
        Returns:
            Список словарей с информацией о посещениях:
            [
                {
                    "date": "2025-11-22",
                    "time": "14:30:25",
                    "ip_address": "192.168.1.1",
                    "device": "desktop",
                    "browser": "Chrome",
                    "os": "Windows",
                    "country": "Казахстан",
                    "city": "Алматы",
                    "start_url": "https://example.com/page",
                    "referer": "https://google.com",
                    "pageviews": 5,
                    "duration": 120,
                    "is_new_user": True
                },
                ...
            ]
        """
        from datetime import datetime, timedelta
        
        date_to = datetime.now().date()
        date_from = date_to - timedelta(days=days)
        
        try:
            # Получаем данные с максимальным количеством dimensions
            result = await self.get_report(
                counter_id=counter_id,
                metrics=[
                    "ym:s:visits",
                    "ym:s:pageviews",
                    "ym:s:avgVisitDurationSeconds"
                ],
                date1=date_from.isoformat(),
                date2=date_to.isoformat(),
                dimensions=[
                    "ym:s:date",
                    "ym:s:dateTime",
                    "ym:s:startURL",
                    "ym:s:referer",
                    "ym:s:deviceCategory",
                    "ym:s:browser",
                    "ym:s:operatingSystem",
                    "ym:s:regionCountry",
                    "ym:s:regionCity",
                    "ym:s:isNewUser"
                    # Примечание: ym:s:clientID недоступен через Reporting API
                    # Используем комбинацию параметров для идентификации посетителя
                ]
            )
            
            if not result.get("data"):
                logger.warning("Нет данных о посещениях")
                return []
            
            logger.info(f"Получено {len(result['data'])} строк данных из API")
            
            # Преобразуем данные в нужный формат
            visits_raw = []
            for row in result["data"][:limit * 3]:  # Берем больше для группировки
                dimensions = row.get("dimensions", [])
                metrics = row.get("metrics", [])
                
                # Проверяем количество dimensions (должно быть 10)
                if not dimensions or len(dimensions) < 10:
                    continue
                
                # Извлекаем данные из dimensions
                date_str = dimensions[0].get("name") if isinstance(dimensions[0], dict) else dimensions[0]
                datetime_str = dimensions[1].get("name") if isinstance(dimensions[1], dict) else dimensions[1]
                start_url = dimensions[2].get("name") if isinstance(dimensions[2], dict) else dimensions[2]
                referer = dimensions[3].get("name") if isinstance(dimensions[3], dict) else dimensions[3]
                device = dimensions[4].get("name") if isinstance(dimensions[4], dict) else dimensions[4]
                browser = dimensions[5].get("name") if isinstance(dimensions[5], dict) else dimensions[5]
                os = dimensions[6].get("name") if isinstance(dimensions[6], dict) else dimensions[6]
                country = dimensions[7].get("name") if isinstance(dimensions[7], dict) else dimensions[7]
                city = dimensions[8].get("name") if isinstance(dimensions[8], dict) else dimensions[8]
                is_new_user = dimensions[9].get("name") if isinstance(dimensions[9], dict) else dimensions[9]
                
                # ClientID недоступен через Reporting API, создаем уникальный идентификатор
                # из комбинации параметров для группировки посещений одного посетителя
                # Используем: browser + os + device + country + city
                client_id = f"{browser}_{os}_{device}_{country}_{city}".lower().replace(" ", "_")
                
                # Извлекаем метрики
                visits_count = int(metrics[0]) if len(metrics) > 0 else 0
                pageviews = int(metrics[1]) if len(metrics) > 1 else 0
                duration = int(metrics[2]) if len(metrics) > 2 else 0
                
                # Парсим дату и время
                time_str = ""
                if datetime_str:
                    try:
                        dt = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
                        time_str = dt.strftime("%H:%M:%S")
                    except:
                        time_str = datetime_str.split("T")[1][:8] if "T" in datetime_str else ""
                
                visits_raw.append({
                    "date": date_str,
                    "time": time_str,
                    "datetime_full": datetime_str,  # Для сортировки
                    "ip_address": "N/A",  # IP недоступен через Reporting API, нужен Logs API
                    "device": device or "Unknown",
                    "browser": browser or "Unknown",
                    "os": os or "Unknown",
                    "country": country or "Unknown",
                    "city": city or "Unknown",
                    "start_url": start_url or "",
                    "referer": referer or "Direct",
                    "pageviews": pageviews,
                    "duration": duration,  # в секундах
                    "is_new_user": is_new_user == "Yes" if isinstance(is_new_user, str) else bool(is_new_user),
                    "visits": visits_count,
                    "client_id": client_id or "unknown"
                })
            
            # Группируем по client_id и считаем номер посещения
            # Сортируем все визиты по времени (старые первыми для правильного подсчета)
            visits_raw.sort(key=lambda x: (x["date"], x["time"]))
            
            # Подсчитываем номер посещения для каждого клиента
            client_visit_counts = {}  # {client_id: count}
            visits = []
            
            for visit in visits_raw:
                client_id = visit["client_id"]
                
                # Увеличиваем счетчик для этого клиента
                if client_id not in client_visit_counts:
                    client_visit_counts[client_id] = 0
                client_visit_counts[client_id] += 1
                
                # Добавляем номер посещения
                visit["visit_number"] = client_visit_counts[client_id]
                
                # Удаляем временное поле
                del visit["datetime_full"]
                
                visits.append(visit)
            
            # Сортируем по дате и времени (новые первыми) для отображения
            visits.sort(key=lambda x: (x["date"], x["time"]), reverse=True)
            
            return visits[:limit]
            
        except Exception as e:
            logger.error(f"Ошибка получения последних посещений: {e}", exc_info=True)
            return []
    
    async def get_landing_pages_by_search(
        self,
        counter_id: int,
        search_phrase: str,
        date1: str,
        date2: str,
        limit: int = 5
    ) -> List[str]:
        """
        Получить страницы входа для конкретного поискового запроса
        
        Args:
            counter_id: ID счетчика
            search_phrase: Поисковый запрос
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
            limit: Лимит результатов
        
        Returns:
            Список URL страниц входа
        """
        try:
            # Используем комбинированный запрос: searchPhrase + URL
            # Это более эффективно, чем отдельный запрос с фильтром
            result = await self.get_report(
                counter_id=counter_id,
                metrics=["ym:s:visits"],
                date1=date1,
                date2=date2,
                dimensions=["ym:s:searchPhrase", "ym:pv:URL"]
            )
            
            # Извлекаем URL для конкретного запроса
            landing_pages = []
            if result.get("data"):
                for row in result["data"]:
                    dimensions = row.get("dimensions", [])
                    if not dimensions or len(dimensions) < 2:
                        continue
                    
                    # Первое измерение - поисковый запрос
                    query_dim = dimensions[0]
                    query_text = query_dim.get("name") if isinstance(query_dim, dict) else query_dim
                    
                    # Второе измерение - URL
                    url_dim = dimensions[1]
                    url = url_dim.get("name") if isinstance(url_dim, dict) else url_dim
                    
                    # Проверяем, что запрос совпадает (без учета регистра)
                    if query_text and url and query_text.lower() == search_phrase.lower():
                        if url not in landing_pages:
                            landing_pages.append(url)
                            if len(landing_pages) >= limit:
                                break
            
            return landing_pages
        except Exception as e:
            # Если не удалось получить landing pages, возвращаем пустой список
            logger.warning(f"Не удалось получить landing pages для '{search_phrase}': {e}")
            return []
    
    async def get_geography(
        self,
        counter_id: int,
        date1: str,
        date2: str
    ) -> Dict[str, Any]:
        """
        Получить географию посетителей
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
        
        Returns:
            Отчет с географией
        """
        return await self.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits", "ym:s:users"],
            date1=date1,
            date2=date2,
            dimensions=["ym:s:regionCountry", "ym:s:regionCity"]
        )
    
    async def get_utm_path(
        self,
        counter_id: int,
        date1: str,
        date2: str
    ) -> Dict[str, Any]:
        """
        Получить путь: utm_source → utm_medium → utm_campaign
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (YYYY-MM-DD)
            date2: Конечная дата (YYYY-MM-DD)
        
        Returns:
            Отчет с UTM путями
        """
        return await self.get_report(
            counter_id=counter_id,
            metrics=["ym:s:visits", "ym:s:users"],
            date1=date1,
            date2=date2,
            dimensions=["ym:s:UTMSource", "ym:s:UTMMedium", "ym:s:UTMCampaign"]
        )
    
    async def get_report(
        self,
        counter_id: int,
        metrics: List[str],
        date1: str,
        date2: str,
        dimensions: Optional[List[str]] = None,
        filters: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Получить отчет из Reporting API
        
        Args:
            counter_id: ID счетчика
            metrics: Список метрик (например: ["ym:s:visits", "ym:s:pageviews"])
            date1: Начальная дата (формат: YYYY-MM-DD)
            date2: Конечная дата (формат: YYYY-MM-DD)
            dimensions: Опциональные измерения (например: ["ym:s:date", "ym:s:UTMSource"])
            filters: Опциональные фильтры
        
        Returns:
            Словарь с данными отчета
        
        Raises:
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        params = {
            "ids": str(counter_id),
            "metrics": ",".join(metrics),
            "date1": date1,
            "date2": date2,
        }
        
        if dimensions:
            params["dimensions"] = ",".join(dimensions)
        
        if filters:
            params["filters"] = filters
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    REPORTING_API_BASE,
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка получения отчета: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                return response.json()
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к Reporting API")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")
    
    async def get_logs(
        self,
        counter_id: int,
        date1: str,
        date2: str,
        fields: Optional[List[str]] = None,
        source: str = "visits"
    ) -> Dict[str, Any]:
        """
        Создать запрос на экспорт логов через Logs API
        
        Args:
            counter_id: ID счетчика
            date1: Начальная дата (формат: YYYY-MM-DD)
            date2: Конечная дата (формат: YYYY-MM-DD)
            fields: Список полей для экспорта (по умолчанию базовые поля)
            source: Тип данных ("visits" или "hits")
        
        Returns:
            Словарь с log_request_id и количеством частей:
            {
                "log_request_id": "12345",
                "parts": 3
            }
        
        Raises:
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        if fields is None:
            fields = [
                "ym:s:visitID",
                "ym:s:clientID",
                "ym:s:dateTime",
                "ym:s:UTMSource",
                "ym:s:UTMMedium",
                "ym:s:UTMCampaign",
                "ym:s:UTMTerm",
                "ym:s:UTMContent",
                "ym:s:pageURL",
                "ym:s:referer",
                "ym:s:ipAddress",
                "ym:s:regionCountry",
                "ym:s:regionCity",
            ]
        
        url = f"{LOGS_API_BASE}/{source}"
        params = {"counter_id": str(counter_id)}
        
        payload = {
            "date1": date1,
            "date2": date2,
            "fields": fields
        }
        
        async with httpx.AsyncClient(timeout=LOGS_TIMEOUT) as client:
            try:
                response = await client.post(
                    url,
                    params=params,
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка создания запроса на экспорт: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                return response.json()
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к Logs API")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")
    
    async def check_log_status(
        self,
        counter_id: int,
        log_request_id: str
    ) -> str:
        """
        Проверить статус обработки запроса на экспорт логов
        
        Args:
            counter_id: ID счетчика
            log_request_id: ID запроса на экспорт
        
        Returns:
            Статус: "processed", "processing", "canceled"
        
        Raises:
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        url = f"{LOGS_API_BASE}/{log_request_id}/status"
        params = {"counter_id": str(counter_id)}
        
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка проверки статуса: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                data = response.json()
                return data.get("status", "unknown")
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к Logs API")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")
    
    async def download_log_part(
        self,
        counter_id: int,
        log_request_id: str,
        part_number: int
    ) -> List[List[str]]:
        """
        Скачать часть экспортированных логов
        
        Args:
            counter_id: ID счетчика
            log_request_id: ID запроса на экспорт
            part_number: Номер части (начинается с 0)
        
        Returns:
            Список строк данных (каждая строка - список значений)
        
        Raises:
            YandexMetrikaAPIError: Если произошла ошибка API
        """
        url = f"{LOGS_API_BASE}/{log_request_id}/part/{part_number}/download"
        params = {"counter_id": str(counter_id)}
        
        async with httpx.AsyncClient(timeout=LOGS_TIMEOUT) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers()
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    error_code = error_data.get("code", response.status_code)
                    
                    raise YandexMetrikaAPIError(
                        f"Ошибка скачивания данных: {error_message}",
                        code=error_code,
                        response=error_data
                    )
                
                # Данные приходят в формате TSV (tab-separated values)
                text = response.text
                lines = [line.split("\t") for line in text.strip().split("\n") if line.strip()]
                
                return lines
                
            except httpx.TimeoutException:
                raise YandexMetrikaAPIError("Таймаут запроса к Logs API")
            except httpx.RequestError as e:
                raise YandexMetrikaAPIError(f"Ошибка подключения: {str(e)}")

