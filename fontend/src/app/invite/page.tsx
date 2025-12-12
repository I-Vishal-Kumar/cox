'use client';

import Header from '@/components/ui/Header';
import InviteDashboard from '@/components/dashboard/InviteDashboard';

export default function InvitePage() {
  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Invite Dashboard"
        subtitle="Cox Automotive • Service Marketing Campaign Performance • Powered by Xtime"
      />
      <div className="flex-1 p-6 overflow-auto">
        <InviteDashboard />
      </div>
    </div>
  );
}
