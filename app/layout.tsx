import type { Metadata } from 'next';
import './globals.css';
import { ClaimsProvider } from '@/lib/context/ClaimsContext';

export const metadata: Metadata = {
  title: 'NexusClaim AI Copilot | Intelligent Claims Processing Engine',
  description: 'Enterprise Multi-Agent AI Copilot for Insurance Claims Processing, Document OCR, LangMem Memory Search, and Fraud Risk Detection.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased font-sans">
        <ClaimsProvider>
          {children}
        </ClaimsProvider>
      </body>
    </html>
  );
}
