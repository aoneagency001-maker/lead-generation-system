/**
 * Клиент для работы с Яндекс.Метрикой
 * Использует Logs API для получения данных в реальном времени
 */
interface MetrikaLogsApiParams {
    counterId: string;
    date1: string;
    date2: string;
    fields?: string[];
    source?: 'visits' | 'hits';
}
interface MetrikaLogsApiResponse {
    log_request_id: string;
    parts: number;
}
/**
 * Получить данные из Яндекс.Метрики через Logs API
 *
 * Документация: https://yandex.ru/dev/metrika/doc/api2/logs/about.html
 */
export declare function getMetrikaLogs(token: string, params: MetrikaLogsApiParams): Promise<MetrikaLogsApiResponse | null>;
/**
 * Получить готовые данные из Logs API
 * После создания запроса нужно дождаться обработки и скачать части
 */
export declare function downloadMetrikaLogPart(token: string, counterId: string, logRequestId: string, partNumber: number): Promise<string[][] | null>;
/**
 * Проверить статус запроса логов
 */
export declare function checkMetrikaLogStatus(token: string, counterId: string, logRequestId: string): Promise<'processed' | 'processing' | 'canceled' | null>;
/**
 * Получить список доступных полей для экспорта
 */
export declare function getMetrikaAvailableFields(token: string, counterId: string, source?: 'visits' | 'hits'): Promise<string[] | null>;
export {};
//# sourceMappingURL=metrika-client.d.ts.map