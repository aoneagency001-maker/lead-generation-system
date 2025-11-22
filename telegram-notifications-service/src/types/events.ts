/**
 * Единые типы событий для микросервиса
 * Основа для всех типов событий: VISIT, FORM, QUIZ, METRIKA
 */

/**
 * Базовый тип события
 */
export interface BaseEvent {
  id: string;
  clientId: string;
  timestamp: string; // ISO 8601
  source: 'tracker' | 'tilda' | 'metrika' | 'manual';
}

/**
 * Событие визита (VISIT)
 */
export interface VisitEvent extends BaseEvent {
  type: 'VISIT';
  
  // Сессия
  sessionId?: string;
  
  // Геолокация
  ip: string;
  country: string;
  city: string;
  region?: string;
  timezone?: string;
  isp?: string;
  
  // Устройство и браузер
  userAgent: string;
  device: 'mobile' | 'tablet' | 'desktop';
  browser?: string;
  os?: string;
  screenResolution?: string;
  
  // Навигация
  referrer: string | null;
  page: string;
  landingPage: string;
  
  // UTM метки
  utmSource?: string | null;
  utmMedium?: string | null;
  utmCampaign?: string | null;
  utmTerm?: string | null;
  utmContent?: string | null;
  
  // Поведение
  timeOnSite?: number; // секунды
  clicks?: number;
  pagesViewed?: number;
  conversions?: string[];
  
  // Детальные события
  clickEvents?: ClickEvent[];
  conversionEvents?: ConversionEvent[];
}

/**
 * Событие формы (FORM)
 */
export interface FormEvent extends BaseEvent {
  type: 'FORM';
  
  formType: 'contact' | 'callback' | 'custom' | 'quiz';
  
  // Контактные данные
  name?: string;
  email?: string;
  phone?: string;
  message?: string;
  
  // Для квизов
  answers?: Record<string, unknown>;
  
  // Контекст
  ip: string;
  userAgent: string;
  pageUrl?: string;
  formName?: string;
  submittedAt: string;
}

/**
 * Событие из Яндекс.Метрики (METRIKA)
 */
export interface MetrikaEvent extends BaseEvent {
  type: 'METRIKA';
  
  // Данные из Метрики
  counterId: string;
  visitId?: string;
  sessionId?: string;
  
  // События
  eventName?: string;
  eventParams?: Record<string, unknown>;
  
  // Обогащенные данные
  enriched?: boolean; // были ли данные обогащены из нашей БД
  matchedVisitId?: string; // ID визита из нашей БД, если найден
}

/**
 * Детальное событие клика
 */
export interface ClickEvent {
  element: string; // селектор или ID элемента
  type: string; // 'button', 'link', 'form', etc.
  timestamp: string; // ISO 8601
  page?: string;
}

/**
 * Событие конверсии
 */
export interface ConversionEvent {
  type: string; // 'purchase', 'signup', 'download', etc.
  data: Record<string, unknown>;
  timestamp: string; // ISO 8601
  value?: number; // стоимость конверсии
}

/**
 * Union тип всех событий
 */
export type Event = VisitEvent | FormEvent | MetrikaEvent;

/**
 * Тип события для определения типа
 */
export type EventType = 'VISIT' | 'FORM' | 'METRIKA';

