"""
Telegram Assistant Bot с Gemini API
Поддерживает: текст, голос, изображения

Команды:
/start - Приветствие и начало работы
/help - Справка по командам
/clear - Очистить историю разговора

Usage:
    python -m shared.telegram_assistant_bot
"""

import asyncio
import httpx
import os
import logging
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import base64

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("google-generativeai not installed. Install with: pip install google-generativeai")

from core.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class TelegramAssistantBot:
    """Telegram бот-ассистент с Gemini API"""
    
    def __init__(self, bot_token: Optional[str] = None, gemini_api_key: Optional[str] = None):
        """
        Args:
            bot_token: Telegram Bot Token (если None - берет из env)
            gemini_api_key: Gemini API Key (если None - берет из env)
        """
        # Telegram Bot Token
        self.bot_token = bot_token or os.getenv("TELEGRAM_ASSISTANT_BOT_TOKEN")
        
        if not self.bot_token:
            raise ValueError(
                "TELEGRAM_ASSISTANT_BOT_TOKEN not set in environment"
            )
        
        # Gemini API Key
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY not set in environment"
            )
        
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai not installed. Install with: pip install google-generativeai"
            )
        
        # Инициализация Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.gemini_model = genai.GenerativeModel(
            os.getenv("GEMINI_MODEL", "gemini-pro")
        )
        self.gemini_vision_model = genai.GenerativeModel(
            os.getenv("GEMINI_VISION_MODEL", "gemini-pro-vision")
        )
        
        self.bot_type = "assistant"
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Для хранения последних обновлений
        self.last_update_id = 0
        
        # Для хранения истории разговоров (в памяти, можно перенести в БД)
        self.conversation_history: Dict[int, List[Dict[str, str]]] = {}
        
        logger.info("✅ Telegram Assistant Bot initialized with Gemini API")
    
    async def start_polling(self):
        """Запустить бота в режиме polling"""
        logger.info("🤖 Starting Telegram Assistant Bot polling...")
        
        while True:
            try:
                # Получить обновления
                updates = await self._get_updates()
                
                for update in updates:
                    await self._handle_update(update)
                
                # Небольшая задержка между запросами
                await asyncio.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in bot polling: {e}", exc_info=True)
                await asyncio.sleep(5)  # Подождать перед повтором
    
    async def _get_updates(self) -> list:
        """Получить новые обновления от Telegram"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/getUpdates",
                    params={
                        "offset": self.last_update_id + 1,
                        "timeout": 30
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        
                        # Обновить last_update_id
                        if updates:
                            self.last_update_id = max(
                                u["update_id"] for u in updates
                            )
                        
                        return updates
                
                return []
        
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Обработать одно обновление"""
        if "message" not in update:
            return
        
        message = update["message"]
        chat = message.get("chat", {})
        chat_id = chat.get("id")
        from_user = message.get("from", {})
        
        # Извлекаем данные пользователя
        user_data = {
            "chat_id": chat_id,
            "username": from_user.get("username"),
            "first_name": from_user.get("first_name"),
            "last_name": from_user.get("last_name"),
            "language_code": from_user.get("language_code")
        }
        
        # Обработка команд
        text = message.get("text", "").strip()
        if text.startswith("/"):
            command = text.split()[0] if text else ""
            
            if command == "/start":
                await self._save_subscriber(user_data)
                await self._cmd_start(chat_id, user_data)
            elif command == "/help":
                await self._cmd_help(chat_id)
            elif command == "/clear":
                await self._cmd_clear(chat_id)
            else:
                await self._send_message(
                    chat_id,
                    f"❓ Неизвестная команда: {command}\n\nИспользуй /help для списка команд"
                )
            return
        
        # Обработка текстовых сообщений
        if text:
            await self._update_subscriber_activity(chat_id)
            await self._handle_text_message(chat_id, text)
            return
        
        # Обработка голосовых сообщений
        if "voice" in message:
            await self._update_subscriber_activity(chat_id)
            await self._handle_voice_message(chat_id, message["voice"], message)
            return
        
        # Обработка изображений
        if "photo" in message:
            await self._update_subscriber_activity(chat_id)
            await self._handle_photo_message(chat_id, message["photo"], message.get("caption", ""))
            return
        
        # Обработка документов (изображения как документы)
        if "document" in message:
            document = message["document"]
            mime_type = document.get("mime_type", "")
            if mime_type.startswith("image/"):
                await self._update_subscriber_activity(chat_id)
                await self._handle_document_image(chat_id, document, message.get("caption", ""))
                return
        
        # Если ничего не подошло
        await self._send_message(
            chat_id,
            "🤔 Я понимаю текст, голосовые сообщения и изображения. Попробуй отправить что-то из этого!"
        )
    
    async def _handle_text_message(self, chat_id: int, text: str):
        """Обработать текстовое сообщение через Gemini"""
        try:
            # Показать индикатор печати
            await self._send_typing_action(chat_id)
            
            # Получить историю разговора
            history = self.conversation_history.get(chat_id, [])
            
            # Добавить сообщение пользователя в историю
            history.append({"role": "user", "parts": [text]})
            
            # Отправить запрос в Gemini
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                history
            )
            
            # Получить ответ
            assistant_response = response.text if hasattr(response, 'text') else str(response)
            
            # Добавить ответ ассистента в историю
            history.append({"role": "model", "parts": [assistant_response]})
            
            # Сохранить историю (ограничить размер)
            if len(history) > 20:  # Ограничить до 10 пар вопрос-ответ
                history = history[-20:]
            self.conversation_history[chat_id] = history
            
            # Отправить ответ пользователю
            await self._send_message(chat_id, assistant_response)
            
            # Сохранить в БД для аналитики
            await self._save_conversation(chat_id, text, assistant_response, "text")
        
        except Exception as e:
            logger.error(f"Error handling text message: {e}", exc_info=True)
            await self._send_message(
                chat_id,
                f"❌ Произошла ошибка при обработке сообщения: {str(e)}"
            )
    
    async def _handle_voice_message(self, chat_id: int, voice: Dict[str, Any], message: Dict[str, Any] = None):
        """Обработать голосовое сообщение"""
        try:
            await self._send_message(chat_id, "🎤 Обрабатываю голосовое сообщение...")
            await self._send_typing_action(chat_id)
            
            # Проверить, есть ли уже распознанный текст от Telegram
            # Telegram автоматически распознает речь, если пользователь включил эту функцию
            if message and "text" in message:
                recognized_text = message["text"]
                await self._send_message(
                    chat_id,
                    f"📝 Распознанный текст: {recognized_text}\n\nОбрабатываю через Gemini..."
                )
                # Обработать как обычное текстовое сообщение
                await self._handle_text_message(chat_id, recognized_text)
                return
            
            # Если текста нет, пытаемся получить файл и обработать
            file_id = voice.get("file_id")
            file_path = await self._get_file_path(file_id)
            
            if not file_path:
                await self._send_message(chat_id, "❌ Не удалось получить голосовое сообщение")
                return
            
            # Скачать файл
            audio_data = await self._download_file(file_path)
            
            # Попытка использовать Gemini для распознавания речи
            # Gemini может работать с аудио через специальные модели
            try:
                # Конвертировать OGG в формат, который понимает Gemini
                # Для этого используем временный файл
                with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
                    tmp_file.write(audio_data)
                    tmp_path = tmp_file.name
                
                # Попытка использовать Gemini для обработки аудио
                # Примечание: Gemini может не поддерживать прямую обработку аудио в текущей версии
                # В этом случае предлагаем пользователю использовать текстовый ввод
                
                await self._send_message(
                    chat_id,
                    "🎤 Для лучшей работы с голосовыми сообщениями:\n\n"
                    "1. Включи распознавание речи в настройках Telegram\n"
                    "2. Или отправь текст напрямую\n\n"
                    "Я обработаю твое сообщение через Gemini! 💬"
                )
                
                # Удалить временный файл
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            
            except Exception as e:
                logger.error(f"Error processing voice: {e}")
                await self._send_message(
                    chat_id,
                    "❌ Не удалось обработать голосовое сообщение. "
                    "Попробуй отправить текст или включи распознавание речи в Telegram."
                )
            
        except Exception as e:
            logger.error(f"Error handling voice message: {e}", exc_info=True)
            await self._send_message(
                chat_id,
                f"❌ Ошибка при обработке голосового сообщения: {str(e)}"
            )
    
    async def _handle_photo_message(self, chat_id: int, photos: List[Dict[str, Any]], caption: str = ""):
        """Обработать изображение через Gemini Vision"""
        try:
            await self._send_message(chat_id, "🖼️ Анализирую изображение...")
            await self._send_typing_action(chat_id)
            
            # Получить самое большое изображение
            largest_photo = max(photos, key=lambda p: p.get("file_size", 0))
            file_id = largest_photo.get("file_id")
            
            # Скачать изображение
            file_path = await self._get_file_path(file_id)
            if not file_path:
                await self._send_message(chat_id, "❌ Не удалось получить изображение")
                return
            
            image_data = await self._download_file(file_path)
            
            # Конвертировать в base64 для Gemini
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Подготовить промпт
            prompt = caption if caption else "Опиши это изображение подробно на русском языке."
            
            # Отправить в Gemini Vision
            response = await asyncio.to_thread(
                self._process_image_with_gemini,
                image_data,
                prompt
            )
            
            # Отправить ответ
            await self._send_message(chat_id, response)
            
            # Сохранить в БД
            await self._save_conversation(chat_id, f"[Изображение: {caption}]", response, "image")
        
        except Exception as e:
            logger.error(f"Error handling photo message: {e}", exc_info=True)
            await self._send_message(
                chat_id,
                f"❌ Ошибка при обработке изображения: {str(e)}"
            )
    
    async def _handle_document_image(self, chat_id: int, document: Dict[str, Any], caption: str = ""):
        """Обработать изображение, отправленное как документ"""
        try:
            await self._send_message(chat_id, "🖼️ Анализирую изображение...")
            await self._send_typing_action(chat_id)
            
            file_id = document.get("file_id")
            file_path = await self._get_file_path(file_id)
            
            if not file_path:
                await self._send_message(chat_id, "❌ Не удалось получить изображение")
                return
            
            image_data = await self._download_file(file_path)
            
            prompt = caption if caption else "Опиши это изображение подробно на русском языке."
            
            response = await asyncio.to_thread(
                self._process_image_with_gemini,
                image_data,
                prompt
            )
            
            await self._send_message(chat_id, response)
            await self._save_conversation(chat_id, f"[Изображение: {caption}]", response, "image")
        
        except Exception as e:
            logger.error(f"Error handling document image: {e}", exc_info=True)
            await self._send_message(
                chat_id,
                f"❌ Ошибка при обработке изображения: {str(e)}"
            )
    
    def _process_image_with_gemini(self, image_data: bytes, prompt: str) -> str:
        """Обработать изображение через Gemini Vision API"""
        import PIL.Image
        import io
        
        # Конвертировать bytes в PIL Image
        image = PIL.Image.open(io.BytesIO(image_data))
        
        # Отправить в Gemini Vision
        response = self.gemini_vision_model.generate_content([prompt, image])
        
        return response.text if hasattr(response, 'text') else str(response)
    
    async def _get_file_path(self, file_id: str) -> Optional[str]:
        """Получить путь к файлу по file_id"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/getFile",
                    params={"file_id": file_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result", {}).get("file_path")
                
                return None
        
        except Exception as e:
            logger.error(f"Error getting file path: {e}")
            return None
    
    async def _download_file(self, file_path: str) -> bytes:
        """Скачать файл с Telegram серверов"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                )
                
                if response.status_code == 200:
                    return response.content
                
                raise Exception(f"Failed to download file: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    async def _cmd_start(self, chat_id: int, user_data: Dict[str, Any]):
        """Команда /start"""
        username = user_data.get("username") or user_data.get("first_name", "there")
        
        message = f"""
🤖 <b>Привет, {username}!</b>

Я твой AI-ассистент на базе Gemini API.

<b>Что я умею:</b>
• 💬 Отвечать на текстовые сообщения
• 🎤 Обрабатывать голосовые сообщения (в разработке)
• 🖼️ Анализировать изображения
• 📝 Помнить контекст разговора

<b>Команды:</b>
/help - Справка
/clear - Очистить историю разговора

Просто напиши мне что-нибудь или отправь изображение! 🚀
        """
        await self._send_message(chat_id, message, parse_mode="HTML")
    
    async def _cmd_help(self, chat_id: int):
        """Команда /help"""
        message = """
📖 <b>Справка по командам</b>

<b>/start</b> - Начать работу с ботом
<b>/help</b> - Показать эту справку
<b>/clear</b> - Очистить историю разговора

<b>Как использовать:</b>
• Просто напиши мне вопрос или сообщение
• Отправь изображение - я его проанализирую
• Я помню контекст нашего разговора

<b>Примеры:</b>
• "Расскажи о Python"
• "Что такое машинное обучение?"
• Отправь фото - я опишу что на нем
        """
        await self._send_message(chat_id, message, parse_mode="HTML")
    
    async def _cmd_clear(self, chat_id: int):
        """Команда /clear - очистить историю"""
        if chat_id in self.conversation_history:
            del self.conversation_history[chat_id]
        
        await self._send_message(
            chat_id,
            "✅ История разговора очищена. Начнем с чистого листа!"
        )
    
    async def _send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None
    ) -> bool:
        """Отправить сообщение"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text
            }
            
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=payload
                )
                
                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return False
        
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def _send_typing_action(self, chat_id: int):
        """Показать индикатор "печатает..." """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.base_url}/sendChatAction",
                    json={
                        "chat_id": chat_id,
                        "action": "typing"
                    }
                )
        except:
            pass  # Не критично если не работает
    
    async def _save_subscriber(self, user_data: Dict[str, Any]) -> bool:
        """Сохранить подписчика в базу данных"""
        try:
            supabase = get_supabase_client()
            
            subscriber_data = {
                "bot_type": self.bot_type,
                "chat_id": user_data["chat_id"],
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "language_code": user_data.get("language_code"),
                "status": "active",
                "metadata": {}
            }
            
            result = supabase.table("telegram_bot_subscribers").upsert(
                subscriber_data,
                on_conflict="bot_type,chat_id"
            ).execute()
            
            logger.info(f"✅ Subscriber saved: chat_id={user_data['chat_id']}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving subscriber: {e}", exc_info=True)
            return False
    
    async def _update_subscriber_activity(self, chat_id: int) -> bool:
        """Обновить время последней активности"""
        try:
            supabase = get_supabase_client()
            
            supabase.table("telegram_bot_subscribers").update({
                "last_activity_at": datetime.now().isoformat()
            }).eq("bot_type", self.bot_type).eq("chat_id", chat_id).execute()
            
            return True
        
        except Exception as e:
            logger.debug(f"Could not update subscriber activity: {e}")
            return False
    
    async def _save_conversation(
        self,
        chat_id: int,
        user_message: str,
        assistant_response: str,
        message_type: str = "text"
    ):
        """Сохранить разговор в БД для аналитики"""
        try:
            supabase = get_supabase_client()
            
            # TODO: Создать таблицу для истории разговоров если нужно
            # Пока просто логируем
            logger.debug(
                f"Conversation saved: chat_id={chat_id}, type={message_type}, "
                f"user_msg={user_message[:50]}..."
            )
        
        except Exception as e:
            logger.debug(f"Could not save conversation: {e}")


# ============================================================================
# Запуск бота
# ============================================================================

async def main():
    """Главная функция для запуска бота"""
    try:
        bot = TelegramAssistantBot()
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())

