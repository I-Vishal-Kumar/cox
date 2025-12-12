'use client';

import { useSearchParams } from 'next/navigation';
import ChatInterface from '@/components/chat/ChatInterface';

export default function HomeContent() {
  const searchParams = useSearchParams();
  const queryParam = searchParams.get('query');

  return <ChatInterface initialQuery={queryParam || undefined} />;
}

