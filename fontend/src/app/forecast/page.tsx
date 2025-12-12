'use client';

import { useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ChartBarIcon,
  CalendarIcon,
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
  Area,
  ComposedChart,
} from 'recharts';
import clsx from 'clsx';
import { kpiMonitoringService, Forecast } from '@/lib/api/kpiMonitoring';

const METRIC_COLORS: Record<string, string> = {
  'F&I Revenue': '#3b82f6',
  'Service Appointments': '#10b981',
  'Shipment Delays': '#ef4444',
};

export default function ForecastPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string>('all');
  const [daysAhead, setDaysAhead] = useState(7);
  const queryClient = useQueryClient();

  // Fetch forecasts
  const { data: forecastData, isLoading, error } = useQuery({
    queryKey: ['forecasts', daysAhead],
    queryFn: () => kpiMonitoringService.getForecasts(undefined, daysAhead),
    refetchInterval: 600000, // Refresh every 10 minutes
  });

  // Fetch scheduler status
  const { data: schedulerStatus } = useQuery({
    queryKey: ['schedulerStatus'],
    queryFn: () => kpiMonitoringService.getSchedulerStatus(),
  });

  const handleGenerateForecasts = async () => {
    setIsGenerating(true);
    try {
      await kpiMonitoringService.generateForecasts(daysAhead);
      await queryClient.invalidateQueries({ queryKey: ['forecasts'] });
      alert('Forecasts generated successfully!');
    } catch (error) {
      console.error('Failed to generate forecasts:', error);
      alert('Failed to generate forecasts. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  // Get unique metrics
  const metrics = useMemo(() => {
    if (!forecastData?.forecasts) return [];
    return Array.from(new Set(forecastData.forecasts.map((f) => f.metric_name)));
  }, [forecastData]);

  // Filter forecasts by selected metric
  const filteredForecasts = useMemo(() => {
    if (!forecastData?.forecasts) return [];
    if (selectedMetric === 'all') return forecastData.forecasts;
    return forecastData.forecasts.filter((f) => f.metric_name === selectedMetric);
  }, [forecastData, selectedMetric]);

  // Group forecasts by metric for chart
  const chartData = useMemo(() => {
    if (!forecastData?.forecasts) return [];

    // Group by date
    const byDate: Record<string, any> = {};
    forecastData.forecasts.forEach((f) => {
      if (!byDate[f.forecast_date]) {
        byDate[f.forecast_date] = { date: f.forecast_date };
      }
      byDate[f.forecast_date][f.metric_name] = f.predicted_value;
      byDate[f.forecast_date][`${f.metric_name}_lower`] = f.lower_bound;
      byDate[f.forecast_date][`${f.metric_name}_upper`] = f.upper_bound;
      byDate[f.forecast_date][`${f.metric_name}_at_risk`] = f.at_risk;
    });

    return Object.values(byDate).sort((a, b) =>
      new Date(a.date).getTime() - new Date(b.date).getTime()
    );
  }, [forecastData]);

  // Count at-risk forecasts
  const atRiskCount = useMemo(() => {
    if (!forecastData?.forecasts) return 0;
    return forecastData.forecasts.filter((f) => f.at_risk).length;
  }, [forecastData]);

  // Prepare page context for the bot
  const pageContext = useMemo(() => ({
    page: 'KPI Forecasts',
    forecasts: {
      total: forecastData?.forecasts?.length || 0,
      atRisk: atRiskCount,
      metrics: metrics,
      daysAhead: daysAhead,
    },
  }), [forecastData, atRiskCount, metrics, daysAhead]);

  if (isLoading) {
    return (
      <div className="flex flex-col h-screen">
        <Header title="KPI Forecasts" subtitle="Cox Automotive - Predictive analytics" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <ArrowPathIcon className="w-12 h-12 text-gray-400 mx-auto animate-spin mb-4" />
            <p className="text-gray-500">Loading forecasts...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col h-screen">
        <Header title="KPI Forecasts" subtitle="Cox Automotive - Predictive analytics" />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <p className="text-gray-900 font-medium mb-2">Failed to load forecasts</p>
            <button
              onClick={() => queryClient.invalidateQueries({ queryKey: ['forecasts'] })}
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
      <Header title="KPI Forecasts" subtitle="Cox Automotive - Predictive analytics with confidence intervals" />
      <div className="flex-1 p-6 overflow-auto">
        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
            >
              <option value="all">All Metrics</option>
              {metrics.map((metric) => (
                <option key={metric} value={metric}>{metric}</option>
              ))}
            </select>
            <select
              value={daysAhead}
              onChange={(e) => setDaysAhead(Number(e.target.value))}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
            </select>
          </div>
          <div className="flex items-center space-x-4">
            {schedulerStatus && (
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <div className={clsx(
                  'w-2 h-2 rounded-full',
                  schedulerStatus.running ? 'bg-green-500' : 'bg-gray-400'
                )} />
                <span>Scheduler: {schedulerStatus.running ? 'Active' : 'Inactive'}</span>
              </div>
            )}
            <button
              onClick={handleGenerateForecasts}
              disabled={isGenerating}
              className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 disabled:opacity-50 flex items-center space-x-2"
            >
              <ArrowPathIcon className={clsx('w-4 h-4', isGenerating && 'animate-spin')} />
              <span>{isGenerating ? 'Generating...' : 'Generate Forecasts'}</span>
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-500">Total Forecasts</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2">{forecastData?.forecasts?.length || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="flex items-center space-x-2">
              <CalendarIcon className="w-5 h-5 text-blue-600" />
              <span className="text-sm text-gray-500">Days Forecasted</span>
            </div>
            <p className="text-2xl font-bold text-gray-900 mt-2">{daysAhead}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="w-5 h-5 text-green-600" />
              <span className="text-sm text-gray-500">On Track</span>
            </div>
            <p className="text-2xl font-bold text-green-700 mt-2">
              {(forecastData?.forecasts?.length || 0) - atRiskCount}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-4">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
              <span className="text-sm text-gray-500">At Risk</span>
            </div>
            <p className="text-2xl font-bold text-red-700 mt-2">{atRiskCount}</p>
          </div>
        </div>

        {/* Forecast Chart */}
        {chartData.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  fontSize={12}
                />
                <YAxis fontSize={12} />
                <Tooltip
                  labelFormatter={(label) => new Date(label).toLocaleDateString()}
                  formatter={(value: number, name: string) => {
                    if (name.includes('_lower') || name.includes('_upper')) return null;
                    return [value.toFixed(2), name];
                  }}
                />
                <Legend />
                {metrics.map((metric) => (
                  <Line
                    key={metric}
                    type="monotone"
                    dataKey={metric}
                    stroke={METRIC_COLORS[metric] || '#6b7280'}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                ))}
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Forecast Details Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Forecast Details</h3>
          {filteredForecasts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Metric</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Category</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Date</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-500">Predicted</th>
                    <th className="text-right py-3 px-4 font-medium text-gray-500">Confidence Interval</th>
                    <th className="text-center py-3 px-4 font-medium text-gray-500">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-500">Risk Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredForecasts.map((forecast, idx) => (
                    <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium text-gray-900">{forecast.metric_name}</td>
                      <td className="py-3 px-4 text-gray-600">{forecast.category}</td>
                      <td className="py-3 px-4 text-gray-600">
                        {new Date(forecast.forecast_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-right font-medium text-gray-900">
                        {forecast.predicted_value.toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600">
                        [{forecast.lower_bound.toFixed(2)} - {forecast.upper_bound.toFixed(2)}]
                      </td>
                      <td className="py-3 px-4 text-center">
                        {forecast.at_risk ? (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                            At Risk
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                            On Track
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-sm">
                        {forecast.risk_reason || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <ChartBarIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>No forecasts available. Click "Generate Forecasts" to create predictions.</p>
            </div>
          )}
        </div>
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot pageContext={pageContext} />
    </div>
  );
}
