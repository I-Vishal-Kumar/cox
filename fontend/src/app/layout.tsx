'use client';

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/ui/Sidebar';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';

const inter = Inter({ subsets: ['latin'] });

import Footer from '@/components/ui/Footer';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <title>Cox Automotive AI Analytics</title>
        <meta name="description" content="Cox Automotive AI Analytics Platform - Powered by Xtime. Get instant insights from your automotive data." />
      </head>
      <body className={inter.className}>
        <QueryClientProvider client={queryClient}>
          <div className="flex flex-col min-h-screen bg-gray-50">
            <div className="flex flex-1">
              <Sidebar />
              <main className="flex-1 flex flex-col">{children}</main>
            </div>
            <Footer />
          </div>
        </QueryClientProvider>
      </body>
    </html>
  );
}
