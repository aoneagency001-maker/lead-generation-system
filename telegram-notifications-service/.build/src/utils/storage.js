"use strict";
/**
 * Storage для DynamoDB
 * Обёртка над AWS SDK для работы с событиями
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveEvent = saveEvent;
exports.getEvents = getEvents;
exports.findVisitBySessionId = findVisitBySessionId;
const client_dynamodb_1 = require("@aws-sdk/client-dynamodb");
const lib_dynamodb_1 = require("@aws-sdk/lib-dynamodb");
const logger_1 = require("./logger");
const log = logger_1.logger.component('STORAGE');
let client = null;
/**
 * Инициализация DynamoDB клиента
 */
function getClient() {
    if (!client) {
        const dynamoClient = new client_dynamodb_1.DynamoDBClient({
            region: process.env.AWS_REGION || 'eu-central-1',
        });
        client = lib_dynamodb_1.DynamoDBDocumentClient.from(dynamoClient);
        log.info('DynamoDB client initialized', {
            region: process.env.AWS_REGION || 'eu-central-1',
            table: process.env.DYNAMODB_TABLE,
        });
    }
    return client;
}
/**
 * Сохранить событие в DynamoDB
 *
 * Структура ключей:
 * - pk (partition key) = clientId
 * - sk (sort key) = type#timestamp#id
 */
async function saveEvent(event) {
    const tableName = process.env.DYNAMODB_TABLE;
    if (!tableName) {
        throw new Error('DYNAMODB_TABLE environment variable is not set');
    }
    const docClient = getClient();
    // Формируем ключи
    const pk = event.clientId;
    const sk = `${event.type}#${event.timestamp}#${event.id}`;
    // Подготовка записи
    const item = {
        pk,
        sk,
        type: event.type,
        id: event.id,
        clientId: event.clientId,
        timestamp: event.timestamp,
        source: event.source,
        payload: event, // Полное событие в JSON
        // TTL для автоматической очистки старых данных (опционально, 90 дней)
        ttl: Math.floor(Date.now() / 1000) + 90 * 24 * 60 * 60,
    };
    try {
        await docClient.send(new lib_dynamodb_1.PutCommand({
            TableName: tableName,
            Item: item,
        }));
        log.info('Event saved to DynamoDB', {
            eventId: event.id,
            eventType: event.type,
            clientId: event.clientId,
        });
    }
    catch (error) {
        log.error('Error saving event to DynamoDB', error, {
            eventId: event.id,
            eventType: event.type,
            clientId: event.clientId,
        });
        throw error;
    }
}
/**
 * Получить события по clientId и типу
 */
async function getEvents(clientId, eventType, limit = 100) {
    const tableName = process.env.DYNAMODB_TABLE;
    if (!tableName) {
        throw new Error('DYNAMODB_TABLE environment variable is not set');
    }
    const docClient = getClient();
    let keyConditionExpression = 'pk = :clientId';
    const expressionAttributeValues = {
        ':clientId': clientId,
    };
    // Если указан тип события, фильтруем по нему
    if (eventType) {
        keyConditionExpression += ' AND begins_with(sk, :eventType)';
        expressionAttributeValues[':eventType'] = `${eventType}#`;
    }
    try {
        const result = await docClient.send(new lib_dynamodb_1.QueryCommand({
            TableName: tableName,
            KeyConditionExpression: keyConditionExpression,
            ExpressionAttributeValues: expressionAttributeValues,
            Limit: limit,
            ScanIndexForward: false, // Сортировка по убыванию (новые сначала)
        }));
        if (!result.Items) {
            return [];
        }
        // Извлекаем события из payload
        const events = result.Items
            .map(item => item.payload)
            .filter((event) => event !== undefined);
        log.debug('Events retrieved from DynamoDB', {
            clientId,
            eventType,
            count: events.length,
        });
        return events;
    }
    catch (error) {
        log.error('Error getting events from DynamoDB', error, {
            clientId,
            eventType,
        });
        throw error;
    }
}
/**
 * Найти событие визита по sessionId
 */
async function findVisitBySessionId(clientId, sessionId) {
    const events = await getEvents(clientId, 'VISIT', 1000);
    const visitEvent = events.find((event) => event.type === 'VISIT' && event.sessionId === sessionId);
    return visitEvent || null;
}
//# sourceMappingURL=storage.js.map