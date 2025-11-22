/**
 * Форматтеры сообщений для Telegram
 * Единый стиль для всех типов событий
 */

import { VisitEvent, FormEvent, MetrikaEvent } from '../types/events';

/**
 * Форматировать сообщение о визите
 */
export function formatVisitorMessage(event: VisitEvent, clientName?: string): string {
  const parts: string[] = [];
  
  // Заголовок
  const icon = event.source === 'tracker' ? '👤' : '🤖';
  parts.push(`${icon} <b>Новый посетитель</b>`);
  
  if (clientName) {
    parts.push(`<b>Клиент:</b> ${clientName}`);
  }
  
  parts.push('');
  
  // Тип визита
  const visitIcon = event.conversions && event.conversions.length > 0 ? '🎯' : '🆕';
  const visitType = event.conversions && event.conversions.length > 0
    ? 'Конверсия!'
    : 'Новый визит';
  parts.push(`${visitIcon} <b>Тип:</b> ${visitType}`);
  
  // Устройство
  const deviceIcons = {
    mobile: '📱',
    tablet: '📱',
    desktop: '💻',
  };
  const deviceIcon = deviceIcons[event.device] || '💻';
  parts.push(`${deviceIcon} <b>Устройство:</b> ${event.device}`);
  
  // Геолокация
  if (event.city || event.country) {
    const location = [event.city, event.country].filter(Boolean).join(', ');
    parts.push(`📍 <b>Местоположение:</b> ${location}`);
  }
  
  // Страница
  if (event.page) {
    parts.push(`📄 <b>Страница:</b> ${event.page}`);
  }
  
  // Реферер
  if (event.referrer) {
    const referrer = event.referrer.length > 50
      ? event.referrer.substring(0, 47) + '...'
      : event.referrer;
    parts.push(`🔗 <b>Источник:</b> ${referrer}`);
  }
  
  // UTM метки
  const utmParts: string[] = [];
  if (event.utmSource) utmParts.push(`Source: ${event.utmSource}`);
  if (event.utmMedium) utmParts.push(`Medium: ${event.utmMedium}`);
  if (event.utmCampaign) utmParts.push(`Campaign: ${event.utmCampaign}`);
  
  if (utmParts.length > 0) {
    parts.push(`📊 <b>UTM:</b> ${utmParts.join(' | ')}`);
  }
  
  // Разрешение экрана
  if (event.screenResolution) {
    parts.push(`🖥️ <b>Разрешение:</b> ${event.screenResolution}`);
  }
  
  // Поведение
  if (event.timeOnSite) {
    const minutes = Math.floor(event.timeOnSite / 60);
    const seconds = event.timeOnSite % 60;
    parts.push(`⏱️ <b>Время на сайте:</b> ${minutes}м ${seconds}с`);
  }
  
  if (event.pagesViewed && event.pagesViewed > 1) {
    parts.push(`📚 <b>Просмотрено страниц:</b> ${event.pagesViewed}`);
  }
  
  // Конверсии
  if (event.conversions && event.conversions.length > 0) {
    parts.push(`🎯 <b>Конверсии:</b> ${event.conversions.join(', ')}`);
  }
  
  // Источник
  parts.push(`🔌 <b>Источник:</b> ${event.source}`);
  
  // Время
  const date = new Date(event.timestamp);
  parts.push(`🕐 <b>Время:</b> ${date.toLocaleString('ru-RU')}`);
  
  return parts.join('\n');
}

/**
 * Форматировать сообщение о форме
 */
export function formatContactMessage(event: FormEvent, clientName?: string): string {
  const parts: string[] = [];
  
  // Заголовок
  const icon = event.formType === 'quiz' ? '🎯' : '📝';
  parts.push(`${icon} <b>Новая заявка${event.formType === 'quiz' ? ' (квиз)' : ''}!</b>`);
  
  if (clientName) {
    parts.push(`<b>Клиент:</b> ${clientName}`);
  }
  
  parts.push('');
  
  // Имя
  if (event.name) {
    parts.push(`👤 <b>Имя:</b> ${event.name}`);
  }
  
  // Телефон
  if (event.phone) {
    parts.push(`📞 <b>Телефон:</b> ${event.phone}`);
  }
  
  // Email
  if (event.email) {
    parts.push(`📧 <b>Email:</b> ${event.email}`);
  }
  
  // Сообщение
  if (event.message) {
    parts.push(`💬 <b>Сообщение:</b>\n${event.message}`);
  }
  
  // Ответы квиза
  if (event.formType === 'quiz' && event.answers) {
    parts.push(`📋 <b>Ответы:</b>`);
    for (const [question, answer] of Object.entries(event.answers)) {
      parts.push(`  • ${question}: ${JSON.stringify(answer)}`);
    }
  }
  
  // Форма
  if (event.formName) {
    parts.push(`📝 <b>Форма:</b> ${event.formName}`);
  }
  
  // URL страницы
  if (event.pageUrl) {
    const url = event.pageUrl.length > 50
      ? event.pageUrl.substring(0, 47) + '...'
      : event.pageUrl;
    parts.push(`🔗 <b>Страница:</b> ${url}`);
  }
  
  // Источник
  parts.push(`🔌 <b>Источник:</b> ${event.source}`);
  
  // Время
  const date = new Date(event.submittedAt || event.timestamp);
  parts.push(`🕐 <b>Время:</b> ${date.toLocaleString('ru-RU')}`);
  
  return parts.join('\n');
}

/**
 * Форматировать сообщение о событии из Метрики
 */
export function formatMetrikaMessage(event: MetrikaEvent, clientName?: string): string {
  const parts: string[] = [];
  
  // Заголовок
  parts.push(`📊 <b>Событие из Яндекс.Метрики</b>`);
  
  if (clientName) {
    parts.push(`<b>Клиент:</b> ${clientName}`);
  }
  
  parts.push('');
  
  // Название события
  if (event.eventName) {
    parts.push(`🎯 <b>Событие:</b> ${event.eventName}`);
  }
  
  // Параметры
  if (event.eventParams && Object.keys(event.eventParams).length > 0) {
    parts.push(`📋 <b>Параметры:</b>`);
    for (const [key, value] of Object.entries(event.eventParams)) {
      parts.push(`  • ${key}: ${JSON.stringify(value)}`);
    }
  }
  
  // Обогащенные данные
  if (event.enriched && event.matchedVisitId) {
    parts.push(`🔗 <b>Связано с визитом:</b> ${event.matchedVisitId}`);
  }
  
  // Время
  const date = new Date(event.timestamp);
  parts.push(`🕐 <b>Время:</b> ${date.toLocaleString('ru-RU')}`);
  
  return parts.join('\n');
}

