'use client';

import { ChangeEvent, useTransition } from 'react';
import { useLocale, useTranslations } from 'next-intl';
import { useRouter } from 'next/navigation';
import { setUserLocale } from '@/lib/locale';
import { locales, type Locale } from '@/i18n/locales';

// Each language is shown in its own endonym (e.g. "English", "Español"),
// not translated into the currently active language — this is the
// standard convention for language switchers.
const LOCALE_LABELS: Record<Locale, string> = {
  pt: 'Português',
  en: 'English',
  es: 'Español',
};

export function LanguageSwitcher() {
  const locale = useLocale();
  const t = useTranslations('language');
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  function handleChange(event: ChangeEvent<HTMLSelectElement>) {
    const nextLocale = event.target.value as Locale;
    startTransition(async () => {
      await setUserLocale(nextLocale);
      router.refresh();
    });
  }

  return (
    <select
      aria-label={t('label')}
      value={locale}
      onChange={handleChange}
      disabled={isPending}
      className="bg-surface border border-slate-600 text-slate-300 text-sm rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50"
    >
      {locales.map((code) => (
        <option key={code} value={code}>
          {LOCALE_LABELS[code]}
        </option>
      ))}
    </select>
  );
}
