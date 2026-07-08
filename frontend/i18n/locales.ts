export const locales = ['pt', 'en', 'es'] as const;

export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = 'pt';

export const LOCALE_COOKIE_NAME = 'NEXT_LOCALE';

export function isLocale(value: string | undefined): value is Locale {
  return locales.includes(value as Locale);
}
