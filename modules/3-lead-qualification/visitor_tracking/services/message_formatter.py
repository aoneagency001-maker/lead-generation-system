"""
Message Formatter
Форматирование сообщений для Telegram
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessageFormatter:
    """Форматирование сообщений для отправки в Telegram"""
    
    @staticmethod
    def format_visitor_message(visitor_data: Dict[str, Any]) -> str:
        """
        Форматировать сообщение о посетителе
        
        Args:
            visitor_data: Данные посетителя
        
        Returns:
            Отформатированное сообщение
        """
        # Эмодзи для типов устройств
        device_emoji = {
            "mobile": "📱",
            "tablet": "📱",
            "desktop": "💻"
        }
        
        device_type = visitor_data.get("device_type", "desktop")
        device_icon = device_emoji.get(device_type, "💻")
        
        # Эмодзи для первого визита
        first_visit_icon = "🆕" if visitor_data.get("is_first_visit") else "🔄"
        
        # Эмодзи для бота
        bot_icon = "🤖" if visitor_data.get("is_bot") else "👤"
        
        message_parts = [
            f"{bot_icon} <b>Новый посетитель</b>",
            "",
            f"{first_visit_icon} <b>Тип:</b> {'Первый визит' if visitor_data.get('is_first_visit') else 'Повторный визит'}",
            f"{device_icon} <b>Устройство:</b> {device_type}",
        ]
        
        # Геолокация
        city = visitor_data.get("city")
        country = visitor_data.get("country")
        if city or country:
            location = ", ".join(filter(None, [city, country]))
            message_parts.append(f"📍 <b>Местоположение:</b> {location}")
        
        # Страница
        page = visitor_data.get("page") or visitor_data.get("landing_page")
        if page:
            message_parts.append(f"📄 <b>Страница:</b> {page}")
        
        # Реферер
        referrer = visitor_data.get("referrer")
        if referrer:
            # Укорачиваем длинные URL
            if len(referrer) > 50:
                referrer = referrer[:47] + "..."
            message_parts.append(f"🔗 <b>Источник:</b> {referrer}")
        
        # UTM метки
        utm_parts = []
        if visitor_data.get("utm_source"):
            utm_parts.append(f"Source: {visitor_data['utm_source']}")
        if visitor_data.get("utm_medium"):
            utm_parts.append(f"Medium: {visitor_data['utm_medium']}")
        if visitor_data.get("utm_campaign"):
            utm_parts.append(f"Campaign: {visitor_data['utm_campaign']}")
        
        if utm_parts:
            message_parts.append(f"📊 <b>UTM:</b> {' | '.join(utm_parts)}")
        
        # Разрешение экрана
        resolution = visitor_data.get("screen_resolution")
        if resolution:
            message_parts.append(f"🖥️ <b>Разрешение:</b> {resolution}")
        
        # Время
        created_at = visitor_data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                message_parts.append(f"🕐 <b>Время:</b> {created_at}")
            else:
                message_parts.append(f"🕐 <b>Время:</b> {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(message_parts)
    
    @staticmethod
    def format_tilda_lead_message(lead_data: Dict[str, Any]) -> str:
        """
        Форматировать сообщение о заявке с Tilda
        
        Args:
            lead_data: Данные заявки
        
        Returns:
            Отформатированное сообщение
        """
        message_parts = [
            "🎯 <b>Новая заявка с лендинга!</b>",
            "",
        ]
        
        # Имя
        name = lead_data.get("name")
        if name:
            message_parts.append(f"👤 <b>Имя:</b> {name}")
        
        # Телефон
        phone = lead_data.get("phone")
        if phone:
            message_parts.append(f"📞 <b>Телефон:</b> {phone}")
        
        # Email
        email = lead_data.get("email")
        if email:
            message_parts.append(f"📧 <b>Email:</b> {email}")
        
        # Сообщение
        message = lead_data.get("message")
        if message:
            message_parts.append(f"💬 <b>Сообщение:</b>\n{message}")
        
        # Форма
        form_name = lead_data.get("form_name")
        if form_name:
            message_parts.append(f"📝 <b>Форма:</b> {form_name}")
        
        # URL страницы
        page_url = lead_data.get("page_url")
        if page_url:
            # Укорачиваем длинные URL
            if len(page_url) > 50:
                page_url = page_url[:47] + "..."
            message_parts.append(f"🔗 <b>Страница:</b> {page_url}")
        
        # Время
        created_at = lead_data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                message_parts.append(f"🕐 <b>Время:</b> {created_at}")
            else:
                message_parts.append(f"🕐 <b>Время:</b> {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return "\n".join(message_parts)

