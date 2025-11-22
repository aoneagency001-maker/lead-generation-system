'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/lib/i18n/context';
import { BarChart3, TrendingUp, ExternalLink, Database, Flame, Brain, Sparkles } from 'lucide-react';

export default function AnalyticsPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('analytics.title')}</h2>
        <p className="text-muted-foreground">
          {t('analytics.subtitle')}
        </p>
      </div>

      {/* Яндекс.Метрика */}
      <Card className="border-2 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-6 w-6 text-blue-500" />
              <div>
                <CardTitle>Яндекс.Метрика</CardTitle>
                <CardDescription>
                  Аналитика и отчеты по счетчикам Яндекс.Метрики
                </CardDescription>
              </div>
            </div>
            <Link href="/dashboard/analytics/yandex-metrika">
              <Button>
                Открыть
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-blue-500">9</div>
              <div className="text-sm text-muted-foreground mt-1">Счетчиков</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-green-500">✓</div>
              <div className="text-sm text-muted-foreground mt-1">Подключено</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <TrendingUp className="h-6 w-6 mx-auto text-purple-500" />
              <div className="text-sm text-muted-foreground mt-1">Активно</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Просматривайте визиты, просмотры, посетителей и другие метрики по вашим счетчикам Яндекс.Метрики.
            Выберите счетчик и получите детальные отчеты за любой период.
          </p>
        </CardContent>
      </Card>

      {/* Google Analytics 4 */}
      <Card className="border-2 border-orange-200 dark:border-orange-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-6 w-6 text-orange-500" />
              <div>
                <CardTitle>Google Analytics 4</CardTitle>
                <CardDescription>
                  Аналитика и отчеты по Properties Google Analytics 4
                </CardDescription>
              </div>
            </div>
            <Link href="/dashboard/analytics/google-analytics">
              <Button>
                Открыть
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-orange-500">GA4</div>
              <div className="text-sm text-muted-foreground mt-1">Properties</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-green-500">✓</div>
              <div className="text-sm text-muted-foreground mt-1">Подключено</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <TrendingUp className="h-6 w-6 mx-auto text-purple-500" />
              <div className="text-sm text-muted-foreground mt-1">Real-time</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Просматривайте sessions, users, pageviews и другие метрики по вашим Properties GA4.
            Real-time данные, события, география и детальная аналитика за любой период.
          </p>
        </CardContent>
      </Card>

      {/* Data Intake Pipeline */}
      <Card className="border-2 border-purple-200 dark:border-purple-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database className="h-6 w-6 text-purple-500" />
              <div>
                <CardTitle>Data Intake Pipeline</CardTitle>
                <CardDescription>
                  ETL Pipeline: Raw → Normalized → Features (L1 → L2 → L3)
                </CardDescription>
              </div>
            </div>
            <Link href="/dashboard/analytics/data-intake">
              <Button variant="outline" className="border-purple-300">
                Открыть
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-purple-500">L1</div>
              <div className="text-sm text-muted-foreground mt-1">Raw Data</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-blue-500">L2</div>
              <div className="text-sm text-muted-foreground mt-1">Normalized</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <Flame className="h-6 w-6 mx-auto text-orange-500" />
              <div className="text-sm text-muted-foreground mt-1">Features (L3)</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Загружайте данные из Яндекс.Метрики, нормализуйте в единый формат и вычисляйте
            признаки (hot_score, segment_type, decision_stage) для аналитического агента.
          </p>
        </CardContent>
      </Card>

      {/* LLM Pipeline */}
      <Card className="border-2 border-green-200 dark:border-green-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Brain className="h-6 w-6 text-green-500" />
              <div>
                <CardTitle>LLM Pipeline</CardTitle>
                <CardDescription>
                  3-Layer AI: GPT-4 → Claude → Perplexity (L2 → L3 → L4)
                </CardDescription>
              </div>
            </div>
            <Link href="/dashboard/analytics/llm-pipeline">
              <Button className="bg-green-600 hover:bg-green-700">
                Открыть
                <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <div className="text-center p-4 bg-muted rounded-md">
              <Database className="h-6 w-6 mx-auto text-blue-500" />
              <div className="text-sm text-muted-foreground mt-1">GPT-4</div>
              <div className="text-xs text-muted-foreground">Normalization</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <Sparkles className="h-6 w-6 mx-auto text-purple-500" />
              <div className="text-sm text-muted-foreground mt-1">Claude</div>
              <div className="text-xs text-muted-foreground">Features</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <Brain className="h-6 w-6 mx-auto text-green-500" />
              <div className="text-sm text-muted-foreground mt-1">Perplexity</div>
              <div className="text-xs text-muted-foreground">Insights</div>
            </div>
            <div className="text-center p-4 bg-muted rounded-md">
              <div className="text-2xl font-bold text-green-500">AI</div>
              <div className="text-sm text-muted-foreground mt-1">Ready</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            Трехслойный AI pipeline: нормализация данных (GPT-4), вычисление features (Claude),
            генерация бизнес-инсайтов и рекомендаций (Perplexity Sonar).
          </p>
        </CardContent>
      </Card>

      {/* Placeholder для других аналитик */}
      <Card>
        <CardContent className="py-12 text-center">
          <BarChart3 className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">{t('analytics.comingSoon')}</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('analytics.description1')}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('analytics.description2')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
