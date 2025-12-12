'use client';

import { useState, useMemo } from 'react';
import Header from '@/components/ui/Header';
import KPICard from '@/components/ui/KPICard';
import DataTable from '@/components/ui/DataTable';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import {
  TruckIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  MapPinIcon,
} from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import ErrorState from '@/components/ui/ErrorState';
import { 
  logisticsDashboardService, 
  transformCarrierData, 
  transformRouteData, 
  transformDelayReasons 
} from '@/lib/api/logisticsDashboard';

// Dwell time comparison will come from backend

const carrierColumns = [
  { key: 'carrier', header: 'Carrier', align: 'left' as const },
  { key: 'total', header: 'Total Shipments', align: 'right' as const, format: 'number' as const },
  { key: 'delayed', header: 'Delayed', align: 'right' as const, format: 'number' as const },
  {
    key: 'delay_rate',
    header: 'Delay Rate',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) > 10 ? 'text-red-600 font-medium' : 'text-green-600'}>
        {Number(value).toFixed(1)}%
      </span>
    ),
  },
  {
    key: 'avg_dwell',
    header: 'Avg Dwell (hrs)',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) > 2 ? 'text-red-600 font-medium' : ''}>
        {Number(value).toFixed(1)}
      </span>
    ),
  },
];

const routeColumns = [
  { key: 'route', header: 'Route', align: 'left' as const },
  { key: 'carrier', header: 'Carrier', align: 'left' as const },
  { key: 'delayed', header: 'Delayed', align: 'right' as const, format: 'number' as const },
  { key: 'total', header: 'Total', align: 'right' as const, format: 'number' as const },
  {
    key: 'reason',
    header: 'Primary Reason',
    align: 'left' as const,
    render: (value: unknown) => (
      <span className={`px-2 py-1 text-xs font-medium rounded ${
        value === 'Carrier' ? 'bg-red-100 text-red-700' :
        value === 'Route' ? 'bg-yellow-100 text-yellow-700' :
        'bg-blue-100 text-blue-700'
      }`}>
        {String(value)}
      </span>
    ),
  },
];

export default function LogisticsPage() {
  const [carrierChartType, setCarrierChartType] = useState<'bar' | 'pie' | 'line'>('bar');
  const [delayChartType, setDelayChartType] = useState<'bar' | 'pie' | 'line'>('pie');
  const [dwellChartType, setDwellChartType] = useState<'bar' | 'pie' | 'line'>('bar');

  // Fetch logistics dashboard data
  const { data: logisticsData, isLoading, error } = useQuery({
    queryKey: ['logisticsDashboard'],
    queryFn: logisticsDashboardService.getLogisticsDashboard,
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  // Transform data for frontend use
  const carrierData = logisticsData?.carrier_breakdown?.map(transformCarrierData) || [];
  const routeData = logisticsData?.route_analysis?.map(transformRouteData) || [];
  const delayReasons = logisticsData?.delay_reasons ? transformDelayReasons(logisticsData.delay_reasons) : [];
  const overallStats = logisticsData?.overall_stats;
  const dwellTimeComparison = logisticsData?.dwell_time_comparison || [];

  // Prepare page context for the chatbot
  const pageContext = useMemo(() => ({
    page: 'Logistics Analysis',
    charts: [
      {
        id: 'carrier-performance',
        title: 'Carrier Performance',
        type: carrierChartType,
        data: carrierData,
      },
      {
        id: 'delay-attribution',
        title: 'Delay Attribution',
        type: delayChartType,
        data: delayReasons,
      },
      {
        id: 'dwell-time-comparison',
        title: 'Dwell Time Comparison',
        type: dwellChartType,
        data: dwellTimeComparison,
      },
    ],
    logistics: {
      overallStats,
      carrierCount: carrierData.length,
      routeCount: routeData.length,
      topCarrier: carrierData[0]?.carrier,
      topDelayReason: delayReasons[0]?.name,
    },
  }), [carrierData, delayReasons, overallStats, carrierChartType, delayChartType, dwellChartType, dwellTimeComparison]);

  // Handle chart updates from chatbot
  const handleChartUpdate = (chartId: string, updates: { type?: string; data?: any }) => {
    if (chartId === 'carrier-performance' && updates.type) {
      setCarrierChartType(updates.type as 'bar' | 'pie' | 'line');
    } else if (chartId === 'delay-attribution' && updates.type) {
      setDelayChartType(updates.type as 'bar' | 'pie' | 'line');
    } else if (chartId === 'dwell-time-comparison' && updates.type) {
      setDwellChartType(updates.type as 'bar' | 'pie' | 'line');
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Logistics Analysis"
        subtitle="Cox Automotive • Shipment delays, carrier performance, and route analysis"
      />
      <div className="flex-1 p-6 overflow-auto space-y-6">
        {isLoading ? (
          <LoadingSkeleton variant="card" rows={6} />
        ) : error ? (
          <ErrorState 
            title="Failed to load logistics data"
            message="There was an error loading the logistics analysis data."
            onRetry={() => window.location.reload()}
          />
        ) : (
          <>
            {/* Alert Banner */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-3 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800">Logistics Performance Alert</h3>
                <p className="text-sm text-red-700 mt-1">
                  {overallStats 
                    ? `${overallStats.delay_rate}% of shipments delayed over the past 7 days (${overallStats.delayed_shipments} out of ${overallStats.total_shipments} shipments).`
                    : 'Loading logistics performance data...'
                  }
                  {carrierData.length > 0 && ` Primary issues with ${carrierData.filter(c => c.delay_rate > 15).map(c => c.carrier).join(', ')}.`}
                </p>
              </div>
            </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4">
          <KPICard
            title="Total Shipments"
            value={overallStats?.total_shipments || 245}
            change={8.2}
            changeLabel="vs last week"
            icon={<TruckIcon className="w-6 h-6" />}
          />
          <KPICard
            title="On-Time Rate"
            value={overallStats ? Math.round(100 - overallStats.delay_rate) : 82}
            format="percent"
            change={overallStats ? -overallStats.delay_rate : -10}
            changeLabel="vs last week"
            icon={<ClockIcon className="w-6 h-6" />}
          />
          <KPICard
            title="Delayed Shipments"
            value={overallStats?.delayed_shipments || 33}
            change={125}
            changeLabel="vs last week"
            icon={<ExclamationTriangleIcon className="w-6 h-6" />}
          />
          <KPICard
            title="Avg Dwell Time"
            value={carrierData.length > 0 
              ? `${(carrierData.reduce((sum, c) => sum + c.avg_dwell, 0) / carrierData.length).toFixed(1)} hrs`
              : "2.1 hrs"
            }
            icon={<MapPinIcon className="w-6 h-6" />}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-3 gap-6">
          {/* Carrier Performance */}
          <div className="col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Carrier Performance
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                {carrierChartType === 'pie' ? (
                  <PieChart>
                    <Pie
                      data={carrierData}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="delayed"
                      label={({ carrier, delayed }) => `${carrier}: ${delayed}`}
                    >
                      {carrierData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#ef4444', '#f59e0b', '#3b82f6', '#10b981'][index % 4]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                ) : carrierChartType === 'line' ? (
                  <LineChart data={carrierData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="carrier" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="total" name="Total" stroke="#93c5fd" strokeWidth={2} />
                    <Line type="monotone" dataKey="delayed" name="Delayed" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                ) : (
                  <BarChart data={carrierData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="carrier" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="total" name="Total" fill="#93c5fd" />
                    <Bar dataKey="delayed" name="Delayed" fill="#ef4444" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>

          {/* Delay Reasons */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Delay Attribution
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                {delayChartType === 'bar' ? (
                  <BarChart data={delayReasons}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#ef4444" />
                  </BarChart>
                ) : delayChartType === 'line' ? (
                  <LineChart data={delayReasons}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#ef4444" strokeWidth={2} />
                  </LineChart>
                ) : (
                  <PieChart>
                    <Pie
                      data={delayReasons}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {delayReasons.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                )}
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Dwell Time Comparison */}
        {dwellTimeComparison.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Dwell Time Comparison (Hours)
            </h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                {dwellChartType === 'pie' ? (
                  // For pie chart, we'll show the comparison for the first period
                  dwellTimeComparison.length > 0 && carrierData.length > 0 ? (
                    <PieChart>
                      <Pie
                        data={carrierData.slice(0, 5).map(carrier => {
                          const periodData = dwellTimeComparison[0];
                          return {
                            name: carrier.carrier,
                            value: periodData[carrier.carrier] as number || 0,
                          };
                        })}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value.toFixed(1)}h`}
                      >
                        {carrierData.slice(0, 5).map((entry, index) => {
                          const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
                          return (
                            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                          );
                        })}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  ) : null
                ) : dwellChartType === 'line' ? (
                  // For line chart, transpose data to show carriers on X-axis and periods as lines
                  carrierData.length > 0 ? (
                    <LineChart 
                      data={carrierData.slice(0, 5).map(carrier => {
                        const lastWeek = dwellTimeComparison.find(d => d.period === 'Last Week');
                        const thisWeek = dwellTimeComparison.find(d => d.period === 'This Week');
                        return {
                          carrier: carrier.carrier,
                          'Last Week': lastWeek ? (lastWeek[carrier.carrier] as number || 0) : 0,
                          'This Week': thisWeek ? (thisWeek[carrier.carrier] as number || 0) : 0,
                        };
                      })}
                    >
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="carrier" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="Last Week" stroke="#3b82f6" strokeWidth={2} name="Last Week" />
                      <Line type="monotone" dataKey="This Week" stroke="#ef4444" strokeWidth={2} name="This Week" />
                    </LineChart>
                  ) : null
                ) : (
                  <BarChart data={dwellTimeComparison} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="period" type="category" width={100} />
                    <Tooltip />
                    {carrierData.length > 0 && carrierData.slice(0, 5).map((carrier, index) => {
                      const colors = ['#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'];
                      return (
                        <Bar 
                          key={carrier.carrier} 
                          dataKey={carrier.carrier} 
                          fill={colors[index % colors.length]} 
                          name={carrier.carrier} 
                        />
                      );
                    })}
                  </BarChart>
                )}
              </ResponsiveContainer>
            </div>
            {dwellTimeComparison.length >= 2 && carrierData.length > 0 && (() => {
              const lastWeek = dwellTimeComparison.find(d => d.period === 'Last Week');
              const thisWeek = dwellTimeComparison.find(d => d.period === 'This Week');
              const topCarrier = carrierData[0];
              if (lastWeek && thisWeek && topCarrier) {
                const lastWeekDwell = lastWeek[topCarrier.carrier] as number;
                const thisWeekDwell = thisWeek[topCarrier.carrier] as number;
                if (lastWeekDwell && thisWeekDwell && thisWeekDwell > lastWeekDwell) {
                  const increase = ((thisWeekDwell - lastWeekDwell) / lastWeekDwell) * 100;
                  return (
                    <p className="text-sm text-red-600 mt-4">
                      ⚠️ {topCarrier.carrier} dwell time increased from {lastWeekDwell.toFixed(1)} to {thisWeekDwell.toFixed(1)} hours ({increase.toFixed(0)}% increase)
                    </p>
                  );
                }
              }
              return null;
            })()}
          </div>
        )}

        {/* Tables */}
        <div className="grid grid-cols-2 gap-6">
          {/* Carrier Table */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Carrier Summary
            </h3>
            <DataTable
              columns={carrierColumns}
              data={carrierData}
              highlightRow={(row) => Number(row.delay_rate) > 20}
            />
          </div>

          {/* Route Table */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Problem Routes
            </h3>
            <DataTable
              columns={routeColumns}
              data={routeData}
              highlightRow={(row) => Number(row.delayed) > 5}
            />
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-red-50 rounded-lg">
              <h4 className="font-semibold text-red-800">Immediate Action</h4>
              <ul className="mt-2 space-y-1 text-sm text-red-700">
                {carrierData.filter(c => c.delay_rate > 20).length > 0 ? (
                  carrierData.filter(c => c.delay_rate > 20).slice(0, 3).map((carrier, idx) => (
                    <li key={idx}>• Escalate with {carrier.carrier} (delay rate: {carrier.delay_rate}%)</li>
                  ))
                ) : carrierData.filter(c => c.delay_rate > 15).length > 0 ? (
                  carrierData.filter(c => c.delay_rate > 15).slice(0, 2).map((carrier, idx) => (
                    <li key={idx}>• Monitor {carrier.carrier} closely (delay rate: {carrier.delay_rate}%)</li>
                  ))
                ) : (
                  <li>• Monitor carrier performance closely</li>
                )}
                {routeData.filter(r => r.delayed > 5).length > 0 ? (
                  routeData.filter(r => r.delayed > 5).slice(0, 2).map((route, idx) => (
                    <li key={`route-${idx}`}>• Review {route.route} route ({route.delayed} delays)</li>
                  ))
                ) : routeData.filter(r => r.delayed > 3).length > 0 ? (
                  routeData.filter(r => r.delayed > 3).slice(0, 1).map((route, idx) => (
                    <li key={`route-${idx}`}>• Monitor {route.route} route ({route.delayed} delays)</li>
                  ))
                ) : null}
                {carrierData.length > 0 && carrierData.some(c => c.avg_dwell > 2) && (
                  <li>• Address high dwell time issues (avg: {carrierData.filter(c => c.avg_dwell > 2).map(c => `${c.carrier} (${c.avg_dwell.toFixed(1)}h)`).join(', ')})</li>
                )}
              </ul>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-800">Short-term</h4>
              <ul className="mt-2 space-y-1 text-sm text-blue-700">
                {carrierData.length > 0 && (
                  <li>• Review carrier allocation strategy (currently {carrierData.length} active carriers)</li>
                )}
                {routeData.length > 0 && (
                  <li>• Consider backup carriers for {routeData.slice(0, 2).map(r => r.route).join(', ')} routes</li>
                )}
                {dwellTimeComparison.length > 0 && (
                  <li>• Set up automated dwell time monitoring</li>
                )}
                {delayReasons.length > 0 && (
                  <li>• Address top delay reason: {delayReasons[0]?.name} ({delayReasons[0]?.value} occurrences)</li>
                )}
                {overallStats && overallStats.delay_rate > 15 && (
                  <li>• Overall delay rate ({overallStats.delay_rate}%) exceeds acceptable threshold</li>
                )}
              </ul>
            </div>
          </div>
        </div>
          </>
        )}
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot 
        pageContext={pageContext}
        onChartUpdate={handleChartUpdate}
      />
    </div>
  );
}
