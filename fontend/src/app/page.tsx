'use client';

import Header from '@/components/ui/Header';
import ChatInterface from '@/components/chat/ChatInterface';

export default function Home() {
  return (
    <div className="flex flex-col h-screen">
      <Header
        title="AI Data Analytics"
        subtitle="Ask questions in natural language and get instant insights"
      />
      <div className="flex-1 p-6 overflow-hidden">
        <ChatInterface />
      </div>
    </div>
  );
}
