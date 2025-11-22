'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  Globe, 
  Monitor, 
  Smartphone, 
  Tablet,
  MapPin,
  RefreshCw,
  Clock,
  Activity
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { Loader2 } from 'lucide-react';
import type { GA4OnlineVisitor } from '@/types/ga4';

interface OnlineVisitorsProps {
  propertyId: string;
  limit?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function OnlineVisitors({ 
  propertyId,
  limit = 100,
  autoRefresh = true,
  refreshInterval = 5000 // 5 секунд для real-time
}: OnlineVisitorsProps) {
  const [visitors, setVisitors] = useState<GA4OnlineVisitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [totalActiveUsers, setTotalActiveUsers] = useState(0);

  const loadVisitors = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.getGA4OnlineVisitors(propertyId, limit);
      
      // Преобразуем данные из формата GA4 API
      const transformedVisitors: GA4OnlineVisitor[] = [];
      let totalUsers = 0;
      
      if (response.data && Array.isArray(response.data)) {
        response.data.forEach((row) => {
          if (row.dimensions && row.metrics) {
            const country = row.dimensions[0] || 'Unknown';
            const device = row.dimensions[1] || 'Unknown';
            const event = row.dimensions[2] || 'Unknown';
            const os = row.dimensions[3] || 'Unknown';
            const activeUsers = row.metrics[0] || 0;
            const eventCount = row.metrics[1] || 0;
            
            totalUsers += activeUsers;
            
            transformedVisitors.push({
              country,
              device,
              event,
              os,
              active_users: activeUsers,
              event_count: eventCount
            });
          }
        });
      }
      
      setVisitors(transformedVisitors);
      setTotalActiveUsers(totalUsers);
      setLastUpdate(new Date());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Не удалось загрузить онлайн посетителей";
      setError(errorMessage);
      console.error("Ошибка загрузки онлайн посетителей GA4:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (propertyId) {
      loadVisitors();
    }
  }, [propertyId, limit]);

  useEffect(() => {
    if (!autoRefresh || !propertyId) return;
    
    const interval = setInterval(() => {
      loadVisitors();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, propertyId, limit]);

  const getDeviceIcon = (device: string) => {
    switch (device?.toLowerCase()) {
      case 'mobile':
        return <Smartphone className="h-4 w-4" />;
      case 'tablet':
        return <Tablet className="h-4 w-4" />;
      case 'desktop':
        return <Monitor className="h-4 w-4" />;
      default:
        return <Monitor className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    
    if (diffSecs < 5) return 'только что';
    if (diffSecs < 60) return `${diffSecs} сек назад`;
    
    const diffMins = Math.floor(diffSecs / 60);
    if (diffMins === 1) return '1 минуту назад';
    if (diffMins < 5) return `${diffMins} минуты назад`;
    if (diffMins < 60) return `${diffMins} минут назад`;
    
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading && visitors.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Онлайн-посетители (Real-time)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Загрузка...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-orange-200 dark:border-orange-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-orange-500" />
              Онлайн-посетители (Real-time)
            </CardTitle>
            <CardDescription className="mt-1">
              Данные за последние 30 минут
              {lastUpdate && (
                <span className="ml-2 text-xs">
                  (обновлено {formatTimeAgo(lastUpdate)})
                </span>
              )}
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-2xl font-bold text-orange-500">{totalActiveUsers}</div>
              <div className="text-xs text-muted-foreground">активных</div>
            </div>
            <Button
              onClick={loadVisitors}
              variant="outline"
              size="sm"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Обновить
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200 text-sm rounded-md">
            <div className="font-medium mb-1">Информация:</div>
            <div>{error}</div>
          </div>
        )}

        {visitors.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Нет активных посетителей</p>
            <p className="text-xs mt-2">
              Real-time данные показывают активность за последние 30 минут.
              Если на сайте нет активности, здесь будет пусто.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {visitors.map((visitor, index) => (
              <div
                key={index}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getDeviceIcon(visitor.device)}
                        <span className="font-medium">
                          {visitor.active_users} активных пользователей
                        </span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {visitor.event_count} событий
                      </Badge>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        <span>{visitor.country}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {getDeviceIcon(visitor.device)}
                        <span className="capitalize">{visitor.device}</span>
                      </div>
                      {visitor.os && (
                        <div className="flex items-center gap-1">
                          <Monitor className="h-3 w-3" />
                          <span>{visitor.os}</span>
                        </div>
                      )}
                    </div>

                    {visitor.event && (
                      <div className="flex items-center gap-2 text-sm">
                        <Activity className="h-3 w-3 text-muted-foreground" />
                        <span className="text-muted-foreground">Событие:</span>
                        <Badge variant="outline" className="text-xs">
                          {visitor.event}
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {visitors.length > 0 && (
          <div className="mt-4 pt-4 border-t text-center text-sm text-muted-foreground">
            Показано {visitors.length} групп активностей • Всего {totalActiveUsers} активных пользователей
          </div>
        )}
      </CardContent>
    </Card>
  );
}

