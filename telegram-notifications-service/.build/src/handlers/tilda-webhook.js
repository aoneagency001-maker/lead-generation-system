"use strict";
/**
 * Handler для обработки webhook'ов от Tilda
 * POST /tilda-webhook
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = handler;
const uuid_1 = require("uuid");
const logger_1 = require("../utils/logger");
const validators_1 = require("../utils/validators");
const storage_1 = require("../utils/storage");
const formatters_1 = require("../utils/formatters");
const telegram_1 = require("../utils/telegram");
const cloudwatch_1 = require("../utils/cloudwatch");
const log = logger_1.logger.component('TILDA-WEBHOOK');
/**
 * Извлечь IP адрес из запроса
 */
function extractIP(event) {
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
function detectFormType(payload) {
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
function createFormEvent(payload, ip, userAgent) {
    // Валидация
    if (!(0, validators_1.validateTildaPayload)(payload)) {
        return null;
    }
    // Определение clientId (может быть в payload или в заголовках)
    const clientId = payload.clientId || 'default';
    // Определение типа формы
    const formType = detectFormType(payload);
    // Создание события
    const event = {
        type: 'FORM',
        id: (0, uuid_1.v4)(),
        clientId,
        formType,
        name: payload.name || undefined,
        email: payload.email || undefined,
        phone: payload.phone || undefined,
        message: payload.message || undefined,
        answers: payload.answers || undefined,
        ip: ip || 'unknown',
        userAgent: userAgent || 'unknown',
        pageUrl: payload.pageUrl || payload.page_url || undefined,
        formName: payload.formName || payload.form_name || undefined,
        submittedAt: new Date().toISOString(),
        timestamp: new Date().toISOString(),
        source: 'tilda',
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
        // Валидация payload
        if (!(0, validators_1.validateTildaPayload)(payload)) {
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
            await (0, storage_1.saveEvent)(formEvent);
            log.info('Form event saved', { ...logContext, eventId: formEvent.id });
        }
        catch (error) {
            log.error('Error saving form event', error, { ...logContext, eventId: formEvent.id });
            // Продолжаем выполнение
        }
        // Отправка уведомления в Telegram
        const botToken = process.env.TELEGRAM_BOT_TOKEN;
        const chatId = process.env.TELEGRAM_CHAT_ID;
        if (botToken && chatId) {
            const message = (0, formatters_1.formatContactMessage)(formEvent);
            await (0, telegram_1.sendMessageSafe)(botToken, chatId, message);
            log.info('Telegram notification sent', { ...logContext, eventId: formEvent.id });
        }
        else {
            log.warn('Telegram credentials not configured', logContext);
        }
        // Отправка метрики в CloudWatch
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('form', true, duration);
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
    }
    catch (error) {
        log.error('Unexpected error in tilda-webhook handler', error, logContext);
        // Отправка метрики ошибки
        const duration = Date.now() - startTime;
        await (0, cloudwatch_1.trackEvent)('form', false, duration);
        await (0, cloudwatch_1.trackError)('tilda-webhook', error instanceof Error ? error.name : 'Unknown');
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
//# sourceMappingURL=tilda-webhook.js.map