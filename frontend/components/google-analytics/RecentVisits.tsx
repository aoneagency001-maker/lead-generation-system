"use client";

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, ExternalLink, Clock, Globe, Monitor, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { GA4RecentVisit } from '@/types/ga4';

interface RecentVisitsProps {
  propertyId: string | null;
}

export default function RecentVisits({ propertyId }: RecentVisitsProps) {
  const [visits, setVisits] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    if (propertyId) {
      fetchVisits();
    }
  }, [propertyId, days, limit]);

  const fetchVisits = async () => {
    if (!propertyId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getGA4RecentVisits(propertyId, days, limit);
      
      // Преобразуем данные из формата GA4 API
      const transformedVisits: any[] = [];
      
      if (response.data && Array.isArray(response.data)) {
        response.data.forEach((row) => {
          if (row.dimensions && row.metrics) {
            const date = row.dimensions[0] || '';
            const country = row.dimensions[1] || 'Unknown';
            const city = row.dimensions[2] || 'Unknown';
            const device = row.dimensions[3] || 'Unknown';
            const landing_page = row.dimensions[4] || '';
            const sessions = row.metrics[0] || 0;
            const users = row.metrics[1] || 0;
            const pageviews = row.metrics[2] || 0;
            
            transformedVisits.push({
              date,
              country,
              city,
              device,
              landing_page,
              sessions,
              users,
              pageviews,
            });
          }
        });
      }
      
      setVisits(transformedVisits);
    } catch (err: any) {
      console.error('Ошибка при загрузке посещений GA4:', err);
      setError(err.message || 'Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    if (!dateString) return '—';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  if (!propertyId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Последние посещения</CardTitle>
          <CardDescription>Выберите Property для просмотра данных</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Последние посещения</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Последние посещения</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-destructive">{error}</div>
          <Button onClick={fetchVisits} variant="outline" className="mt-4">
            Повторить
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Последние посещения</CardTitle>
            <CardDescription>
              Детальная информация о последних посещениях
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 border rounded-md bg-background text-sm"
            >
              <option value={3}>3 дня</option>
              <option value={7}>7 дней</option>
              <option value={14}>14 дней</option>
              <option value={30}>30 дней</option>
            </select>
            <select
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="px-3 py-1.5 border rounded-md bg-background text-sm"
            >
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {visits.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Нет данных о посещениях за выбранный период
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-muted">
                <tr>
                  <th className="px-4 py-2 text-sm font-medium">Дата/Время</th>
                  <th className="px-4 py-2 text-sm font-medium">География</th>
                  <th className="px-4 py-2 text-sm font-medium">Устройство</th>
                  <th className="px-4 py-2 text-sm font-medium">Страница входа</th>
                  <th className="px-4 py-2 text-sm font-medium text-right">Sessions</th>
                  <th className="px-4 py-2 text-sm font-medium text-right">Users</th>
                  <th className="px-4 py-2 text-sm font-medium text-right">Pageviews</th>
                </tr>
              </thead>
              <tbody>
                {visits.map((visit, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-border hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-4 py-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        {formatDate(visit.date)}
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Globe className="h-3 w-3 text-muted-foreground" />
                        <span>
                          {visit.city && visit.city !== 'Unknown' ? `${visit.city}, ` : ''}
                          {visit.country}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm">
                      <div className="flex items-center gap-1">
                        <Monitor className="h-3 w-3 text-muted-foreground" />
                        <Badge variant="outline" className="text-xs capitalize">
                          {visit.device}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-4 py-2 text-sm">
                      {visit.landing_page ? (
                        <a
                          href={visit.landing_page}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline flex items-center gap-1"
                        >
                          <ExternalLink className="h-3 w-3" />
                          <span className="truncate max-w-xs">
                            {visit.landing_page.length > 40
                              ? visit.landing_page.substring(0, 40) + '...'
                              : visit.landing_page}
                          </span>
                        </a>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-sm font-bold text-right">
                      {visit.sessions.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-muted-foreground">
                      {visit.users.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-sm text-right text-muted-foreground">
                      {visit.pageviews.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {visits.length > 0 && (
          <div className="mt-4 pt-4 border-t text-center text-sm text-muted-foreground">
            Показано {visits.length} посещений
          </div>
        )}
      </CardContent>
    </Card>
  );
}

