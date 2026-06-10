import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Football Manager Simulator',
  description: 'Simulador de gerenciamento de futebol',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
