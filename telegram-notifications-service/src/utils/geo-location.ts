/**
 * Геолокация по IP адресу
 * Использует бесплатный сервис ip-api.com
 */

import axios from 'axios';
import { logger } from './logger';
import { isLocalIP } from './validators';

const log = logger.component('GEO-LOCATION');

interface GeoLocationData {
  city: string | null;
  country: string | null;
  region?: string | null;
  timezone?: string | null;
  isp?: string | null;
}

// Кэш для избежания повторных запросов (в Lambda это будет работать только в рамках одного инстанса)
const cache = new Map<string, { data: GeoLocationData; timestamp: number }>();
const CACHE_TTL = 3600000; // 1 час в миллисекундах

/**
 * Получить геолокацию по IP
 */
export async function getGeoLocation(ip: string | undefined | null): Promise<GeoLocationData> {
  if (!ip || isLocalIP(ip)) {
    log.debug('Local IP or no IP provided', { ip });
    return {
      city: null,
      country: null,
      region: null,
      timezone: null,
      isp: null,
    };
  }
  
  // Проверяем кэш
  const cached = cache.get(ip);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    log.debug('Using cached geo location', { ip });
    return cached.data;
  }
  
  try {
    const response = await axios.get(`http://ip-api.com/json/${ip}`, {
      params: {
        fields: 'status,message,city,country,countryCode,region,regionName,timezone,isp',
      },
      timeout: 5000,
    });
    
    if (response.data.status === 'success') {
      const data: GeoLocationData = {
        city: response.data.city || null,
        country: response.data.country || null,
        region: response.data.regionName || null,
        timezone: response.data.timezone || null,
        isp: response.data.isp || null,
      };
      
      // Сохраняем в кэш
      cache.set(ip, { data, timestamp: Date.now() });
      
      log.debug('Geo location retrieved', { ip, ...data });
      return data;
    } else {
      log.warn('Geo API returned error', { ip, message: response.data.message });
      return {
        city: null,
        country: null,
        region: null,
        timezone: null,
        isp: null,
      };
    }
  } catch (error) {
    log.error('Error getting geo location', error, { ip });
    return {
      city: null,
      country: null,
      region: null,
      timezone: null,
      isp: null,
    };
  }
}

/**
 * Очистить кэш (для тестирования)
 */
export function clearGeoCache(): void {
  cache.clear();
}

