/**
 * Storage для DynamoDB
 * Обёртка над AWS SDK для работы с событиями
 */

import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { Event, EventType } from '../types/events';
import { logger } from './logger';

const log = logger.component('STORAGE');

let client: DynamoDBDocumentClient | null = null;

/**
 * Инициализация DynamoDB клиента
 */
function getClient(): DynamoDBDocumentClient {
  if (!client) {
    // AWS_REGION автоматически доступен в Lambda
    const dynamoClient = new DynamoDBClient({
      region: process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'eu-central-1',
    });
    
    client = DynamoDBDocumentClient.from(dynamoClient);
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
export async function saveEvent(event: Event): Promise<void> {
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
    await docClient.send(new PutCommand({
      TableName: tableName,
      Item: item,
    }));
    
    log.info('Event saved to DynamoDB', {
      eventId: event.id,
      eventType: event.type,
      clientId: event.clientId,
    });
  } catch (error) {
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
export async function getEvents(
  clientId: string,
  eventType?: EventType,
  limit: number = 100
): Promise<Event[]> {
  const tableName = process.env.DYNAMODB_TABLE;
  
  if (!tableName) {
    throw new Error('DYNAMODB_TABLE environment variable is not set');
  }
  
  const docClient = getClient();
  
  let keyConditionExpression = 'pk = :clientId';
  const expressionAttributeValues: Record<string, string> = {
    ':clientId': clientId,
  };
  
  // Если указан тип события, фильтруем по нему
  if (eventType) {
    keyConditionExpression += ' AND begins_with(sk, :eventType)';
    expressionAttributeValues[':eventType'] = `${eventType}#`;
  }
  
  try {
    const result = await docClient.send(new QueryCommand({
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
      .map(item => item.payload as Event)
      .filter((event): event is Event => event !== undefined);
    
    log.debug('Events retrieved from DynamoDB', {
      clientId,
      eventType,
      count: events.length,
    });
    
    return events;
  } catch (error) {
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
export async function findVisitBySessionId(
  clientId: string,
  sessionId: string
): Promise<Event | null> {
  const events = await getEvents(clientId, 'VISIT', 1000);
  
  const visitEvent = events.find(
    (event): event is Extract<Event, { type: 'VISIT' }> =>
      event.type === 'VISIT' && event.sessionId === sessionId
  );
  
  return visitEvent || null;
}

