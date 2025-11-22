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
  Activity
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { Loader2 } from 'lucide-react';
import { OnlineVisitors } from './OnlineVisitors';

interface SummaryData {
  counter: {
    id: number;
    name: string;
    domain: string;
    code_status: string;
    permission: string;
  };
  stats: {
    last_7_days: {
      visits: number;
      users: number;
      pageviews: number;
      bounce_rate: number;
      avg_duration: number;
      top_sources: Array<{ source: string; visits: number }>;
    };
  };
  sync: {
    visits_in_db: number;
    hits_in_db: number;
    last_sync: string | null;
  };
}

interface SummaryViewProps {
  counterId: number;
  onRefresh?: () => void;
}

export function SummaryView({ counterId, onRefresh }: SummaryViewProps) {
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const summary = await apiClient.getMetrikaSummary(counterId);
      setData(summary);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Не удалось загрузить сводку";
      setError(errorMessage);
      console.error("Ошибка загрузки сводки:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (counterId) {
      loadSummary();
    }
  }, [counterId]);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds} сек`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes} мин ${secs} сек`;
  };

  const getCodeStatusBadge = (status: string) => {
    // Статусы кода Яндекс.Метрики
    const statusMap: Record<string, { label: string; variant: "default" | "destructive" | "secondary"; className: string }> = {
      'CS_OK': {
        label: 'Код установлен',
        variant: 'default',
        className: 'bg-green-500 hover:bg-green-600'
      },
      'CS_ERR_UNKNOWN': {
        label: 'Неизвестная ошибка',
        variant: 'destructive',
        className: 'bg-orange-500 hover:bg-orange-600'
      },
      'CS_ERR_NOT_FOUND': {
        label: 'Код не найден',
        variant: 'destructive',
        className: 'bg-red-500 hover:bg-red-600'
      },
      'CS_ERR_DUPLICATE': {
        label: 'Дублирование кода',
        variant: 'destructive',
        className: 'bg-red-500 hover:bg-red-600'
      },
      'CS_ERR_OLD_CODE': {
        label: 'Устаревший код',
        variant: 'destructive',
        className: 'bg-yellow-500 hover:bg-yellow-600'
      },
      'CS_ERR_INVALID': {
        label: 'Неверный код',
        variant: 'destructive',
        className: 'bg-red-500 hover:bg-red-600'
      },
      'CS_PENDING': {
        label: 'Проверка...',
        variant: 'secondary',
        className: 'bg-gray-500 hover:bg-gray-600'
      }
    };

    const statusInfo = statusMap[status] || {
      label: status || 'Неизвестный статус',
      variant: 'destructive' as const,
      className: 'bg-gray-500 hover:bg-gray-600'
    };

    return (
      <Badge 
        variant={statusInfo.variant} 
        className={statusInfo.className}
        title={status ? `Статус: ${status}` : 'Статус не определен'}
      >
        {statusInfo.label}
      </Badge>
    );
  };

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

  const { counter, stats, sync } = data;
  const metrics = stats.last_7_days;

  return (
    <div className="space-y-6">
      {/* Информация о счетчике */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                {counter.name}
              </CardTitle>
              <CardDescription className="mt-1">
                {counter.domain || 'Домен не указан'}
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">ID счетчика</div>
              <div className="font-mono font-medium">{counter.id}</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Статус кода</div>
              <div className="flex items-center gap-2">
                {getCodeStatusBadge(counter.code_status)}
                {counter.code_status && counter.code_status !== 'CS_OK' && (
                  <span 
                    className="text-xs text-muted-foreground cursor-help" 
                    title={`Статус: ${counter.code_status}. CS_ERR_UNKNOWN может означать, что код еще не проиндексирован Яндекс.Метрикой или сайт временно недоступен для проверки.`}
                  >
                    ⓘ
                  </span>
                )}
              </div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Доступ</div>
              <div className="font-medium capitalize">{counter.permission}</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Домен</div>
              <div className="font-medium truncate">{counter.domain || '—'}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Метрики за последние 7 дней */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Визиты</CardTitle>
            <Users className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.visits.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              За последние 7 дней
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Посетители</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.users.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Уникальных посетителей
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Просмотры</CardTitle>
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
            <CardTitle className="text-sm font-medium">Показатель отказов</CardTitle>
            <Activity className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.bounce_rate.toFixed(1)}%</div>
            <p className="text-xs text-muted-foreground mt-1">
              Процент отказов
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Средняя длительность</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatDuration(metrics.avg_duration)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Среднее время на сайте
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Топ источников трафика */}
      {metrics.top_sources && metrics.top_sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Топ источников трафика (7 дней)
            </CardTitle>
            <CardDescription>
              Основные источники посещений за последнюю неделю
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.top_sources.map((source, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-md">
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted font-bold text-sm">
                      {index + 1}
                    </div>
                    <div>
                      <div className="font-medium">{source.source || 'Прямой трафик'}</div>
                      <div className="text-sm text-muted-foreground">
                        {source.visits.toLocaleString()} визитов
                      </div>
                    </div>
                  </div>
                  <div className="text-sm font-medium text-muted-foreground">
                    {((source.visits / metrics.visits) * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Статистика синхронизации */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            Статистика синхронизации
          </CardTitle>
          <CardDescription>
            Данные о загруженных в базу данных записях
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Визиты в БД</span>
              </div>
              <div className="text-2xl font-bold">{sync.visits_in_db.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">
                Всего записей в normalized_events
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">Хиты в БД</span>
              </div>
              <div className="text-2xl font-bold">{sync.hits_in_db.toLocaleString()}</div>
              <div className="text-xs text-muted-foreground">
                Всего записей в raw_events
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium">Последняя синхронизация</span>
              </div>
              <div className="text-lg font-bold">
                {sync.last_sync || 'Не синхронизировано'}
              </div>
              <div className="text-xs text-muted-foreground">
                Время последней загрузки данных
              </div>
            </div>
          </div>

          {/* Индикаторы работы синхронизации */}
          <div className="mt-6 p-4 bg-muted rounded-md space-y-2">
            <div className="flex items-center gap-2">
              {sync.visits_in_db > 0 ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              )}
              <span className="text-sm">
                {sync.visits_in_db > 0 
                  ? 'Данные успешно загружаются в базу' 
                  : 'Данные еще не загружены в базу'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {sync.hits_in_db > 0 ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              )}
              <span className="text-sm">
                {sync.hits_in_db > 0 
                  ? 'Сырые данные (hits) загружаются' 
                  : 'Сырые данные (hits) еще не загружены'}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Онлайн-посетители */}
      <OnlineVisitors minutes={15} autoRefresh={true} refreshInterval={10000} />
    </div>
  );
}

