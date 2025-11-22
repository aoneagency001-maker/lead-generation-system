/**
 * Валидаторы для входящих данных
 */
/**
 * Проверка валидности IP адреса
 */
export declare function isValidIP(ip: string | undefined | null): boolean;
/**
 * Проверка является ли User-Agent ботом
 */
export declare function isBot(userAgent: string | undefined | null): boolean;
/**
 * Определение типа устройства
 */
export declare function getDeviceType(userAgent: string | undefined | null): 'mobile' | 'tablet' | 'desktop';
/**
 * Проверка является ли IP локальным
 */
export declare function isLocalIP(ip: string): boolean;
/**
 * Валидация clientId
 */
export declare function isValidClientId(clientId: string | undefined | null): boolean;
/**
 * Валидация payload от Tilda
 */
export declare function validateTildaPayload(payload: unknown): payload is {
    name?: string;
    phone?: string;
    email?: string;
    message?: string;
    formName?: string;
    pageUrl?: string;
    [key: string]: unknown;
};
/**
 * Валидация payload от track-visitor
 */
export declare function validateTrackVisitorPayload(payload: unknown): payload is {
    clientId: string;
    page?: string;
    landingPage?: string;
    referrer?: string;
    screenResolution?: string;
    sessionId?: string;
    utmSource?: string;
    utmMedium?: string;
    utmCampaign?: string;
    utmTerm?: string;
    utmContent?: string;
    isFirstVisit?: boolean;
    [key: string]: unknown;
};
//# sourceMappingURL=validators.d.ts.map