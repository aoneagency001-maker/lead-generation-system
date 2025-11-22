"""
Geo Location Service
Определение геолокации по IP адресу
"""

import httpx
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class GeoLocationService:
    """Определение геолокации по IP адресу"""
    
    def __init__(self):
        self.api_url = "http://ip-api.com/json"
        self.timeout = 5.0
        # Кэш для избежания повторных запросов
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 1 час
    
    async def get_location(self, ip_address: Optional[str] = None) -> Dict[str, Optional[str]]:
        """
        Получить геолокацию по IP
        
        Args:
            ip_address: IP адрес (если None - будет использован публичный IP)
        
        Returns:
            Словарь с city и country
        """
        if not ip_address:
            return {"city": None, "country": None}
        
        # Проверяем локальные IP
        if self._is_local_ip(ip_address):
            logger.debug(f"Local IP detected: {ip_address}")
            return {"city": None, "country": None}
        
        # Проверяем кэш
        if ip_address in self._cache:
            return self._cache[ip_address]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.api_url}/{ip_address}",
                    params={"fields": "status,message,city,country,countryCode"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("status") == "success":
                        result = {
                            "city": data.get("city"),
                            "country": data.get("country")
                        }
                        # Сохраняем в кэш
                        self._cache[ip_address] = result
                        return result
                    else:
                        logger.warning(f"Geo API error: {data.get('message')}")
                        return {"city": None, "country": None}
                else:
                    logger.warning(f"Geo API HTTP error: {response.status_code}")
                    return {"city": None, "country": None}
        
        except httpx.TimeoutException:
            logger.warning(f"Geo API timeout for IP: {ip_address}")
            return {"city": None, "country": None}
        except Exception as e:
            logger.error(f"Geo location error: {e}")
            return {"city": None, "country": None}
    
    def _is_local_ip(self, ip: str) -> bool:
        """Проверить является ли IP локальным"""
        local_patterns = [
            "127.0.0.1",
            "localhost",
            "192.168.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
        ]
        
        return any(ip.startswith(pattern) for pattern in local_patterns)

