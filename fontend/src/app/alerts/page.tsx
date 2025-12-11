'use client';

import { useState } from 'react';
import Header from '@/components/ui/Header';
import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ArrowTrendingDownIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useAlerts } from '@/hooks/useAlerts';

const severityConfig = {
  critical: {
    icon: ExclamationCircleIcon,
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-800',
    badge: 'bg-red-100 text-red-800',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-800',
    badge: 'bg-yellow-100 text-yellow-800',
  },
  info: {
    icon: InformationCircleIcon,
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    text: 'text-blue-800',
    badge: 'bg-blue-100 text-blue-800',
  },
};

export default function AlertsPage() {
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  // Use TanStack Query directly
  const { data: alerts = [], isLoading, error } = useAlerts();

  const categories = Array.from(new Set(alerts.map((a) => a.category)));

  const filteredAlerts = alerts.filter((alert) => {
    if (filter !== 'all' && alert.severity !== filter) return false;
    if (categoryFilter !== 'all' && alert.category !== categoryFilter) return false;
    return true;
  });

  const alertCounts = {
    critical: alerts.filter((a) => a.severity === 'critical').length,
    warning: alerts.filter((a) => a.severity === 'warning').length,
    info: alerts.filter((a) => a.severity === 'info').length,
  };

  return (
    <div className="flex flex-col h-screen">
      <Header title="KPI Alerts" subtitle="Real-time monitoring and anomaly detection" />
      <div className="flex-1 p-6 overflow-auto">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={clsx(
              'p-4 rounded-lg border transition-colors text-left',
              filter === 'all'
                ? 'bg-gray-100 border-gray-300'
                : 'bg-white border-gray-200 hover:bg-gray-50'
            )}
          >
            <p className="text-sm text-gray-500">Total Alerts</p>
            {isLoading ? (
              <div className="h-8 bg-gray-300 rounded animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-gray-900">{alerts.length}</p>
            )}
          </button>
          <button
            onClick={() => setFilter('critical')}
            className={clsx(
              'p-4 rounded-lg border transition-colors text-left',
              filter === 'critical'
                ? 'bg-red-100 border-red-300'
                : 'bg-white border-gray-200 hover:bg-red-50'
            )}
          >
            <p className="text-sm text-red-600">Critical</p>
            {isLoading ? (
              <div className="h-8 bg-gray-300 rounded animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-red-700">{alertCounts.critical}</p>
            )}
          </button>
          <button
            onClick={() => setFilter('warning')}
            className={clsx(
              'p-4 rounded-lg border transition-colors text-left',
              filter === 'warning'
                ? 'bg-yellow-100 border-yellow-300'
                : 'bg-white border-gray-200 hover:bg-yellow-50'
            )}
          >
            <p className="text-sm text-yellow-600">Warning</p>
            {isLoading ? (
              <div className="h-8 bg-gray-300 rounded animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-yellow-700">{alertCounts.warning}</p>
            )}
          </button>
          <button
            onClick={() => setFilter('info')}
            className={clsx(
              'p-4 rounded-lg border transition-colors text-left',
              filter === 'info'
                ? 'bg-blue-100 border-blue-300'
                : 'bg-white border-gray-200 hover:bg-blue-50'
            )}
          >
            <p className="text-sm text-blue-600">Info</p>
            {isLoading ? (
              <div className="h-8 bg-gray-300 rounded animate-pulse" />
            ) : (
              <p className="text-2xl font-bold text-blue-700">{alertCounts.info}</p>
            )}
          </button>
        </div>

        {/* Filters */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
            >
              <option value="all">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <button className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700">
            Configure Alerts
          </button>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {isLoading ? (
            // Loading skeletons
            Array.from({ length: 3 }).map((_, idx) => (
              <div key={idx} className="p-4 rounded-lg border bg-gray-50 animate-pulse">
                <div className="flex items-start justify-between">
                  <div className="flex items-start flex-1">
                    <div className="w-6 h-6 bg-gray-300 rounded mt-0.5" />
                    <div className="ml-4 flex-1">
                      <div className="flex items-center">
                        <div className="h-5 bg-gray-300 rounded w-48" />
                        <div className="ml-2 h-5 bg-gray-300 rounded w-16" />
                        <div className="ml-2 h-5 bg-gray-300 rounded w-20" />
                      </div>
                      <div className="h-4 bg-gray-300 rounded w-full mt-2" />
                      <div className="h-4 bg-gray-300 rounded w-3/4 mt-2" />
                      <div className="mt-3 p-3 bg-white rounded border">
                        <div className="h-3 bg-gray-300 rounded w-20 mb-2" />
                        <div className="h-4 bg-gray-300 rounded w-full" />
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="h-3 bg-gray-300 rounded w-24" />
                    <div className="mt-2 space-x-2">
                      <div className="inline-block h-6 bg-gray-300 rounded w-16" />
                      <div className="inline-block h-6 bg-gray-300 rounded w-16" />
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : error ? (
            // Error state
            <div className="text-center py-12">
              <ExclamationCircleIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load alerts</h3>
              <p className="text-gray-500 mb-4">There was an error loading the alerts data.</p>
              <button 
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700"
              >
                Retry
              </button>
            </div>
          ) : filteredAlerts.length === 0 ? (
            // Empty state
            <div className="text-center py-12">
              <CheckCircleIcon className="w-12 h-12 text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No alerts found</h3>
              <p className="text-gray-500">All systems are running normally.</p>
            </div>
          ) : (
            filteredAlerts.map((alert) => {
            const config = severityConfig[alert.severity];
            const Icon = config.icon;
            const isNegative = alert.change_percent < 0;

            return (
              <div
                key={alert.id}
                className={clsx(
                  'p-4 rounded-lg border',
                  config.bg,
                  config.border
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start">
                    <Icon className={clsx('w-6 h-6 mt-0.5', config.text)} />
                    <div className="ml-4">
                      <div className="flex items-center">
                        <h3 className="font-semibold text-gray-900">
                          {alert.metric_name}
                        </h3>
                        <span
                          className={clsx(
                            'ml-2 px-2 py-0.5 text-xs font-medium rounded-full',
                            config.badge
                          )}
                        >
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-700">
                          {alert.category}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-1">{alert.message}</p>
                      <div className="flex items-center mt-2 text-sm text-gray-500">
                        {isNegative ? (
                          <ArrowTrendingDownIcon className="w-4 h-4 text-red-500 mr-1" />
                        ) : (
                          <ArrowTrendingUpIcon className="w-4 h-4 text-green-500 mr-1" />
                        )}
                        <span>
                          {Math.abs(alert.change_percent).toFixed(1)}%{' '}
                          {isNegative ? 'decrease' : 'increase'} from{' '}
                          {alert.previous_value} to {alert.current_value}
                        </span>
                      </div>
                      {alert.root_cause && (
                        <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                          <p className="text-xs font-medium text-gray-500 uppercase mb-1">
                            Root Cause
                          </p>
                          <p className="text-sm text-gray-700">{alert.root_cause}</p>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                    <div className="mt-2 space-x-2">
                      <button className="px-3 py-1 text-xs font-medium text-cox-blue-700 bg-cox-blue-50 rounded hover:bg-cox-blue-100">
                        Investigate
                      </button>
                      <button className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200">
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
          )}
        </div>
      </div>
    </div>
  );
}
