'use client';

import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  GripVertical,
  Trash2,
  Activity,
  AlertCircle,
  CheckCircle2,
  Server,
  ExternalLink,
} from 'lucide-react';

interface ModuleCardProps {
  module: any;
  onDelete: (id: string) => void;
  onCheckHealth: (id: string) => void;
}

export function ModuleCard({ module, onDelete, onCheckHealth }: ModuleCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: module.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-500';
      case 'testing':
        return 'bg-yellow-500';
      case 'inactive':
        return 'bg-gray-500';
      case 'archived':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active':
        return 'Активен';
      case 'testing':
        return 'Тестируется';
      case 'inactive':
        return 'Неактивен';
      case 'archived':
        return 'Архив';
      default:
        return status;
    }
  };

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'olx':
        return '🛒';
      case 'satu':
        return '🏪';
      case 'kaspi':
        return '💳';
      default:
        return '📦';
    }
  };

  return (
    <div ref={setNodeRef} style={style}>
      <Card className="group hover:shadow-lg transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <div
                {...attributes}
                {...listeners}
                className="cursor-grab active:cursor-grabbing touch-none"
              >
                <GripVertical className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="text-2xl">{getPlatformIcon(module.platform)}</div>
              <div>
                <CardTitle className="text-lg">{module.name}</CardTitle>
                <p className="text-xs text-muted-foreground">v{module.version}</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {module.is_healthy ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground line-clamp-2">
            {module.description}
          </p>

          {/* Features */}
          {module.features && module.features.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {module.features.slice(0, 3).map((feature: string, idx: number) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {feature}
                </Badge>
              ))}
              {module.features.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{module.features.length - 3}
                </Badge>
              )}
            </div>
          )}

          {/* API URL */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Server className="h-3 w-3" />
            <code className="flex-1 truncate">{module.api_url}</code>
            <a
              href={module.api_url + '/docs'}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-primary"
            >
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onCheckHealth(module.id)}
              className="text-xs"
            >
              <Activity className="mr-1 h-3 w-3" />
              Health Check
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(module.id)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
