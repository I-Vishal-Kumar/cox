'use client';

import Header from '@/components/ui/Header';
import KPICard from '@/components/ui/KPICard';
import DataTable from '@/components/ui/DataTable';
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

// Keep dwell time comparison as hardcoded for now (not available in backend yet)
const dwellTimeComparison = [
  { period: 'Last Week', 'Carrier X': 1.2, 'Carrier Y': 1.1, 'Carrier Z': 1.0 },
  { period: 'This Week', 'Carrier X': 3.1, 'Carrier Y': 1.3, 'Carrier Z': 1.1 },
];

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

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Logistics Analysis"
        subtitle="Shipment delays, carrier performance, and route analysis"
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
                <BarChart data={carrierData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="carrier" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" name="Total" fill="#93c5fd" />
                  <Bar dataKey="delayed" name="Delayed" fill="#ef4444" />
                </BarChart>
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
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Dwell Time Comparison */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Dwell Time Comparison (Hours)
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dwellTimeComparison} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="period" type="category" width={100} />
                <Tooltip />
                <Bar dataKey="Carrier X" fill="#ef4444" name="Carrier X" />
                <Bar dataKey="Carrier Y" fill="#3b82f6" name="Carrier Y" />
                <Bar dataKey="Carrier Z" fill="#10b981" name="Carrier Z" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-sm text-red-600 mt-4">
            ⚠️ Carrier X dwell time increased from 1.2 to 3.1 hours (158% increase)
          </p>
        </div>

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
                {carrierData.filter(c => c.delay_rate > 20).slice(0, 2).map((carrier, idx) => (
                  <li key={idx}>• Escalate with {carrier.carrier} (delay rate: {carrier.delay_rate}%)</li>
                ))}
                {routeData.filter(r => r.delayed > 5).slice(0, 2).map((route, idx) => (
                  <li key={`route-${idx}`}>• Review {route.route} route ({route.delayed} delays)</li>
                ))}
                {carrierData.length === 0 && (
                  <>
                    <li>• Monitor carrier performance closely</li>
                    <li>• Review high-delay routes for optimization</li>
                  </>
                )}
              </ul>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-semibold text-blue-800">Short-term</h4>
              <ul className="mt-2 space-y-1 text-sm text-blue-700">
                <li>• Review carrier allocation strategy</li>
                <li>• Consider backup carriers for critical routes</li>
                <li>• Set up automated dwell time monitoring</li>
                {delayReasons.length > 0 && (
                  <li>• Address top delay reason: {delayReasons[0]?.name}</li>
                )}
              </ul>
            </div>
          </div>
        </div>
          </>
        )}
      </div>
    </div>
  );
}
