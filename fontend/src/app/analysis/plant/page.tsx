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
  BuildingOffice2Icon,
  ClockIcon,
  WrenchScrewdriverIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

// Mock plant downtime data
const plantSummary = [
  { plant: 'Plant A - Michigan', code: 'PLANT-A', total_downtime: 6.5, events: 4, unplanned: 5.3 },
  { plant: 'Plant B - Ohio', code: 'PLANT-B', total_downtime: 4.2, events: 1, unplanned: 4.2 },
  { plant: 'Plant C - Indiana', code: 'PLANT-C', total_downtime: 2.3, events: 1, unplanned: 0.8 },
];

const downtimeDetails = [
  { plant: 'Plant A', line: 'Line 3', hours: 3.1, category: 'Maintenance', detail: 'Unplanned conveyor maintenance', supplier: null },
  { plant: 'Plant A', line: 'Line 3', hours: 2.2, category: 'Quality', detail: 'Paint defects quality hold', supplier: null },
  { plant: 'Plant A', line: 'Line 1', hours: 0.8, category: 'Equipment', detail: 'Robotic arm calibration', supplier: null },
  { plant: 'Plant A', line: 'Line 2', hours: 0.4, category: 'Maintenance', detail: 'Belt replacement (planned)', supplier: null },
  { plant: 'Plant B', line: 'Line 1', hours: 4.2, category: 'Supply', detail: 'Component shortage - ECUs', supplier: 'Supplier Q' },
  { plant: 'Plant C', line: 'Line 2', hours: 2.3, category: 'Maintenance', detail: 'Planned maintenance overrun', supplier: null },
];

const causeBreakdown = [
  { name: 'Maintenance', value: 5.8, color: '#3b82f6' },
  { name: 'Quality', value: 2.2, color: '#ef4444' },
  { name: 'Supply', value: 4.2, color: '#f59e0b' },
  { name: 'Equipment', value: 0.8, color: '#10b981' },
];

const plantColumns = [
  { key: 'plant', header: 'Plant', align: 'left' as const },
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
  { key: 'plant', header: 'Plant', align: 'left' as const },
  { key: 'line', header: 'Line', align: 'left' as const },
  {
    key: 'hours',
    header: 'Hours',
    align: 'right' as const,
    render: (value: unknown) => `${Number(value).toFixed(1)}`,
  },
  {
    key: 'category',
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
  { key: 'detail', header: 'Details', align: 'left' as const },
  {
    key: 'supplier',
    header: 'Supplier',
    align: 'left' as const,
    render: (value: unknown) => value ? (
      <span className="text-orange-600 font-medium">{String(value)}</span>
    ) : '-',
  },
];

export default function PlantAnalysisPage() {
  const totalDowntime = plantSummary.reduce((sum, p) => sum + p.total_downtime, 0);
  const totalUnplanned = plantSummary.reduce((sum, p) => sum + p.unplanned, 0);

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Plant Downtime Analysis"
        subtitle="Manufacturing plant downtime and root cause analysis"
      />
      <div className="flex-1 p-6 overflow-auto space-y-6">
        {/* Alert Banner */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
          <ExclamationTriangleIcon className="w-6 h-6 text-red-600 mr-3 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-800">Plant A - Critical Downtime</h3>
            <p className="text-sm text-red-700 mt-1">
              6.5 hours of downtime this week at Plant A (Michigan Assembly). Paint defects on Line 3
              at 2.5x normal rate. Immediate root cause investigation recommended.
            </p>
          </div>
        </div>

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
            value={3}
            icon={<BuildingOffice2Icon className="w-6 h-6" />}
          />
          <KPICard
            title="Total Events"
            value={6}
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
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={plantSummary} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="plant" type="category" width={150} />
                  <Tooltip formatter={(value: number) => `${value.toFixed(1)} hours`} />
                  <Bar dataKey="total_downtime" name="Total" fill="#3b82f6" />
                  <Bar dataKey="unplanned" name="Unplanned" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Cause Breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Cause Breakdown
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
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
              </ResponsiveContainer>
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
            <DataTable
              columns={plantColumns}
              data={plantSummary}
              highlightRow={(row) => Number(row.total_downtime) > 5}
            />
          </div>

          {/* Cause Legend */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Cause Categories
            </h3>
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
          </div>
        </div>

        {/* Detail Table */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Downtime Events Detail
          </h3>
          <DataTable
            columns={detailColumns}
            data={downtimeDetails}
            highlightRow={(row) => Number(row.hours) > 3}
          />
        </div>

        {/* Root Cause Analysis */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Root Cause Analysis & Recommendations</h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <h4 className="font-semibold text-red-800">Plant A - Critical</h4>
              <p className="text-sm text-red-700 mt-2">
                <strong>Issue:</strong> Paint defects at 2.5x normal rate on Line 3.
              </p>
              <ul className="mt-2 space-y-1 text-sm text-red-700">
                <li>• Fast-track root cause analysis</li>
                <li>• Check paint booth calibration</li>
                <li>• Review recent material changes</li>
              </ul>
            </div>
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h4 className="font-semibold text-yellow-800">Plant B - Supply Chain</h4>
              <p className="text-sm text-yellow-700 mt-2">
                <strong>Issue:</strong> ECU shortage from Supplier Q.
              </p>
              <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                <li>• Review PO lead times</li>
                <li>• Increase safety stock</li>
                <li>• Identify alternate supplier</li>
              </ul>
            </div>
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-semibold text-blue-800">Plant C - Maintenance</h4>
              <p className="text-sm text-blue-700 mt-2">
                <strong>Issue:</strong> Planned maintenance overrun.
              </p>
              <ul className="mt-2 space-y-1 text-sm text-blue-700">
                <li>• Review scheduling accuracy</li>
                <li>• Add buffer to estimates</li>
                <li>• Consider predictive maintenance</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
