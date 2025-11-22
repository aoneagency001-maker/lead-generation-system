/**
 * Утилиты для работы с AWS CloudWatch
 * Отправка метрик и кастомных логов
 */
/**
 * Отправить кастомную метрику в CloudWatch
 */
export declare function putMetric(metricName: string, value: number, unit?: 'Count' | 'Seconds' | 'Milliseconds' | 'Bytes' | 'Percent', dimensions?: Record<string, string>): Promise<void>;
/**
 * Отправить метрику события
 */
export declare function trackEvent(eventType: 'visit' | 'form' | 'metrika', success: boolean, duration?: number): Promise<void>;
/**
 * Отправить метрику ошибки
 */
export declare function trackError(handler: string, errorType: string): Promise<void>;
/**
 * Отправить метрику Telegram уведомлений
 */
export declare function trackTelegramNotification(success: boolean, messageLength?: number): Promise<void>;
//# sourceMappingURL=cloudwatch.d.ts.map