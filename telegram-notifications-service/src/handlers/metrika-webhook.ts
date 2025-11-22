/**
 * Handler для обработки webhook'ов от Яндекс.Метрики
 * POST /metrika-webhook
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { randomUUID } from 'crypto';

const uuidv4 = () => randomUUID();
import { MetrikaEvent } from '../types/events';
import { logger } from '../utils/logger';
import { saveEvent } from '../utils/storage';
import { formatMetrikaMessage } from '../utils/formatters';
import { sendMessageSafe } from '../utils/telegram';
import { trackEvent, trackError } from '../utils/cloudwatch';

const log = logger.component('METRIKA-WEBHOOK');

/**
 * Создать MetrikaEvent из payload
 */
function createMetrikaEvent(
  payload: Record<string, unknown>
): MetrikaEvent | null {
  // Минимальная валидация
  if (!payload.counterId && !process.env.METRIKA_COUNTER_ID) {
    log.warn('No counter ID provided');
    return null;
  }
  
  const counterId = (payload.counterId as string) || process.env.METRIKA_COUNTER_ID || '';
  const clientId = (payload.clientId as string) || 'default';
  
  // Попытка найти связанный визит
  let enriched = false;
  let matchedVisitId: string | undefined;
  
  if (payload.sessionId) {
    // В будущем можно добавить логику поиска визита
    // const visit = await findVisitBySessionId(clientId, payload.sessionId as string);
    // if (visit) {
    //   enriched = true;
    //   matchedVisitId = visit.id;
    // }
  }
  
  const event: MetrikaEvent = {
    type: 'METRIKA',
    id: uuidv4(),
    clientId,
    counterId,
    visitId: (payload.visitId as string) || undefined,
    sessionId: (payload.sessionId as string) || undefined,
    eventName: (payload.eventName as string) || undefined,
    eventParams: (payload.eventParams as Record<string, unknown>) || undefined,
    enriched,
    matchedVisitId,
    timestamp: new Date().toISOString(),
    source: 'metrika',
  };
  
  return event;
}

/**
 * Lambda handler
 */
export async function handler(
  event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  const requestId = uuidv4().substring(0, 8);
  const logContext = { requestId };
  const startTime = Date.now();
  
  log.info('Metrika webhook received', logContext);
  
  try {
    // Парсинг body
    if (!event.body) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          success: false,
          message: 'Request body is required',
          requestId,
        }),
      };
    }
    
    let payload: Record<string, unknown>;
    try {
      payload = JSON.parse(event.body);
    } catch (error) {
      log.error('Invalid JSON in request body', error, logContext);
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          success: false,
          message: 'Invalid JSON',
          requestId,
        }),
      };
    }
    
    // Создание события
    const metrikaEvent = createMetrikaEvent(payload);
    
    if (!metrikaEvent) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          success: false,
          message: 'Failed to create metrika event',
          requestId,
        }),
      };
    }
    
    // Сохранение в DynamoDB
    try {
      await saveEvent(metrikaEvent);
      log.info('Metrika event saved', { ...logContext, eventId: metrikaEvent.id });
    } catch (error) {
      log.error('Error saving metrika event', error, { ...logContext, eventId: metrikaEvent.id });
    }
    
    // Отправка уведомления в Telegram (опционально, только для важных событий)
    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;
    const notifyOnMetrika = process.env.NOTIFY_ON_METRIKA === 'true';
    
    if (botToken && chatId && notifyOnMetrika && metrikaEvent.eventName) {
      const message = formatMetrikaMessage(metrikaEvent);
      await sendMessageSafe(botToken, chatId, message);
      log.info('Telegram notification sent', { ...logContext, eventId: metrikaEvent.id });
    }
    
    // Отправка метрики в CloudWatch
    const duration = Date.now() - startTime;
    await trackEvent('metrika', true, duration);
    
    // Успешный ответ
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        success: true,
        message: 'Event processed',
        requestId,
      }),
    };
    
  } catch (error) {
    log.error('Unexpected error in metrika-webhook handler', error, logContext);
    
    // Отправка метрики ошибки
    const duration = Date.now() - startTime;
    await trackEvent('metrika', false, duration);
    await trackError('metrika-webhook', error instanceof Error ? error.name : 'Unknown');
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        success: false,
        message: 'Internal server error',
        requestId,
      }),
    };
  }
}

