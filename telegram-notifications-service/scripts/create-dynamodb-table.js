#!/usr/bin/env node

/**
 * Скрипт для создания DynamoDB таблицы
 */

const { DynamoDBClient, CreateTableCommand } = require('@aws-sdk/client-dynamodb');

// ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения, не хардкод!
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_REGION = process.env.AWS_REGION || 'eu-central-1';

if (!AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.error('❌ Ошибка: AWS_ACCESS_KEY_ID и AWS_SECRET_ACCESS_KEY должны быть установлены в переменных окружения');
  console.error('   Установите: export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=...');
  process.exit(1);
}

const client = new DynamoDBClient({
  region: AWS_REGION,
  credentials: {
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
  },
});

async function createTable() {
  const tableName = 'telegram-notifications-events-dev';
  
  try {
    const command = new CreateTableCommand({
      TableName: tableName,
      AttributeDefinitions: [
        {
          AttributeName: 'pk',
          AttributeType: 'S',
        },
        {
          AttributeName: 'sk',
          AttributeType: 'S',
        },
      ],
      KeySchema: [
        {
          AttributeName: 'pk',
          KeyType: 'HASH',
        },
        {
          AttributeName: 'sk',
          KeyType: 'RANGE',
        },
      ],
      BillingMode: 'PAY_PER_REQUEST',
      TimeToLiveSpecification: {
        AttributeName: 'ttl',
        Enabled: true,
      },
      StreamSpecification: {
        StreamEnabled: true,
        StreamViewType: 'NEW_AND_OLD_IMAGES',
      },
      Tags: [
        {
          Key: 'Service',
          Value: 'telegram-notifications-service',
        },
        {
          Key: 'Stage',
          Value: 'dev',
        },
      ],
    });
    
    const response = await client.send(command);
    
    console.log('✅ Таблица DynamoDB создана:');
    console.log(`   Название: ${response.TableDescription.TableName}`);
    console.log(`   Статус: ${response.TableDescription.TableStatus}`);
    console.log(`   Регион: ${AWS_REGION}`);
    console.log('\n⏳ Ожидание активации таблицы...');
    
    // Ждём пока таблица станет активной
    let attempts = 0;
    while (attempts < 30) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const { DynamoDBClient: CheckClient, DescribeTableCommand } = require('@aws-sdk/client-dynamodb');
      const checkClient = new CheckClient({
        region: AWS_REGION,
        credentials: {
          accessKeyId: AWS_ACCESS_KEY_ID,
          secretAccessKey: AWS_SECRET_ACCESS_KEY,
        },
      });
      
      try {
        const { DescribeTableCommand: DescCmd } = require('@aws-sdk/client-dynamodb');
        const descResponse = await checkClient.send(new DescCmd({ TableName: tableName }));
        
        if (descResponse.Table.TableStatus === 'ACTIVE') {
          console.log('✅ Таблица активна и готова к использованию!');
          return true;
        }
        
        console.log(`   Статус: ${descResponse.Table.TableStatus}...`);
        attempts++;
      } catch (error) {
        console.error('Ошибка при проверке статуса:', error.message);
        break;
      }
    }
    
    return true;
  } catch (error) {
    if (error.name === 'ResourceInUseException') {
      console.log('✅ Таблица уже существует');
      return true;
    } else {
      console.error('❌ Ошибка при создании таблицы:', error.message);
      return false;
    }
  }
}

createTable().then(success => {
  process.exit(success ? 0 : 1);
});

