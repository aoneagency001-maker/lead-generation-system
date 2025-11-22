#!/usr/bin/env node

/**
 * Скрипт для получения Chat ID
 * Отправьте боту @leadlovebot любое сообщение, затем запустите этот скрипт
 */

const axios = require('axios');

// ⚠️ БЕЗОПАСНОСТЬ: Используем переменные окружения
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;

if (!TELEGRAM_BOT_TOKEN) {
  console.error('❌ Ошибка: TELEGRAM_BOT_TOKEN должен быть установлен в переменных окружения');
  console.error('   Установите: export TELEGRAM_BOT_TOKEN=...');
  process.exit(1);
}

async function getChatId() {
  console.log('🔍 Получение Chat ID...\n');
  console.log('📱 Убедитесь, что вы отправили боту @leadlovebot любое сообщение!\n');
  
  try {
    const response = await axios.get(
      `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates`,
      { timeout: 5000 }
    );
    
    if (response.data.ok && response.data.result.length > 0) {
      const updates = response.data.result;
      const chatIds = new Set();
      
      updates.forEach(update => {
        if (update.message && update.message.chat) {
          chatIds.add(update.message.chat.id);
        }
      });
      
      if (chatIds.size > 0) {
        console.log('✅ Найдены Chat ID:');
        chatIds.forEach(id => {
          console.log(`   ${id}`);
        });
        
        const firstChatId = Array.from(chatIds)[0];
        console.log(`\n💡 Используйте первый Chat ID: ${firstChatId}`);
        console.log(`\n📝 Для сохранения в SSM запустите:`);
        console.log(`   node scripts/setup-aws.js ${firstChatId}\n`);
        
        return firstChatId;
      }
    }
    
    console.log('⚠️  Обновлений не найдено.');
    console.log('\n📝 Инструкция:');
    console.log('   1. Откройте Telegram');
    console.log('   2. Найдите бота @leadlovebot');
    console.log('   3. Отправьте ему любое сообщение (например: /start)');
    console.log('   4. Запустите этот скрипт снова\n');
    
    return null;
  } catch (error) {
    console.error('❌ Ошибка:', error.message);
    return null;
  }
}

getChatId();

