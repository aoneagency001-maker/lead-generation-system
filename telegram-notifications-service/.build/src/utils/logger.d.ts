/**
 * Единый логгер для микросервиса
 * Поддерживает префиксы для разных компонентов
 */
type LogLevel = 'debug' | 'info' | 'warn' | 'error';
interface LogContext {
    requestId?: string;
    component?: string;
    [key: string]: unknown;
}
declare class Logger {
    private logLevel;
    constructor(logLevel?: LogLevel);
    setLogLevel(level: LogLevel): void;
    private shouldLog;
    private formatMessage;
    debug(message: string, context?: LogContext): void;
    info(message: string, context?: LogContext): void;
    warn(message: string, context?: LogContext): void;
    error(message: string, error?: Error | unknown, context?: LogContext): void;
    /**
     * Логирование с префиксом компонента
     */
    component(component: string): ComponentLogger;
}
/**
 * Логгер для конкретного компонента
 */
declare class ComponentLogger {
    private logger;
    private component;
    constructor(logger: Logger, component: string);
    debug(message: string, context?: LogContext): void;
    info(message: string, context?: LogContext): void;
    warn(message: string, context?: LogContext): void;
    error(message: string, error?: Error | unknown, context?: LogContext): void;
}
export declare const logger: Logger;
export {};
//# sourceMappingURL=logger.d.ts.map