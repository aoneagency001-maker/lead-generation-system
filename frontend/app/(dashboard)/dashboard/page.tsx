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
} from 'lucide-react';
import { useI18n } from '@/lib/i18n/context';

export default function DashboardPage() {
  const { t } = useI18n();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

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
