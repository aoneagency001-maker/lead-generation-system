'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { apiClient } from '@/lib/api-client';
import { Loader2, RefreshCw } from 'lucide-react';

interface AnalyticsData {
  visitors: Array<{ date: string; visits: number; users: number; pageviews: number }>;
  sources: Array<{ source: string; visits: number; users: number }>;
  queries: Array<{ query: string; visits: number; landing_pages: string[] }>;
  geography: Array<{ country: string; city: string; visits: number; users: number }>;
}

interface AnalyticsDashboardProps {
  counterId: number;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];

export function AnalyticsDashboard({ counterId }: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [queriesPageSize, setQueriesPageSize] = useState(25);
  const [queriesPage, setQueriesPage] = useState(1);

  useEffect(() => {
    fetchAnalytics();
  }, [counterId, days]);

  const fetchAnalytics = async () => {
    if (!counterId) return;

    try {
      setLoading(true);
      
      // Загружаем больше запросов для пагинации (до 100)
      const [visitorsRes, sourcesRes, queriesRes, geographyRes] = await Promise.all([
        apiClient.getMetrikaVisitorsByDate(counterId, days),
        apiClient.getMetrikaTrafficSources(counterId, days, 20),
        apiClient.getMetrikaSearchQueriesDetailed(counterId, days, 100),
        apiClient.getMetrikaGeography(counterId, days),
      ]);

      // Преобразуем данные в нужный формат
      const visitors = transformVisitorsData(visitorsRes);
      const sources = transformSourcesData(sourcesRes);
      const queries = transformQueriesData(queriesRes);
      const geography = transformGeographyData(geographyRes);

      setData({
        visitors,
        sources,
        queries,
        geography,
      });
    } catch (error) {
      console.error('Ошибка при загрузке аналитики:', error);
    } finally {
      setLoading(false);
    }
  };

  // Преобразование данных посетителей по дням
  const transformVisitorsData = (response: any): Array<{ date: string; visits: number; users: number; pageviews: number }> => {
    if (!response?.data || !Array.isArray(response.data)) return [];
    
    return response.data.map((row: any) => {
      const dimensions = row.dimensions || [];
      const metrics = row.metrics || [];
      
      // Получаем дату из первого измерения (может быть объект с name или строка)
      let date = '';
      if (dimensions[0]) {
        date = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].name || '';
      }
      
      // Форматируем дату (может быть в формате "2025-11-16" или "2025-11-16T00:00:00")
      const formattedDate = date.split('T')[0] || date;
      
      return {
        date: formattedDate,
        visits: Math.round(metrics[0] || 0),
        users: Math.round(metrics[1] || 0),
        pageviews: Math.round(metrics[2] || 0),
      };
    }).sort((a, b) => a.date.localeCompare(b.date)); // Сортируем по дате
  };

  // Преобразование данных источников
  const transformSourcesData = (response: any): Array<{ source: string; visits: number; users: number }> => {
    if (!response?.data || !Array.isArray(response.data)) return [];
    
    return response.data.slice(0, 10).map((row: any) => {
      const dimensions = row.dimensions || [];
      const metrics = row.metrics || [];
      
      // Берем utm_source или referer (dimensions может быть массивом объектов или строк)
      let utmSource = '';
      let referer = '';
      
      if (dimensions[0]) {
        utmSource = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].name || '';
      }
      if (dimensions[1]) {
        referer = typeof dimensions[1] === 'string' ? dimensions[1] : dimensions[1].name || '';
      }
      
      const source = utmSource || referer || 'Прямой трафик';
      
      return {
        source: source.length > 30 ? source.substring(0, 30) + '...' : source,
        visits: Math.round(metrics[0] || 0),
        users: Math.round(metrics[1] || 0),
      };
    }).sort((a, b) => b.visits - a.visits); // Сортируем по визитам
  };

  // Преобразование данных поисковых запросов (из detailed endpoint)
  const transformQueriesData = (response: any[]): Array<{ query: string; visits: number; landing_pages: string[] }> => {
    if (!Array.isArray(response)) return [];
    
    return response
      .map((item: any) => {
        const query = item.query || 'Без запроса';
        const visits = item.visits || 0;
        const landing_pages = item.landing_pages || [];
        
        return {
          query: query.length > 50 ? query.substring(0, 50) + '...' : query,
          visits,
          landing_pages,
        };
      })
      .filter(item => item.query !== 'Без запроса' && item.visits > 0) // Фильтруем пустые
      .sort((a, b) => b.visits - a.visits); // Сортируем по визитам
  };

  // Преобразование данных географии
  const transformGeographyData = (response: any): Array<{ country: string; city: string; visits: number; users: number }> => {
    if (!response?.data || !Array.isArray(response.data)) return [];
    
    return response.data
      .slice(0, 20)
      .map((row: any) => {
        const dimensions = row.dimensions || [];
        const metrics = row.metrics || [];
        
        let country = 'Неизвестно';
        let city = 'Неизвестно';
        
        if (dimensions[0]) {
          country = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].name || 'Неизвестно';
        }
        if (dimensions[1]) {
          city = typeof dimensions[1] === 'string' ? dimensions[1] : dimensions[1].name || 'Неизвестно';
        }
        
        return {
          country,
          city,
          visits: Math.round(metrics[0] || 0),
          users: Math.round(metrics[1] || 0),
        };
      })
      .filter(item => item.visits > 0) // Фильтруем нулевые
      .sort((a, b) => b.visits - a.visits); // Сортируем по визитам
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Загрузка аналитики...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            Нет данных для отображения
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Выбор периода */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Период анализа</CardTitle>
              <CardDescription>
                Выберите период для отображения данных
              </CardDescription>
            </div>
            <Button
              onClick={fetchAnalytics}
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
          <div className="flex gap-2">
            {[7, 14, 30, 90].map((d) => (
              <Button
                key={d}
                variant={days === d ? 'default' : 'outline'}
                size="sm"
                onClick={() => setDays(d)}
              >
                {d} дней
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 1. Временной график посещаемости */}
      {data.visitors.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>📈 Посещаемость по дням</CardTitle>
            <CardDescription>
              Динамика визитов, посетителей и просмотров за выбранный период
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={data.visitors}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  style={{ fontSize: '12px' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="hsl(var(--muted-foreground))" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                  }}
                />
                <Legend />
                <Bar dataKey="visits" fill="#8884d8" name="Визиты" />
                <Line
                  type="monotone"
                  dataKey="users"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Посетители"
                />
                <Line
                  type="monotone"
                  dataKey="pageviews"
                  stroke="#ffc658"
                  strokeWidth={2}
                  name="Просмотры"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* 2. Распределение по источникам */}
      {data.sources.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pie Chart */}
          <Card>
            <CardHeader>
              <CardTitle>🎯 Источники трафика (Pie)</CardTitle>
              <CardDescription>
                Распределение по источникам в процентах
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.sources}
                    dataKey="visits"
                    nameKey="source"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ source, percent }) => `${source}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {data.sources.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Bar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>📊 Источники трафика (Bar)</CardTitle>
              <CardDescription>
                Сравнение визитов и посетителей по источникам
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.sources}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--muted))" />
                  <XAxis
                    dataKey="source"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    stroke="hsl(var(--muted-foreground))"
                    style={{ fontSize: '11px' }}
                  />
                  <YAxis stroke="hsl(var(--muted-foreground))" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--popover))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                  />
                  <Legend />
                  <Bar dataKey="visits" fill="#8884d8" name="Визиты" />
                  <Bar dataKey="users" fill="#82ca9d" name="Посетители" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 3. ТОП поисковых запросов */}
      {data.queries.length > 0 && (() => {
        const totalQueries = data.queries.length;
        const totalPages = Math.ceil(totalQueries / queriesPageSize);
        const startIndex = (queriesPage - 1) * queriesPageSize;
        const endIndex = startIndex + queriesPageSize;
        const paginatedQueries = data.queries.slice(startIndex, endIndex);
        
        return (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>🔍 ТОП поисковых запросов</CardTitle>
                  <CardDescription>
                    Самые популярные поисковые запросы, приведшие на сайт
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-muted-foreground">На странице:</label>
                  <select
                    value={queriesPageSize}
                    onChange={(e) => {
                      setQueriesPageSize(Number(e.target.value));
                      setQueriesPage(1); // Сбрасываем на первую страницу
                    }}
                    className="px-3 py-1.5 border rounded-md bg-background text-sm"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                  </select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-sm font-medium">#</th>
                      <th className="px-4 py-2 text-sm font-medium">Запрос</th>
                      <th className="px-4 py-2 text-sm font-medium text-right">Визиты</th>
                      <th className="px-4 py-2 text-sm font-medium">🌐 Страница входа</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedQueries.map((q, idx) => (
                      <tr
                        key={startIndex + idx}
                        className="border-b border-border hover:bg-muted/50 transition-colors"
                      >
                        <td className="px-4 py-2 text-sm">{startIndex + idx + 1}</td>
                        <td className="px-4 py-2 text-sm font-medium">{q.query}</td>
                        <td className="px-4 py-2 text-sm font-bold text-right">
                          {q.visits.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          {q.landing_pages && q.landing_pages.length > 0 ? (
                            <div className="max-w-xs">
                              <a
                                href={q.landing_pages[0]}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline truncate block"
                                title={q.landing_pages[0]}
                              >
                                {q.landing_pages[0].length > 40 
                                  ? q.landing_pages[0].substring(0, 40) + '...'
                                  : q.landing_pages[0]}
                              </a>
                              {q.landing_pages.length > 1 && (
                                <div className="text-xs text-muted-foreground mt-1">
                                  +{q.landing_pages.length - 1} ещё
                                </div>
                              )}
                            </div>
                          ) : (
                            <span className="text-muted-foreground">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Пагинация */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t">
                  <div className="text-sm text-muted-foreground">
                    Показано {startIndex + 1}–{Math.min(endIndex, totalQueries)} из {totalQueries}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setQueriesPage(p => Math.max(1, p - 1))}
                      disabled={queriesPage === 1}
                    >
                      Назад
                    </Button>
                    <div className="text-sm text-muted-foreground">
                      Страница {queriesPage} из {totalPages}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setQueriesPage(p => Math.min(totalPages, p + 1))}
                      disabled={queriesPage === totalPages}
                    >
                      Вперёд
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        );
      })()}

      {/* 4. География */}
      {data.geography.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>🌍 География посетителей</CardTitle>
            <CardDescription>
              Распределение посетителей по странам и городам
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-muted">
                  <tr>
                    <th className="px-4 py-2 text-sm font-medium">Страна</th>
                    <th className="px-4 py-2 text-sm font-medium">Город</th>
                    <th className="px-4 py-2 text-sm font-medium text-right">Визиты</th>
                    <th className="px-4 py-2 text-sm font-medium text-right">Посетители</th>
                  </tr>
                </thead>
                <tbody>
                  {data.geography.map((g, idx) => (
                    <tr
                      key={idx}
                      className="border-b border-border hover:bg-muted/50 transition-colors"
                    >
                      <td className="px-4 py-2 text-sm">{g.country}</td>
                      <td className="px-4 py-2 text-sm font-medium">{g.city}</td>
                      <td className="px-4 py-2 text-sm font-bold text-right">
                        {g.visits.toLocaleString()}
                      </td>
                      <td className="px-4 py-2 text-sm text-right text-muted-foreground">
                        {g.users.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

