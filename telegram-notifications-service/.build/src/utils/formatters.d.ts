/**
 * Форматтеры сообщений для Telegram
 * Единый стиль для всех типов событий
 */
import { VisitEvent, FormEvent, MetrikaEvent } from '../types/events';
/**
 * Форматировать сообщение о визите
 */
export declare function formatVisitorMessage(event: VisitEvent, clientName?: string): string;
/**
 * Форматировать сообщение о форме
 */
export declare function formatContactMessage(event: FormEvent, clientName?: string): string;
/**
 * Форматировать сообщение о событии из Метрики
 */
export declare function formatMetrikaMessage(event: MetrikaEvent, clientName?: string): string;
//# sourceMappingURL=formatters.d.ts.map