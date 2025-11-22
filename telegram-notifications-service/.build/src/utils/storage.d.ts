/**
 * Storage для DynamoDB
 * Обёртка над AWS SDK для работы с событиями
 */
import { Event, EventType } from '../types/events';
/**
 * Сохранить событие в DynamoDB
 *
 * Структура ключей:
 * - pk (partition key) = clientId
 * - sk (sort key) = type#timestamp#id
 */
export declare function saveEvent(event: Event): Promise<void>;
/**
 * Получить события по clientId и типу
 */
export declare function getEvents(clientId: string, eventType?: EventType, limit?: number): Promise<Event[]>;
/**
 * Найти событие визита по sessionId
 */
export declare function findVisitBySessionId(clientId: string, sessionId: string): Promise<Event | null>;
//# sourceMappingURL=storage.d.ts.map