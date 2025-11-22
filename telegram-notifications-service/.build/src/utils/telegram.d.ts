/**
 * Утилиты для отправки сообщений в Telegram
 */
/**
 * Отправить сообщение в Telegram
 */
export declare function sendToTelegram(botToken: string, chatId: string, text: string, parseMode?: 'HTML' | 'Markdown' | 'MarkdownV2'): Promise<boolean>;
/**
 * Отправить сообщение с обработкой ошибок
 */
export declare function sendMessageSafe(botToken: string, chatId: string, text: string): Promise<void>;
//# sourceMappingURL=telegram.d.ts.map