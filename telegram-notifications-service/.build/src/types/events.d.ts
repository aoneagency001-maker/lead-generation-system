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
    timestamp: string;
    source: 'tracker' | 'tilda' | 'metrika' | 'manual';
}
/**
 * Событие визита (VISIT)
 */
export interface VisitEvent extends BaseEvent {
    type: 'VISIT';
    sessionId?: string;
    ip: string;
    country: string;
    city: string;
    region?: string;
    timezone?: string;
    isp?: string;
    userAgent: string;
    device: 'mobile' | 'tablet' | 'desktop';
    browser?: string;
    os?: string;
    screenResolution?: string;
    referrer: string | null;
    page: string;
    landingPage: string;
    utmSource?: string | null;
    utmMedium?: string | null;
    utmCampaign?: string | null;
    utmTerm?: string | null;
    utmContent?: string | null;
    timeOnSite?: number;
    clicks?: number;
    pagesViewed?: number;
    conversions?: string[];
    clickEvents?: ClickEvent[];
    conversionEvents?: ConversionEvent[];
}
/**
 * Событие формы (FORM)
 */
export interface FormEvent extends BaseEvent {
    type: 'FORM';
    formType: 'contact' | 'callback' | 'custom' | 'quiz';
    name?: string;
    email?: string;
    phone?: string;
    message?: string;
    answers?: Record<string, unknown>;
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
    counterId: string;
    visitId?: string;
    sessionId?: string;
    eventName?: string;
    eventParams?: Record<string, unknown>;
    enriched?: boolean;
    matchedVisitId?: string;
}
/**
 * Детальное событие клика
 */
export interface ClickEvent {
    element: string;
    type: string;
    timestamp: string;
    page?: string;
}
/**
 * Событие конверсии
 */
export interface ConversionEvent {
    type: string;
    data: Record<string, unknown>;
    timestamp: string;
    value?: number;
}
/**
 * Union тип всех событий
 */
export type Event = VisitEvent | FormEvent | MetrikaEvent;
/**
 * Тип события для определения типа
 */
export type EventType = 'VISIT' | 'FORM' | 'METRIKA';
//# sourceMappingURL=events.d.ts.map