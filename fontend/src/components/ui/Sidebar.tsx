'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import {
  ChartBarIcon,
  ChatBubbleLeftRightIcon,
  EnvelopeIcon,
  CalendarIcon,
  ClipboardDocumentCheckIcon,
  TruckIcon,
  BuildingOffice2Icon,
  BellAlertIcon,
  CircleStackIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Analytics Chat', href: '/', icon: ChatBubbleLeftRightIcon },
  { name: 'Invite Dashboard', href: '/invite', icon: EnvelopeIcon },
  { name: 'Schedule', href: '/schedule', icon: CalendarIcon },
  { name: 'Engage', href: '/engage', icon: ClipboardDocumentCheckIcon },
  { name: 'Inspect', href: '/inspect', icon: ClipboardDocumentCheckIcon },
  { name: 'KPI Alerts', href: '/alerts', icon: BellAlertIcon },
  { name: 'Data Catalog', href: '/catalog', icon: CircleStackIcon },
];

const analysisShortcuts = [
  { name: 'F&I Analysis', href: '/analysis/fni', icon: ChartBarIcon },
  { name: 'Logistics', href: '/analysis/logistics', icon: TruckIcon },
  { name: 'Plant Downtime', href: '/analysis/plant', icon: BuildingOffice2Icon },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col w-64 bg-white border-r border-gray-200 min-h-screen">
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-cox-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">X</span>
          </div>
          <span className="ml-2 text-lg font-semibold text-gray-900">xtime</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Main
        </div>
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-cox-blue-50 text-cox-blue-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon
                className={clsx(
                  'mr-3 h-5 w-5',
                  isActive ? 'text-cox-blue-600' : 'text-gray-400'
                )}
              />
              {item.name}
            </Link>
          );
        })}

        <div className="px-3 py-2 mt-6 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Quick Analysis
        </div>
        {analysisShortcuts.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive
                  ? 'bg-cox-orange-50 text-cox-orange-700'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
            >
              <item.icon
                className={clsx(
                  'mr-3 h-5 w-5',
                  isActive ? 'text-cox-orange-600' : 'text-gray-400'
                )}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
            <span className="text-gray-600 text-sm font-medium">AI</span>
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">AI Analytics</p>
            <p className="text-xs text-gray-500">Powered by GPT-4</p>
          </div>
        </div>
      </div>
    </div>
  );
}
