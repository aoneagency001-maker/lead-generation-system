'use client';

import { useDroppable } from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ModuleCard } from './ModuleCard';

interface ModuleColumnProps {
  id: string;
  title: string;
  modules: any[];
  onDelete: (id: string) => void;
  onCheckHealth: (id: string) => void;
}

export function ModuleColumn({
  id,
  title,
  modules,
  onDelete,
  onCheckHealth,
}: ModuleColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  const getColumnColor = () => {
    switch (id) {
      case 'active':
        return 'border-green-500/50 bg-green-50/50 dark:bg-green-950/20';
      case 'testing':
        return 'border-yellow-500/50 bg-yellow-50/50 dark:bg-yellow-950/20';
      case 'inactive':
        return 'border-gray-500/50 bg-gray-50/50 dark:bg-gray-950/20';
      case 'archived':
        return 'border-red-500/50 bg-red-50/50 dark:bg-red-950/20';
      default:
        return '';
    }
  };

  return (
    <div
      ref={setNodeRef}
      className={`flex min-h-[500px] flex-col rounded-lg border-2 p-4 transition-colors ${
        isOver ? 'border-primary bg-primary/5' : getColumnColor()
      }`}
    >
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold">{title}</h3>
        <Badge variant="secondary">{modules.length}</Badge>
      </div>

      <SortableContext
        items={modules.map((m) => m.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-3 flex-1">
          {modules.map((module) => (
            <ModuleCard
              key={module.id}
              module={module}
              onDelete={onDelete}
              onCheckHealth={onCheckHealth}
            />
          ))}
          {modules.length === 0 && (
            <div className="flex h-full items-center justify-center rounded-lg border-2 border-dashed p-8 text-center text-sm text-muted-foreground">
              Перетащите модули сюда
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  );
}
