"use strict";
/**
 * Клиент для работы с Яндекс.Метрикой
 * Использует Logs API для получения данных в реальном времени
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getMetrikaLogs = getMetrikaLogs;
exports.downloadMetrikaLogPart = downloadMetrikaLogPart;
exports.checkMetrikaLogStatus = checkMetrikaLogStatus;
exports.getMetrikaAvailableFields = getMetrikaAvailableFields;
const axios_1 = __importDefault(require("axios"));
const logger_1 = require("./logger");
const log = logger_1.logger.component('METRIKA-CLIENT');
/**
 * Получить данные из Яндекс.Метрики через Logs API
 *
 * Документация: https://yandex.ru/dev/metrika/doc/api2/logs/about.html
 */
async function getMetrikaLogs(token, params) {
    try {
        const response = await axios_1.default.post('https://api-metrika.yandex.net/logs/v1/export/visits', {
            date1: params.date1,
            date2: params.date2,
            fields: params.fields || [
                'ym:s:visitID',
                'ym:s:clientID',
                'ym:s:dateTime',
                'ym:s:UTMSource',
                'ym:s:UTMMedium',
                'ym:s:UTMCampaign',
                'ym:s:UTMTerm',
                'ym:s:UTMContent',
                'ym:s:pageURL',
                'ym:s:referer',
                'ym:s:ipAddress',
                'ym:s:regionCountry',
                'ym:s:regionCity',
            ],
        }, {
            headers: {
                'Authorization': `OAuth ${token}`,
                'Content-Type': 'application/json',
            },
            params: {
                counter_id: params.counterId,
            },
            timeout: 30000,
        });
        log.info('Metrika logs request created', {
            logRequestId: response.data.log_request_id,
            parts: response.data.parts,
        });
        return response.data;
    }
    catch (error) {
        log.error('Error requesting Metrika logs', error, {
            counterId: params.counterId,
        });
        return null;
    }
}
/**
 * Получить готовые данные из Logs API
 * После создания запроса нужно дождаться обработки и скачать части
 */
async function downloadMetrikaLogPart(token, counterId, logRequestId, partNumber) {
    try {
        const response = await axios_1.default.get(`https://api-metrika.yandex.net/logs/v1/export/${logRequestId}/part/${partNumber}/download`, {
            headers: {
                'Authorization': `OAuth ${token}`,
            },
            params: {
                counter_id: counterId,
            },
            timeout: 60000,
        });
        // Данные приходят в формате TSV (tab-separated values)
        const lines = response.data.split('\n').filter((line) => line.trim());
        const data = lines.map((line) => line.split('\t'));
        log.debug('Metrika log part downloaded', {
            logRequestId,
            partNumber,
            rows: data.length,
        });
        return data;
    }
    catch (error) {
        log.error('Error downloading Metrika log part', error, {
            logRequestId,
            partNumber,
        });
        return null;
    }
}
/**
 * Проверить статус запроса логов
 */
async function checkMetrikaLogStatus(token, counterId, logRequestId) {
    try {
        const response = await axios_1.default.get(`https://api-metrika.yandex.net/logs/v1/export/${logRequestId}/status`, {
            headers: {
                'Authorization': `OAuth ${token}`,
            },
            params: {
                counter_id: counterId,
            },
            timeout: 10000,
        });
        return response.data.status;
    }
    catch (error) {
        log.error('Error checking Metrika log status', error, {
            logRequestId,
        });
        return null;
    }
}
/**
 * Получить список доступных полей для экспорта
 */
async function getMetrikaAvailableFields(token, counterId, source = 'visits') {
    try {
        const response = await axios_1.default.get(`https://api-metrika.yandex.net/logs/v1/export/${source}/fields`, {
            headers: {
                'Authorization': `OAuth ${token}`,
            },
            params: {
                counter_id: counterId,
            },
            timeout: 10000,
        });
        return response.data.map((field) => field.name);
    }
    catch (error) {
        log.error('Error getting Metrika available fields', error, {
            counterId,
            source,
        });
        return null;
    }
}
//# sourceMappingURL=metrika-client.js.map