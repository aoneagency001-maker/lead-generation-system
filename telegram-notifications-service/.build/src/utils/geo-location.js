"use strict";
/**
 * Геолокация по IP адресу
 * Использует бесплатный сервис ip-api.com
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getGeoLocation = getGeoLocation;
exports.clearGeoCache = clearGeoCache;
const axios_1 = __importDefault(require("axios"));
const logger_1 = require("./logger");
const validators_1 = require("./validators");
const log = logger_1.logger.component('GEO-LOCATION');
// Кэш для избежания повторных запросов (в Lambda это будет работать только в рамках одного инстанса)
const cache = new Map();
const CACHE_TTL = 3600000; // 1 час в миллисекундах
/**
 * Получить геолокацию по IP
 */
async function getGeoLocation(ip) {
    if (!ip || (0, validators_1.isLocalIP)(ip)) {
        log.debug('Local IP or no IP provided', { ip });
        return {
            city: null,
            country: null,
            region: null,
            timezone: null,
            isp: null,
        };
    }
    // Проверяем кэш
    const cached = cache.get(ip);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        log.debug('Using cached geo location', { ip });
        return cached.data;
    }
    try {
        const response = await axios_1.default.get(`http://ip-api.com/json/${ip}`, {
            params: {
                fields: 'status,message,city,country,countryCode,region,regionName,timezone,isp',
            },
            timeout: 5000,
        });
        if (response.data.status === 'success') {
            const data = {
                city: response.data.city || null,
                country: response.data.country || null,
                region: response.data.regionName || null,
                timezone: response.data.timezone || null,
                isp: response.data.isp || null,
            };
            // Сохраняем в кэш
            cache.set(ip, { data, timestamp: Date.now() });
            log.debug('Geo location retrieved', { ip, ...data });
            return data;
        }
        else {
            log.warn('Geo API returned error', { ip, message: response.data.message });
            return {
                city: null,
                country: null,
                region: null,
                timezone: null,
                isp: null,
            };
        }
    }
    catch (error) {
        log.error('Error getting geo location', error, { ip });
        return {
            city: null,
            country: null,
            region: null,
            timezone: null,
            isp: null,
        };
    }
}
/**
 * Очистить кэш (для тестирования)
 */
function clearGeoCache() {
    cache.clear();
}
//# sourceMappingURL=geo-location.js.map