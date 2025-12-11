'use client';

import { useState } from 'react';
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
  LineChart,
  Line,
  Legend,
} from 'recharts';
import {
  CurrencyDollarIcon,
  UserGroupIcon,
  DocumentCheckIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import ErrorState from '@/components/ui/ErrorState';
import { fniDashboardService, transformDealerData, transformManagerData } from '@/lib/api/fniDashboard';

const columns = [
  { key: 'dealer', header: 'Dealer', align: 'left' as const },
  { key: 'this_week', header: 'This Week', align: 'right' as const, format: 'currency' as const },
  { key: 'last_week', header: 'Last Week', align: 'right' as const, format: 'currency' as const },
  {
    key: 'change',
    header: 'Change',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) < 0 ? 'text-red-600 font-medium' : 'text-green-600 font-medium'}>
        {Number(value) > 0 ? '+' : ''}{Number(value).toFixed(1)}%
      </span>
    ),
  },
  {
    key: 'penetration',
    header: 'Penetration',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) < 30 ? 'text-orange-600' : 'text-green-600'}>
        {Number(value)}%
      </span>
    ),
  },
];

const managerColumns = [
  { key: 'manager', header: 'Finance Manager', align: 'left' as const },
  { key: 'dealer', header: 'Dealer', align: 'left' as const },
  {
    key: 'penetration',
    header: 'Penetration',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) < 25 ? 'text-red-600 font-medium' : 'text-green-600'}>
        {Number(value).toFixed(1)}%
      </span>
    ),
  },
  { key: 'transactions', header: 'Transactions', align: 'right' as const, format: 'number' as const },
  { key: 'revenue', header: 'Revenue', align: 'right' as const, format: 'currency' as const },
];

export default function FNIAnalysisPage() {
  const [region, setRegion] = useState('Midwest');

  // Fetch F&I dashboard data
  const { data: fniData, isLoading, error } = useQuery({
    queryKey: ['fniDashboard', region],
    queryFn: () => fniDashboardService.getFNIDashboard(region),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  // Fetch weekly trends data using chat API
  const { data: weeklyTrendsData, isLoading: trendsLoading, error: trendsError } = useQuery({
    queryKey: ['weeklyTrends'],
    queryFn: () => fniDashboardService.getWeeklyTrends(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Fetch enhanced KPI data using chat API
  const { data: enhancedKPIData, isLoading: kpiLoading, error: kpiError } = useQuery({
    queryKey: ['enhancedKPI'],
    queryFn: () => fniDashboardService.getEnhancedKPIData(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Transform data for frontend use
  const dealerComparisonData = fniData?.dealer_comparison?.map(transformDealerData) || [];
  const managerBreakdown = fniData?.manager_breakdown?.map(transformManagerData) || [];
  
  // Use live weekly trends data or fallback to empty array
  const weeklyTrend = weeklyTrendsData || [];

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="F&I Analysis"
        subtitle="Finance & Insurance revenue and penetration analysis"
      />
      <div className="flex-1 p-6 overflow-auto space-y-6">
        {isLoading ? (
          <LoadingSkeleton variant="card" rows={6} />
        ) : error ? (
          <ErrorState 
            title="Failed to load F&I data"
            message="There was an error loading the F&I analysis data."
            onRetry={() => window.location.reload()}
          />
        ) : (
          <>
            {/* Alert Banner */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
              <ArrowTrendingDownIcon className="w-6 h-6 text-red-600 mr-3 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-800">F&I Revenue Alert - {region}</h3>
                <p className="text-sm text-red-700 mt-1">
                  {dealerComparisonData.length > 0 
                    ? `Analyzing ${dealerComparisonData.length} dealers in ${region} region. Last updated: ${fniData?.analysis_date ? new Date(fniData.analysis_date).toLocaleString() : 'Unknown'}`
                    : 'Loading F&I analysis data...'
                  }
                </p>
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="border border-gray-200 rounded-lg px-3 py-2 text-sm"
                >
                  <option>Midwest</option>
                  <option>Northeast</option>
                  <option>Southeast</option>
                  <option>West</option>
                </select>
                <select className="border border-gray-200 rounded-lg px-3 py-2 text-sm">
                  <option>This Week</option>
                  <option>Last 2 Weeks</option>
                  <option>This Month</option>
                  <option>Last Month</option>
                </select>
              </div>
              <button className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700">
                Export Report
              </button>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-4 gap-4">
              <KPICard
                title="Total F&I Revenue"
                value={enhancedKPIData?.total_revenue_this_week || 
                       dealerComparisonData.reduce((sum, dealer) => sum + dealer.this_week, 0) || 
                       167000}
                format="currency"
                change={enhancedKPIData && enhancedKPIData.total_revenue_last_week > 0
                  ? ((enhancedKPIData.total_revenue_this_week - enhancedKPIData.total_revenue_last_week) / enhancedKPIData.total_revenue_last_week) * 100
                  : dealerComparisonData.length > 0 
                    ? dealerComparisonData.reduce((sum, dealer) => sum + dealer.change, 0) / dealerComparisonData.length
                    : -11
                }
                changeLabel="vs last week"
                icon={<CurrencyDollarIcon className="w-6 h-6" />}
              />
              <KPICard
                title="Avg Penetration Rate"
                value={enhancedKPIData?.avg_penetration_this_week ? 
                       Math.round(enhancedKPIData.avg_penetration_this_week * 100) :
                       dealerComparisonData.length > 0 
                         ? Math.round(dealerComparisonData.reduce((sum, dealer) => sum + dealer.penetration, 0) / dealerComparisonData.length)
                         : 27
                }
                format="percent"
                change={enhancedKPIData && enhancedKPIData.avg_penetration_last_week > 0
                  ? ((enhancedKPIData.avg_penetration_this_week - enhancedKPIData.avg_penetration_last_week) / enhancedKPIData.avg_penetration_last_week) * 100
                  : dealerComparisonData.length > 0 
                    ? dealerComparisonData.reduce((sum, dealer) => sum + dealer.change, 0) / dealerComparisonData.length
                    : -12
                }
                changeLabel="vs last week"
                icon={<DocumentCheckIcon className="w-6 h-6" />}
              />
              <KPICard
                title="Total Transactions"
                value={enhancedKPIData?.total_transactions_this_week || 
                       managerBreakdown.reduce((sum, manager) => sum + manager.transactions, 0) || 
                       420}
                change={enhancedKPIData && enhancedKPIData.total_transactions_last_week > 0
                  ? ((enhancedKPIData.total_transactions_this_week - enhancedKPIData.total_transactions_last_week) / enhancedKPIData.total_transactions_last_week) * 100
                  : -3.2
                }
                changeLabel="vs last week"
                icon={<UserGroupIcon className="w-6 h-6" />}
              />
              <KPICard
                title="Avg F&I per Deal"
                value={dealerComparisonData.length > 0 
                  ? Math.round(dealerComparisonData.reduce((sum, dealer) => sum + dealer.this_week, 0) / 
                              managerBreakdown.reduce((sum, manager) => sum + manager.transactions, 1))
                  : 2145
                }
                format="currency"
                change={-8.1}
                changeLabel="vs last week"
                icon={<CurrencyDollarIcon className="w-6 h-6" />}
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-2 gap-6">
              {/* Dealer Comparison Chart */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Revenue by Dealer
                </h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={dealerComparisonData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="dealer" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toLocaleString()}`} />
                      <Legend />
                      <Bar dataKey="this_week" name="This Week" fill="#3b82f6" />
                      <Bar dataKey="last_week" name="Last Week" fill="#93c5fd" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Weekly Trend */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Weekly Trend by Region
                  </h3>
                  {trendsLoading && (
                    <div className="text-sm text-gray-500">Loading trends...</div>
                  )}
                  {trendsError && (
                    <div className="text-sm text-red-600">Failed to load trends</div>
                  )}
                </div>
                <div className="h-64">
                  {trendsLoading ? (
                    <div className="flex items-center justify-center h-full">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cox-blue-600"></div>
                    </div>
                  ) : weeklyTrend.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={weeklyTrend}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="week" />
                        <YAxis />
                        <Tooltip formatter={(value: number) => `$${value.toLocaleString()}`} />
                        <Legend />
                        <Line type="monotone" dataKey="midwest" stroke="#ef4444" strokeWidth={2} name="Midwest" />
                        <Line type="monotone" dataKey="northeast" stroke="#3b82f6" strokeWidth={2} name="Northeast" />
                        <Line type="monotone" dataKey="southeast" stroke="#10b981" strokeWidth={2} name="Southeast" />
                        <Line type="monotone" dataKey="west" stroke="#f59e0b" strokeWidth={2} name="West" />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      <div className="text-center">
                        <div className="text-lg mb-2">📊</div>
                        <div>No weekly trend data available</div>
                        <div className="text-sm mt-1">
                          {trendsError ? 'Please try again later' : 'Data will appear when available'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Tables */}
            <div className="grid grid-cols-2 gap-6">
              {/* Dealer Comparison Table */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Dealer Comparison
                </h3>
                <DataTable
                  columns={columns}
                  data={dealerComparisonData}
                  highlightRow={(row) => Number(row.change) < -10}
                />
              </div>

              {/* Manager Breakdown */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Finance Manager Performance
                </h3>
                <DataTable
                  columns={managerColumns}
                  data={managerBreakdown}
                  highlightRow={(row) => Number(row.penetration) < 25}
                />
              </div>
            </div>

            {/* Root Cause Analysis */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Root Cause Analysis</h3>
              <div className="prose prose-sm max-w-none">
                {dealerComparisonData.length > 0 ? (
                  <>
                    <p className="text-gray-700">
                      <strong>Analysis for {region} Region:</strong> {dealerComparisonData.length} dealers analyzed.
                      {dealerComparisonData.filter(d => d.change < 0).length > 0 && 
                        ` ${dealerComparisonData.filter(d => d.change < 0).length} dealers showing revenue decline.`
                      }
                    </p>
                    <ul className="mt-4 space-y-2">
                      {dealerComparisonData
                        .filter(dealer => dealer.change < -10)
                        .slice(0, 3)
                        .map((dealer, idx) => (
                          <li key={idx}>
                            <strong>{dealer.dealer}:</strong> Revenue down {Math.abs(dealer.change).toFixed(1)}% 
                            (${dealer.this_week.toLocaleString()} vs ${dealer.last_week.toLocaleString()}). 
                            Current penetration: {dealer.penetration}%.
                          </li>
                        ))
                      }
                      {managerBreakdown
                        .filter(manager => manager.penetration < 25)
                        .slice(0, 2)
                        .map((manager, idx) => (
                          <li key={`manager-${idx}`}>
                            <strong>{manager.manager} at {manager.dealer}:</strong> Penetration at {manager.penetration.toFixed(1)}% 
                            with {manager.transactions} transactions.
                          </li>
                        ))
                      }
                    </ul>
                  </>
                ) : (
                  <p className="text-gray-700">
                    <strong>Primary Driver:</strong> Service contract penetration analysis in progress. 
                    Data will be available once F&I dashboard loads.
                  </p>
                )}
                <div className="mt-6 p-4 bg-cox-blue-50 rounded-lg">
                  <h4 className="font-semibold text-cox-blue-900">Recommendations</h4>
                  <ol className="mt-2 space-y-1 text-cox-blue-800">
                    <li>1. Focus on dealers with penetration below 25%</li>
                    <li>2. Review service contract pricing and competitive positioning</li>
                    <li>3. Implement coaching for underperforming finance managers</li>
                    <li>4. Monitor weekly trends and adjust strategies accordingly</li>
                  </ol>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}