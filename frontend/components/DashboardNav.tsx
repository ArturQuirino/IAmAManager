'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { clearToken } from '@/lib/api';

// The primary in-game screens, in navigation order (see docs/screens.md).
const NAV_ITEMS = [
  { key: 'home', href: '/home' },
  { key: 'squad', href: '/squad' },
  { key: 'tactics', href: '/tactics' },
  { key: 'matches', href: '/matches' },
  { key: 'league', href: '/league' },
  { key: 'youth', href: '/youth' },
] as const;

export function DashboardNav() {
  const t = useTranslations('nav');
  const pathname = usePathname();
  const router = useRouter();

  function handleLogout() {
    clearToken();
    router.replace('/login');
  }

  return (
    <nav className="border-b border-slate-700/50 bg-surface/80 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between gap-4">
        <ul className="flex items-center gap-1 overflow-x-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <li key={item.key}>
                <Link
                  href={item.href}
                  aria-current={isActive ? 'page' : undefined}
                  className={`inline-block px-3 py-3 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                    isActive
                      ? 'border-accent text-white'
                      : 'border-transparent text-slate-400 hover:text-white'
                  }`}
                >
                  {t(item.key)}
                </Link>
              </li>
            );
          })}
        </ul>
        <button
          onClick={handleLogout}
          className="shrink-0 text-sm font-medium text-slate-400 hover:text-white transition-colors"
        >
          {t('logout')}
        </button>
      </div>
    </nav>
  );
}
