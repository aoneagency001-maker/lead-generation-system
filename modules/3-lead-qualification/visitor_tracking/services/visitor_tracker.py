"""
Visitor Tracker Service
Основной сервис для отслеживания посетителей
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from core.database.supabase_client import create_record, get_records
from shared.telegram_notifier import telegram_notifier
from .bot_detector import BotDetector
from .geo_location import GeoLocationService
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class VisitorTracker:
    """Сервис отслеживания посетителей"""
    
    def __init__(self):
        self.bot_detector = BotDetector()
        self.geo_service = GeoLocationService()
        self.formatter = MessageFormatter()
        # Кэш для проверки новых посетителей (in-memory, для production лучше Redis)
        self._recent_visitors: Dict[str, datetime] = {}
        self._cache_ttl = 3600  # 1 час
    
    async def track_visitor(
        self,
        request_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отследить посетителя
        
        Args:
            request_data: Данные из запроса
            ip_address: IP адрес посетителя
            user_agent: User-Agent строка
        
        Returns:
            Результат отслеживания
        """
        request_id = str(uuid.uuid4())[:8]
        
        try:
            # Определяем бота
            is_bot = self.bot_detector.is_bot(user_agent)
            
            # Если это бот - не отслеживаем
            if is_bot:
                logger.debug(f"[TRACK-{request_id}] Bot detected, skipping")
                return {
                    "tracked": False,
                    "visitorId": None,
                    "requestId": request_id,
                    "message": "Bot detected, not tracked"
                }
            
            # Определяем тип устройства
            device_type = self.bot_detector.get_device_type(user_agent)
            
            # Получаем геолокацию
            geo_data = await self.geo_service.get_location(ip_address)
            
            # Формируем данные посетителя
            session_id = request_data.get("sessionId") or str(uuid.uuid4())
            visitor_id = str(uuid.uuid4())
            
            visitor_data = {
                "id": visitor_id,
                "session_id": session_id,
                "page": request_data.get("page"),
                "landing_page": request_data.get("landingPage"),
                "referrer": request_data.get("referrer"),
                "screen_resolution": request_data.get("screenResolution"),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "city": geo_data.get("city"),
                "country": geo_data.get("country"),
                "device_type": device_type,
                "utm_source": request_data.get("utmSource"),
                "utm_medium": request_data.get("utmMedium"),
                "utm_campaign": request_data.get("utmCampaign"),
                "utm_term": request_data.get("utmTerm"),
                "utm_content": request_data.get("utmContent"),
                "is_first_visit": request_data.get("isFirstVisit", False),
                "is_bot": False,
                "created_at": datetime.now().isoformat()
            }
            
            # Проверяем не новый ли это посетитель (по session_id)
            is_new_visitor = self._is_new_visitor(session_id)
            
            # Сохраняем в БД
            try:
                saved_visitor = create_record("visitors", visitor_data)
                logger.info(f"[TRACK-{request_id}] Visitor saved: {visitor_id}")
            except Exception as e:
                logger.error(f"[TRACK-{request_id}] Error saving visitor: {e}")
                # Продолжаем даже если не удалось сохранить
            
            # Отправляем уведомление только для новых посетителей или важных событий
            if is_new_visitor or request_data.get("isFirstVisit"):
                message = self.formatter.format_visitor_message(visitor_data)
                
                await telegram_notifier.send_info(
                    message=message,
                    module="VisitorTracking"
                )
            
            return {
                "tracked": True,
                "visitorId": visitor_id,
                "requestId": request_id
            }
        
        except Exception as e:
            logger.error(f"[TRACK-{request_id}] Error tracking visitor: {e}", exc_info=True)
            return {
                "tracked": False,
                "visitorId": None,
                "requestId": request_id,
                "message": f"Error: {str(e)}"
            }
    
    def _is_new_visitor(self, session_id: str) -> bool:
        """
        Проверить является ли посетитель новым
        
        Args:
            session_id: ID сессии
        
        Returns:
            True если новый посетитель
        """
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Очищаем старые записи из кэша
        self._recent_visitors = {
            sid: timestamp
            for sid, timestamp in self._recent_visitors.items()
            if (now - timestamp).total_seconds() < self._cache_ttl
        }
        
        # Проверяем есть ли уже такой session_id
        if session_id in self._recent_visitors:
            return False
        
        # Добавляем в кэш
        self._recent_visitors[session_id] = now
        return True

