'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { apiClient } from '@/lib/api-client';
import type { DashboardStats } from '@/types';
import {
  Users,
  Target,
  TrendingUp,
  DollarSign,
  Megaphone,
  Flame,
  BarChart3,
} from 'lucide-react';
import { useI18n } from '@/lib/i18n/context';
import { CounterSelector } from '@/components/yandex-metrika/CounterSelector';

export default function DashboardPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCounterId, setSelectedCounterId] = useState<number | null>(null);
  const [counterInfo, setCounterInfo] = useState<{ name: string; site: string } | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await apiClient.getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  const metrics = [
    {
      title: t('dashboard.metrics.totalLeads'),
      value: stats?.total_leads || 0,
      icon: Users,
      description: t('dashboard.descriptions.allTime'),
      color: 'text-blue-500',
    },
    {
      title: t('dashboard.metrics.hotLeads'),
      value: stats?.hot_leads || 0,
      icon: Flame,
      description: t('dashboard.descriptions.readyToConvert'),
      color: 'text-orange-500',
    },
    {
      title: t('dashboard.metrics.activeCampaigns'),
      value: stats?.active_campaigns || 0,
      icon: Megaphone,
      description: t('dashboard.descriptions.runningNow'),
      color: 'text-green-500',
    },
    {
      title: t('dashboard.metrics.conversions'),
      value: stats?.total_conversions || 0,
      icon: TrendingUp,
      description: t('dashboard.descriptions.wonLeads'),
      color: 'text-purple-500',
    },
    {
      title: t('dashboard.metrics.avgCpl'),
      value: `$${stats?.avg_cpl?.toFixed(2) || '0.00'}`,
      icon: DollarSign,
      description: t('dashboard.descriptions.costPerLead'),
      color: 'text-yellow-500',
    },
    {
      title: t('dashboard.metrics.totalNiches'),
      value: stats?.total_niches || 0,
      icon: Target,
      description: t('dashboard.descriptions.marketsTested'),
      color: 'text-indigo-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('dashboard.title')}</h2>
        <p className="text-muted-foreground">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {metric.title}
              </CardTitle>
              <metric.icon className={`h-4 w-4 ${metric.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metric.value}</div>
              <p className="text-xs text-muted-foreground">
                {metric.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Yandex Metrika Test Section */}
      <Card className="border-2 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-500" />
            <CardTitle>Тест интеграции Яндекс.Метрики</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Выберите счетчик Яндекс.Метрики:
            </label>
            <CounterSelector
              onCounterSelect={(counterId) => {
                setSelectedCounterId(counterId);
                // Найдем информацию о счетчике
                fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/yandex-metrika/counters`)
                  .then(res => res.json())
                  .then(data => {
                    const counter = data.counters?.find((c: any) => c.id === counterId);
                    if (counter) {
                      setCounterInfo({
                        name: counter.name,
                        site: counter.site || 'Не указан'
                      });
                    }
                  })
                  .catch(err => console.error('Ошибка получения информации о счетчике:', err));
              }}
              selectedCounterId={selectedCounterId}
            />
          </div>

          {selectedCounterId && counterInfo && (
            <div className="mt-4 p-4 bg-muted rounded-md space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500"></div>
                <span className="text-sm font-medium">Счетчик выбран</span>
              </div>
              <div className="text-sm space-y-1">
                <div>
                  <span className="text-muted-foreground">ID:</span>{' '}
                  <span className="font-mono font-medium">{selectedCounterId}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Название:</span>{' '}
                  <span className="font-medium">{counterInfo.name}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Сайт:</span>{' '}
                  <span className="font-medium">{counterInfo.site}</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t text-xs text-muted-foreground">
                ✅ Счетчик сохранен в localStorage. Теперь можно использовать его ID для получения отчетов.
              </div>
            </div>
          )}

          {selectedCounterId && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950 rounded-md">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                <strong>Готово к использованию!</strong> Выбранный счетчик (ID: {selectedCounterId}) можно использовать 
                для получения отчетов через API endpoint: 
                <code className="ml-1 px-1 py-0.5 bg-blue-100 dark:bg-blue-900 rounded text-xs">
                  GET /api/yandex-metrika/counters/{selectedCounterId}/report
                </code>
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity / Charts Section */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.recentActivity')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              {t('dashboard.noActivity')}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('dashboard.performance')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-muted-foreground">
              {t('dashboard.chartsPlaceholder')}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
