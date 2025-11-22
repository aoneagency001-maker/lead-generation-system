'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { PropertySelector } from '@/components/google-analytics/PropertySelector';
import { SummaryView } from '@/components/google-analytics/SummaryView';
import { AnalyticsDashboard } from '@/components/google-analytics/AnalyticsDashboard';
import RecentVisits from '@/components/google-analytics/RecentVisits';
import { BarChart3 } from 'lucide-react';

export default function GoogleAnalyticsPage() {
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  useEffect(() => {
    // Загружаем сохраненный Property при монтировании
    if (typeof window !== 'undefined') {
      const savedId = localStorage.getItem('ga4_property_id');
      if (savedId) {
        setSelectedPropertyId(savedId);
      }
    }
  }, []);

  useEffect(() => {
    // Сохраняем выбранный Property в localStorage
    if (selectedPropertyId && typeof window !== 'undefined') {
      localStorage.setItem('ga4_property_id', selectedPropertyId);
    }
  }, [selectedPropertyId]);

  const handlePropertySelect = (propertyId: string) => {
    setSelectedPropertyId(propertyId);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <BarChart3 className="h-8 w-8 text-orange-500" />
          Google Analytics 4
        </h2>
        <p className="text-muted-foreground mt-2">
          Аналитика и отчеты по Properties Google Analytics 4
        </p>
      </div>

      {/* Выбор Property */}
      <Card>
        <CardHeader>
          <CardTitle>Выбор Property</CardTitle>
          <CardDescription>
            Выберите Property для просмотра аналитики
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PropertySelector
            onPropertySelect={handlePropertySelect}
            selectedPropertyId={selectedPropertyId}
          />
        </CardContent>
      </Card>

      {/* Полная сводка по Property */}
      {selectedPropertyId && (
        <>
          <SummaryView 
            propertyId={selectedPropertyId}
            days={7}
            onRefresh={() => {
              // Можно добавить дополнительную логику при обновлении
            }}
          />
          
          {/* Аналитика с графиками */}
          <AnalyticsDashboard propertyId={selectedPropertyId} />
          
          {/* Последние посещения */}
          <RecentVisits propertyId={selectedPropertyId} />
        </>
      )}
    </div>
  );
}

