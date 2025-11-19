'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Blocks,
  Users,
  Target,
  Megaphone,
  BarChart3,
  Settings,
  Languages,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useI18n } from '@/lib/i18n/context';

export function Sidebar() {
  const pathname = usePathname();
  const { language, setLanguage, t } = useI18n();

  const navigation = [
    { name: t('nav.dashboard'), href: '/dashboard', icon: LayoutDashboard },
    { name: t('nav.modules'), href: '/dashboard/modules', icon: Blocks },
    { name: t('nav.leads'), href: '/dashboard/leads', icon: Users },
    { name: t('nav.niches'), href: '/dashboard/niches', icon: Target },
    { name: t('nav.campaigns'), href: '/dashboard/campaigns', icon: Megaphone },
    { name: t('nav.analytics'), href: '/dashboard/analytics', icon: BarChart3 },
    { name: t('nav.settings'), href: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="flex h-full w-64 flex-col bg-background border-r">
      {/* Logo & Language Selector */}
      <div className="flex h-16 items-center justify-between border-b px-6">
        <Link href="/dashboard" className="flex items-center">
          <Blocks className="h-7 w-7 text-primary" />
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              <Languages className="h-4 w-4" />
              <span className="text-xs font-medium uppercase">{language}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setLanguage('en')}>
              <span className="flex items-center gap-2">
                🇬🇧 English
              </span>
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setLanguage('ru')}>
              <span className="flex items-center gap-2">
                🇷🇺 Русский
              </span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <div className="text-xs text-muted-foreground">
          {t('common.version')}
        </div>
      </div>
    </div>
  );
}
