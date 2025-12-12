'use client';

import { Suspense } from 'react';
import Header from '@/components/ui/Header';
import HomeContent from './HomeContent';

export default function Home() {
  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Cox Automotive AI Analytics"
        subtitle="Powered by Xtime • Ask questions in natural language and get instant insights"
      />
      <div className="flex-1 p-6 overflow-hidden">
        <Suspense fallback={<div className="flex items-center justify-center h-full">Loading...</div>}>
          <HomeContent />
        </Suspense>
      </div>
    </div>
  );
}
