"use strict";
/**
 * Единый логгер для микросервиса
 * Поддерживает префиксы для разных компонентов
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.logger = void 0;
class Logger {
    constructor(logLevel = 'info') {
        this.logLevel = logLevel;
    }
    setLogLevel(level) {
        this.logLevel = level;
    }
    shouldLog(level) {
        const levels = ['debug', 'info', 'warn', 'error'];
        return levels.indexOf(level) >= levels.indexOf(this.logLevel);
    }
    formatMessage(prefix, message, context) {
        const parts = [prefix, message];
        if (context) {
            const contextStr = Object.entries(context)
                .filter(([_, value]) => value !== undefined)
                .map(([key, value]) => `${key}=${JSON.stringify(value)}`)
                .join(' ');
            if (contextStr) {
                parts.push(`[${contextStr}]`);
            }
        }
        return parts.join(' ');
    }
    debug(message, context) {
        if (this.shouldLog('debug')) {
            console.debug(this.formatMessage('[DEBUG]', message, context));
        }
    }
    info(message, context) {
        if (this.shouldLog('info')) {
            console.info(this.formatMessage('[INFO]', message, context));
        }
    }
    warn(message, context) {
        if (this.shouldLog('warn')) {
            console.warn(this.formatMessage('[WARN]', message, context));
        }
    }
    error(message, error, context) {
        if (this.shouldLog('error')) {
            const errorContext = {
                ...context,
                error: error instanceof Error ? error.message : String(error),
                stack: error instanceof Error ? error.stack : undefined,
            };
            console.error(this.formatMessage('[ERROR]', message, errorContext));
        }
    }
    /**
     * Логирование с префиксом компонента
     */
    component(component) {
        return new ComponentLogger(this, component);
    }
}
/**
 * Логгер для конкретного компонента
 */
class ComponentLogger {
    constructor(logger, component) {
        this.logger = logger;
        this.component = component;
    }
    debug(message, context) {
        this.logger.debug(message, { ...context, component: this.component });
    }
    info(message, context) {
        this.logger.info(message, { ...context, component: this.component });
    }
    warn(message, context) {
        this.logger.warn(message, { ...context, component: this.component });
    }
    error(message, error, context) {
        this.logger.error(message, error, { ...context, component: this.component });
    }
}
// Singleton instance
exports.logger = new Logger(process.env.LOG_LEVEL || 'info');
//# sourceMappingURL=logger.js.map