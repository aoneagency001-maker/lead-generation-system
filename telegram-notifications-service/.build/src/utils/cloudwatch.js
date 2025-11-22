"use strict";
/**
 * Утилиты для работы с AWS CloudWatch
 * Отправка метрик и кастомных логов
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.putMetric = putMetric;
exports.trackEvent = trackEvent;
exports.trackError = trackError;
exports.trackTelegramNotification = trackTelegramNotification;
const client_cloudwatch_1 = require("@aws-sdk/client-cloudwatch");
const logger_1 = require("./logger");
const log = logger_1.logger.component('CLOUDWATCH');
let cloudwatchClient = null;
/**
 * Получить CloudWatch клиент
 */
function getClient() {
    if (!cloudwatchClient) {
        cloudwatchClient = new client_cloudwatch_1.CloudWatchClient({
            region: process.env.AWS_REGION || 'eu-central-1',
        });
        log.info('CloudWatch client initialized');
    }
    return cloudwatchClient;
}
/**
 * Отправить кастомную метрику в CloudWatch
 */
async function putMetric(metricName, value, unit = 'Count', dimensions) {
    const client = getClient();
    const namespace = process.env.CLOUDWATCH_NAMESPACE || 'TelegramNotifications';
    const metricData = {
        MetricName: metricName,
        Value: value,
        Unit: unit,
        Timestamp: new Date(),
        Dimensions: dimensions
            ? Object.entries(dimensions).map(([Name, Value]) => ({ Name, Value }))
            : undefined,
    };
    try {
        await client.send(new client_cloudwatch_1.PutMetricDataCommand({
            Namespace: namespace,
            MetricData: [metricData],
        }));
        log.debug('Metric sent to CloudWatch', {
            metricName,
            value,
            unit,
        });
    }
    catch (error) {
        log.error('Error sending metric to CloudWatch', error, {
            metricName,
            value,
        });
        // Не бросаем ошибку, чтобы не ломать основной flow
    }
}
/**
 * Отправить метрику события
 */
async function trackEvent(eventType, success, duration) {
    const dimensions = {
        EventType: eventType,
        Status: success ? 'success' : 'error',
    };
    // Метрика количества событий
    await putMetric(`${eventType}_events`, 1, 'Count', dimensions);
    // Метрика длительности (если указана)
    if (duration !== undefined) {
        await putMetric(`${eventType}_duration`, duration, 'Milliseconds', dimensions);
    }
}
/**
 * Отправить метрику ошибки
 */
async function trackError(handler, errorType) {
    await putMetric('errors', 1, 'Count', {
        Handler: handler,
        ErrorType: errorType,
    });
}
/**
 * Отправить метрику Telegram уведомлений
 */
async function trackTelegramNotification(success, messageLength) {
    const dimensions = {
        Status: success ? 'success' : 'error',
    };
    await putMetric('telegram_notifications', 1, 'Count', dimensions);
    if (messageLength !== undefined) {
        await putMetric('telegram_message_length', messageLength, 'Bytes', dimensions);
    }
}
//# sourceMappingURL=cloudwatch.js.map