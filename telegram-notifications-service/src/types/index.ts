/**
 * Экспорт всех типов
 */

export * from './events';

/**
 * Ответ API
 */
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  requestId?: string;
}

/**
 * Конфигурация сервиса
 */
export interface ServiceConfig {
  telegram: {
    botToken: string;
    chatId: string;
  };
  dynamodb: {
    tableName: string;
    region: string;
  };
  metrika?: {
    token: string;
    counterId: string;
  };
  tilda?: {
    secret?: string;
  };
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

