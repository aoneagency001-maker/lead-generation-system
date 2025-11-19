'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useI18n } from '@/lib/i18n/context';
import {
  Search,
  Megaphone,
  MessageSquare,
  Send,
  BarChart3,
} from 'lucide-react';

export default function ModulesPage() {
  const { t } = useI18n();

  const modules = [
    {
      id: '1',
      name: t('modules.names.marketResearch'),
      type: 'market-research',
      icon: Search,
      status: 'idle' as const,
      description: t('modules.descriptions.marketResearch'),
      color: 'bg-blue-500',
    },
    {
      id: '2',
      name: t('modules.names.trafficGeneration'),
      type: 'traffic-generation',
      icon: Megaphone,
      status: 'idle' as const,
      description: t('modules.descriptions.trafficGeneration'),
      color: 'bg-green-500',
    },
    {
      id: '3',
      name: t('modules.names.leadQualification'),
      type: 'lead-qualification',
      icon: MessageSquare,
      status: 'idle' as const,
      description: t('modules.descriptions.leadQualification'),
      color: 'bg-purple-500',
    },
    {
      id: '4',
      name: t('modules.names.salesHandoff'),
      type: 'sales-handoff',
      icon: Send,
      status: 'idle' as const,
      description: t('modules.descriptions.salesHandoff'),
      color: 'bg-orange-500',
    },
    {
      id: '5',
      name: t('modules.names.analytics'),
      type: 'analytics',
      icon: BarChart3,
      status: 'idle' as const,
      description: t('modules.descriptions.analytics'),
      color: 'bg-indigo-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('modules.title')}</h2>
        <p className="text-muted-foreground">
          {t('modules.subtitle')}
        </p>
      </div>

      {/* Pipeline Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>{t('modules.pipelineFlow')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 overflow-x-auto pb-4">
            {modules.map((module, index) => (
              <div key={module.id} className="flex items-center">
                <div className="flex min-w-[200px] flex-col items-center gap-2">
                  <div
                    className={`flex h-16 w-16 items-center justify-center rounded-full ${module.color} text-white`}
                  >
                    <module.icon className="h-8 w-8" />
                  </div>
                  <div className="text-center">
                    <div className="font-medium">{module.name}</div>
                    <Badge variant="outline" className="mt-1">
                      {t(`modules.status.${module.status}`)}
                    </Badge>
                  </div>
                </div>
                {index < modules.length - 1 && (
                  <div className="h-0.5 w-12 bg-border" />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Modules Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {modules.map((module) => (
          <Card
            key={module.id}
            className="cursor-pointer transition-colors hover:bg-accent"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-lg ${module.color} text-white`}
                >
                  <module.icon className="h-6 w-6" />
                </div>
                <Badge variant="outline">{t(`modules.status.${module.status}`)}</Badge>
              </div>
              <CardTitle className="mt-4">{module.name}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {module.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>{t('modules.howItWorks')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            {t('modules.description1')}
          </p>
          <p>
            {t('modules.description2')}
          </p>
          <p>
            {t('modules.description3')}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
