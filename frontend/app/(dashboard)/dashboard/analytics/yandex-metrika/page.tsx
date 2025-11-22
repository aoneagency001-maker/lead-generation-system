'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { CounterSelector } from '@/components/yandex-metrika/CounterSelector';
import { SummaryView } from '@/components/yandex-metrika/SummaryView';
import { AnalyticsDashboard } from '@/components/yandex-metrika/AnalyticsDashboard';
import SearchQueriesSegmented from '@/components/yandex-metrika/SearchQueriesSegmented';
import RecentVisits from '@/components/yandex-metrika/RecentVisits';
import { BarChart3 } from 'lucide-react';

export default function YandexMetrikaPage() {
  const [selectedCounterId, setSelectedCounterId] = useState<number | null>(null);

  useEffect(() => {
    // Загружаем сохраненный счетчик при монтировании
    if (typeof window !== 'undefined') {
      const savedId = localStorage.getItem('yandex_metrika_counter_id');
      if (savedId) {
        const id = parseInt(savedId, 10);
        setSelectedCounterId(id);
      }
    }
  }, []);

  useEffect(() => {
    // Сохраняем выбранный счетчик в localStorage
    if (selectedCounterId && typeof window !== 'undefined') {
      localStorage.setItem('yandex_metrika_counter_id', selectedCounterId.toString());
    }
  }, [selectedCounterId]);

  const handleCounterSelect = (counterId: number) => {
    setSelectedCounterId(counterId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-8 w-8 text-blue-500" />
          Яндекс.Метрика
        </h2>
        <p className="text-muted-foreground mt-2">
          Аналитика и отчеты по счетчикам Яндекс.Метрики
        </p>
      </div>

      {/* Выбор счетчика */}
      <Card>
        <CardHeader>
          <CardTitle>Выбор счетчика</CardTitle>
          <CardDescription>
            Выберите счетчик для просмотра аналитики
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CounterSelector
            onCounterSelect={handleCounterSelect}
            selectedCounterId={selectedCounterId}
          />
        </CardContent>
      </Card>

      {/* Полная сводка по счетчику */}
      {selectedCounterId && (
        <>
          <SummaryView 
            counterId={selectedCounterId}
            onRefresh={() => {
              // Можно добавить дополнительную логику при обновлении
            }}
          />
          
          {/* Аналитика с графиками */}
          <AnalyticsDashboard counterId={selectedCounterId} />
          
          {/* Сегментированные поисковые запросы */}
          <SearchQueriesSegmented counterId={selectedCounterId} />
          
          {/* Последние посещения */}
          <RecentVisits counterId={selectedCounterId} />
        </>
      )}
    </div>
  );
}

