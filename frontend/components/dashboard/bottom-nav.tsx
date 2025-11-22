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
} from 'lucide-react';
import { useI18n } from '@/lib/i18n/context';

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useI18n();

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
    <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 md:hidden safe-area-inset-bottom">
      <div className="flex h-14 items-center justify-around overflow-x-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'flex flex-col items-center justify-center gap-0.5 flex-1 min-w-0 px-1 h-full transition-colors',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <item.icon className={cn(
                'h-5 w-5 shrink-0',
                isActive && 'text-primary'
              )} />
              <span className="text-[10px] font-medium truncate max-w-full text-center leading-tight">
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

