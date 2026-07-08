import type { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages, getTranslations } from 'next-intl/server';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import './globals.css';

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations('metadata');
  return {
    title: t('title'),
    description: t('description'),
  };
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body>
        <NextIntlClientProvider messages={messages}>
          <div className="flex justify-end px-4 py-2">
            <LanguageSwitcher />
          </div>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
