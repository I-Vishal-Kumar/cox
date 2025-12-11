'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import ErrorState from '@/components/ui/ErrorState';
import { inviteDashboardService, transformCampaignData, transformMonthlyData } from '@/lib/api/inviteDashboard';
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
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import KPICard from '@/components/ui/KPICard';
import DataTable from '@/components/ui/DataTable';
import GaugeChart from '@/components/ui/GaugeChart';
import {
  EnvelopeIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  EyeIcon,
  WrenchScrewdriverIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

// Mock data matching the Invite dashboard from PDF
const programPerformanceData = [
  { campaign_name: '1st Service Due', category: 'Service Reminder', emails_sent: 2145, unique_opens: 687, open_rate: 32.0, ro_count: 89, revenue: 26700 },
  { campaign_name: '6-Month Checkup', category: 'Service Reminder', emails_sent: 1823, unique_opens: 547, open_rate: 30.0, ro_count: 71, revenue: 19880 },
  { campaign_name: 'A Service Due', category: 'Maintenance', emails_sent: 1567, unique_opens: 438, open_rate: 28.0, ro_count: 52, revenue: 18200 },
  { campaign_name: 'Alignment Check', category: 'Maintenance', emails_sent: 1342, unique_opens: 375, open_rate: 27.9, ro_count: 45, revenue: 9900 },
  { campaign_name: 'B Service Due', category: 'Maintenance', emails_sent: 1298, unique_opens: 350, open_rate: 27.0, ro_count: 42, revenue: 14700 },
  { campaign_name: 'Battery Check', category: 'Seasonal', emails_sent: 1876, unique_opens: 525, open_rate: 28.0, ro_count: 63, revenue: 11970 },
  { campaign_name: 'Brake Service', category: 'Safety', emails_sent: 987, unique_opens: 276, open_rate: 28.0, ro_count: 33, revenue: 13200 },
  { campaign_name: 'C Service Due', category: 'Maintenance', emails_sent: 1145, unique_opens: 309, open_rate: 27.0, ro_count: 37, revenue: 12950 },
  { campaign_name: 'Cabin Air Filter', category: 'Maintenance', emails_sent: 1432, unique_opens: 401, open_rate: 28.0, ro_count: 48, revenue: 7200 },
  { campaign_name: 'Coolant Flush', category: 'Maintenance', emails_sent: 1198, unique_opens: 335, open_rate: 28.0, ro_count: 40, revenue: 8000 },
  { campaign_name: 'D Service Due', category: 'Maintenance', emails_sent: 1087, unique_opens: 294, open_rate: 27.0, ro_count: 35, revenue: 12250 },
  { campaign_name: 'Declined Service Follow-up', category: 'Follow-up', emails_sent: 2341, unique_opens: 702, open_rate: 30.0, ro_count: 84, revenue: 21000 },
  { campaign_name: 'Engine Air Filter', category: 'Maintenance', emails_sent: 1543, unique_opens: 432, open_rate: 28.0, ro_count: 52, revenue: 7800 },
  { campaign_name: 'Express Lube', category: 'Quick Service', emails_sent: 2876, unique_opens: 920, open_rate: 32.0, ro_count: 110, revenue: 8250 },
  { campaign_name: 'Factory Scheduled Maintenance', category: 'Maintenance', emails_sent: 1654, unique_opens: 463, open_rate: 28.0, ro_count: 56, revenue: 22400 },
  { campaign_name: 'Multi Point Inspection Due', category: 'Inspection', emails_sent: 1987, unique_opens: 596, open_rate: 30.0, ro_count: 72, revenue: 14400 },
  { campaign_name: 'Oil Change', category: 'Quick Service', emails_sent: 3245, unique_opens: 1038, open_rate: 32.0, ro_count: 125, revenue: 9375 },
  { campaign_name: 'Tire Rotation', category: 'Quick Service', emails_sent: 2654, unique_opens: 797, open_rate: 30.0, ro_count: 96, revenue: 4800 },
  { campaign_name: 'Transmission Service', category: 'Maintenance', emails_sent: 876, unique_opens: 245, open_rate: 28.0, ro_count: 29, revenue: 11600 },
  { campaign_name: 'Winter Prep', category: 'Seasonal', emails_sent: 1654, unique_opens: 463, open_rate: 28.0, ro_count: 56, revenue: 16800 },
];

const monthlyData = [
  { month: 'Jul', emails: 28500, opens: 8550, ro: 1026, revenue: 168570 },
  { month: 'Aug', emails: 29200, opens: 8760, ro: 1051, revenue: 159533 },
  { month: 'Sep', emails: 31500, opens: 9450, ro: 1134, revenue: 180360 },
  { month: 'Oct', emails: 32100, opens: 9630, ro: 1156, revenue: 190460 },
  { month: 'Nov', emails: 30800, opens: 9240, ro: 1109, revenue: 175510 },
  { month: 'Dec', emails: 29500, opens: 8850, ro: 1062, revenue: 164740 },
];

const columns = [
  { key: 'campaign_name', header: 'Program', align: 'left' as const },
  { key: 'category', header: 'Category', align: 'left' as const },
  { key: 'emails_sent', header: 'Emails Sent', align: 'right' as const, format: 'number' as const },
  { key: 'unique_opens', header: 'Unique Opens', align: 'right' as const, format: 'number' as const },
  {
    key: 'open_rate',
    header: 'Open Rate',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className="text-green-600 font-medium">{Number(value).toFixed(1)}%</span>
    ),
  },
  { key: 'ro_count', header: 'RO Count', align: 'right' as const, format: 'number' as const },
  { key: 'revenue', header: 'Revenue', align: 'right' as const, format: 'currency' as const },
];

// Category colors for pie chart
const CATEGORY_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function InviteDashboard() {
  const [filter, setFilter] = useState('all');
  const [dateRange, setDateRange] = useState('Dec 2024');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch invite dashboard data
  const { data: inviteData, isLoading, error } = useQuery({
    queryKey: ['inviteDashboard', dateRange],
    queryFn: () => inviteDashboardService.getInviteDashboard(dateRange),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  });

  // Fetch campaign performance data using chat API
  const { data: campaignData, isLoading: campaignLoading, error: campaignError } = useQuery({
    queryKey: ['inviteCampaigns', dateRange, filter],
    queryFn: () => inviteDashboardService.getCampaignPerformance({ 
      dateRange, 
      category: filter 
    }),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Fetch monthly trends data using chat API
  const { data: monthlyTrendsData, isLoading: trendsLoading, error: trendsError } = useQuery({
    queryKey: ['inviteMonthlyTrends'],
    queryFn: () => inviteDashboardService.getMonthlyTrends(6),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Fetch enhanced KPI data using chat API
  const { data: enhancedKPIData, isLoading: kpiLoading, error: kpiError } = useQuery({
    queryKey: ['inviteEnhancedKPI', dateRange],
    queryFn: () => inviteDashboardService.getEnhancedKPIData(dateRange),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Transform data for frontend use
  const campaignPerformanceData = campaignData?.map(transformCampaignData) || programPerformanceData;
  
  // Debug logging
  console.log('Campaign data from API:', campaignData);
  console.log('Transformed campaign data:', campaignPerformanceData);
  console.log('Enhanced KPI data:', enhancedKPIData);
  const monthlyData = monthlyTrendsData?.map(transformMonthlyData) || [
    { month: 'Jul', emails: 28500, opens: 8550, ro: 1026, revenue: 168570 },
    { month: 'Aug', emails: 29200, opens: 8760, ro: 1051, revenue: 159533 },
    { month: 'Sep', emails: 31500, opens: 9450, ro: 1134, revenue: 180360 },
    { month: 'Oct', emails: 32100, opens: 9630, ro: 1156, revenue: 190460 },
    { month: 'Nov', emails: 30800, opens: 9240, ro: 1109, revenue: 175510 },
    { month: 'Dec', emails: 29500, opens: 8850, ro: 1062, revenue: 164740 },
  ];

  // Calculate summary metrics from live or fallback data with NaN protection
  const campaignTotals = {
    emails: campaignPerformanceData.reduce((sum, p) => sum + (p.emails_sent || 0), 0),
    opens: campaignPerformanceData.reduce((sum, p) => sum + (p.unique_opens || 0), 0),
    ros: campaignPerformanceData.reduce((sum, p) => sum + (p.ro_count || 0), 0),
    revenue: campaignPerformanceData.reduce((sum, p) => sum + (p.revenue || 0), 0),
  };

  const summary = {
    totalEmails: enhancedKPIData?.total_emails_sent || campaignTotals.emails || 35000,
    totalOpens: enhancedKPIData?.total_unique_opens || campaignTotals.opens || 10500,
    totalROs: enhancedKPIData?.total_ro_count || campaignTotals.ros || 1200,
    totalRevenue: enhancedKPIData?.total_revenue || campaignTotals.revenue || 300000,
  };

  // Protect against NaN in open rate calculation
  const avgOpenRate = enhancedKPIData?.avg_open_rate || 
    (summary.totalEmails > 0 ? (summary.totalOpens / summary.totalEmails) * 100 : 30);

  // Filter data based on category
  const filteredData =
    filter === 'all'
      ? campaignPerformanceData
      : campaignPerformanceData.filter((p) => p.category === filter);

  const categories = Array.from(new Set(campaignPerformanceData.map((p) => p.category)));

  // Category breakdown for pie chart using live data
  const categoryBreakdown = categories.map((cat, index) => ({
    name: cat,
    value: campaignPerformanceData.filter((p) => p.category === cat).reduce((sum, p) => sum + (p.revenue || 0), 0),
    color: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
  }));

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Trigger refetch for all queries
    window.location.reload(); // Simple approach to refresh all data
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  // Show loading state while main data is loading
  if (isLoading || campaignLoading) {
    return <LoadingSkeleton variant="card" rows={8} />;
  }

  // Show error state if there's a critical error
  if (error) {
    return (
      <ErrorState 
        title="Failed to load Invite Dashboard data"
        message="There was an error loading the invite dashboard data."
        onRetry={() => window.location.reload()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="bg-gradient-to-r from-cox-blue-600 to-cox-blue-800 rounded-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Xtime Invite Dashboard</h1>
            <p className="text-cox-blue-100 mt-1">Service Marketing Campaign Performance</p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-right">
              <p className="text-sm text-cox-blue-100">Last Updated</p>
              <p className="font-medium">Dec 8, 2024 at 9:15 AM</p>
            </div>
            <button
              onClick={handleRefresh}
              className="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
              disabled={isRefreshing}
            >
              <ArrowPathIcon className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Filters Row */}
      <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <CalendarDaysIcon className="w-5 h-5 text-gray-400" />
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
            >
              <option>Dec 2024</option>
              <option>Nov 2024</option>
              <option>Oct 2024</option>
              <option>Q4 2024</option>
              <option>2024</option>
            </select>
          </div>

          <div className="h-6 w-px bg-gray-200" />

          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
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
          <button className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg border border-gray-200">
            Export CSV
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 hover:bg-cox-blue-700 rounded-lg">
            + Create Campaign
          </button>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        <KPICard
          title="Emails Sent"
          value={summary.totalEmails}
          change={enhancedKPIData?.emails_sent_change || 11.2}
          changeLabel="vs last month"
          icon={<EnvelopeIcon className="w-6 h-6 text-blue-500" />}
        />
        <KPICard
          title="Unique Opens"
          value={summary.totalOpens}
          change={enhancedKPIData?.opens_change || 8.5}
          changeLabel="vs last month"
          icon={<EyeIcon className="w-6 h-6 text-green-500" />}
        />
        <KPICard
          title="Open Rate"
          value={avgOpenRate}
          format="percent"
          change={enhancedKPIData?.open_rate_change || 2.3}
          changeLabel="vs last month"
          icon={<DocumentTextIcon className="w-6 h-6 text-purple-500" />}
        />
        <KPICard
          title="Repair Orders"
          value={summary.totalROs}
          change={enhancedKPIData?.ro_count_change || 5.8}
          changeLabel="vs last month"
          icon={<WrenchScrewdriverIcon className="w-6 h-6 text-orange-500" />}
        />
        <KPICard
          title="Revenue"
          value={summary.totalRevenue}
          format="currency"
          change={enhancedKPIData?.revenue_change || 9.3}
          changeLabel="vs last month"
          icon={<CurrencyDollarIcon className="w-6 h-6 text-emerald-500" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-6">
        {/* Program Performance Summary - Top 10 by Revenue */}
        <div className="col-span-7 bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Top Programs by Revenue</h3>
            <div className="flex items-center space-x-2">
              {campaignLoading && (
                <div className="text-sm text-gray-500">Loading campaigns...</div>
              )}
              {campaignError && (
                <div className="text-sm text-red-600">Failed to load campaigns</div>
              )}
              <span className="text-sm text-gray-500">Top 10 campaigns</span>
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={filteredData.slice(0, 10)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis
                  type="number"
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <YAxis
                  dataKey="campaign_name"
                  type="category"
                  width={140}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip
                  formatter={(value: number) =>
                    new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(value)
                  }
                  labelStyle={{ fontWeight: 'bold' }}
                />
                <Bar dataKey="revenue" fill="#3b82f6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Pie Chart */}
        <div className="col-span-5 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Category</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryBreakdown}
                  cx="50%"
                  cy="45%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  labelLine={false}
                >
                  {categoryBreakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) =>
                    new Intl.NumberFormat('en-US', {
                      style: 'currency',
                      currency: 'USD',
                    }).format(value)
                  }
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Open Rate Gauges Row */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-4 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Channel Performance</h3>
          <div className="flex justify-around items-center">
            <GaugeChart value={isNaN(avgOpenRate) ? 30 : Math.round(avgOpenRate)} label="Email" color="#3b82f6" />
            <GaugeChart value={65} label="SMS" color="#f97316" />
            <GaugeChart value={42} label="Direct Mail" color="#10b981" />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-gray-500">
            <div>
              <p className="font-medium text-gray-900">{summary.totalEmails.toLocaleString()}</p>
              <p>Sent</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">8,542</p>
              <p>Sent</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">4,218</p>
              <p>Sent</p>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="col-span-8 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Highlights</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-blue-600 font-medium">Best Performing</p>
              <p className="text-lg font-bold text-gray-900 mt-1">1st Service Due</p>
              <p className="text-sm text-gray-500">32% open rate</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-green-600 font-medium">Highest Revenue</p>
              <p className="text-lg font-bold text-gray-900 mt-1">Oil Change</p>
              <p className="text-sm text-gray-500">$26,700 generated</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-purple-600 font-medium">Most ROs</p>
              <p className="text-lg font-bold text-gray-900 mt-1">Oil Change</p>
              <p className="text-sm text-gray-500">125 repair orders</p>
            </div>
            <div className="bg-orange-50 rounded-lg p-4">
              <p className="text-sm text-orange-600 font-medium">Avg RO Value</p>
              <p className="text-lg font-bold text-gray-900 mt-1">$183.42</p>
              <p className="text-sm text-gray-500">+5.2% vs last month</p>
            </div>
          </div>
        </div>
      </div>

      {/* Monthly Trend Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Monthly Trend</h3>
          {trendsLoading && (
            <div className="text-sm text-gray-500">Loading trends...</div>
          )}
          {trendsError && (
            <div className="text-sm text-red-600">Failed to load trends</div>
          )}
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="emails"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
                name="Emails"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="revenue"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ fill: '#10b981' }}
                name="Revenue"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Program Performance Table */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Program Details</h3>
          <div className="text-sm text-gray-500">
            Showing {filteredData.length} programs
          </div>
        </div>
        <DataTable
          columns={columns}
          data={filteredData}
          striped
          highlightRow={(row) => Number(row.open_rate) > 30}
        />
      </div>
    </div>
  );
}
