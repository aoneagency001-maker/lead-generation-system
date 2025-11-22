"use strict";
/**
 * Валидаторы для входящих данных
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.isValidIP = isValidIP;
exports.isBot = isBot;
exports.getDeviceType = getDeviceType;
exports.isLocalIP = isLocalIP;
exports.isValidClientId = isValidClientId;
exports.validateTildaPayload = validateTildaPayload;
exports.validateTrackVisitorPayload = validateTrackVisitorPayload;
const logger_1 = require("./logger");
const log = logger_1.logger.component('VALIDATOR');
/**
 * Проверка валидности IP адреса
 */
function isValidIP(ip) {
    if (!ip)
        return false;
    // IPv4
    const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (ipv4Regex.test(ip)) {
        const parts = ip.split('.').map(Number);
        return parts.every(part => part >= 0 && part <= 255);
    }
    // IPv6 (упрощенная проверка)
    const ipv6Regex = /^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$/;
    if (ipv6Regex.test(ip)) {
        return true;
    }
    // IPv6 сокращенная форма
    if (ip.includes('::')) {
        return true;
    }
    return false;
}
/**
 * Проверка является ли User-Agent ботом
 */
function isBot(userAgent) {
    if (!userAgent)
        return false;
    const botPatterns = [
        /googlebot/i,
        /bingbot/i,
        /slurp/i, // Yahoo
        /duckduckbot/i,
        /baiduspider/i,
        /yandexbot/i,
        /sogou/i,
        /exabot/i,
        /facebot/i,
        /ia_archiver/i,
        /facebookexternalhit/i,
        /twitterbot/i,
        /linkedinbot/i,
        /embedly/i,
        /quora link preview/i,
        /showyoubot/i,
        /outbrain/i,
        /pinterest/i,
        /slackbot/i,
        /vkShare/i,
        /W3C_Validator/i,
        /whatsapp/i,
        /flipboard/i,
        /tumblr/i,
        /bitlybot/i,
        /skypeuripreview/i,
        /nuzzel/i,
        /redditbot/i,
        /Applebot/i,
        /headless/i,
        /phantom/i,
        /puppeteer/i,
        /selenium/i,
        /webdriver/i,
        /curl/i,
        /wget/i,
        /python-requests/i,
        /postman/i,
        /insomnia/i,
        /httpie/i,
        /go-http-client/i,
        /java/i,
        /okhttp/i,
        /apache-httpclient/i,
        /bot/i,
        /crawler/i,
        /spider/i,
        /scraper/i,
    ];
    return botPatterns.some(pattern => pattern.test(userAgent));
}
/**
 * Определение типа устройства
 */
function getDeviceType(userAgent) {
    if (!userAgent)
        return 'desktop';
    const ua = userAgent.toLowerCase();
    // Планшеты
    if (/ipad|android(?!.*mobile)|kindle|silk|playbook/i.test(ua)) {
        return 'tablet';
    }
    // Мобильные
    if (/mobile|android|iphone|ipod|blackberry|windows phone|opera mini/i.test(ua)) {
        return 'mobile';
    }
    return 'desktop';
}
/**
 * Проверка является ли IP локальным
 */
function isLocalIP(ip) {
    if (!ip)
        return false;
    const localPatterns = [
        '127.0.0.1',
        'localhost',
        '192.168.',
        '10.',
        '172.16.',
        '172.17.',
        '172.18.',
        '172.19.',
        '172.20.',
        '172.21.',
        '172.22.',
        '172.23.',
        '172.24.',
        '172.25.',
        '172.26.',
        '172.27.',
        '172.28.',
        '172.29.',
        '172.30.',
        '172.31.',
    ];
    return localPatterns.some(pattern => ip.startsWith(pattern));
}
/**
 * Валидация clientId
 */
function isValidClientId(clientId) {
    if (!clientId)
        return false;
    // Минимальная валидация: не пустой, не слишком длинный
    return clientId.length > 0 && clientId.length <= 100;
}
/**
 * Валидация payload от Tilda
 */
function validateTildaPayload(payload) {
    if (typeof payload !== 'object' || payload === null) {
        log.warn('Invalid Tilda payload: not an object');
        return false;
    }
    // Минимальная валидация: должен быть хотя бы phone или email
    const obj = payload;
    if (!obj.phone && !obj.email) {
        log.warn('Invalid Tilda payload: missing phone and email');
        return false;
    }
    return true;
}
/**
 * Валидация payload от track-visitor
 */
function validateTrackVisitorPayload(payload) {
    if (typeof payload !== 'object' || payload === null) {
        log.warn('Invalid track-visitor payload: not an object');
        return false;
    }
    const obj = payload;
    if (!obj.clientId || typeof obj.clientId !== 'string') {
        log.warn('Invalid track-visitor payload: missing or invalid clientId');
        return false;
    }
    return true;
}
//# sourceMappingURL=validators.js.map