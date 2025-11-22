"use strict";
/**
 * Handler для отслеживания посетителей
 * POST /track-visitor
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = handler;
const uuid_1 = require("uuid");
const logger_1 = require("../utils/logger");
const validators_1 = require("../utils/validators");
const geo_location_1 = require("../utils/geo-location");
const storage_1 = require("../utils/storage");
const formatters_1 = require("../utils/formatters");
const telegram_1 = require("../utils/telegram");
const cloudwatch_1 = require("../utils/cloudwatch");
const log = logger_1.logger.component('TRACK-VISITOR');
/**
 * Извлечь IP адрес из запроса
 */
function extractIP(event) {
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
function extractUserAgent(event) {
    return event.headers['user-agent'] || event.headers['User-Agent'] || null;
}
/**
 * Создать VisitEvent из payload
 */
async function createVisitEvent(payload, ip, userAgent) {
    const requestId = (0, uuid_1.v4)().substring(0, 8);
    // Валидация clientId
    const clientId = payload.clientId;
    if (!(0, validators_1.isValidClientId)(clientId)) {
        log.warn('Invalid clientId', { requestId, clientId });
        return null;
    }
    // Проверка IP
    if (!ip || !(0, validators_1.isValidIP)(ip)) {
        log.warn('Invalid IP address', { requestId, ip });
        return null;
    }
    // Проверка на бота
    if ((0, validators_1.isBot)(userAgent)) {
        log.debug('Bot detected, skipping', { requestId, userAgent });
        return null;
    }
    // Определение устройства
    const device = (0, validators_1.getDeviceType)(userAgent);
    // Получение геолокации
    const geo = await (0, geo_location_1.getGeoLocation)(ip);
    // Создание события
    const event = {
        type: 'VISIT',
        id: (0, uuid_1.v4)(),
        clientId,
        sessionId: payload.sessionId || (0, uuid_1.v4)(),
        ip,
        userAgent: userAgent || 'unknown',
        country: geo.country || 'Unknown',
        city: geo.city || 'Unknown',
        region: geo.region || undefined,
        timezone: geo.timezone || undefined,
        isp: geo.isp || undefined,
        device,
        screenResolution: payload.screenResolution || undefined,
        referrer: payload.referrer || null,
        page: payload.page || '/',
        landingPage: payload.landingPage || payload.page || '/',
        utmSource: payload.utmSource || null,
        utmMedium: payload.utmMedium || null,
        utmCampaign: payload.utmCampaign || null,
        utmTerm: payload.utmTerm || null,
        utmContent: payload.utmContent || null,
        timeOnSite: payload.timeOnSite || undefined,
        clicks: payload.clicks || undefined,
        pagesViewed: payload.pagesViewed || undefined,
        conversions: payload.conversions || undefined,
        timestamp: new Date().toISOString(),
        source: 'tracker',
    };
    return event;
}
/**
 * Lambda handler
 */
async function handler(event) {
    const requestId = (0, uuid_1.v4)().substring(0, 8);
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
        let payload;
        try {
            payload = JSON.parse(event.body);
        }
        catch (error) {
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
        if (!(0, validators_1.validateTrackVisitorPayload)(payload)) {
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
            await (0, storage_1.saveEvent)(visitEvent);
            log.info('Visit event saved', { ...logContext, eventId: visitEvent.id });
        }
        catch (error) {
            log.error('Error saving visit event', error, { ...logContext, eventId: visitEvent.id });
            // Продолжаем выполнение даже если не удалось сохранить
        }
        // Отправка уведомления в Telegram
        const botToken = process.env.TELEGRAM_BOT_TOKEN;
        const chatId = process.env.TELEGRAM_CHAT_ID;
        if (botToken && chatId) {
            // Отправляем только для новых визитов или конверсий
            const shouldNotify = payload.isFirstVisit ||
                (visitEvent.conversions && visitEvent.conversions.length > 0);
            if (shouldNotify) {
                const message = (0, formatters_1.formatVisitorMessage)(visitEvent);
                await (0, telegram_1.sendMessageSafe)(botToken, chatId, message);
                log.info('Telegram notification sent', { ...logContext, eventId: visitEvent.id });
            }
        }
        else {
            log.warn('Telegram credentials not configured', logContext);
        }
        // Отправка метрики в CloudWatch
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('visit', true, duration);
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
    }
    catch (error) {
        log.error('Unexpected error in track-visitor handler', error, logContext);
        // Отправка метрики ошибки
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('visit', false, duration);
        await (0, cloudwatch_1.trackError)('track-visitor', error instanceof Error ? error.name : 'Unknown');
        return {
            statusCode: 500,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tracked: false,
                error: 'Internal server error',
                requestId,
            }),
        };
    }
}
//# sourceMappingURL=track-visitor.js.map