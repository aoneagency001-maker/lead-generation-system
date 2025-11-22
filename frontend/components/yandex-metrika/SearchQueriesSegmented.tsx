"use client";

import React, { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

interface Query {
  query: string;
  visits: number;
  segment: string;
  segments: string[];
  heat_score: number;
  color: string;
  priority: number;
  landing_pages: string[];
  first_visit: string | null;
  last_visit: string | null;
}

interface SegmentData {
  total_visits: number;
  queries: Query[];
  color: string;
  priority: number;
}

interface SegmentedData {
  [key: string]: SegmentData;
}

export default function SearchQueriesSegmented({ counterId }: { counterId: number | null }) {
  const [segmentedData, setSegmentedData] = useState<SegmentedData | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    if (counterId) {
      fetchSegmentedQueries();
    }
  }, [counterId, days]);

  const fetchSegmentedQueries = async () => {
    if (!counterId) return;

    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.getMetrikaSearchQueriesBySegment(counterId, days, 200);
      setSegmentedData(response);

      // Автоматически выбираем самый "горячий" сегмент
      const hottest = Object.entries(response).sort(
        ([, a], [, b]) => b.priority - a.priority
      )[0]?.[0];
      setSelectedSegment(hottest || null);
    } catch (err: any) {
      console.error('Ошибка при загрузке данных', err);
      setError(err.message || 'Ошибка при загрузке данных');
    } finally {
      setLoading(false);
    }
  };

  if (!counterId) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Поисковые запросы по сегментам</CardTitle>
          <CardDescription>Выберите счетчик для просмотра данных</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Поисковые запросы по сегментам</CardTitle>
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
          <CardTitle>Поисковые запросы по сегментам</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (!segmentedData || Object.keys(segmentedData).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Поисковые запросы по сегментам</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-muted-foreground">Нет данных для отображения</div>
        </CardContent>
      </Card>
    );
  }

  const currentSegment = selectedSegment ? segmentedData[selectedSegment] : null;
  const filteredQueries = currentSegment
    ? currentSegment.queries.filter((q) =>
        q.query.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : [];

  // Данные для графика
  const chartData = Object.entries(segmentedData).map(([segment, data]) => ({
    segment,
    visits: data.total_visits,
    fill: data.color,
  }));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            🔥 Поисковые запросы по сегментам
          </CardTitle>
          <CardDescription>
            Анализ поисковых запросов с сегментацией по намерению и горячести
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Выбор периода */}
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Период:</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-3 py-1.5 border rounded-md bg-background"
            >
              <option value={7}>7 дней</option>
              <option value={14}>14 дней</option>
              <option value={30}>30 дней</option>
              <option value={90}>90 дней</option>
            </select>
          </div>

          {/* График распределения по сегментам */}
          <div>
            <h3 className="text-lg font-semibold mb-4">📊 Распределение запросов по сегментам</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="segment"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="visits" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Кнопки для выбора сегмента */}
          <div className="flex flex-wrap gap-3">
            {Object.entries(segmentedData).map(([segment, data]) => (
              <button
                key={segment}
                onClick={() => setSelectedSegment(segment)}
                className={`px-4 py-2 rounded-lg font-semibold text-white transition-all ${
                  selectedSegment === segment
                    ? 'ring-2 ring-offset-2 ring-white scale-105'
                    : 'opacity-70 hover:opacity-100 hover:scale-105'
                }`}
                style={{ backgroundColor: data.color }}
              >
                {segment} ({data.total_visits})
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Таблица запросов для выбранного сегмента */}
      {currentSegment && (
        <Card>
          <CardHeader>
            <CardTitle>
              {selectedSegment} ({filteredQueries.length} запросов)
            </CardTitle>
            <CardDescription>
              Всего визитов: {currentSegment.total_visits}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Поле поиска */}
            <Input
              type="text"
              placeholder="Фильтр по запросу..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-md"
            />

            {/* Таблица */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-muted sticky top-0">
                  <tr>
                    <th className="px-4 py-3 font-semibold">🔍 Запрос</th>
                    <th className="px-4 py-3 font-semibold">📊 Визиты</th>
                    <th className="px-4 py-3 font-semibold">🔥 Температура</th>
                    <th className="px-4 py-3 font-semibold">🌐 Страница входа</th>
                    <th className="px-4 py-3 font-semibold">🏷️ Сегменты</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQueries.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                        Нет запросов, соответствующих фильтру
                      </td>
                    </tr>
                  ) : (
                    filteredQueries.map((q, idx) => (
                      <tr
                        key={idx}
                        className="border-b hover:bg-muted/50 transition-colors"
                      >
                        <td className="px-4 py-3 font-semibold">{q.query}</td>
                        <td className="px-4 py-3">
                          <span className="bg-muted px-2 py-1 rounded text-sm">
                            {q.visits}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-4 h-4 rounded"
                              style={{ backgroundColor: q.color }}
                            />
                            <span className="font-medium">{q.heat_score.toFixed(1)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="max-w-xs">
                            {q.landing_pages.length > 0 ? (
                              <>
                                <a
                                  href={q.landing_pages[0]}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-primary hover:underline truncate block"
                                >
                                  {q.landing_pages[0]}
                                </a>
                                {q.landing_pages.length > 1 && (
                                  <div className="text-xs text-muted-foreground mt-1">
                                    +{q.landing_pages.length - 1} ещё
                                  </div>
                                )}
                              </>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {q.segments.slice(0, 2).map((seg, i) => (
                              <span
                                key={i}
                                className="text-xs bg-muted px-2 py-0.5 rounded"
                              >
                                {seg}
                              </span>
                            ))}
                            {q.segments.length > 2 && (
                              <span className="text-xs text-muted-foreground">
                                +{q.segments.length - 2}
                              </span>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

