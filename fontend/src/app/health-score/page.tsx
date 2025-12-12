'use client';

import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import GaugeChart from '@/components/ui/GaugeChart';
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  LightBulbIcon,
  ChartBarIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';
import clsx from 'clsx';
import { kpiMonitoringService, HealthScoreResponse, HealthScoreHistoryItem } from '@/lib/api/kpiMonitoring';

const CATEGORY_COLORS = {
  sales: '#3b82f6',
  service: '#10b981',
  fni: '#f59e0b',
  logistics: '#8b5cf6',
  manufacturing: '#ef4444',
};

export default function HealthScorePage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const queryClient = useQueryClient();

  // Fetch health score
  const { data: healthScore, isLoading, error } = useQuery({
    queryKey: ['healthScore'],
    queryFn: () => kpiMonitoringService.getHealthScore(),
    refetchInterval: 300000, // Refresh every 5 minutes
  });

  // Fetch history
  const { data: historyData } = useQuery({
    queryKey: ['healthScoreHistory'],
    queryFn: () => kpiMonitoringService.getHealthScoreHistory(30),
  });

  const handleGenerateScore = async () => {
    setIsGenerating(true);
    try {
      await kpiMonitoringService.generateHealthScore();
      await queryClient.invalidateQueries({ queryKey: ['healthScore'] });
      await queryClient.invalidateQueries({ queryKey: ['healthScoreHistory'] });
    } catch (error) {
      console.error('Failed to generate health score:', error);
      alert('Failed to generate health score. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Get score color based on value
  const getScoreColor = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'gray';
    if (score >= 80) return 'green';
    if (score >= 60) return 'orange';
    return 'red';
  };

  // Get score label
  const getScoreLabel = (score: number | null | undefined) => {
    if (score === null || score === undefined) return 'N/A';
    if (score >= 80) return 'Healthy';
    if (score >= 60) return 'Fair';
    return 'Critical';
  };

  // Prepare page context for the bot
  const pageContext = useMemo(() => ({
    page: 'KPI Health Score',
    healthScore: healthScore ? {
      overall: healthScore.overall_score,
      date: healthScore.score_date,
      categories: healthScore.category_scores,
      kpiCounts: healthScore.kpi_counts,
      topRisks: healthScore.top_risks?.slice(0, 3),
      recommendations: healthScore.recommendations?.slice(0, 3),
    } : null,
  }), [healthScore]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen">
        <Header title="KPI Health Score" subtitle="Cox Automotive - Daily health monitoring" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <ArrowPathIcon className="w-12 h-12 text-gray-400 mx-auto animate-spin mb-4" />
            <p className="text-gray-500">Loading health score...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-screen">
        <Header title="KPI Health Score" subtitle="Cox Automotive - Daily health monitoring" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-gray-900 font-medium mb-2">Failed to load health score</p>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['healthScore'] })}
              className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <Header title="KPI Health Score" subtitle="Cox Automotive - Daily health monitoring and recommendations" />
      <div className="flex-1 p-6 overflow-auto">
        {/* Top Row: Overall Score + Category Scores */}
        <div className="grid grid-cols-6 gap-4 mb-6">
          {/* Overall Health Score */}
          <div className="col-span-2 bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Overall Health</h3>
              <button
                onClick={handleGenerateScore}
                disabled={isGenerating}
                className="flex items-center space-x-1 text-sm text-cox-blue-600 hover:text-cox-blue-700 disabled:opacity-50"
              >
                <ArrowPathIcon className={clsx('w-4 h-4', isGenerating && 'animate-spin')} />
                <span>{isGenerating ? 'Generating...' : 'Refresh'}</span>
              </button>
            </div>
            <div className="flex items-center justify-center">
              <GaugeChart
                value={healthScore?.overall_score || 0}
                maxValue={100}
                size="lg"
                color={getScoreColor(healthScore?.overall_score)}
              />
            </div>
            <div className="text-center mt-4">
              <span className={clsx(
                'px-3 py-1 rounded-full text-sm font-medium',
                healthScore && healthScore.overall_score >= 80 ? 'bg-green-100 text-green-800' :
                healthScore && healthScore.overall_score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              )}>
                {getScoreLabel(healthScore?.overall_score)}
              </span>
              <p className="text-xs text-gray-500 mt-2">
                As of {healthScore?.score_date ? new Date(healthScore.score_date).toLocaleDateString() : 'Today'}
              </p>
            </div>
          </div>

          {/* Category Scores */}
          <div className="col-span-4 bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Health</h3>
            <div className="grid grid-cols-5 gap-4">
              {[
                { key: 'sales', label: 'Sales', score: healthScore?.category_scores?.sales },
                { key: 'service', label: 'Service', score: healthScore?.category_scores?.service },
                { key: 'fni', label: 'F&I', score: healthScore?.category_scores?.fni },
                { key: 'logistics', label: 'Logistics', score: healthScore?.category_scores?.logistics },
                { key: 'manufacturing', label: 'Manufacturing', score: healthScore?.category_scores?.manufacturing },
              ].map((cat) => (
                <div key={cat.key} className="text-center">
                  <GaugeChart
                    value={cat.score || 0}
                    maxValue={100}
                    size="sm"
                    color={getScoreColor(cat.score)}
                  />
                  <p className="text-sm font-medium text-gray-700 mt-2">{cat.label}</p>
                  <p className={clsx(
                    'text-xs',
                    cat.score && cat.score >= 80 ? 'text-green-600' :
                    cat.score && cat.score >= 60 ? 'text-yellow-600' :
                    'text-red-600'
                  )}>
                    {cat.score?.toFixed(1) || 'N/A'}%
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Middle Row: KPI Counts + Health Score Trend */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          {/* KPI Counts */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">KPI Status</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Total KPIs Monitored</span>
                <span className="text-lg font-bold text-gray-900">{healthScore?.kpi_counts?.total || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  <span className="text-sm text-green-700">On Target</span>
                </div>
                <span className="text-lg font-bold text-green-700">{healthScore?.kpi_counts?.on_target || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
                  <span className="text-sm text-yellow-700">At Risk</span>
                </div>
                <span className="text-lg font-bold text-yellow-700">{healthScore?.kpi_counts?.at_risk || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
                  <span className="text-sm text-red-700">Critical</span>
                </div>
                <span className="text-lg font-bold text-red-700">{healthScore?.kpi_counts?.critical || 0}</span>
              </div>
            </div>
          </div>

          {/* Health Score Trend */}
          <div className="col-span-2 bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Health Score Trend</h3>
            {historyData?.history && historyData.history.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={historyData.history.slice().reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    fontSize={12}
                  />
                  <YAxis domain={[0, 100]} fontSize={12} />
                  <Tooltip
                    formatter={(value: number) => [`${value.toFixed(1)}%`, 'Score']}
                    labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="overall_score" name="Overall" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="sales_score" name="Sales" stroke={CATEGORY_COLORS.sales} strokeWidth={1} dot={false} />
                  <Line type="monotone" dataKey="fni_score" name="F&I" stroke={CATEGORY_COLORS.fni} strokeWidth={1} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[200px] text-gray-500">
                <p>No historical data available yet</p>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Row: Top Risks + Recommendations */}
        <div className="grid grid-cols-2 gap-4">
          {/* Top Risks */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <ArrowTrendingDownIcon className="w-5 h-5 text-red-600" />
              <h3 className="text-lg font-semibold text-gray-900">Top Risks</h3>
            </div>
            {healthScore?.top_risks && healthScore.top_risks.length > 0 ? (
              <div className="space-y-3">
                {healthScore.top_risks.map((risk, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'p-3 rounded-lg border',
                      risk.severity === 'critical' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium text-gray-900">{risk.metric}</p>
                        <p className="text-xs text-gray-500">{risk.category} - {risk.region || 'All Regions'}</p>
                      </div>
                      <span className={clsx(
                        'px-2 py-0.5 text-xs font-medium rounded-full',
                        risk.severity === 'critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                      )}>
                        {risk.change_percent?.toFixed(1)}%
                      </span>
                    </div>
                    {risk.root_cause && (
                      <p className="text-sm text-gray-600 mt-2">{risk.root_cause}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                <div className="text-center">
                  <CheckCircleIcon className="w-8 h-8 mx-auto mb-2 text-green-500" />
                  <p>No critical risks detected</p>
                </div>
              </div>
            )}
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <LightBulbIcon className="w-5 h-5 text-yellow-500" />
              <h3 className="text-lg font-semibold text-gray-900">Recommendations</h3>
            </div>
            {healthScore?.recommendations && healthScore.recommendations.length > 0 ? (
              <div className="space-y-3">
                {healthScore.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className={clsx(
                      'p-3 rounded-lg border',
                      rec.priority === 'critical' ? 'bg-red-50 border-red-200' :
                      rec.priority === 'high' ? 'bg-orange-50 border-orange-200' :
                      'bg-blue-50 border-blue-200'
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className={clsx(
                            'px-2 py-0.5 text-xs font-medium rounded-full',
                            rec.priority === 'critical' ? 'bg-red-100 text-red-800' :
                            rec.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          )}>
                            {rec.priority.toUpperCase()}
                          </span>
                          <span className="text-xs text-gray-500">{rec.category}</span>
                        </div>
                        <p className="font-medium text-gray-900 mt-1">{rec.action}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          <span className="font-medium">Expected impact:</span> {rec.expected_impact}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex items-center justify-center h-32 text-gray-500">
                <p>No recommendations at this time</p>
              </div>
            )}
          </div>
        </div>

        {/* Top Performers */}
        {healthScore?.top_performers && healthScore.top_performers.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-100 p-6">
            <div className="flex items-center space-x-2 mb-4">
              <ArrowTrendingUpIcon className="w-5 h-5 text-green-600" />
              <h3 className="text-lg font-semibold text-gray-900">Top Performers</h3>
            </div>
            <div className="grid grid-cols-5 gap-4">
              {healthScore.top_performers.map((performer, idx) => (
                <div key={idx} className="p-3 bg-green-50 rounded-lg border border-green-200 text-center">
                  <p className="font-medium text-gray-900 text-sm">{performer.metric}</p>
                  <p className="text-xs text-gray-500">{performer.category}</p>
                  <p className="text-lg font-bold text-green-600 mt-1">{performer.performance}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot pageContext={pageContext} />
    </div>
  );
}
