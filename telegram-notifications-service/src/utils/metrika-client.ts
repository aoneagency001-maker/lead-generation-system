/**
 * Клиент для работы с Яндекс.Метрикой
 * Использует Logs API для получения данных в реальном времени
 */

import axios from 'axios';
import { logger } from './logger';

const log = logger.component('METRIKA-CLIENT');

interface MetrikaLogsApiParams {
  counterId: string;
  date1: string; // YYYY-MM-DD
  date2: string; // YYYY-MM-DD
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
export async function getMetrikaLogs(
  token: string,
  params: MetrikaLogsApiParams
): Promise<MetrikaLogsApiResponse | null> {
  try {
    const response = await axios.post(
      'https://api-metrika.yandex.net/logs/v1/export/visits',
      {
        date1: params.date1,
        date2: params.date2,
        fields: params.fields || [
          'ym:s:visitID',
          'ym:s:clientID',
          'ym:s:dateTime',
          'ym:s:UTMSource',
          'ym:s:UTMMedium',
          'ym:s:UTMCampaign',
          'ym:s:UTMTerm',
          'ym:s:UTMContent',
          'ym:s:pageURL',
          'ym:s:referer',
          'ym:s:ipAddress',
          'ym:s:regionCountry',
          'ym:s:regionCity',
        ],
      },
      {
        headers: {
          'Authorization': `OAuth ${token}`,
          'Content-Type': 'application/json',
        },
        params: {
          counter_id: params.counterId,
        },
        timeout: 30000,
      }
    );
    
    log.info('Metrika logs request created', {
      logRequestId: response.data.log_request_id,
      parts: response.data.parts,
    });
    
    return response.data;
  } catch (error) {
    log.error('Error requesting Metrika logs', error, {
      counterId: params.counterId,
    });
    return null;
  }
}

/**
 * Получить готовые данные из Logs API
 * После создания запроса нужно дождаться обработки и скачать части
 */
export async function downloadMetrikaLogPart(
  token: string,
  counterId: string,
  logRequestId: string,
  partNumber: number
): Promise<string[][] | null> {
  try {
    const response = await axios.get(
      `https://api-metrika.yandex.net/logs/v1/export/${logRequestId}/part/${partNumber}/download`,
      {
        headers: {
          'Authorization': `OAuth ${token}`,
        },
        params: {
          counter_id: counterId,
        },
        timeout: 60000,
      }
    );
    
    // Данные приходят в формате TSV (tab-separated values)
    const lines = response.data.split('\n').filter((line: string) => line.trim());
    const data = lines.map((line: string) => line.split('\t'));
    
    log.debug('Metrika log part downloaded', {
      logRequestId,
      partNumber,
      rows: data.length,
    });
    
    return data;
  } catch (error) {
    log.error('Error downloading Metrika log part', error, {
      logRequestId,
      partNumber,
    });
    return null;
  }
}

/**
 * Проверить статус запроса логов
 */
export async function checkMetrikaLogStatus(
  token: string,
  counterId: string,
  logRequestId: string
): Promise<'processed' | 'processing' | 'canceled' | null> {
  try {
    const response = await axios.get(
      `https://api-metrika.yandex.net/logs/v1/export/${logRequestId}/status`,
      {
        headers: {
          'Authorization': `OAuth ${token}`,
        },
        params: {
          counter_id: counterId,
        },
        timeout: 10000,
      }
    );
    
    return response.data.status;
  } catch (error) {
    log.error('Error checking Metrika log status', error, {
      logRequestId,
    });
    return null;
  }
}

/**
 * Получить список доступных полей для экспорта
 */
export async function getMetrikaAvailableFields(
  token: string,
  counterId: string,
  source: 'visits' | 'hits' = 'visits'
): Promise<string[] | null> {
  try {
    const response = await axios.get(
      `https://api-metrika.yandex.net/logs/v1/export/${source}/fields`,
      {
        headers: {
          'Authorization': `OAuth ${token}`,
        },
        params: {
          counter_id: counterId,
        },
        timeout: 10000,
      }
    );
    
    return response.data.map((field: { name: string }) => field.name);
  } catch (error) {
    log.error('Error getting Metrika available fields', error, {
      counterId,
      source,
    });
    return null;
  }
}

