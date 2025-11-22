"use client";

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, ExternalLink, Clock, Globe, Monitor, User } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Visit {
  date: string;
  time: string;
  ip_address: string;
  device: string;
  browser: string;
  os: string;
  country: string;
  city: string;
  start_url: string;
  referer: string;
  pageviews: number;
  duration: number;
  is_new_user: boolean;
  visit_number: number;  // Номер посещения для этого посетителя
}

interface RecentVisitsProps {
  counterId: number | null;
}

export default function RecentVisits({ counterId }: RecentVisitsProps) {
  const [visits, setVisits] = useState<Visit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);
  const [limit, setLimit] = useState(50);

  useEffect(() => {
    if (counterId) {
      fetchVisits();
    }
  }, [counterId, days, limit]);

  const fetchVisits = async () => {
    if (!counterId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getMetrikaRecentVisits(counterId, days, limit);
      setVisits(response.visits);
    } catch (err: any) {
      console.error('Ошибка при загрузке посещений:', err);
      setError(err.message || 'Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${seconds}с`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}м ${secs}с`;
  };

  const formatDateTime = (date: string, time: string): string => {
    return `${date} ${time}`;
  };

  if (!counterId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Последние посещения</CardTitle>
          <CardDescription>Выберите счетчик для просмотра данных</CardDescription>
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
              <Clock className="h-5 w-5" />
              Последние посещения
            </CardTitle>
            <CardDescription>
              ТОП {limit} последних посещений с детальной информацией
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">Период:</label>
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
            <label className="text-sm text-muted-foreground">Лимит:</label>
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
          <div className="text-center py-12 text-muted-foreground">
            Нет данных о посещениях за выбранный период
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-muted sticky top-0">
                <tr>
                  <th className="px-4 py-3 font-semibold">#</th>
                  <th className="px-4 py-3 font-semibold">Дата/Время</th>
                  <th className="px-4 py-3 font-semibold">📍 География</th>
                  <th className="px-4 py-3 font-semibold">💻 Устройство</th>
                  <th className="px-4 py-3 font-semibold">🌐 Страница входа</th>
                  <th className="px-4 py-3 font-semibold">📊 Страниц</th>
                  <th className="px-4 py-3 font-semibold">⏱️ Длительность</th>
                  <th className="px-4 py-3 font-semibold">👤 Тип</th>
                </tr>
              </thead>
              <tbody>
                {visits.map((visit, idx) => (
                  <tr
                    key={idx}
                    className="border-b hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Badge variant="outline" className="font-mono">
                        #{visit.visit_number}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">
                        {formatDateTime(visit.date, visit.time)}
                      </div>
                      {visit.ip_address !== "N/A" && (
                        <div className="text-xs text-muted-foreground">
                          {visit.ip_address}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Globe className="h-3 w-3 text-muted-foreground" />
                        <span>{visit.country}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {visit.city}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Monitor className="h-3 w-3 text-muted-foreground" />
                        <span className="capitalize">{visit.device}</span>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {visit.browser} / {visit.os}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="max-w-xs">
                        {visit.start_url ? (
                          <a
                            href={visit.start_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary hover:underline truncate block flex items-center gap-1"
                            title={visit.start_url}
                          >
                            {visit.start_url.length > 40
                              ? visit.start_url.substring(0, 40) + '...'
                              : visit.start_url}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                        {visit.referer && visit.referer !== "Direct" && (
                          <div className="text-xs text-muted-foreground mt-1">
                            из: {visit.referer.length > 30
                              ? visit.referer.substring(0, 30) + '...'
                              : visit.referer}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary">
                        {visit.pageviews}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span>{formatDuration(visit.duration)}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {visit.is_new_user ? (
                        <Badge variant="default" className="bg-green-500">
                          <User className="h-3 w-3 mr-1" />
                          Новый
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          <User className="h-3 w-3 mr-1" />
                          Возврат
                        </Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

