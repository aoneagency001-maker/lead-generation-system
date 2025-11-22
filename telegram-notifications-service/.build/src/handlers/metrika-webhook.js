"use strict";
/**
 * Handler для обработки webhook'ов от Яндекс.Метрики
 * POST /metrika-webhook
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = handler;
const uuid_1 = require("uuid");
const logger_1 = require("../utils/logger");
const storage_1 = require("../utils/storage");
const formatters_1 = require("../utils/formatters");
const telegram_1 = require("../utils/telegram");
const cloudwatch_1 = require("../utils/cloudwatch");
const log = logger_1.logger.component('METRIKA-WEBHOOK');
/**
 * Создать MetrikaEvent из payload
 */
function createMetrikaEvent(payload) {
    // Минимальная валидация
    if (!payload.counterId && !process.env.METRIKA_COUNTER_ID) {
        log.warn('No counter ID provided');
        return null;
    }
    const counterId = payload.counterId || process.env.METRIKA_COUNTER_ID || '';
    const clientId = payload.clientId || 'default';
    // Попытка найти связанный визит
    let enriched = false;
    let matchedVisitId;
    if (payload.sessionId) {
        // В будущем можно добавить логику поиска визита
        // const visit = await findVisitBySessionId(clientId, payload.sessionId as string);
        // if (visit) {
        //   enriched = true;
        //   matchedVisitId = visit.id;
        // }
    }
    const event = {
        type: 'METRIKA',
        id: (0, uuid_1.v4)(),
        clientId,
        counterId,
        visitId: payload.visitId || undefined,
        sessionId: payload.sessionId || undefined,
        eventName: payload.eventName || undefined,
        eventParams: payload.eventParams || undefined,
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
async function handler(event) {
    const requestId = (0, uuid_1.v4)().substring(0, 8);
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
            await (0, storage_1.saveEvent)(metrikaEvent);
            log.info('Metrika event saved', { ...logContext, eventId: metrikaEvent.id });
        }
        catch (error) {
            log.error('Error saving metrika event', error, { ...logContext, eventId: metrikaEvent.id });
        }
        // Отправка уведомления в Telegram (опционально, только для важных событий)
        const botToken = process.env.TELEGRAM_BOT_TOKEN;
        const chatId = process.env.TELEGRAM_CHAT_ID;
        const notifyOnMetrika = process.env.NOTIFY_ON_METRIKA === 'true';
        if (botToken && chatId && notifyOnMetrika && metrikaEvent.eventName) {
            const message = (0, formatters_1.formatMetrikaMessage)(metrikaEvent);
            await (0, telegram_1.sendMessageSafe)(botToken, chatId, message);
            log.info('Telegram notification sent', { ...logContext, eventId: metrikaEvent.id });
        }
        // Отправка метрики в CloudWatch
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('metrika', true, duration);
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
    }
    catch (error) {
        log.error('Unexpected error in metrika-webhook handler', error, logContext);
        // Отправка метрики ошибки
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('metrika', false, duration);
        await (0, cloudwatch_1.trackError)('metrika-webhook', error instanceof Error ? error.name : 'Unknown');
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
//# sourceMappingURL=metrika-webhook.js.map