/**
 * Геолокация по IP адресу
 * Использует бесплатный сервис ip-api.com
 */
interface GeoLocationData {
    city: string | null;
    country: string | null;
    region?: string | null;
    timezone?: string | null;
    isp?: string | null;
}
/**
 * Получить геолокацию по IP
 */
export declare function getGeoLocation(ip: string | undefined | null): Promise<GeoLocationData>;
/**
 * Очистить кэш (для тестирования)
 */
export declare function clearGeoCache(): void;
export {};
//# sourceMappingURL=geo-location.d.ts.map