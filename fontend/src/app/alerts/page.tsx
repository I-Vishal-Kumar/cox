'use client';

import { useState, useMemo } from 'react';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ArrowTrendingDownIcon,
  ArrowTrendingUpIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useAlerts } from '@/hooks/useAlerts';
import { alertsService, Alert } from '@/lib/api/alerts';
import { useQueryClient } from '@tanstack/react-query';
import { sendChatMessage } from '@/lib/api';
import { SessionManager } from '@/utils/sessionManager';

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
  const [isDetecting, setIsDetecting] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [dismissingAlertId, setDismissingAlertId] = useState<string | null>(null);
  const [investigatingAlertId, setInvestigatingAlertId] = useState<string | null>(null);
  const [investigationChatOpen, setInvestigationChatOpen] = useState(false);

  const queryClient = useQueryClient();

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

  // Prepare page context for the bot
  const pageContext = useMemo(() => {
    const criticalAlerts = alerts.filter(a => a.severity === 'critical');
    const warningAlerts = alerts.filter(a => a.severity === 'warning');
    const alertsByCategory = alerts.reduce((acc, alert) => {
      if (!acc[alert.category]) acc[alert.category] = [];
      acc[alert.category].push(alert);
      return acc;
    }, {} as Record<string, typeof alerts>);

    return {
      page: 'KPI Alerts',
      alerts: {
        total: alerts.length,
        critical: alertCounts.critical,
        warning: alertCounts.warning,
        info: alertCounts.info,
        criticalAlerts: criticalAlerts.map(a => ({
          metric: a.metric_name,
          message: a.message,
          change: a.change_percent,
          rootCause: a.root_cause,
          category: a.category,
        })),
        warningAlerts: warningAlerts.map(a => ({
          metric: a.metric_name,
          message: a.message,
          change: a.change_percent,
          rootCause: a.root_cause,
          category: a.category,
        })),
        byCategory: Object.entries(alertsByCategory).map(([category, categoryAlerts]) => ({
          category,
          count: categoryAlerts.length,
          alerts: categoryAlerts.map(a => ({
            metric: a.metric_name,
            severity: a.severity,
            message: a.message,
          })),
        })),
        allAlerts: alerts.map(a => ({
          id: a.id,
          metric: a.metric_name,
          severity: a.severity,
          message: a.message,
          change: a.change_percent,
          rootCause: a.root_cause,
          category: a.category,
          currentValue: a.current_value,
          previousValue: a.previous_value,
        })),
      },
    };
  }, [alerts, alertCounts]);

  return (
    <div className="flex flex-col h-screen">
      <Header title="KPI Alerts" subtitle="Cox Automotive • Real-time monitoring and anomaly detection" />
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

        {/* Filters and Actions */}
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
          <div className="flex items-center space-x-2">
            <button
              onClick={async () => {
                setIsSeeding(true);
                try {
                  await alertsService.seedAnomalies();
                  await queryClient.invalidateQueries({ queryKey: ['alerts'] });
                  alert('Sample anomalies seeded successfully!');
                } catch (error) {
                  console.error('Failed to seed anomalies:', error);
                  alert('Failed to seed anomalies. Please try again.');
                } finally {
                  setIsSeeding(false);
                }
              }}
              disabled={isSeeding}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <SparklesIcon className="w-4 h-4" />
              <span>{isSeeding ? 'Seeding...' : 'Seed Anomalies'}</span>
            </button>
            <button
              onClick={async () => {
                setIsDetecting(true);
                try {
                  const result = await alertsService.detectAnomalies();
                  await queryClient.invalidateQueries({ queryKey: ['alerts'] });
                  alert(`Anomaly detection complete! Found ${result.anomalies_detected} anomalies, stored ${result.alerts_stored} new alerts.`);
                } catch (error) {
                  console.error('Failed to detect anomalies:', error);
                  alert('Failed to detect anomalies. Please try again.');
                } finally {
                  setIsDetecting(false);
                }
              }}
              disabled={isDetecting}
              className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <SparklesIcon className="w-4 h-4" />
              <span>{isDetecting ? 'Detecting...' : 'Detect Anomalies'}</span>
            </button>
            <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
              Configure Alerts
            </button>
          </div>
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
                      <button
                        onClick={async () => {
                          setInvestigatingAlertId(alert.id);
                          setInvestigationChatOpen(true);
                        }}
                        className="px-3 py-1 text-xs font-medium text-cox-blue-700 bg-cox-blue-50 rounded hover:bg-cox-blue-100 flex items-center space-x-1"
                      >
                        <MagnifyingGlassIcon className="w-3 h-3" />
                        <span>Investigate</span>
                      </button>
                      <button
                        onClick={async () => {
                          if (!confirm('Are you sure you want to dismiss this alert?')) return;
                          setDismissingAlertId(alert.id);
                          try {
                            await alertsService.dismissAlert(alert.id);
                            await queryClient.invalidateQueries({ queryKey: ['alerts'] });
                          } catch (error) {
                            console.error('Failed to dismiss alert:', error);
                            alert('Failed to dismiss alert. Please try again.');
                          } finally {
                            setDismissingAlertId(null);
                          }
                        }}
                        disabled={dismissingAlertId === alert.id}
                        className="px-3 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {dismissingAlertId === alert.id ? 'Dismissing...' : 'Dismiss'}
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

      {/* Floating Chat Bot */}
      <FloatingChatBot 
        pageContext={pageContext}
      />

      {/* Investigation Chat Modal */}
      {investigationChatOpen && investigatingAlertId && (
        <InvestigationChatModal
          alertId={investigatingAlertId}
          alert={alerts.find(a => a.id === investigatingAlertId)}
          onClose={() => {
            setInvestigationChatOpen(false);
            setInvestigatingAlertId(null);
          }}
        />
      )}
    </div>
  );
}

// Investigation Chat Modal Component
function InvestigationChatModal({ 
  alertId, 
  alert, 
  onClose 
}: { 
  alertId: string; 
  alert?: Alert; 
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Build context-aware query about the specific alert
      const alertContext = alert ? `
**Alert Details:**
- Metric: ${alert.metric_name}
- Severity: ${alert.severity}
- Current Value: ${alert.current_value}
- Previous Value: ${alert.previous_value}
- Change: ${alert.change_percent}%
- Category: ${alert.category}
- Root Cause: ${alert.root_cause}
- Message: ${alert.message}
` : '';

      const query = `${alertContext}

User is investigating this specific alert (ID: ${alertId}). User query: ${userMessage}. 

**Available Tools:**
- **generate_sql_query**: Query related data to understand the root cause
- **analyze_kpi_data**: Analyze KPI data to understand why this anomaly occurred
- Use these tools to provide detailed analysis, root cause explanation, and actionable recommendations for this specific alert.`;

      const conversationId = SessionManager.getConversationId();
      const response = await sendChatMessage(query, conversationId);

      if (response.conversation_id) {
        SessionManager.refreshSession();
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: response.message }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Investigate Alert</h3>
            {alert && (
              <p className="text-sm text-gray-500 mt-1">
                {alert.metric_name} - {alert.severity.toUpperCase()}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 py-8">
              <p className="mb-2">Ask questions about this alert to get detailed analysis.</p>
              <p className="text-sm">Example: "Why did this happen?" or "What should I do about this?"</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={clsx(
                'flex',
                msg.role === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={clsx(
                  'max-w-[80%] rounded-lg p-3',
                  msg.role === 'user'
                    ? 'bg-cox-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg p-3">
                <p className="text-sm text-gray-500">Thinking...</p>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about this alert..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
