/**
 * Handler для отслеживания посетителей
 * POST /track-visitor
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { randomUUID } from 'crypto';

const uuidv4 = () => randomUUID();
import { VisitEvent } from '../types/events';
import { logger } from '../utils/logger';
import { isBot, isValidIP, getDeviceType, isValidClientId, validateTrackVisitorPayload } from '../utils/validators';
import { getGeoLocation } from '../utils/geo-location';
import { saveEvent } from '../utils/storage';
import { formatVisitorMessage } from '../utils/formatters';
import { sendMessageSafe } from '../utils/telegram';
import { trackEvent, trackError } from '../utils/cloudwatch';

const log = logger.component('TRACK-VISITOR');

/**
 * Извлечь IP адрес из запроса
 */
function extractIP(event: APIGatewayProxyEvent): string | null {
  // Проверяем заголовки (для прокси/CDN)
  const forwardedFor = event.headers['x-forwarded-for'] || event.headers['X-Forwarded-For'];
  if (forwardedFor) {
    return forwardedFor.split(',')[0].trim();
  }
  
  // Проверяем requestContext (для API Gateway)
  if (event.requestContext?.identity?.sourceIp) {
    return event.requestContext.identity.sourceIp;
  }
  
  return null;
}

/**
 * Извлечь User-Agent из запроса
 */
function extractUserAgent(event: APIGatewayProxyEvent): string | null {
  return event.headers['user-agent'] || event.headers['User-Agent'] || null;
}

/**
 * Создать VisitEvent из payload
 */
async function createVisitEvent(
  payload: Record<string, unknown>,
  ip: string | null,
  userAgent: string | null
): Promise<VisitEvent | null> {
  const requestId = uuidv4().substring(0, 8);
  
  // Валидация clientId
  const clientId = payload.clientId as string;
  if (!isValidClientId(clientId)) {
    log.warn('Invalid clientId', { requestId, clientId });
    return null;
  }
  
  // Проверка IP
  if (!ip || !isValidIP(ip)) {
    log.warn('Invalid IP address', { requestId, ip });
    return null;
  }
  
  // Проверка на бота
  if (isBot(userAgent)) {
    log.debug('Bot detected, skipping', { requestId, userAgent });
    return null;
  }
  
  // Определение устройства
  const device = getDeviceType(userAgent);
  
  // Получение геолокации
  const geo = await getGeoLocation(ip);
  
  // Создание события
  const event: VisitEvent = {
    type: 'VISIT',
    id: uuidv4(),
    clientId,
    sessionId: (payload.sessionId as string) || uuidv4(),
    ip,
    userAgent: userAgent || 'unknown',
    country: geo.country || 'Unknown',
    city: geo.city || 'Unknown',
    region: geo.region || undefined,
    timezone: geo.timezone || undefined,
    isp: geo.isp || undefined,
    device,
    screenResolution: (payload.screenResolution as string) || undefined,
    referrer: (payload.referrer as string) || null,
    page: (payload.page as string) || '/',
    landingPage: (payload.landingPage as string) || (payload.page as string) || '/',
    utmSource: (payload.utmSource as string) || null,
    utmMedium: (payload.utmMedium as string) || null,
    utmCampaign: (payload.utmCampaign as string) || null,
    utmTerm: (payload.utmTerm as string) || null,
    utmContent: (payload.utmContent as string) || null,
    timeOnSite: (payload.timeOnSite as number) || undefined,
    clicks: (payload.clicks as number) || undefined,
    pagesViewed: (payload.pagesViewed as number) || undefined,
    conversions: (payload.conversions as string[]) || undefined,
    timestamp: new Date().toISOString(),
    source: 'tracker',
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
  
  log.info('Track visitor request received', logContext);
  
  try {
    // Парсинг body
    if (!event.body) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tracked: false,
          error: 'Request body is required',
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
          tracked: false,
          error: 'Invalid JSON',
          requestId,
        }),
      };
    }
    
    // Валидация payload
    if (!validateTrackVisitorPayload(payload)) {
      return {
        statusCode: 400,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tracked: false,
          error: 'Invalid payload',
          requestId,
        }),
      };
    }
    
    // Извлечение IP и User-Agent
    const ip = extractIP(event);
    const userAgent = extractUserAgent(event);
    
    // Создание события
    const visitEvent = await createVisitEvent(payload, ip, userAgent);
    
    if (!visitEvent) {
      // Бот или невалидные данные - возвращаем успех, но не сохраняем
      return {
        statusCode: 200,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tracked: false,
          message: 'Bot detected or invalid data',
          requestId,
        }),
      };
    }
    
    // Сохранение в DynamoDB
    try {
      await saveEvent(visitEvent);
      log.info('Visit event saved', { ...logContext, eventId: visitEvent.id });
    } catch (error) {
      log.error('Error saving visit event', error, { ...logContext, eventId: visitEvent.id });
      // Продолжаем выполнение даже если не удалось сохранить
    }
    
    // Отправка уведомления в Telegram
    const botToken = process.env.TELEGRAM_BOT_TOKEN;
    const chatId = process.env.TELEGRAM_CHAT_ID;
    
    if (botToken && chatId) {
      // Отправляем только для новых визитов или конверсий
      const shouldNotify = 
        (payload.isFirstVisit as boolean) || 
        (visitEvent.conversions && visitEvent.conversions.length > 0);
      
      if (shouldNotify) {
        const message = formatVisitorMessage(visitEvent);
        await sendMessageSafe(botToken, chatId, message);
        log.info('Telegram notification sent', { ...logContext, eventId: visitEvent.id });
      }
    } else {
      log.warn('Telegram credentials not configured', logContext);
    }
    
    // Отправка метрики в CloudWatch
    const duration = Date.now() - startTime;
    await trackEvent('visit', true, duration);
    
    // Успешный ответ
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tracked: true,
        visitorId: visitEvent.id,
        requestId,
      }),
    };
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorStack = error instanceof Error ? error.stack : undefined;
    
    log.error('Unexpected error in track-visitor handler', error, {
      ...logContext,
      errorMessage,
      errorStack: errorStack?.substring(0, 500), // Первые 500 символов стека
    });
    
    // Отправка метрики ошибки (не блокируем если не удалось)
    try {
      const duration = Date.now() - startTime;
      await trackEvent('visit', false, duration);
      await trackError('track-visitor', error instanceof Error ? error.name : 'Unknown');
    } catch (metricError) {
      log.warn('Failed to send error metrics', { ...logContext, error: metricError instanceof Error ? metricError.message : String(metricError) });
    }
    
    return {
      statusCode: 500,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tracked: false,
        error: 'Internal server error',
        requestId,
        // В development показываем детали ошибки
        ...(process.env.NODE_ENV === 'development' && {
          errorMessage,
        }),
      }),
    };
  }
}

