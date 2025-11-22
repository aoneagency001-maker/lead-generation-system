/**
 * Health check handler
 * GET /health
 */

import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { logger } from '../utils/logger';

const log = logger.component('HEALTH');

/**
 * Lambda handler
 */
export async function handler(
  _event: APIGatewayProxyEvent
): Promise<APIGatewayProxyResult> {
  log.info('Health check requested');
  
  const health = {
    status: 'ok',
    service: 'telegram-notifications-service',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development',
    checks: {
      dynamodb: !!process.env.DYNAMODB_TABLE,
      telegram: !!(process.env.TELEGRAM_BOT_TOKEN && process.env.TELEGRAM_CHAT_ID),
    },
  };
  
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(health),
  };
}

