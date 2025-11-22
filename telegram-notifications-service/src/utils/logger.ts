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

class Logger {
  private logLevel: LogLevel;

  constructor(logLevel: LogLevel = 'info') {
    this.logLevel = logLevel;
  }

  setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  private shouldLog(level: LogLevel): boolean {
    const levels: LogLevel[] = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.logLevel);
  }

  private formatMessage(prefix: string, message: string, context?: LogContext): string {
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

  debug(message: string, context?: LogContext): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatMessage('[DEBUG]', message, context));
    }
  }

  info(message: string, context?: LogContext): void {
    if (this.shouldLog('info')) {
      console.info(this.formatMessage('[INFO]', message, context));
    }
  }

  warn(message: string, context?: LogContext): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatMessage('[WARN]', message, context));
    }
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
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
  component(component: string): ComponentLogger {
    return new ComponentLogger(this, component);
  }
}

/**
 * Логгер для конкретного компонента
 */
class ComponentLogger {
  constructor(
    private logger: Logger,
    private component: string
  ) {}

  debug(message: string, context?: LogContext): void {
    this.logger.debug(message, { ...context, component: this.component });
  }

  info(message: string, context?: LogContext): void {
    this.logger.info(message, { ...context, component: this.component });
  }

  warn(message: string, context?: LogContext): void {
    this.logger.warn(message, { ...context, component: this.component });
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    this.logger.error(message, error, { ...context, component: this.component });
  }
}

// Singleton instance
export const logger = new Logger(
  (process.env.LOG_LEVEL as LogLevel) || 'info'
);

