#!/usr/bin/env node

/**
 * Скрипт для проверки DynamoDB таблицы
 */

const { DynamoDBClient, DescribeTableCommand } = require('@aws-sdk/client-dynamodb');

// ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_REGION = process.env.AWS_REGION || 'eu-central-1';

if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.error('❌ Ошибка: AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY должны быть установлены');
  process.exit(1);
}

const client = new DynamoDBClient({
  region: AWS_REGION,
  credentials: {
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
  },
});

async function checkTable() {
  const tableName = 'telegram-notifications-events-dev';
  
  try {
    const command = new DescribeTableCommand({
      TableName: tableName,
    });
    
    const response = await client.send(command);
    
    console.log('✅ Таблица DynamoDB найдена:');
    console.log(`   Название: ${response.Table.TableName}`);
    console.log(`   Статус: ${response.Table.TableStatus}`);
    console.log(`   Регион: ${AWS_REGION}`);
    console.log(`   Billing Mode: ${response.Table.BillingModeSummary?.BillingMode || 'N/A'}`);
    console.log(`   Item Count: ${response.Table.ItemCount || 0}`);
    
    return true;
  } catch (error) {
    if (error.name === 'ResourceNotFoundException') {
      console.error(`❌ Таблица ${tableName} не найдена!`);
      console.error('   Возможно она не была создана при деплое.');
      return false;
    } else {
      console.error(`❌ Ошибка при проверке таблицы:`, error.message);
      return false;
    }
  }
}

checkTable().then(success => {
  process.exit(success ? 0 : 1);
});

