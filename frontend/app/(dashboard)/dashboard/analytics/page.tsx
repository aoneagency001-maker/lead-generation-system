'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/lib/i18n/context';
import { BarChart3 } from 'lucide-react';

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

      {/* Placeholder */}
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
