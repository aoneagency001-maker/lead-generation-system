/**
 * Утилиты для работы с AWS CloudWatch
 * Отправка метрик и кастомных логов
 */

import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';
import { logger } from './logger';

const log = logger.component('CLOUDWATCH');

let cloudwatchClient: CloudWatchClient | null = null;

/**
 * Получить CloudWatch клиент
 */
function getClient(): CloudWatchClient {
  if (!cloudwatchClient) {
    // AWS_REGION автоматически доступен в Lambda
    cloudwatchClient = new CloudWatchClient({
      region: process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'eu-central-1',
    });
    log.info('CloudWatch client initialized');
  }
  
  return cloudwatchClient;
}

/**
 * Отправить кастомную метрику в CloudWatch
 */
export async function putMetric(
  metricName: string,
  value: number,
  unit: 'Count' | 'Seconds' | 'Milliseconds' | 'Bytes' | 'Percent' = 'Count',
  dimensions?: Record<string, string>
): Promise<void> {
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
    await client.send(
      new PutMetricDataCommand({
        Namespace: namespace,
        MetricData: [metricData],
      })
    );
    
    log.debug('Metric sent to CloudWatch', {
      metricName,
      value,
      unit,
    });
  } catch (error) {
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
export async function trackEvent(
  eventType: 'visit' | 'form' | 'metrika',
  success: boolean,
  duration?: number
): Promise<void> {
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
export async function trackError(
  handler: string,
  errorType: string
): Promise<void> {
  await putMetric('errors', 1, 'Count', {
    Handler: handler,
    ErrorType: errorType,
  });
}

/**
 * Отправить метрику Telegram уведомлений
 */
export async function trackTelegramNotification(
  success: boolean,
  messageLength?: number
): Promise<void> {
  const dimensions = {
    Status: success ? 'success' : 'error',
  };
  
  await putMetric('telegram_notifications', 1, 'Count', dimensions);
  
  if (messageLength !== undefined) {
    await putMetric('telegram_message_length', messageLength, 'Bytes', dimensions);
  }
}

