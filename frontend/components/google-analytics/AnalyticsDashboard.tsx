'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from 'recharts';
import { apiClient } from '@/lib/api-client';
import { Loader2, RefreshCw, Filter, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AnalyticsData {
  visitors: Array<{ date: string; visits: number; users: number; pageviews: number }>;
  sources: Array<{ source: string; medium: string; visits: number; users: number }>;
  queries: Array<{ event: string; landing_page?: string; count: number; users: number }>;
  geography: Array<{ country: string; city: string; visits: number; users: number }>;
}

interface AnalyticsDashboardProps {
  propertyId: string;
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];

export function AnalyticsDashboard({ propertyId }: AnalyticsDashboardProps) {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [queriesPageSize, setQueriesPageSize] = useState(25);
  const [queriesPage, setQueriesPage] = useState(1);
  
  // Фильтры
  const [filterEvent, setFilterEvent] = useState<string>('all');
  const [filterPage, setFilterPage] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [groupBy, setGroupBy] = useState<'none' | 'page' | 'event'>('none');

  useEffect(() => {
    fetchAnalytics();
  }, [propertyId, days]);

  const fetchAnalytics = async () => {
    if (!propertyId) return;

    try {
      setLoading(true);
      
      const [visitorsRes, sourcesRes, queriesRes, geographyRes] = await Promise.all([
        apiClient.getGA4VisitorsByDate(propertyId, days),
        apiClient.getGA4TrafficSources(propertyId, days, 20),
        apiClient.getGA4SearchQueries(propertyId, days, 100),
        apiClient.getGA4Geography(propertyId, days, 100),
      ]);

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
      console.error('Ошибка при загрузке аналитики GA4:', error);
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
      
      let date = '';
      if (dimensions[0]) {
        date = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].value || dimensions[0].name || '';
      }
      
      const formattedDate = date.split('T')[0] || date;
      
      return {
        date: formattedDate,
        visits: Math.round(metrics[0] || 0), // sessions
        users: Math.round(metrics[1] || 0), // activeUsers
        pageviews: Math.round(metrics[2] || 0), // screenPageViews
      };
    }).sort((a, b) => a.date.localeCompare(b.date));
  };

  // Преобразование данных источников
  const transformSourcesData = (response: any): Array<{ source: string; medium: string; visits: number; users: number }> => {
    if (!response?.data || !Array.isArray(response.data)) return [];
    
    return response.data.slice(0, 10).map((row: any) => {
      const dimensions = row.dimensions || [];
      const metrics = row.metrics || [];
      
      let source = '';
      let medium = '';
      
      if (dimensions[0]) {
        source = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].value || dimensions[0].name || '';
      }
      if (dimensions[1]) {
        medium = typeof dimensions[1] === 'string' ? dimensions[1] : dimensions[1].value || dimensions[1].name || '';
      }
      
      return {
        source: source || 'Прямой трафик',
        medium: medium || 'none',
        visits: Math.round(metrics[0] || 0), // sessions
        users: Math.round(metrics[1] || 0), // activeUsers
      };
    }).sort((a, b) => b.visits - a.visits);
  };

  // Преобразование данных событий/запросов
  const transformQueriesData = (response: any): Array<{ event: string; landing_page?: string; count: number; users: number }> => {
    if (!response?.data || !Array.isArray(response.data)) return [];
    
    return response.data
      .map((row: any) => {
        const dimensions = row.dimensions || [];
        const metrics = row.metrics || [];
        
        let event = '';
        let landing_page = '';
        
        if (dimensions[0]) {
          event = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].value || dimensions[0].name || '';
        }
        if (dimensions[1]) {
          landing_page = typeof dimensions[1] === 'string' ? dimensions[1] : dimensions[1].value || dimensions[1].name || '';
        }
        
        return {
          event: event || 'Без события',
          landing_page: landing_page || undefined,
          count: Math.round(metrics[0] || 0), // eventCount
          users: Math.round(metrics[1] || 0), // activeUsers
        };
      })
      .filter(item => item.event !== 'Без события' && item.count > 0)
      .sort((a, b) => b.count - a.count);
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
          country = typeof dimensions[0] === 'string' ? dimensions[0] : dimensions[0].value || dimensions[0].name || 'Неизвестно';
        }
        if (dimensions[1]) {
          city = typeof dimensions[1] === 'string' ? dimensions[1] : dimensions[1].value || dimensions[1].name || 'Неизвестно';
        }
        
        return {
          country,
          city,
          visits: Math.round(metrics[0] || 0), // sessions
          users: Math.round(metrics[1] || 0), // activeUsers
        };
      })
      .filter(item => item.visits > 0)
      .sort((a, b) => b.visits - a.visits);
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
              Динамика sessions, users и pageviews за выбранный период
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
                <Bar dataKey="visits" fill="#8884d8" name="Sessions" />
                <Line
                  type="monotone"
                  dataKey="users"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Users"
                />
                <Line
                  type="monotone"
                  dataKey="pageviews"
                  stroke="#ffc658"
                  strokeWidth={2}
                  name="Pageviews"
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* 2. Распределение по источникам - Горизонтальный Bar Chart */}
      {data.sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>📊 Источники трафика</CardTitle>
            <CardDescription>
              Распределение sessions и users по источникам (горизонтальный вид)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart 
                data={data.sources.slice(0, 10)} 
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
                  dataKey="source" 
                  width={90}
                  stroke="hsl(var(--muted-foreground))" 
                  style={{ fontSize: '11px' }}
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
          </CardContent>
        </Card>
      )}

      {/* 3. ТОП событий */}
      {data.queries.length > 0 && (() => {
        // Получаем уникальные значения для фильтров
        const uniqueEvents = Array.from(new Set(data.queries.map(q => q.event))).sort();
        const uniquePages = Array.from(
          new Set(data.queries.map(q => q.landing_page).filter(Boolean))
        ).sort() as string[];
        
        // Применяем фильтры
        let filteredQueries = data.queries.filter(q => {
          // Фильтр по событию
          if (filterEvent !== 'all' && q.event !== filterEvent) return false;
          
          // Фильтр по странице
          if (filterPage !== 'all') {
            if (filterPage === 'empty' && q.landing_page) return false;
            if (filterPage !== 'empty' && q.landing_page !== filterPage) return false;
          }
          
          // Поиск по тексту
          if (searchQuery) {
            const query = searchQuery.toLowerCase();
            const matchesEvent = q.event.toLowerCase().includes(query);
            const matchesPage = q.landing_page?.toLowerCase().includes(query) || false;
            if (!matchesEvent && !matchesPage) return false;
          }
          
          return true;
        });
        
        // Применяем группировку
        let processedQueries: Array<{ event: string; landing_page?: string; count: number; users: number; eventCount?: number }>;
        
        if (groupBy === 'page') {
          // Группируем по странице - суммируем все события для каждой страницы
          const grouped = new Map<string, { 
            event: string; 
            landing_page?: string; 
            count: number; 
            users: number;
            eventCount: number;
          }>();
          
          filteredQueries.forEach(q => {
            const key = q.landing_page || '(not set)';
            const existing = grouped.get(key);
            
            if (existing) {
              existing.count += q.count;
              existing.users = Math.max(existing.users, q.users); // Максимум уникальных пользователей
              existing.eventCount += 1;
            } else {
              grouped.set(key, {
                event: q.event, // Показываем первое событие, но ниже укажем количество
                landing_page: q.landing_page,
                count: q.count,
                users: q.users,
                eventCount: 1,
              });
            }
          });
          
          processedQueries = Array.from(grouped.values())
            .map(item => ({
              ...item,
              event: item.eventCount > 1 
                ? `${item.event} (+ еще ${item.eventCount - 1} событий)`
                : item.event,
            }))
            .sort((a, b) => b.count - a.count);
        } else if (groupBy === 'event') {
          // Группируем по событию - суммируем все страницы для каждого события
          const grouped = new Map<string, { 
            event: string; 
            landing_page?: string; 
            count: number; 
            users: number;
            pageCount: number;
          }>();
          
          filteredQueries.forEach(q => {
            const key = q.event;
            const existing = grouped.get(key);
            
            if (existing) {
              existing.count += q.count;
              existing.users = Math.max(existing.users, q.users);
              existing.pageCount += 1;
            } else {
              grouped.set(key, {
                event: q.event,
                landing_page: undefined, // При группировке по событию страница не показывается
                count: q.count,
                users: q.users,
                pageCount: 1,
              });
            }
          });
          
          processedQueries = Array.from(grouped.values())
            .map(item => ({
              ...item,
              event: item.pageCount > 1
                ? `${item.event} (${item.pageCount} страниц)`
                : item.event,
            }))
            .sort((a, b) => b.count - a.count);
        } else {
          // Без группировки
          processedQueries = filteredQueries;
        }
        
        const totalQueries = processedQueries.length;
        const totalPages = Math.ceil(totalQueries / queriesPageSize);
        const startIndex = (queriesPage - 1) * queriesPageSize;
        const endIndex = startIndex + queriesPageSize;
        const paginatedQueries = processedQueries.slice(startIndex, endIndex);
        
        return (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>🔍 ТОП событий</CardTitle>
                  <CardDescription>
                    Самые популярные события в GA4
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-muted-foreground">На странице:</label>
                  <select
                    value={queriesPageSize}
                    onChange={(e) => {
                      setQueriesPageSize(Number(e.target.value));
                      setQueriesPage(1);
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
              {/* Панель фильтров */}
              <div className="mb-6 p-4 border rounded-lg bg-muted/30 space-y-4">
                <div className="flex items-center gap-2 mb-2">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Фильтры и группировка</span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Поиск */}
                  <div className="space-y-2">
                    <Label htmlFor="search" className="text-xs">Поиск</Label>
                    <div className="relative">
                      <Input
                        id="search"
                        placeholder="Событие или страница..."
                        value={searchQuery}
                        onChange={(e) => {
                          setSearchQuery(e.target.value);
                          setQueriesPage(1);
                        }}
                        className="pr-8"
                      />
                      {searchQuery && (
                        <button
                          onClick={() => {
                            setSearchQuery('');
                            setQueriesPage(1);
                          }}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                  
                  {/* Фильтр по событию */}
                  <div className="space-y-2">
                    <Label htmlFor="filter-event" className="text-xs">Событие</Label>
                    <Select
                      value={filterEvent}
                      onValueChange={(value) => {
                        setFilterEvent(value);
                        setQueriesPage(1);
                      }}
                    >
                      <SelectTrigger id="filter-event" className="w-full">
                        <SelectValue placeholder="Все события" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все события</SelectItem>
                        {uniqueEvents.map(event => (
                          <SelectItem key={event} value={event}>
                            {event}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Фильтр по странице */}
                  <div className="space-y-2">
                    <Label htmlFor="filter-page" className="text-xs">Landing Page</Label>
                    <Select
                      value={filterPage}
                      onValueChange={(value) => {
                        setFilterPage(value);
                        setQueriesPage(1);
                      }}
                    >
                      <SelectTrigger id="filter-page" className="w-full">
                        <SelectValue placeholder="Все страницы" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Все страницы</SelectItem>
                        <SelectItem value="empty">Без страницы</SelectItem>
                        {uniquePages.map(page => (
                          <SelectItem key={page} value={page}>
                            {page.length > 40 ? page.substring(0, 40) + '...' : page}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Группировка */}
                  <div className="space-y-2">
                    <Label htmlFor="group-by" className="text-xs">Группировка</Label>
                    <Select
                      value={groupBy}
                      onValueChange={(value: 'none' | 'page' | 'event') => {
                        setGroupBy(value);
                        setQueriesPage(1);
                      }}
                    >
                      <SelectTrigger id="group-by" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Без группировки</SelectItem>
                        <SelectItem value="page">По странице</SelectItem>
                        <SelectItem value="event">По событию</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                {/* Сброс фильтров */}
                {(filterEvent !== 'all' || filterPage !== 'all' || searchQuery || groupBy !== 'none') && (
                  <div className="pt-2 border-t">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setFilterEvent('all');
                        setFilterPage('all');
                        setSearchQuery('');
                        setGroupBy('none');
                        setQueriesPage(1);
                      }}
                      className="text-xs"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Сбросить все фильтры
                    </Button>
                  </div>
                )}
              </div>
              
              {/* Информация о результатах */}
              <div className="mb-4 text-sm text-muted-foreground">
                Найдено записей: {totalQueries}
                {filteredQueries.length !== data.queries.length && (
                  <span className="ml-2">
                    (из {data.queries.length} всего)
                  </span>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-sm font-medium">#</th>
                      <th className="px-4 py-2 text-sm font-medium">
                        Событие
                        {groupBy === 'event' && <span className="ml-1 text-xs text-muted-foreground">(сгруппировано)</span>}
                      </th>
                      <th className="px-4 py-2 text-sm font-medium text-right">Количество</th>
                      <th className="px-4 py-2 text-sm font-medium text-right">Users</th>
                      <th className="px-4 py-2 text-sm font-medium">
                        🌐 Landing Page
                        {groupBy === 'page' && <span className="ml-1 text-xs text-muted-foreground">(сгруппировано)</span>}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedQueries.map((q, idx) => (
                      <tr
                        key={startIndex + idx}
                        className="border-b border-border hover:bg-muted/50 transition-colors"
                      >
                        <td className="px-4 py-2 text-sm">{startIndex + idx + 1}</td>
                        <td className="px-4 py-2 text-sm font-medium">{q.event}</td>
                        <td className="px-4 py-2 text-sm font-bold text-right">
                          {q.count.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-sm text-right text-muted-foreground">
                          {q.users.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-sm">
                          {q.landing_page ? (
                            <div className="max-w-xs">
                              <a
                                href={q.landing_page}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary hover:underline truncate block"
                                title={q.landing_page}
                              >
                                {q.landing_page.length > 40 
                                  ? q.landing_page.substring(0, 40) + '...'
                                  : q.landing_page}
                              </a>
                            </div>
                          ) : (
                            <span className="text-muted-foreground">
                              {groupBy === 'event' ? '—' : '(not set)'}
                            </span>
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
                    <th className="px-4 py-2 text-sm font-medium text-right">Sessions</th>
                    <th className="px-4 py-2 text-sm font-medium text-right">Users</th>
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

