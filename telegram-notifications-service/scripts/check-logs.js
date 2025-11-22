#!/usr/bin/env node

/**
 * Скрипт для проверки логов CloudWatch
 */

const { CloudWatchLogsClient, GetLogEventsCommand } = require('@aws-sdk/client-cloudwatch-logs');

// ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_REGION = process.env.AWS_REGION || 'eu-central-1';

if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.error('❌ Ошибка: AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY должны быть установлены');
  process.exit(1);
}

const client = new CloudWatchLogsClient({
  region: AWS_REGION,
  credentials: {
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
  },
});

async function getLogs(functionName) {
  const logGroupName = `/aws/lambda/telegram-notifications-service-dev-${functionName}`;
  
  try {
    const command = new GetLogEventsCommand({
      logGroupName,
      logStreamName: 'latest', // Попробуем получить последние логи
      limit: 20,
      startFromHead: false,
    });
    
    const response = await client.send(command);
    
    if (response.events && response.events.length > 0) {
      console.log(`\n📋 Последние логи для ${functionName}:`);
      console.log('─'.repeat(60));
      response.events.slice(-10).forEach(event => {
        console.log(event.message);
      });
    } else {
      console.log(`\n⚠️  Логи для ${functionName} не найдены или пусты`);
    }
  } catch (error) {
    if (error.name === 'ResourceNotFoundException') {
      console.log(`\n⚠️  Log group не найден: ${logGroupName}`);
      console.log('   Возможно функция ещё не была вызвана');
    } else {
      console.error(`\n❌ Ошибка при получении логов для ${functionName}:`, error.message);
    }
  }
}

async function main() {
  console.log('🔍 Проверка логов CloudWatch...\n');
  
  await getLogs('trackVisitor');
  await getLogs('tildaWebhook');
  await getLogs('health');
  
  console.log('\n💡 Для просмотра всех логов используйте AWS Console:');
  console.log('   https://console.aws.amazon.com/cloudwatch/');
}

main().catch(console.error);

