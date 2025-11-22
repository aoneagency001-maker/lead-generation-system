"use strict";
/**
 * Health check handler
 * GET /health
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.handler = handler;
const logger_1 = require("../utils/logger");
const log = logger_1.logger.component('HEALTH');
/**
 * Lambda handler
 */
async function handler(_event) {
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
//# sourceMappingURL=health.js.map