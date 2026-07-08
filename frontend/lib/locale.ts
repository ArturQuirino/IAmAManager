'use server';

import { cookies } from 'next/headers';
import { defaultLocale, isLocale, LOCALE_COOKIE_NAME, type Locale } from '@/i18n/locales';

export async function getUserLocale(): Promise<Locale> {
  const cookieStore = await cookies();
  const value = cookieStore.get(LOCALE_COOKIE_NAME)?.value;
  return isLocale(value) ? value : defaultLocale;
}

export async function setUserLocale(locale: Locale): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(LOCALE_COOKIE_NAME, locale);
}
