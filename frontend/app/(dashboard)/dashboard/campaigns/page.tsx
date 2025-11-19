'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/lib/i18n/context';
import { apiClient } from '@/lib/api-client';
import type { Campaign } from '@/types';
import { Plus, Megaphone } from 'lucide-react';

const statusColors: Record<string, string> = {
  draft: 'bg-gray-500',
  active: 'bg-green-500',
  paused: 'bg-yellow-500',
  completed: 'bg-blue-500',
  failed: 'bg-red-500',
};

const platformColors: Record<string, string> = {
  olx: 'bg-purple-500',
  kaspi: 'bg-red-500',
  telegram: 'bg-blue-500',
  whatsapp: 'bg-green-500',
};

export default function CampaignsPage() {
  const { t } = useI18n();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCampaigns() {
      try {
        const data = await apiClient.getCampaigns();
        setCampaigns(data);
      } catch (error) {
        console.error('Failed to load campaigns:', error);
      } finally {
        setLoading(false);
      }
    }

    loadCampaigns();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">{t('common.loading')}</div>
      </div>
    );
  }

  const activeCampaigns = campaigns.filter((c) => c.status === 'active');
  const totalSpent = campaigns.reduce((sum, c) => sum + (c.spent || 0), 0);
  const totalLeads = campaigns.reduce((sum, c) => sum + (c.leads_count || 0), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t('campaigns.title')}</h2>
          <p className="text-muted-foreground">
            {t('campaigns.subtitle')}
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          {t('campaigns.createCampaign')}
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('campaigns.stats.totalCampaigns')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaigns.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('campaigns.stats.active')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{activeCampaigns.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('campaigns.stats.totalSpent')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalSpent.toFixed(2)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('campaigns.stats.totalLeads')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalLeads}</div>
          </CardContent>
        </Card>
      </div>

      {/* Campaigns List */}
      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Megaphone className="mx-auto h-12 w-12 text-muted-foreground" />
            <h3 className="mt-4 text-lg font-semibold">{t('campaigns.noCampaigns')}</h3>
            <p className="mt-2 text-sm text-muted-foreground">
              {t('campaigns.noCampaignsDescription')}
            </p>
            <Button className="mt-4">
              <Plus className="mr-2 h-4 w-4" />
              {t('campaigns.createCampaign')}
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {campaigns.map((campaign) => (
            <Card key={campaign.id} className="cursor-pointer hover:bg-accent">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <CardTitle>{campaign.name}</CardTitle>
                  <div className="flex gap-2">
                    <Badge className={`${platformColors[campaign.platform]} text-white`}>
                      {t(`campaigns.platforms.${campaign.platform}`)}
                    </Badge>
                    <Badge className={`${statusColors[campaign.status]} text-white`}>
                      {t(`campaigns.status.${campaign.status}`)}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">{t('campaigns.fields.ads')}</div>
                    <div className="font-medium">{campaign.ads_count || 0}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">{t('campaigns.fields.leads')}</div>
                    <div className="font-medium">{campaign.leads_count || 0}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">{t('campaigns.fields.budget')}</div>
                    <div className="font-medium">${campaign.budget || 0}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">{t('campaigns.fields.spent')}</div>
                    <div className="font-medium">${campaign.spent || 0}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
