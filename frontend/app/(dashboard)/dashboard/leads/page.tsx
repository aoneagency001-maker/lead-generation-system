'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useI18n } from '@/lib/i18n/context';
import { apiClient } from '@/lib/api-client';
import type { Lead } from '@/types';
import { Plus, Filter } from 'lucide-react';

const statusColors: Record<string, string> = {
  new: 'bg-blue-500',
  contacted: 'bg-yellow-500',
  qualified: 'bg-purple-500',
  hot: 'bg-orange-500',
  won: 'bg-green-500',
  lost: 'bg-gray-500',
  spam: 'bg-red-500',
};

export default function LeadsPage() {
  const { t } = useI18n();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string | undefined>();

  useEffect(() => {
    async function loadLeads() {
      try {
        const data = await apiClient.getLeads(selectedStatus);
        setLeads(data);
      } catch (error) {
        console.error('Failed to load leads:', error);
      } finally {
        setLoading(false);
      }
    }

    loadLeads();
  }, [selectedStatus]);

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
          <h2 className="text-3xl font-bold tracking-tight">{t('leads.title')}</h2>
          <p className="text-muted-foreground">
            {t('leads.subtitle')}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            {t('leads.filter')}
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            {t('leads.addLead')}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('leads.stats.new')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {leads.filter((l) => l.status === 'new').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('leads.stats.qualified')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {leads.filter((l) => l.status === 'qualified').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('leads.stats.hot')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {leads.filter((l) => l.status === 'hot').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">{t('leads.stats.won')}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {leads.filter((l) => l.status === 'won').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle>{t('leads.allLeads')} ({leads.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              {t('leads.noLeads')}
            </div>
          ) : (
            <div className="space-y-2">
              {leads.map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent"
                >
                  <div className="flex-1">
                    <div className="font-medium">
                      {lead.name || t('leads.unknown')}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {lead.phone || lead.email || t('leads.noContact')}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant="outline">{lead.source}</Badge>
                    <Badge
                      className={`${
                        statusColors[lead.status]
                      } text-white`}
                    >
                      {t(`leads.status.${lead.status}`)}
                    </Badge>
                    {lead.quality_score && (
                      <div className="text-sm font-medium">
                        {t('leads.score')}: {lead.quality_score}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
