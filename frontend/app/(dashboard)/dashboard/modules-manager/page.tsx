'use client';

import { useState, useEffect } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import { arrayMove } from '@dnd-kit/sortable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ModuleColumn } from '@/components/modules/ModuleColumn';
import { ModuleCard } from '@/components/modules/ModuleCard';
import { apiClient } from '@/lib/api-client';
import {
  RefreshCw,
  Activity,
  Loader2,
  LayoutGrid,
  TrendingUp,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

type ModuleStatus = 'active' | 'testing' | 'inactive' | 'archived';
type PipelineStage = 'research' | 'acquisition' | 'processing' | 'conversion' | 'analytics';

interface Module {
  id: string;
  name: string;
  platform: string;
  status: ModuleStatus;
  pipeline_stage: PipelineStage;
  description: string;
  version: string;
  api_url: string;
  health_endpoint: string;
  features: string[];
  config: any;
  last_health_check: string | null;
  is_healthy: boolean;
  order: number;
  pipeline_order: number;
  created_at: string;
  updated_at: string;
}

const STATUS_COLUMNS: { id: ModuleStatus; title: string }[] = [
  { id: 'active', title: 'Активные' },
  { id: 'testing', title: 'Тестируются' },
  { id: 'inactive', title: 'Неактивные' },
  { id: 'archived', title: 'Архив' },
];

const PIPELINE_COLUMNS: { id: PipelineStage; title: string; description: string }[] = [
  { id: 'research', title: 'Анализ', description: 'Исследование рынка' },
  { id: 'acquisition', title: 'Привлечение', description: 'Генерация трафика' },
  { id: 'processing', title: 'Обработка', description: 'Квалификация лидов' },
  { id: 'conversion', title: 'Конверсия', description: 'Продажи и сделки' },
  { id: 'analytics', title: 'Аналитика', description: 'Анализ результатов' },
];

export default function ModulesManagerPage() {
  const [modules, setModules] = useState<Module[]>([]);
  const [activeModule, setActiveModule] = useState<Module | null>(null);
  const [loading, setLoading] = useState(true);
  const [healthCheckLoading, setHealthCheckLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'status' | 'pipeline'>('status');
  const { toast } = useToast();

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  // Загрузка модулей
  const loadModules = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getModules();
      setModules(data);
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось загрузить модули',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModules();
  }, []);

  // Получение модулей по статусу
  const getModulesByStatus = (status: ModuleStatus) => {
    return modules
      .filter((m) => m.status === status)
      .sort((a, b) => a.order - b.order);
  };

  // Получение модулей по этапу пайплайна
  const getModulesByPipelineStage = (stage: PipelineStage) => {
    return modules
      .filter((m) => m.pipeline_stage === stage)
      .sort((a, b) => a.pipeline_order - b.pipeline_order);
  };

  // Drag & Drop handlers
  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event;
    const module = modules.find((m) => m.id === active.id);
    setActiveModule(module || null);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    if (viewMode === 'status') {
      // Статусный Kanban
      if (STATUS_COLUMNS.some((col) => col.id === overId)) {
        const newStatus = overId as ModuleStatus;
        setModules((modules) =>
          modules.map((m) =>
            m.id === activeId ? { ...m, status: newStatus } : m
          )
        );
      }
    } else {
      // Стратегический Kanban
      if (PIPELINE_COLUMNS.some((col) => col.id === overId)) {
        const newStage = overId as PipelineStage;
        setModules((modules) =>
          modules.map((m) =>
            m.id === activeId ? { ...m, pipeline_stage: newStage } : m
          )
        );
      }
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveModule(null);

    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    const activeModule = modules.find((m) => m.id === activeId);
    if (!activeModule) return;

    if (viewMode === 'status') {
      // Статусный Kanban - обновляем статус
      if (STATUS_COLUMNS.some((col) => col.id === overId)) {
        const newStatus = overId as ModuleStatus;
        if (activeModule.status !== newStatus) {
          try {
            await apiClient.updateModuleStatus(activeId, newStatus);
            toast({
              title: 'Успешно',
              description: `Модуль "${activeModule.name}" перемещен в "${STATUS_COLUMNS.find((c) => c.id === newStatus)?.title}"`,
            });
            loadModules();
          } catch (error) {
            toast({
              title: 'Ошибка',
              description: 'Не удалось обновить статус модуля',
              variant: 'destructive',
            });
            loadModules();
          }
        }
      }

      // Сортировка внутри колонки
      const activeIndex = modules.findIndex((m) => m.id === activeId);
      const overIndex = modules.findIndex((m) => m.id === overId);

      if (activeIndex !== overIndex && modules[activeIndex].status === modules[overIndex].status) {
        const newModules = arrayMove(modules, activeIndex, overIndex);
        setModules(newModules);

        try {
          const moduleOrders = newModules.map((m, idx) => ({
            id: m.id,
            order: idx,
          }));
          await apiClient.batchReorderModules(moduleOrders);
        } catch (error) {
          console.error('Failed to update order:', error);
        }
      }
    } else {
      // Стратегический Kanban - обновляем pipeline_stage
      if (PIPELINE_COLUMNS.some((col) => col.id === overId)) {
        const newStage = overId as PipelineStage;
        if (activeModule.pipeline_stage !== newStage) {
          try {
            await apiClient.updateModulePipelineStage(activeId, newStage);
            toast({
              title: 'Успешно',
              description: `Модуль "${activeModule.name}" перемещен в этап "${PIPELINE_COLUMNS.find((c) => c.id === newStage)?.title}"`,
            });
            loadModules();
          } catch (error) {
            toast({
              title: 'Ошибка',
              description: 'Не удалось обновить этап модуля',
              variant: 'destructive',
            });
            loadModules();
          }
        }
      }
    }
  };

  // Проверка здоровья модуля
  const handleCheckHealth = async (id: string) => {
    try {
      const result = await apiClient.checkModuleHealth(id);
      toast({
        title: result.is_healthy ? 'Модуль здоров' : 'Модуль недоступен',
        description: result.is_healthy
          ? 'Модуль работает корректно'
          : 'Модуль не отвечает на запросы',
        variant: result.is_healthy ? 'default' : 'destructive',
      });
      loadModules();
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось проверить здоровье модуля',
        variant: 'destructive',
      });
    }
  };

  // Массовая проверка здоровья
  const handleBatchHealthCheck = async () => {
    try {
      setHealthCheckLoading(true);
      const result = await apiClient.batchHealthCheck();
      toast({
        title: 'Проверка завершена',
        description: `Здоровых: ${result.healthy} | Недоступных: ${result.unhealthy}`,
      });
      loadModules();
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось выполнить проверку',
        variant: 'destructive',
      });
    } finally {
      setHealthCheckLoading(false);
    }
  };

  // Удаление модуля
  const handleDelete = async (id: string) => {
    if (!confirm('Вы уверены, что хотите удалить этот модуль?')) return;

    try {
      await apiClient.deleteModule(id);
      toast({
        title: 'Успешно',
        description: 'Модуль удален',
      });
      loadModules();
    } catch (error) {
      toast({
        title: 'Ошибка',
        description: 'Не удалось удалить модуль',
        variant: 'destructive',
      });
    }
  };

  // Статистика
  const stats = {
    total: modules.length,
    active: modules.filter((m) => m.status === 'active').length,
    testing: modules.filter((m) => m.status === 'testing').length,
    healthy: modules.filter((m) => m.is_healthy).length,
    research: modules.filter((m) => m.pipeline_stage === 'research').length,
    acquisition: modules.filter((m) => m.pipeline_stage === 'acquisition').length,
    processing: modules.filter((m) => m.pipeline_stage === 'processing').length,
    conversion: modules.filter((m) => m.pipeline_stage === 'conversion').length,
    analytics: modules.filter((m) => m.pipeline_stage === 'analytics').length,
  };

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Управление модулями</h2>
          <p className="text-muted-foreground">
            Выберите вид: Статусный или Стратегический Kanban
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadModules}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Обновить
          </Button>
          <Button
            variant="outline"
            onClick={handleBatchHealthCheck}
            disabled={healthCheckLoading}
          >
            {healthCheckLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Activity className="mr-2 h-4 w-4" />
            )}
            Проверить все
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего модулей</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Активные</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.active}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Тестируются</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.testing}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Здоровых</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {stats.healthy}/{stats.total}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs для переключения между видами */}
      <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as any)} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="status">
            <LayoutGrid className="mr-2 h-4 w-4" />
            Статусный
          </TabsTrigger>
          <TabsTrigger value="pipeline">
            <TrendingUp className="mr-2 h-4 w-4" />
            Стратегический
          </TabsTrigger>
        </TabsList>

        {/* Статусный Kanban */}
        <TabsContent value="status" className="mt-6">
          <DndContext
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="grid gap-4 md:grid-cols-4">
              {STATUS_COLUMNS.map((column) => (
                <ModuleColumn
                  key={column.id}
                  id={column.id}
                  title={column.title}
                  modules={getModulesByStatus(column.id)}
                  onDelete={handleDelete}
                  onCheckHealth={handleCheckHealth}
                />
              ))}
            </div>

            <DragOverlay>
              {activeModule ? (
                <ModuleCard
                  module={activeModule}
                  onDelete={() => {}}
                  onCheckHealth={() => {}}
                />
              ) : null}
            </DragOverlay>
          </DndContext>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Статусный Kanban</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>• <strong>Активные</strong> - модули, работающие в продакшене</p>
              <p>• <strong>Тестируются</strong> - модули на стадии тестирования</p>
              <p>• <strong>Неактивные</strong> - временно отключенные модули</p>
              <p>• <strong>Архив</strong> - устаревшие или удаленные модули</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Стратегический Kanban */}
        <TabsContent value="pipeline" className="mt-6">
          <DndContext
            sensors={sensors}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
          >
            <div className="grid gap-4 md:grid-cols-5">
              {PIPELINE_COLUMNS.map((column) => (
                <div key={column.id} className="space-y-2">
                  <div className="text-center">
                    <h3 className="font-semibold">{column.title}</h3>
                    <p className="text-xs text-muted-foreground">{column.description}</p>
                  </div>
                  <ModuleColumn
                    id={column.id}
                    title=""
                    modules={getModulesByPipelineStage(column.id)}
                    onDelete={handleDelete}
                    onCheckHealth={handleCheckHealth}
                  />
                </div>
              ))}
            </div>

            <DragOverlay>
              {activeModule ? (
                <ModuleCard
                  module={activeModule}
                  onDelete={() => {}}
                  onCheckHealth={() => {}}
                />
              ) : null}
            </DragOverlay>
          </DndContext>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Стратегический Kanban (Воронка)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-muted-foreground">
              <p>• <strong>Анализ</strong> - модули для исследования рынка и конкурентов</p>
              <p>• <strong>Привлечение</strong> - модули для генерации трафика и лидов</p>
              <p>• <strong>Обработка</strong> - модули для квалификации и обработки лидов</p>
              <p>• <strong>Конверсия</strong> - модули для продаж и закрытия сделок</p>
              <p>• <strong>Аналитика</strong> - модули для анализа результатов и метрик</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Общая информация */}
      <Card>
        <CardHeader>
          <CardTitle>Распределение по этапам воронки</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-5">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{stats.research}</div>
              <div className="text-xs text-muted-foreground">Анализ</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{stats.acquisition}</div>
              <div className="text-xs text-muted-foreground">Привлечение</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{stats.processing}</div>
              <div className="text-xs text-muted-foreground">Обработка</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{stats.conversion}</div>
              <div className="text-xs text-muted-foreground">Конверсия</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{stats.analytics}</div>
              <div className="text-xs text-muted-foreground">Аналитика</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
