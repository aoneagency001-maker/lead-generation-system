/**
 * Handler для обработки webhook'ов от Tilda
 * POST /tilda-webhook
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { randomUUID } from 'crypto';

const uuidv4 = () => randomUUID();
import { FormEvent } from '../types/events';
import { logger } from '../utils/logger';
import { validateTildaPayload } from '../utils/validators';
import { saveEvent } from '../utils/storage';
import { formatContactMessage } from '../utils/formatters';
import { sendMessageSafe } from '../utils/telegram';
import { trackEvent, trackError } from '../utils/cloudwatch';

const log = logger.component('TILDA-WEBHOOK');

/**
 * Извлечь IP адрес из запроса
 */
function extractIP(event: APIGatewayProxyEvent): string | null {
  const forwardedFor = event.headers['x-forwarded-for'] || event.headers['X-Forwarded-For'];
  if (forwardedFor) {
    return forwardedFor.split(',')[0].trim();
  }
  
  if (event.requestContext?.identity?.sourceIp) {
    return event.requestContext.identity.sourceIp;
  }
  
  return null;
}

/**
 * Определить тип формы
 */
function detectFormType(payload: Record<string, unknown>): 'contact' | 'callback' | 'custom' | 'quiz' {
  // Если есть answers - это квиз
  if (payload.answers && typeof payload.answers === 'object') {
    return 'quiz';
  }
  
  // Если есть только phone - callback
  if (payload.phone && !payload.email && !payload.message) {
    return 'callback';
  }
  
  // Если есть message или email - contact
  if (payload.message || payload.email) {
    return 'contact';
  }
  
  return 'custom';
}

/**
 * Создать FormEvent из payload Tilda
 */
function createFormEvent(
  payload: Record<string, unknown>,
  ip: string | null,
  userAgent: string | null
): FormEvent | null {
  // Валидация
  if (!validateTildaPayload(payload)) {
    return null;
  }
  
  // Определение clientId (может быть в payload или в заголовках)
  const clientId = (payload.clientId as string) || 'default';
  
  // Определение типа формы
  const formType = detectFormType(payload);
  
  // Создание события
  const event: FormEvent = {
    type: 'FORM',
    id: uuidv4(),
    clientId,
    formType,
    name: (payload.name as string) || undefined,
    email: (payload.email as string) || undefined,
    phone: (payload.phone as string) || undefined,
    message: (payload.message as string) || undefined,
    answers: (payload.answers as Record<string, unknown>) || undefined,
    ip: ip || 'unknown',
    userAgent: userAgent || 'unknown',
    pageUrl: (payload.pageUrl as string) || (payload.page_url as string) || undefined,
    formName: (payload.formName as string) || (payload.form_name as string) || undefined,
    submittedAt: new Date().toISOString(),
    timestamp: new Date().toISOString(),
    source: 'tilda',
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
  
  log.info('Tilda webhook received', logContext);
  
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
    
    // Валидация payload
    if (!validateTildaPayload(payload)) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          success: false,
          message: 'Invalid payload: phone or email is required',
          requestId,
        }),
      };
    }
    
    // Извлечение IP и User-Agent
    const ip = extractIP(event);
    const userAgent = event.headers['user-agent'] || event.headers['User-Agent'] || null;
    
    // Создание события
    const formEvent = createFormEvent(payload, ip, userAgent);
    
    if (!formEvent) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          success: false,
          message: 'Failed to create form event',
          requestId,
        }),
      };
    }
    
    // Сохранение в DynamoDB
    try {
      await saveEvent(formEvent);
      log.info('Form event saved', { ...logContext, eventId: formEvent.id });
    } catch (error) {
      log.error('Error saving form event', error, { ...logContext, eventId: formEvent.id });
      // Продолжаем выполнение
    }
    
    // Отправка уведомления в Telegram
    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;
    
    if (botToken && chatId) {
      const message = formatContactMessage(formEvent);
      await sendMessageSafe(botToken, chatId, message);
      log.info('Telegram notification sent', { ...logContext, eventId: formEvent.id });
    } else {
      log.warn('Telegram credentials not configured', logContext);
    }
    
    // Отправка метрики в CloudWatch
    const duration = Date.now() - startTime;
    await trackEvent('form', true, duration);
    
    // Успешный ответ
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        success: true,
        message: 'Notification sent',
        requestId,
      }),
    };
    
  } catch (error) {
    log.error('Unexpected error in tilda-webhook handler', error, logContext);
    
    // Отправка метрики ошибки
    const duration = Date.now() - startTime;
    await trackEvent('form', false, duration);
    await trackError('tilda-webhook', error instanceof Error ? error.name : 'Unknown');
    
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

