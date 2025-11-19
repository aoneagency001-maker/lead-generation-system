'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/lib/i18n/context';
import { apiClient } from '@/lib/api-client';
import type { Niche } from '@/types';
import { Plus, Target } from 'lucide-react';

const statusColors: Record<string, string> = {
  research: 'bg-blue-500',
  active: 'bg-green-500',
  paused: 'bg-yellow-500',
  completed: 'bg-purple-500',
  rejected: 'bg-red-500',
};

export default function NichesPage() {
  const { t } = useI18n();
  const [niches, setNiches] = useState<Niche[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadNiches() {
      try {
        const data = await apiClient.getNiches();
        setNiches(data);
      } catch (error) {
        console.error('Failed to load niches:', error);
      } finally {
        setLoading(false);
      }
    }

    loadNiches();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t('niches.title')}</h2>
          <p className="text-muted-foreground">
            {t('niches.subtitle')}
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t('niches.addNiche')}
        </Button>
      </div>

      {/* Niches Grid */}
      {niches.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Target className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-semibold">{t('niches.noNiches')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('niches.noNichesDescription')}
            </p>
            <Button className="mt-4">
              <Plus className="mr-2 h-4 w-4" />
              {t('niches.createNiche')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {niches.map((niche) => (
            <Card key={niche.id} className="cursor-pointer hover:bg-accent">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle>{niche.name}</CardTitle>
                  <Badge className={`${statusColors[niche.status]} text-white`}>
                    {t(`niches.status.${niche.status}`)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">{t('niches.category')}:</span>
                    <span className="font-medium">{niche.category}</span>
                  </div>
                  {niche.cpl_target && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{t('niches.targetCpl')}:</span>
                      <span className="font-medium">${niche.cpl_target}</span>
                    </div>
                  )}
                  {niche.roi_target && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{t('niches.targetRoi')}:</span>
                      <span className="font-medium">{niche.roi_target}%</span>
                    </div>
                  )}
                  {niche.market_size !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">{t('niches.marketSize')}:</span>
                      <span className="font-medium">{niche.market_size}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
