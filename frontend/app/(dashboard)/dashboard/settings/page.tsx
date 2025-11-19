'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useI18n } from '@/lib/i18n/context';
import { Settings as SettingsIcon } from 'lucide-react';

export default function SettingsPage() {
  const { t } = useI18n();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('settings.title')}</h2>
        <p className="text-muted-foreground">
          {t('settings.subtitle')}
        </p>
      </div>

      {/* Placeholder */}
      <Card>
        <CardContent className="py-12 text-center">
          <SettingsIcon className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold">{t('settings.comingSoon')}</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {t('settings.description')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
