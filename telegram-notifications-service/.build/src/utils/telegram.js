"use strict";
/**
 * Утилиты для отправки сообщений в Telegram
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendToTelegram = sendToTelegram;
exports.sendMessageSafe = sendMessageSafe;
const axios_1 = __importDefault(require("axios"));
const logger_1 = require("./logger");
const cloudwatch_1 = require("./cloudwatch");
const log = logger_1.logger.component('TELEGRAM');
const TELEGRAM_API_URL = 'https://api.telegram.org/bot';
/**
 * Отправить сообщение в Telegram
 */
async function sendToTelegram(botToken, chatId, text, parseMode = 'HTML') {
    if (!botToken || !chatId) {
        log.warn('Telegram credentials not provided');
        return false;
    }
    try {
        const response = await axios_1.default.post(`${TELEGRAM_API_URL}${botToken}/sendMessage`, {
            chat_id: chatId,
            text: text.substring(0, 4096), // Telegram лимит 4096 символов
            parse_mode: parseMode,
            disable_web_page_preview: false,
        }, {
            timeout: 10000,
        });
        if (response.data.ok) {
            log.debug('Message sent to Telegram', {
                chatId,
                messageLength: text.length,
            });
            // Отправка метрики в CloudWatch
            await (0, cloudwatch_1.trackTelegramNotification)(true, text.length);
            return true;
        }
        else {
            log.warn('Telegram API returned error', {
                error: response.data.description,
            });
            // Отправка метрики ошибки
            await (0, cloudwatch_1.trackTelegramNotification)(false);
            return false;
        }
    }
    catch (error) {
        log.error('Error sending message to Telegram', error, {
            chatId,
        });
        // Отправка метрики ошибки
        await (0, cloudwatch_1.trackTelegramNotification)(false);
        return false;
    }
}
/**
 * Отправить сообщение с обработкой ошибок
 */
async function sendMessageSafe(botToken, chatId, text) {
    const success = await sendToTelegram(botToken, chatId, text);
    if (!success) {
        log.warn('Failed to send Telegram message, but continuing execution');
        // Не бросаем ошибку, чтобы не ломать основной flow
    }
}
//# sourceMappingURL=telegram.js.map