'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Database,
  Play,
  RefreshCw,
  Flame,
  CheckCircle2,
  XCircle,
  Clock,
  Layers,
  TrendingUp,
  Users,
  Filter
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface PipelineStatus {
  batch_id: string;
  status: string;
  raw_count: number;
  normalized_count: number;
  features_count: number;
  errors: string[];
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

interface HealthStatus {
  status: string;
  sources: Record<string, boolean>;
  timestamp: string;
}

interface Feature {
  id: string;
  session_id: string;
  source: string;
  event_date: string;
  hot_score_base: number | null;
  engagement_score: number | null;
  intent_score: number | null;
  segment_type: string | null;
  decision_stage: string | null;
  page_depth: number | null;
  active_time_sec: number | null;
  bounce_flag: boolean | null;
  return_flag: boolean | null;
  key_pages_visited: Record<string, boolean> | null;
}

export default function DataIntakePage() {
  // State
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [selectedSource, setSelectedSource] = useState('YANDEX_METRIKA');
  const [dateFrom, setDateFrom] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [features, setFeatures] = useState<Feature[]>([]);
  const [hotLeads, setHotLeads] = useState<Feature[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingFeatures, setLoadingFeatures] = useState(false);
  const [minHotScore, setMinHotScore] = useState(50);

  // Load initial data
  useEffect(() => {
    loadHealth();
    loadSources();
    loadHotLeads();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await apiClient.getDataIntakeHealth();
      setHealth(data);
    } catch (error) {
      console.error('Failed to load health:', error);
    }
  };

  const loadSources = async () => {
    try {
      const data = await apiClient.getDataIntakeSources();
      setSources(data.sources);
      if (data.sources.length > 0 && !selectedSource) {
        setSelectedSource(data.sources[0]);
      }
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const loadHotLeads = async () => {
    try {
      const data = await apiClient.getDataIntakeHotLeads(minHotScore, 20);
      setHotLeads(data.items);
    } catch (error) {
      console.error('Failed to load hot leads:', error);
    }
  };

  const loadFeatures = async () => {
    setLoadingFeatures(true);
    try {
      const data = await apiClient.getDataIntakeFeatures({
        source: selectedSource,
        dateFrom,
        dateTo,
        limit: 100,
      });
      setFeatures(data.items);
    } catch (error) {
      console.error('Failed to load features:', error);
    } finally {
      setLoadingFeatures(false);
    }
  };

  const runPipeline = async () => {
    setLoading(true);
    setPipelineStatus(null);
    try {
      const status = await apiClient.runDataIntakePipeline(selectedSource, dateFrom, dateTo);
      setPipelineStatus(status);
      // Reload features after pipeline
      await loadFeatures();
      await loadHotLeads();
    } catch (error: any) {
      console.error('Pipeline failed:', error);
      setPipelineStatus({
        batch_id: 'error',
        status: 'failed',
        raw_count: 0,
        normalized_count: 0,
        features_count: 0,
        errors: [error.message || 'Unknown error'],
        started_at: new Date().toISOString(),
        completed_at: null,
        duration_ms: null,
      });
    } finally {
      setLoading(false);
    }
  };

  const getSegmentColor = (segment: string | null) => {
    switch (segment) {
      case 'горячий': return 'bg-red-500';
      case 'методичный': return 'bg-blue-500';
      case 'осторожный': return 'bg-yellow-500';
      case 'импульсивный': return 'bg-purple-500';
      case 'сомневающийся': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  };

  const getStageColor = (stage: string | null) => {
    switch (stage) {
      case 'purchase_intent': return 'bg-green-500';
      case 'evaluation': return 'bg-blue-500';
      case 'consideration': return 'bg-yellow-500';
      case 'awareness': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Database className="h-8 w-8 text-purple-500" />
          Data Intake Pipeline
        </h2>
        <p className="text-muted-foreground mt-2">
          ETL Pipeline: Raw → Normalized → Features (L1 → L2 → L3)
        </p>
      </div>

      {/* Health Status */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Статус модуля</CardTitle>
            {health?.status === 'healthy' ? (
              <CheckCircle2 className="h-4 w-4 text-green-500" />
            ) : (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.status === 'healthy' ? 'OK' : health?.status || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground">
              {health ? new Date(health.timestamp).toLocaleString() : '-'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Источники</CardTitle>
            <Layers className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{sources.length}</div>
            <p className="text-xs text-muted-foreground">
              {sources.join(', ') || 'Нет'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hot Leads</CardTitle>
            <Flame className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{hotLeads.length}</div>
            <p className="text-xs text-muted-foreground">
              score ≥ {minHotScore}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Features</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{features.length}</div>
            <p className="text-xs text-muted-foreground">
              в выбранном периоде
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Control */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Запуск Pipeline
          </CardTitle>
          <CardDescription>
            Загрузить данные из источника и обработать через 3 слоя
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <Label>Источник</Label>
              <select
                className="w-full p-2 border rounded-md"
                value={selectedSource}
                onChange={(e) => setSelectedSource(e.target.value)}
              >
                {sources.map((source) => (
                  <option key={source} value={source}>
                    {source}
                  </option>
                ))}
                {sources.length === 0 && (
                  <option value="YANDEX_METRIKA">YANDEX_METRIKA</option>
                )}
              </select>
            </div>
            <div className="space-y-2">
              <Label>Дата от</Label>
              <Input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Дата до</Label>
              <Input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>&nbsp;</Label>
              <Button
                onClick={runPipeline}
                disabled={loading}
                className="w-full"
              >
                {loading ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {loading ? 'Загрузка...' : 'Запустить'}
              </Button>
            </div>
          </div>

          {/* Pipeline Status */}
          {pipelineStatus && (
            <div className="mt-4 p-4 rounded-lg bg-muted">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant={pipelineStatus.status === 'completed' ? 'default' : 'destructive'}>
                  {pipelineStatus.status}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Batch: {pipelineStatus.batch_id}
                </span>
                {pipelineStatus.duration_ms && (
                  <span className="text-sm text-muted-foreground flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {pipelineStatus.duration_ms}ms
                  </span>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Raw (L1):</span>{' '}
                  <span className="font-medium">{pipelineStatus.raw_count}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Normalized (L2):</span>{' '}
                  <span className="font-medium">{pipelineStatus.normalized_count}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Features (L3):</span>{' '}
                  <span className="font-medium">{pipelineStatus.features_count}</span>
                </div>
              </div>
              {pipelineStatus.errors.length > 0 && (
                <div className="mt-2 text-sm text-red-500">
                  Ошибки: {pipelineStatus.errors.join(', ')}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Hot Leads */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5 text-orange-500" />
            Hot Leads (Feature Store)
          </CardTitle>
          <CardDescription>
            Сессии с высоким hot_score_base (≥ {minHotScore})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div className="flex items-center gap-2">
              <Label>Min Score:</Label>
              <Input
                type="number"
                value={minHotScore}
                onChange={(e) => setMinHotScore(parseInt(e.target.value) || 0)}
                className="w-20"
                min={0}
                max={100}
              />
            </div>
            <Button variant="outline" size="sm" onClick={loadHotLeads}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Обновить
            </Button>
          </div>

          {hotLeads.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Нет данных. Запустите pipeline для загрузки.
            </div>
          ) : (
            <div className="space-y-3">
              {hotLeads.map((lead, idx) => (
                <div
                  key={lead.id || idx}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex flex-col">
                      <span className="font-medium text-sm">
                        {lead.session_id?.slice(0, 20) || 'N/A'}...
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {lead.event_date}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {lead.segment_type && (
                      <Badge className={getSegmentColor(lead.segment_type)}>
                        {lead.segment_type}
                      </Badge>
                    )}
                    {lead.decision_stage && (
                      <Badge variant="outline">
                        {lead.decision_stage}
                      </Badge>
                    )}
                    <div className="flex items-center gap-1 text-sm">
                      <Flame className="h-4 w-4 text-orange-500" />
                      <span className="font-bold">{lead.hot_score_base || 0}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Features Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Все Features
          </CardTitle>
          <CardDescription>
            Данные из Feature Store (L3) — топливо для Analytics Agent
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="outline"
            onClick={loadFeatures}
            disabled={loadingFeatures}
            className="mb-4"
          >
            {loadingFeatures ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Загрузить Features
          </Button>

          {features.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Нажмите "Загрузить Features" для просмотра данных
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Date</th>
                    <th className="text-left p-2">Session</th>
                    <th className="text-left p-2">Hot Score</th>
                    <th className="text-left p-2">Engagement</th>
                    <th className="text-left p-2">Intent</th>
                    <th className="text-left p-2">Pages</th>
                    <th className="text-left p-2">Time (sec)</th>
                    <th className="text-left p-2">Segment</th>
                    <th className="text-left p-2">Stage</th>
                  </tr>
                </thead>
                <tbody>
                  {features.slice(0, 50).map((f, idx) => (
                    <tr key={f.id || idx} className="border-b hover:bg-muted/50">
                      <td className="p-2">{f.event_date}</td>
                      <td className="p-2 font-mono text-xs">
                        {f.session_id?.slice(0, 15) || '-'}...
                      </td>
                      <td className="p-2">
                        <span className={`font-bold ${(f.hot_score_base || 0) >= 50 ? 'text-orange-500' : ''}`}>
                          {f.hot_score_base ?? '-'}
                        </span>
                      </td>
                      <td className="p-2">{f.engagement_score ?? '-'}</td>
                      <td className="p-2">{f.intent_score ?? '-'}</td>
                      <td className="p-2">{f.page_depth ?? '-'}</td>
                      <td className="p-2">{f.active_time_sec ?? '-'}</td>
                      <td className="p-2">
                        {f.segment_type ? (
                          <Badge variant="secondary" className="text-xs">
                            {f.segment_type}
                          </Badge>
                        ) : '-'}
                      </td>
                      <td className="p-2">
                        {f.decision_stage ? (
                          <Badge variant="outline" className="text-xs">
                            {f.decision_stage}
                          </Badge>
                        ) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
