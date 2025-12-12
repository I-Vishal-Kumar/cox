'use client';

import { useState } from 'react';
import Header from '@/components/ui/Header';
import KPICard from '@/components/ui/KPICard';
import DataTable from '@/components/ui/DataTable';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import ErrorState from '@/components/ui/ErrorState';
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
  AreaChart,
  Area,
  Legend,
} from 'recharts';
import {
  BuildingOffice2Icon,
  ClockIcon,
  WrenchScrewdriverIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { 
  plantDashboardService, 
  PlantSummary, 
  DowntimeDetail, 
  CauseBreakdown 
} from '@/lib/api/plantDashboard';

const plantColumns = [
  { key: 'plant_name', header: 'Plant', align: 'left' as const },
  {
    key: 'total_downtime',
    header: 'Total Downtime',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className={Number(value) > 5 ? 'text-red-600 font-bold' : ''}>
        {Number(value).toFixed(1)} hrs
      </span>
    ),
  },
  { key: 'events', header: 'Events', align: 'right' as const, format: 'number' as const },
  {
    key: 'unplanned',
    header: 'Unplanned',
    align: 'right' as const,
    render: (value: unknown) => (
      <span className="text-red-600">{Number(value).toFixed(1)} hrs</span>
    ),
  },
];

const detailColumns = [
  { key: 'plant_name', header: 'Plant', align: 'left' as const },
  { key: 'line_number', header: 'Line', align: 'left' as const },
  {
    key: 'downtime_hours',
    header: 'Hours',
    align: 'right' as const,
    render: (value: unknown) => `${Number(value).toFixed(1)}`,
  },
  {
    key: 'reason_category',
    header: 'Category',
    align: 'left' as const,
    render: (value: unknown) => {
      const colors: Record<string, string> = {
        Maintenance: 'bg-blue-100 text-blue-700',
        Quality: 'bg-red-100 text-red-700',
        Supply: 'bg-yellow-100 text-yellow-700',
        Equipment: 'bg-green-100 text-green-700',
      };
      return (
        <span className={`px-2 py-1 text-xs font-medium rounded ${colors[String(value)] || ''}`}>
          {String(value)}
        </span>
      );
    },
  },
  { key: 'reason_detail', header: 'Details', align: 'left' as const },
  {
    key: 'supplier',
    header: 'Supplier',
    align: 'left' as const,
    render: (value: unknown) => value ? (
      <span className="text-orange-600 font-medium">{String(value)}</span>
    ) : '-',
  },
];

// Category colors for charts
const CATEGORY_COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function PlantAnalysisPage() {
  const [plantChartType, setPlantChartType] = useState<'bar' | 'pie' | 'line' | 'area'>('bar');
  const [causeChartType, setCauseChartType] = useState<'bar' | 'pie' | 'line' | 'area'>('pie');

  // Fetch plant dashboard data using TanStack Query
  const { data: plantData, isLoading, error } = useQuery({
    queryKey: ['plantDashboard'],
    queryFn: () => plantDashboardService.getPlantDashboard(),
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 2 * 60 * 1000, // Consider data stale after 2 minutes
  });

  // Transform data for display
  const plantSummary: PlantSummary[] = plantData?.plant_summary || [];
  const downtimeDetails: DowntimeDetail[] = plantData?.downtime_details || [];
  const causeBreakdown: CauseBreakdown[] = plantData?.cause_breakdown || [];
  const overallStats = plantData?.overall_stats || {
    total_downtime: 0,
    total_events: 0,
    unplanned_downtime: 0,
    plants_affected: 0,
  };

  // Find plant with most downtime for alert
  const criticalPlant = plantSummary.length > 0 
    ? plantSummary.reduce((max, plant) => 
        plant.total_downtime > max.total_downtime ? plant : max
      )
    : null;

  // Get critical plant details
  const criticalPlantDetails = criticalPlant 
    ? downtimeDetails.filter(d => d.plant_code === criticalPlant.plant_code)
    : [];

  // Calculate totals
  const totalDowntime = overallStats.total_downtime || 
    plantSummary.reduce((sum, p) => sum + p.total_downtime, 0);
  const totalUnplanned = overallStats.unplanned_downtime || 
    plantSummary.reduce((sum, p) => sum + p.unplanned, 0);

  // Chart update handler
  const handleChartUpdate = (chartId: string, updates: { type?: string; data?: any }) => {
    if (updates.type) {
      if (chartId === 'plant-downtime') {
        setPlantChartType(updates.type as 'bar' | 'pie' | 'line' | 'area');
      } else if (chartId === 'cause-breakdown') {
        setCauseChartType(updates.type as 'bar' | 'pie' | 'line' | 'area');
      }
    }
  };

  // Chart context for the bot
  const chartContext = {
    page: 'Plant Downtime Analysis',
    charts: [
      {
        id: 'plant-downtime',
        title: 'Downtime by Plant',
        type: plantChartType,
        data: plantSummary.map(p => ({
          plant: p.plant_name,
          total: p.total_downtime,
          unplanned: p.unplanned,
        })),
      },
      {
        id: 'cause-breakdown',
        title: 'Cause Breakdown',
        type: causeChartType,
        data: causeBreakdown,
      },
    ],
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-screen">
        <Header
          title="Plant Downtime Analysis"
          subtitle="Cox Automotive • Manufacturing plant downtime and root cause analysis"
        />
        <div className="flex-1 p-6 overflow-auto">
          <LoadingSkeleton variant="card" rows={8} />
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="flex flex-col h-screen">
        <Header
          title="Plant Downtime Analysis"
          subtitle="Cox Automotive • Manufacturing plant downtime and root cause analysis"
        />
        <div className="flex-1 p-6 overflow-auto">
          <ErrorState
            title="Failed to load plant downtime data"
            message="There was an error loading the plant downtime analysis data."
            onRetry={() => window.location.reload()}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Plant Downtime Analysis"
        subtitle="Cox Automotive • Manufacturing plant downtime and root cause analysis"
      />
      <div className="flex-1 p-6 overflow-auto space-y-6">
        {/* Alert Banner */}
        {criticalPlant && criticalPlant.total_downtime > 5 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-red-800">
                {criticalPlant.plant_name} - Critical Downtime
              </h3>
              <p className="text-sm text-red-700 mt-1">
                {criticalPlant.total_downtime.toFixed(1)} hours of downtime this week. 
                {criticalPlantDetails.length > 0 && (
                  <>
                    {' '}
                    {criticalPlantDetails[0].reason_category} issues on {criticalPlantDetails[0].line_number}.
                    {criticalPlantDetails[0].reason_category === 'Quality' && ' Immediate root cause investigation recommended.'}
                  </>
                )}
              </p>
            </div>
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4">
          <KPICard
            title="Total Downtime"
            value={`${totalDowntime.toFixed(1)} hrs`}
            icon={<ClockIcon className="w-6 h-6" />}
          />
          <KPICard
            title="Unplanned Downtime"
            value={`${totalUnplanned.toFixed(1)} hrs`}
            icon={<ExclamationTriangleIcon className="w-6 h-6" />}
          />
          <KPICard
            title="Plants Affected"
            value={overallStats.plants_affected || plantSummary.length}
            icon={<BuildingOffice2Icon className="w-6 h-6" />}
          />
          <KPICard
            title="Total Events"
            value={overallStats.total_events || downtimeDetails.length}
            icon={<WrenchScrewdriverIcon className="w-6 h-6" />}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-3 gap-6">
          {/* Plant Downtime Chart */}
          <div className="col-span-2 bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Downtime by Plant
            </h3>
            <div className="h-64">
              {plantSummary.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  {plantChartType === 'bar' ? (
                    <BarChart data={plantSummary.map(p => ({
                      plant: p.plant_name,
                      total: p.total_downtime,
                      unplanned: p.unplanned,
                    }))} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="plant" type="category" width={150} />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Legend />
                      <Bar dataKey="total" name="Total" fill="#3b82f6" />
                      <Bar dataKey="unplanned" name="Unplanned" fill="#ef4444" />
                    </BarChart>
                  ) : plantChartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={plantSummary.map(p => ({
                          name: p.plant_name,
                          value: p.total_downtime,
                        }))}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name.substring(0, 15)} (${(percent * 100).toFixed(0)}%)`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {plantSummary.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                    </PieChart>
                  ) : plantChartType === 'line' ? (
                    <LineChart data={plantSummary.map(p => ({
                      plant: p.plant_name,
                      total: p.total_downtime,
                      unplanned: p.unplanned,
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="plant" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Legend />
                      <Line type="monotone" dataKey="total" stroke="#3b82f6" strokeWidth={2} name="Total" />
                      <Line type="monotone" dataKey="unplanned" stroke="#ef4444" strokeWidth={2} name="Unplanned" />
                    </LineChart>
                  ) : (
                    <AreaChart data={plantSummary.map(p => ({
                      plant: p.plant_name,
                      total: p.total_downtime,
                      unplanned: p.unplanned,
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="plant" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Legend />
                      <Area type="monotone" dataKey="total" stackId="1" stroke="#3b82f6" fill="#3b82f6" name="Total" />
                      <Area type="monotone" dataKey="unplanned" stackId="2" stroke="#ef4444" fill="#ef4444" name="Unplanned" />
                    </AreaChart>
                  )}
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <p>No plant data available</p>
                </div>
              )}
            </div>
          </div>

          {/* Cause Breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Cause Breakdown
            </h3>
            <div className="h-64">
              {causeBreakdown.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  {causeChartType === 'pie' ? (
                    <PieChart>
                      <Pie
                        data={causeBreakdown}
                        cx="50%"
                        cy="50%"
                        innerRadius={40}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}h`}
                      >
                        {causeBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                    </PieChart>
                  ) : causeChartType === 'bar' ? (
                    <BarChart data={causeBreakdown}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Bar dataKey="value" fill="#3b82f6">
                        {causeBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  ) : causeChartType === 'line' ? (
                    <LineChart data={causeBreakdown}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2}>
                        {causeBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Line>
                    </LineChart>
                  ) : (
                    <AreaChart data={causeBreakdown}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                      <Area type="monotone" dataKey="value" stroke="#3b82f6" fill="#3b82f6" />
                    </AreaChart>
                  )}
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  <p>No cause breakdown data available</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Tables */}
        <div className="grid grid-cols-2 gap-6">
          {/* Plant Summary */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Plant Summary
            </h3>
            {plantSummary.length > 0 ? (
              <DataTable
                columns={plantColumns}
                data={plantSummary}
                highlightRow={(row) => Number(row.total_downtime) > 5}
              />
            ) : (
              <p className="text-gray-400 text-center py-8">No plant summary data available</p>
            )}
          </div>

          {/* Cause Legend */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Cause Categories
            </h3>
            {causeBreakdown.length > 0 ? (
              <div className="space-y-4">
                {causeBreakdown.map((cause) => (
                  <div key={cause.name} className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div
                        className="w-4 h-4 rounded mr-3"
                        style={{ backgroundColor: cause.color }}
                      />
                      <span className="font-medium">{cause.name}</span>
                    </div>
                    <span className="text-gray-600">{cause.value.toFixed(1)} hours</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-400 text-center py-8">No cause breakdown data available</p>
            )}
          </div>
        </div>

        {/* Detail Table */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Downtime Events Detail
          </h3>
          {downtimeDetails.length > 0 ? (
            <DataTable
              columns={detailColumns}
              data={downtimeDetails}
              highlightRow={(row) => Number(row.downtime_hours) > 3}
            />
          ) : (
            <p className="text-gray-400 text-center py-8">No downtime events data available</p>
          )}
        </div>

        {/* Root Cause Analysis */}
        {criticalPlant && criticalPlantDetails.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Root Cause Analysis & Recommendations</h3>
            <div className="grid grid-cols-3 gap-4">
              {plantSummary.slice(0, 3).map((plant, index) => {
                const plantDetails = downtimeDetails.filter(d => d.plant_code === plant.plant_code);
                const isCritical = plant.total_downtime > 5;
                const hasQuality = plantDetails.some(d => d.reason_category === 'Quality');
                const hasSupply = plantDetails.some(d => d.reason_category === 'Supply' && d.supplier);
                
                let bgColor = 'bg-blue-50';
                let borderColor = 'border-blue-200';
                let textColor = 'text-blue-800';
                let title = plant.plant_name;
                
                if (isCritical && hasQuality) {
                  bgColor = 'bg-red-50';
                  borderColor = 'border-red-200';
                  textColor = 'text-red-800';
                  title = `${plant.plant_name} - Critical`;
                } else if (hasSupply) {
                  bgColor = 'bg-yellow-50';
                  borderColor = 'border-yellow-200';
                  textColor = 'text-yellow-800';
                  title = `${plant.plant_name} - Supply Chain`;
                }
                
                return (
                  <div key={plant.plant_code} className={`p-4 ${bgColor} rounded-lg border ${borderColor}`}>
                    <h4 className={`font-semibold ${textColor}`}>{title}</h4>
                    {plantDetails.length > 0 && (
                      <>
                        <p className={`text-sm ${textColor.replace('800', '700')} mt-2`}>
                          <strong>Issue:</strong> {plantDetails[0].reason_category} - {plantDetails[0].reason_detail}
                        </p>
                        <ul className={`mt-2 space-y-1 text-sm ${textColor.replace('800', '700')}`}>
                          {hasQuality && (
                            <>
                              <li>• Fast-track root cause analysis</li>
                              <li>• Check quality control processes</li>
                            </>
                          )}
                          {hasSupply && (
                            <>
                              <li>• Review PO lead times</li>
                              <li>• Increase safety stock</li>
                              <li>• Identify alternate supplier</li>
                            </>
                          )}
                          {!hasQuality && !hasSupply && (
                            <>
                              <li>• Review maintenance scheduling</li>
                              <li>• Consider predictive maintenance</li>
                            </>
                          )}
                        </ul>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot 
        pageContext={chartContext}
        onChartUpdate={handleChartUpdate}
      />
    </div>
  );
}
