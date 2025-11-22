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
  ExternalLink,
  RefreshCw,
  Clock
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { Loader2 } from 'lucide-react';

interface OnlineVisitor {
  id: string;
  ip_address: string;
  city: string;
  country: string;
  device_type: string;
  browser: string;
  os: string;
  page: string;
  referrer: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  screen_resolution: string;
  is_first_visit: boolean;
  created_at: string;
}

interface OnlineVisitorsProps {
  minutes?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

export function OnlineVisitors({ 
  minutes = 15, 
  autoRefresh = true,
  refreshInterval = 10000 
}: OnlineVisitorsProps) {
  const [visitors, setVisitors] = useState<OnlineVisitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const loadVisitors = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.getOnlineVisitors(minutes, 50);
      setVisitors(data.visitors || []);
      setLastUpdate(new Date());
      
      // Если есть сообщение об ошибке (например, таблица не найдена)
      if ((data as any).error) {
        setError((data as any).error);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Не удалось загрузить посетителей";
      setError(errorMessage);
      console.error("Ошибка загрузки посетителей:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVisitors();
  }, [minutes]);

  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      loadVisitors();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, minutes]);

  const getDeviceIcon = (deviceType: string) => {
    switch (deviceType?.toLowerCase()) {
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

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'только что';
    if (diffMins === 1) return '1 минуту назад';
    if (diffMins < 5) return `${diffMins} минуты назад`;
    if (diffMins < 60) return `${diffMins} минут назад`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours === 1) return '1 час назад';
    if (diffHours < 24) return `${diffHours} часов назад`;
    
    return date.toLocaleString('ru-RU', { 
      day: '2-digit', 
      month: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getReferrerDisplay = (referrer: string) => {
    if (!referrer || referrer === 'Прямой переход') {
      return 'Прямой переход';
    }
    
    try {
      const url = new URL(referrer);
      return url.hostname.replace('www.', '');
    } catch {
      return referrer.length > 30 ? referrer.substring(0, 30) + '...' : referrer;
    }
  };

  if (loading && visitors.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Онлайн-посетители
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
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Онлайн-посетители
            </CardTitle>
            <CardDescription className="mt-1">
              Посетители за последние {minutes} минут
              {lastUpdate && (
                <span className="ml-2 text-xs">
                  (обновлено {formatTimeAgo(lastUpdate.toISOString())})
                </span>
              )}
            </CardDescription>
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
            <p className="text-xs mt-2">Посетители появятся здесь, когда кто-то зайдет на сайт</p>
          </div>
        ) : (
          <div className="space-y-3">
            {visitors.map((visitor) => (
              <div
                key={visitor.id}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  {/* Левая часть: Основная информация */}
                  <div className="flex-1 space-y-2">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getDeviceIcon(visitor.device_type)}
                        <span className="font-mono text-sm font-medium">
                          {visitor.ip_address}
                        </span>
                      </div>
                      {visitor.is_first_visit && (
                        <Badge variant="secondary" className="text-xs">
                          Новый
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        <span>
                          {visitor.city}, {visitor.country}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        <span>{formatTimeAgo(visitor.created_at)}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      <Badge variant="outline" className="text-xs">
                        {visitor.browser}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {visitor.os}
                      </Badge>
                      <span className="text-muted-foreground">
                        {visitor.screen_resolution}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-sm">
                      <ExternalLink className="h-3 w-3 text-muted-foreground" />
                      <span className="text-muted-foreground">Страница:</span>
                      <span className="font-medium truncate max-w-xs">
                        {visitor.page}
                      </span>
                    </div>

                    {visitor.referrer && visitor.referrer !== 'Прямой переход' && (
                      <div className="flex items-center gap-2 text-sm">
                        <Globe className="h-3 w-3 text-muted-foreground" />
                        <span className="text-muted-foreground">Источник:</span>
                        <span className="font-medium">
                          {getReferrerDisplay(visitor.referrer)}
                        </span>
                      </div>
                    )}

                    {(visitor.utm_source || visitor.utm_medium || visitor.utm_campaign) && (
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>UTM:</span>
                        {visitor.utm_source && (
                          <Badge variant="outline" className="text-xs">
                            {visitor.utm_source}
                          </Badge>
                        )}
                        {visitor.utm_medium && (
                          <Badge variant="outline" className="text-xs">
                            {visitor.utm_medium}
                          </Badge>
                        )}
                        {visitor.utm_campaign && (
                          <Badge variant="outline" className="text-xs">
                            {visitor.utm_campaign}
                          </Badge>
                        )}
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
            Показано {visitors.length} посетителей
          </div>
        )}
      </CardContent>
    </Card>
  );
}

