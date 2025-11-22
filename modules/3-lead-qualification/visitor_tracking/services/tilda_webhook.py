"""
Tilda Webhook Handler
Обработчик webhook'ов от Tilda
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from core.database.supabase_client import create_lead, create_record
from shared.telegram_notifier import telegram_notifier
from .message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


class TildaWebhookHandler:
    """Обработчик webhook'ов от Tilda"""
    
    def __init__(self):
        self.formatter = MessageFormatter()
    
    async def handle_webhook(
        self,
        webhook_data: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обработать webhook от Tilda
        
        Args:
            webhook_data: Данные из webhook
            ip_address: IP адрес отправителя
        
        Returns:
            Результат обработки
        """
        request_id = str(uuid.uuid4())[:8]
        
        try:
            # Извлекаем данные
            name = webhook_data.get("name", "Неизвестно")
            phone = webhook_data.get("phone", "")
            email = webhook_data.get("email")
            message = webhook_data.get("message", "")
            form_name = webhook_data.get("form_name") or webhook_data.get("formName")
            page_url = webhook_data.get("page_url") or webhook_data.get("pageUrl")
            
            # Валидация
            if not phone:
                logger.warning(f"[TILDA-{request_id}] No phone provided")
                return {
                    "success": False,
                    "message": "Phone is required",
                    "requestId": request_id
                }
            
            # Формируем данные для сохранения
            lead_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "source": "tilda",
                "notes": f"Form: {form_name or 'Unknown'}\nPage: {page_url or 'Unknown'}\nMessage: {message}",
                "status": "new",
                "created_at": datetime.now().isoformat()
            }
            
            # Сохраняем как лид
            try:
                saved_lead = create_lead(
                    ad_id="",
                    name=name,
                    phone=phone,
                    source="tilda",
                    platform_user_id=None,
                    budget=None,
                    notes=lead_data["notes"]
                )
                logger.info(f"[TILDA-{request_id}] Lead created: {saved_lead.get('id')}")
            except Exception as e:
                logger.error(f"[TILDA-{request_id}] Error creating lead: {e}")
                # Продолжаем даже если не удалось сохранить
            
            # Сохраняем детали webhook
            webhook_record = {
                "id": str(uuid.uuid4()),
                "lead_id": saved_lead.get("id") if saved_lead else None,
                "form_name": form_name,
                "page_url": page_url,
                "ip_address": ip_address,
                "raw_data": webhook_data,
                "created_at": datetime.now().isoformat()
            }
            
            try:
                create_record("tilda_webhooks", webhook_record)
            except Exception as e:
                logger.warning(f"[TILDA-{request_id}] Error saving webhook record: {e}")
            
            # Формируем сообщение для Telegram
            telegram_data = {
                "name": name,
                "phone": phone,
                "email": email,
                "message": message,
                "form_name": form_name,
                "page_url": page_url,
                "created_at": datetime.now()
            }
            
            message_text = self.formatter.format_tilda_lead_message(telegram_data)
            
            # Отправляем уведомление
            await telegram_notifier.send_success(
                message=message_text,
                module="TildaWebhook"
            )
            
            return {
                "success": True,
                "message": "Notification sent",
                "requestId": request_id
            }
        
        except Exception as e:
            logger.error(f"[TILDA-{request_id}] Error handling webhook: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "requestId": request_id
            }

