"""
Event Bus - Redis Pub/Sub Wrapper
Обертка над Redis для Event-Driven Architecture
"""

import json
import redis
import asyncio
from typing import Callable, Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Event Bus для асинхронной обработки событий через Redis Pub/Sub
    
    Использование:
        event_bus = EventBus(redis_url="redis://localhost:6379/0")
        
        # Подписка на событие
        @event_bus.subscribe("LeadCreated")
        async def on_lead_created(event):
            print(f"New lead: {event['lead_id']}")
        
        # Публикация события
        await event_bus.publish("LeadCreated", {"lead_id": "123", "email": "test@example.com"})
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """
        Инициализация Event Bus
        
        Args:
            redis_url: URL для подключения к Redis
        """
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.handlers: Dict[str, List[Callable]] = {}
        self.running = False
        
        logger.info(f"✅ EventBus инициализирован: {redis_url}")
    
    def subscribe(self, event_type: str):
        """
        Декоратор для подписки на событие
        
        Args:
            event_type: Тип события (например, "LeadCreated")
        
        Example:
            @event_bus.subscribe("LeadCreated")
            async def handle_lead_created(event):
                print(event)
        """
        def decorator(handler: Callable):
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            self.handlers[event_type].append(handler)
            logger.info(f"📌 Подписка на событие: {event_type} → {handler.__name__}")
            return handler
        return decorator
    
    async def publish(self, event_type: str, payload: Dict[str, Any]):
        """
        Опубликовать событие
        
        Args:
            event_type: Тип события
            payload: Данные события
        
        Example:
            await event_bus.publish("LeadCreated", {
                "lead_id": "123",
                "email": "test@example.com",
                "source": "olx"
            })
        """
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Публикуем в Redis channel
        channel = f"events:{event_type}"
        message = json.dumps(event)
        
        self.redis_client.publish(channel, message)
        
        logger.info(f"📤 Событие опубликовано: {event_type} → {payload}")
    
    async def start_listening(self):
        """
        Запустить прослушивание событий (в фоновом режиме)
        
        Подписывается на все каналы для зарегистрированных событий
        """
        if self.running:
            logger.warning("⚠️  EventBus уже запущен")
            return
        
        # Подписываемся на все каналы
        channels = [f"events:{event_type}" for event_type in self.handlers.keys()]
        
        if not channels:
            logger.warning("⚠️  Нет зарегистрированных обработчиков")
            return
        
        self.pubsub.subscribe(*channels)
        self.running = True
        
        logger.info(f"👂 EventBus слушает каналы: {channels}")
        
        # Запускаем цикл обработки сообщений
        await self._process_messages()
    
    async def _process_messages(self):
        """Обработка входящих сообщений из Redis Pub/Sub"""
        while self.running:
            try:
                message = self.pubsub.get_message()
                
                if message and message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    # Извлекаем тип события из канала
                    event_type = channel.replace("events:", "")
                    
                    # Парсим JSON
                    event = json.loads(data)
                    
                    # Вызываем все обработчики для этого события
                    if event_type in self.handlers:
                        for handler in self.handlers[event_type]:
                            try:
                                # Вызываем обработчик асинхронно
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event['payload'])
                                else:
                                    handler(event['payload'])
                                
                                logger.info(f"✅ Обработчик выполнен: {handler.__name__} для {event_type}")
                            
                            except Exception as e:
                                logger.error(f"❌ Ошибка в обработчике {handler.__name__}: {e}")
                
                # Небольшая задержка чтобы не нагружать CPU
                await asyncio.sleep(0.01)
            
            except Exception as e:
                logger.error(f"❌ Ошибка при обработке сообщений: {e}")
                await asyncio.sleep(1)
    
    def stop(self):
        """Остановить прослушивание событий"""
        self.running = False
        self.pubsub.unsubscribe()
        logger.info("🛑 EventBus остановлен")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Получить статистику Event Bus
        
        Returns:
            Словарь со статистикой
        """
        return {
            "running": self.running,
            "registered_events": list(self.handlers.keys()),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "handlers_by_event": {
                event_type: [h.__name__ for h in handlers]
                for event_type, handlers in self.handlers.items()
            }
        }


# Глобальный экземпляр Event Bus
_event_bus_instance = None


def get_event_bus(redis_url: str = None) -> EventBus:
    """
    Получить глобальный экземпляр Event Bus (Singleton)
    
    Args:
        redis_url: URL для подключения к Redis (используется только при первом вызове)
    
    Returns:
        EventBus instance
    """
    global _event_bus_instance
    
    if _event_bus_instance is None:
        from core.api.config import settings
        url = redis_url or settings.redis_url
        _event_bus_instance = EventBus(redis_url=url)
    
    return _event_bus_instance


# Экспорт
__all__ = ["EventBus", "get_event_bus"]

