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
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  EnvelopeIcon,
  CurrencyDollarIcon,
  DocumentTextIcon,
  EyeIcon,
  WrenchScrewdriverIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

// Removed hardcoded data - now using data from backend API

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
  const [topProgramsChartType, setTopProgramsChartType] = useState<'bar' | 'pie' | 'line' | 'area'>('bar');
  const [categoryChartType, setCategoryChartType] = useState<'bar' | 'pie' | 'line' | 'area'>('pie');

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

  // Use data from direct REST API endpoint (primary source)
  const campaignPerformanceData = inviteData?.campaign_performance && inviteData.campaign_performance.length > 0
    ? inviteData.campaign_performance.map(transformCampaignData)
    : (campaignData && campaignData.length > 0 
        ? campaignData.map(transformCampaignData) 
        : []); // Empty array instead of hardcoded data
  
  // Use monthly data from direct REST API endpoint (primary source)
  const monthlyData = inviteData?.monthly_trends && inviteData.monthly_trends.length > 0
    ? inviteData.monthly_trends.map(transformMonthlyData)
    : (monthlyTrendsData?.map(transformMonthlyData) || []); // Empty array instead of hardcoded data

  // Calculate summary metrics from live data with NaN protection
  const campaignTotals = campaignPerformanceData.length > 0 ? {
    emails: campaignPerformanceData.reduce((sum, p) => sum + (p.emails_sent || 0), 0),
    opens: campaignPerformanceData.reduce((sum, p) => sum + (p.unique_opens || 0), 0),
    ros: campaignPerformanceData.reduce((sum, p) => sum + (p.ro_count || 0), 0),
    revenue: campaignPerformanceData.reduce((sum, p) => sum + (p.revenue || 0), 0),
  } : { emails: 0, opens: 0, ros: 0, revenue: 0 };

  // Use data from inviteData (direct REST API) if available, otherwise from enhanced KPI or calculated totals
  const programSummary = inviteData?.program_summary || {};
  const summary = {
    totalEmails: enhancedKPIData?.total_emails_sent || programSummary.total_emails || campaignTotals.emails || 0,
    totalOpens: enhancedKPIData?.total_unique_opens || programSummary.total_opens || campaignTotals.opens || 0,
    totalROs: enhancedKPIData?.total_ro_count || programSummary.total_ros || campaignTotals.ros || 0,
    totalRevenue: enhancedKPIData?.total_revenue || programSummary.total_revenue || campaignTotals.revenue || 0,
  };

  // Protect against NaN in open rate calculation
  const avgOpenRate = enhancedKPIData?.avg_open_rate || 
    programSummary.avg_open_rate ||
    (summary.totalEmails > 0 ? (summary.totalOpens / summary.totalEmails) * 100 : 0);

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

  const handleChartUpdate = (chartId: string, updates: { type?: string; data?: any }) => {
    if (updates.type) {
      if (chartId === 'top-programs') {
        setTopProgramsChartType(updates.type as 'bar' | 'pie' | 'line' | 'area');
      } else if (chartId === 'category-breakdown') {
        setCategoryChartType(updates.type as 'bar' | 'pie' | 'line' | 'area');
      }
    }
  };

  // Chart context for the bot
  const chartContext = {
    page: 'Invite Dashboard',
    charts: [
      {
        id: 'top-programs',
        title: 'Top Programs by Revenue',
        type: topProgramsChartType,
        data: filteredData.slice(0, 10),
      },
      {
        id: 'category-breakdown',
        title: 'Revenue by Category',
        type: categoryChartType,
        data: categoryBreakdown,
      },
    ],
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
      <div className="bg-gradient-to-r from-cox-blue-600 to-cox-blue-800 rounded-lg p-6 text-white shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
              <EnvelopeIcon className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-bold">Invite Dashboard</h1>
                <span className="text-xs bg-white/20 px-2 py-1 rounded-full">Cox Automotive</span>
              </div>
              <p className="text-cox-blue-100 mt-1">Service Marketing Campaign Performance • Powered by Xtime</p>
            </div>
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
          change={enhancedKPIData?.emails_sent_change ?? 0}
          changeLabel="vs last month"
          icon={<EnvelopeIcon className="w-6 h-6 text-blue-500" />}
        />
        <KPICard
          title="Unique Opens"
          value={summary.totalOpens}
          change={enhancedKPIData?.opens_change ?? 0}
          changeLabel="vs last month"
          icon={<EyeIcon className="w-6 h-6 text-green-500" />}
        />
        <KPICard
          title="Open Rate"
          value={avgOpenRate}
          format="percent"
          change={enhancedKPIData?.open_rate_change ?? 0}
          changeLabel="vs last month"
          icon={<DocumentTextIcon className="w-6 h-6 text-purple-500" />}
        />
        <KPICard
          title="Repair Orders"
          value={summary.totalROs}
          change={enhancedKPIData?.ro_count_change ?? 0}
          changeLabel="vs last month"
          icon={<WrenchScrewdriverIcon className="w-6 h-6 text-orange-500" />}
        />
        <KPICard
          title="Revenue"
          value={summary.totalRevenue}
          format="currency"
          change={enhancedKPIData?.revenue_change ?? 0}
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
            {filteredData && filteredData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                {topProgramsChartType === 'bar' ? (
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
                ) : topProgramsChartType === 'pie' ? (
                  <PieChart>
                    <Pie
                      data={filteredData.slice(0, 10)}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ campaign_name, percent }) => `${campaign_name.substring(0, 15)} (${(percent * 100).toFixed(0)}%)`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="revenue"
                    >
                      {filteredData.slice(0, 10).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
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
                ) : topProgramsChartType === 'line' ? (
                  <LineChart data={filteredData.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="campaign_name" angle={-45} textAnchor="end" height={100} />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: number) =>
                        new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                        }).format(value)
                      }
                    />
                    <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                ) : (
                  <BarChart data={filteredData.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="campaign_name" angle={-45} textAnchor="end" height={100} />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: number) =>
                        new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                        }).format(value)
                      }
                    />
                    <Bar dataKey="revenue" fill="#3b82f6" />
                  </BarChart>
                )}
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No data available</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Category Breakdown Pie Chart */}
        <div className="col-span-5 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Category</h3>
          <div className="h-72">
            {categoryBreakdown && categoryBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                {categoryChartType === 'pie' ? (
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
                ) : categoryChartType === 'bar' ? (
                  <BarChart data={categoryBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: number) =>
                        new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                        }).format(value)
                      }
                    />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                ) : categoryChartType === 'line' ? (
                  <LineChart data={categoryBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value: number) =>
                        new Intl.NumberFormat('en-US', {
                          style: 'currency',
                          currency: 'USD',
                        }).format(value)
                      }
                    />
                    <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                ) : (
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
                )}
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <ChartBarIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No data available</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Open Rate Gauges Row */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-4 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Channel Performance</h3>
          <div className="flex justify-around items-center">
            <GaugeChart 
              value={isNaN(avgOpenRate) ? 30 : Math.round(avgOpenRate)} 
              label="Email" 
              color="#3b82f6" 
            />
            <GaugeChart 
              value={inviteData?.channel_performance?.sms?.open_rate 
                ? Math.round(inviteData.channel_performance.sms.open_rate) 
                : 0} 
              label="SMS" 
              color="#f97316" 
            />
            <GaugeChart 
              value={inviteData?.channel_performance?.direct_mail?.open_rate 
                ? Math.round(inviteData.channel_performance.direct_mail.open_rate) 
                : 0} 
              label="Direct Mail" 
              color="#10b981" 
            />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2 text-center text-xs text-gray-500">
            <div>
              <p className="font-medium text-gray-900">
                {inviteData?.channel_performance?.email?.total_sent 
                  ? inviteData.channel_performance.email.total_sent.toLocaleString() 
                  : summary.totalEmails.toLocaleString()}
              </p>
              <p>Email Sent</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {inviteData?.channel_performance?.sms?.total_sent 
                  ? inviteData.channel_performance.sms.total_sent.toLocaleString() 
                  : 'N/A'}
              </p>
              <p>SMS Sent</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {inviteData?.channel_performance?.direct_mail?.total_sent 
                  ? inviteData.channel_performance.direct_mail.total_sent.toLocaleString() 
                  : 'N/A'}
              </p>
              <p>Direct Mail Sent</p>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="col-span-8 bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Highlights</h3>
          <div className="grid grid-cols-4 gap-4">
            {campaignPerformanceData.length > 0 ? (
              <>
                {(() => {
                  const bestOpenRate = [...campaignPerformanceData].sort((a, b) => (b.open_rate || 0) - (a.open_rate || 0))[0];
                  const highestRevenue = [...campaignPerformanceData].sort((a, b) => (b.revenue || 0) - (a.revenue || 0))[0];
                  const mostROs = [...campaignPerformanceData].sort((a, b) => (b.ro_count || 0) - (a.ro_count || 0))[0];
                  const avgROValue = summary.totalROs > 0 ? summary.totalRevenue / summary.totalROs : 0;
                  // Use real data from enhanced KPI, fallback to calculated change if available
                  const roValueChange = enhancedKPIData?.ro_count_change ?? 
                    (enhancedKPIData?.revenue_change ?? 0);
                  
                  return (
                    <>
                      <div className="bg-blue-50 rounded-lg p-4">
                        <p className="text-sm text-blue-600 font-medium">Best Performing</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">{bestOpenRate?.campaign_name || 'N/A'}</p>
                        <p className="text-sm text-gray-500">{bestOpenRate?.open_rate?.toFixed(1) || 0}% open rate</p>
                      </div>
                      <div className="bg-green-50 rounded-lg p-4">
                        <p className="text-sm text-green-600 font-medium">Highest Revenue</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">{highestRevenue?.campaign_name || 'N/A'}</p>
                        <p className="text-sm text-gray-500">${(highestRevenue?.revenue || 0).toLocaleString()} generated</p>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-4">
                        <p className="text-sm text-purple-600 font-medium">Most ROs</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">{mostROs?.campaign_name || 'N/A'}</p>
                        <p className="text-sm text-gray-500">{mostROs?.ro_count || 0} repair orders</p>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-4">
                        <p className="text-sm text-orange-600 font-medium">Avg RO Value</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">${avgROValue.toFixed(2)}</p>
                        <p className="text-sm text-gray-500">
                          {roValueChange !== 0 
                            ? `${roValueChange > 0 ? '+' : ''}${roValueChange.toFixed(1)}% vs last month`
                            : enhancedKPIData?.revenue_change !== undefined
                              ? `${enhancedKPIData.revenue_change > 0 ? '+' : ''}${enhancedKPIData.revenue_change.toFixed(1)}% vs last month`
                              : 'No change'}
                        </p>
                      </div>
                    </>
                  );
                })()}
              </>
            ) : (
              <div className="col-span-4 text-center text-gray-400 py-4">
                No performance data available
              </div>
            )}
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

      {/* Floating Chat Bot */}
      <FloatingChatBot 
        pageContext={chartContext}
        onChartUpdate={handleChartUpdate}
      />
    </div>
  );
}
