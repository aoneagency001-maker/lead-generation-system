#!/usr/bin/env node

/**
 * Скрипт для настройки AWS SSM параметров и получения Chat ID
 */

const { SSMClient, PutParameterCommand } = require('@aws-sdk/client-ssm');
const axios = require('axios');

// ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const AWS_ACCESS_KEY_ID = process.env.AWS_ACCESS_KEY_ID;
const AWS_SECRET_ACCESS_KEY = process.env.AWS_SECRET_ACCESS_KEY;
const AWS_REGION = process.env.AWS_REGION || 'eu-central-1';

if (!TELEGRAM_BOT_TOKEN || !AWS_ACCESS_KEY_ID || !AWS_SECRET_ACCESS_KEY) {
  console.error('❌ Ошибка: Требуются переменные окружения:');
  console.error('   - TELEGRAM_BOT_TOKEN');
  console.error('   - AWS_ACCESS_KEY_ID');
  console.error('   - AWS_SECRET_ACCESS_KEY');
  console.error('\n   Установите: export TELEGRAM_BOT_TOKEN=... && export AWS_ACCESS_KEY_ID=... && export AWS_SECRET_ACCESS_KEY=...');
  process.exit(1);
}

const ssmClient = new SSMClient({
  region: AWS_REGION,
  credentials: {
    accessKeyId: AWS_ACCESS_KEY_ID,
    secretAccessKey: AWS_SECRET_ACCESS_KEY,
  },
});

async function getChatId() {
  console.log('🔍 Получение Chat ID через Telegram API...');
  
  try {
    // Пробуем получить последние обновления
    const updatesResponse = await axios.get(
      `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates`
    );
    
    if (updatesResponse.data.ok && updatesResponse.data.result.length > 0) {
      const lastUpdate = updatesResponse.data.result[updatesResponse.data.result.length - 1];
      if (lastUpdate.message && lastUpdate.message.chat) {
        const chatId = lastUpdate.message.chat.id.toString();
        console.log(`✅ Chat ID найден: ${chatId}`);
        return chatId;
      }
    }
    
    // Если обновлений нет, пробуем отправить сообщение самому себе
    console.log('⚠️  Обновлений не найдено. Пожалуйста, отправьте любое сообщение боту @leadlovebot');
    console.log('   Затем запустите скрипт снова или укажите Chat ID вручную.');
    
    // Пробуем получить информацию о боте
    const botInfo = await axios.get(
      `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe`
    );
    
    console.log(`\n📱 Бот: @${botInfo.data.result.username}`);
    console.log(`   Напишите боту любое сообщение, затем запустите скрипт снова.\n`);
    
    return null;
  } catch (error) {
    console.error('❌ Ошибка при получении Chat ID:', error.message);
    return null;
  }
}

async function putSSMParameter(name, value, type = 'String') {
  try {
    await ssmClient.send(
      new PutParameterCommand({
        Name: name,
        Value: value,
        Type: type,
        Overwrite: true,
      })
    );
    console.log(`✅ Параметр сохранён: ${name}`);
    return true;
  } catch (error) {
    console.error(`❌ Ошибка при сохранении ${name}:`, error.message);
    return false;
  }
}

async function main() {
  console.log('🚀 Настройка AWS SSM параметров...\n');
  
  // Получаем Chat ID
  let chatId = await getChatId();
  
  if (!chatId) {
    console.log('\n💡 Если вы знаете Chat ID, можете указать его вручную:');
    console.log('   node scripts/setup-aws.js <chat_id>\n');
    
    // Проверяем аргумент командной строки
    if (process.argv[2]) {
      chatId = process.argv[2];
      console.log(`📝 Используется Chat ID из аргумента: ${chatId}\n`);
    } else {
      console.log('⚠️  Chat ID не найден. Пропускаем сохранение TELEGRAM_CHAT_ID.');
      console.log('   Вы можете сохранить его позже вручную.\n');
    }
  }
  
  // Сохраняем параметры в SSM
  const results = [];
  
  // Telegram Bot Token
  results.push(
    await putSSMParameter(
      '/telegram-notifications/BOT_TOKEN',
      TELEGRAM_BOT_TOKEN,
      'SecureString'
    )
  );
  
  // Telegram Chat ID (если получен)
  if (chatId) {
    results.push(
      await putSSMParameter(
        '/telegram-notifications/CHAT_ID',
        chatId,
        'String'
      )
    );
  }
  
  // Метрика (опционально, не создаём если не указаны)
  // Эти параметры можно добавить позже если понадобятся
  
  console.log('\n📊 Результаты:');
  const successCount = results.filter(r => r).length;
  const totalCount = results.length;
  
  if (successCount === totalCount) {
    console.log(`✅ Все параметры успешно сохранены (${successCount}/${totalCount})`);
  } else {
    console.log(`⚠️  Сохранено параметров: ${successCount}/${totalCount}`);
  }
  
  console.log('\n📝 Созданные параметры:');
  console.log('   - /telegram-notifications/BOT_TOKEN');
  if (chatId) {
    console.log('   - /telegram-notifications/CHAT_ID');
  }
  console.log('\n💡 Для добавления параметров Метрики используйте:');
  console.log('   aws ssm put-parameter --name "/telegram-notifications/METRIKA_TOKEN" --value "..." --type "SecureString"');
  
  console.log('\n✅ Настройка завершена!');
}

main().catch(console.error);

