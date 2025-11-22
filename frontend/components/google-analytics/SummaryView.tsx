'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  BarChart3, 
  Users, 
  Eye, 
  TrendingUp, 
  Clock, 
  Database, 
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Globe,
  Activity,
  Table,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { apiClient } from '@/lib/api-client';
import { Loader2 } from 'lucide-react';
import { OnlineVisitors } from './OnlineVisitors';
import type { GA4Summary } from '@/types/ga4';

interface SummaryViewProps {
  propertyId: string;
  days?: number;
  onRefresh?: () => void;
}

export function SummaryView({ propertyId, days = 7, onRefresh }: SummaryViewProps) {
  const [data, setData] = useState<GA4Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSummaryTable, setShowSummaryTable] = useState(false);

  const loadSummary = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const summary = await apiClient.getGA4Summary(propertyId, days);
      setData(summary);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Не удалось загрузить сводку";
      setError(errorMessage);
      console.error("Ошибка загрузки сводки GA4:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (propertyId) {
      loadSummary();
    }
  }, [propertyId, days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Загрузка сводки...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button onClick={loadSummary} variant="outline" className="mt-4">
            Повторить
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return null;
  }

  const { metrics, top_sources, traffic_by_type, sync_status } = data;
  
  // Подготовка данных для графика трафика по типам (основные типы)
  const trafficTypeData = traffic_by_type ? Object.entries(traffic_by_type)
    .map(([type, data]) => ({
      type,
      visits: data.visits || 0,
      users: data.users || 0,
    }))
    .filter(item => item.visits > 0)
    .sort((a, b) => b.visits - a.visits) : [];
  
  // Подготовка детализированных данных для рекламы
  const advertisingDetails = traffic_by_type?.Реклама?.subtypes 
    ? Object.entries(traffic_by_type.Реклама.subtypes)
        .map(([subtype, data]: [string, any]) => ({
          type: subtype,
          visits: data.visits || 0,
          users: data.users || 0,
        }))
        .filter(item => item.visits > 0)
        .sort((a, b) => b.visits - a.visits)
    : [];

  return (
    <div className="space-y-6">
      {/* Информация о Property */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Google Analytics 4 Property
              </CardTitle>
              <CardDescription className="mt-1">
                Property ID: {data.property_id}
              </CardDescription>
            </div>
            <Button
              onClick={loadSummary}
              variant="outline"
              size="sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Property ID</div>
              <div className="font-mono font-medium">{data.property_id}</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Период</div>
              <div className="font-medium">
                {data.period.date_from} - {data.period.date_to}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Статус</div>
              <Badge 
                variant={sync_status.status === 'ok' ? 'default' : 'destructive'}
                className={sync_status.status === 'ok' ? 'bg-green-500 hover:bg-green-600' : ''}
              >
                {sync_status.status === 'ok' ? 'Подключено' : 'Ошибка'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Метрики за период */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sessions</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.sessions.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              За {days} дней
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Users</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.users.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Активных пользователей
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pageviews</CardTitle>
            <Eye className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.pageviews.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Всего просмотров страниц
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online Now</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.online_users.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Онлайн сейчас (30 мин)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Анализ трафика по типам */}
      {trafficTypeData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Анализ трафика по типам ({days} дней)
            </CardTitle>
            <CardDescription>
              Распределение: Реклама, Органика, Прямой, Соцсети, С других сайтов
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart 
                data={trafficTypeData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                <XAxis 
                  type="number" 
                  stroke="hsl(var(--muted-foreground))" 
                  style={{ fontSize: '12px' }}
                />
                <YAxis 
                  type="category" 
                  dataKey="type" 
                  width={90}
                  stroke="hsl(var(--muted-foreground))" 
                  style={{ fontSize: '12px' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                  formatter={(value: number, name: string) => [
                    value.toLocaleString(),
                    name === 'visits' ? 'Sessions' : 'Users'
                  ]}
                />
                <Legend />
                <Bar 
                  dataKey="visits" 
                  fill="#8884d8" 
                  name="Sessions"
                  radius={[0, 4, 4, 0]}
                />
                <Bar 
                  dataKey="users" 
                  fill="#82ca9d" 
                  name="Users"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
            
            {/* Статистика по типам */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-5 gap-4">
              {trafficTypeData.map((item) => {
                const percentage = metrics.sessions > 0 
                  ? ((item.visits / metrics.sessions) * 100).toFixed(1) 
                  : 0;
                return (
                  <div key={item.type} className="text-center p-3 bg-muted rounded-md">
                    <div className="text-sm font-medium text-muted-foreground">{item.type}</div>
                    <div className="text-xl font-bold mt-1">{item.visits.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">{percentage}%</div>
                  </div>
                );
              })}
            </div>
            
            {/* Детализация рекламы */}
            {advertisingDetails.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-semibold mb-3">📊 Детализация рекламы:</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {advertisingDetails.map((item) => {
                    const totalAds = traffic_by_type?.Реклама?.visits || 1;
                    const percentage = ((item.visits / totalAds) * 100).toFixed(1);
                    return (
                      <div key={item.type} className="text-center p-2 bg-blue-50 dark:bg-blue-950 rounded-md border border-blue-200 dark:border-blue-800">
                        <div className="text-xs font-medium text-blue-700 dark:text-blue-300">{item.type}</div>
                        <div className="text-lg font-bold text-blue-900 dark:text-blue-100 mt-1">{item.visits.toLocaleString()}</div>
                        <div className="text-xs text-blue-600 dark:text-blue-400">{percentage}% от рекламы</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Сводная таблица - скрыта по умолчанию */}
      {top_sources && top_sources.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Table className="h-5 w-5" />
                  Сводная таблица всех данных
                </CardTitle>
                <CardDescription>
                  Детальная информация по всем источникам трафика
                </CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSummaryTable(!showSummaryTable)}
              >
                {showSummaryTable ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    Скрыть
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    Показать
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          {showSummaryTable && (
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium">#</th>
                      <th className="text-left p-3 font-medium">Источник</th>
                      <th className="text-left p-3 font-medium">Medium</th>
                      <th className="text-left p-3 font-medium">Тип трафика</th>
                      <th className="text-right p-3 font-medium">Sessions</th>
                      <th className="text-right p-3 font-medium">Users</th>
                      <th className="text-right p-3 font-medium">% от всех</th>
                      <th className="text-right p-3 font-medium">Bounce Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {top_sources.map((source: any, index: number) => {
                      const visits = source.visits || source.sessions || source.metrics?.[0] || 0;
                      const users = source.users || source.activeUsers || source.metrics?.[1] || 0;
                      const sourceName = source.source || source.sessionSource || source.dimensions?.[0] || 'Прямой трафик';
                      const medium = source.medium || source.sessionMedium || source.dimensions?.[1] || 'none';
                      const trafficType = source.traffic_type || 'Не определен';
                      const percentage = metrics.sessions > 0 
                        ? ((Number(visits) / metrics.sessions) * 100).toFixed(1) 
                        : 0;
                      
                      return (
                        <tr key={index} className="border-b hover:bg-muted/50">
                          <td className="p-3">{index + 1}</td>
                          <td className="p-3 font-medium">{sourceName}</td>
                          <td className="p-3 text-muted-foreground">{medium}</td>
                          <td className="p-3">
                            <div className="flex flex-col gap-1">
                              <Badge variant="outline">{trafficType}</Badge>
                              {source.traffic_detail && source.traffic_detail !== trafficType && (
                                <span className="text-xs text-muted-foreground">{source.traffic_detail}</span>
                              )}
                            </div>
                          </td>
                          <td className="p-3 text-right">{Number(visits).toLocaleString()}</td>
                          <td className="p-3 text-right">{Number(users).toLocaleString()}</td>
                          <td className="p-3 text-right">{percentage}%</td>
                          <td className="p-3 text-right">
                            {source.bounce_rate !== undefined 
                              ? `${Number(source.bounce_rate).toFixed(1)}%` 
                              : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                  <tfoot>
                    <tr className="border-t font-bold">
                      <td colSpan={4} className="p-3">Итого:</td>
                      <td className="p-3 text-right">{metrics.sessions.toLocaleString()}</td>
                      <td className="p-3 text-right">{metrics.users.toLocaleString()}</td>
                      <td className="p-3 text-right">100%</td>
                      <td className="p-3 text-right">—</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </CardContent>
          )}
        </Card>
      )}

      {/* Статистика синхронизации */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Статус синхронизации
          </CardTitle>
          <CardDescription>
            Информация о последней синхронизации данных
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium">Последняя синхронизация</span>
              </div>
              <div className="text-lg font-bold">
                {sync_status.last_sync ? new Date(sync_status.last_sync).toLocaleString('ru-RU') : 'Не синхронизировано'}
              </div>
              <div className="text-xs text-muted-foreground">
                Время последней загрузки данных
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {sync_status.status === 'ok' ? (
                  <CheckCircle2 className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-yellow-500" />
                )}
                <span className="text-sm font-medium">Статус</span>
              </div>
              <div className="text-lg font-bold capitalize">
                {sync_status.status === 'ok' ? 'Работает' : 'Ошибка'}
              </div>
              <div className="text-xs text-muted-foreground">
                {sync_status.status === 'ok' 
                  ? 'Данные успешно загружаются' 
                  : 'Проверьте настройки подключения'}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Онлайн-посетители */}
      <OnlineVisitors propertyId={propertyId} />
    </div>
  );
}

