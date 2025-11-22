/**
 * Утилиты для отправки сообщений в Telegram
 */

import axios from 'axios';
import { logger } from './logger';
import { trackTelegramNotification } from './cloudwatch';

const log = logger.component('TELEGRAM');

const TELEGRAM_API_URL = 'https://api.telegram.org/bot';

/**
 * Отправить сообщение в Telegram
 */
export async function sendToTelegram(
  botToken: string,
  chatId: string,
  text: string,
  parseMode: 'HTML' | 'Markdown' | 'MarkdownV2' = 'HTML'
): Promise<boolean> {
  if (!botToken || !chatId) {
    log.warn('Telegram credentials not provided');
    return false;
  }
  
  try {
    const response = await axios.post(
      `${TELEGRAM_API_URL}${botToken}/sendMessage`,
      {
        chat_id: chatId,
        text: text.substring(0, 4096), // Telegram лимит 4096 символов
        parse_mode: parseMode,
        disable_web_page_preview: false,
      },
      {
        timeout: 10000,
      }
    );
    
    if (response.data.ok) {
      log.debug('Message sent to Telegram', {
        chatId,
        messageLength: text.length,
      });
      
      // Отправка метрики в CloudWatch
      await trackTelegramNotification(true, text.length);
      
      return true;
    } else {
      log.warn('Telegram API returned error', {
        error: response.data.description,
      });
      
      // Отправка метрики ошибки
      await trackTelegramNotification(false);
      
      return false;
    }
  } catch (error) {
    log.error('Error sending message to Telegram', error, {
      chatId,
    });
    
    // Отправка метрики ошибки
    await trackTelegramNotification(false);
    
    return false;
  }
}

/**
 * Отправить сообщение с обработкой ошибок
 */
export async function sendMessageSafe(
  botToken: string,
  chatId: string,
  text: string
): Promise<void> {
  const success = await sendToTelegram(botToken, chatId, text);
  
  if (!success) {
    log.warn('Failed to send Telegram message, but continuing execution');
    // Не бросаем ошибку, чтобы не ломать основной flow
  }
}

