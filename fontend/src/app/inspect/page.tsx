'use client';

import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  MagnifyingGlassIcon,
  DocumentArrowDownIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { inspectDashboardService, RepairOrder } from '@/lib/api/inspectDashboard';

// Transform backend data to frontend format (add convenience aliases)
const transformRepairOrder = (ro: RepairOrder): RepairOrder & {
  priority: string;
  indicator: string;
  advisor: string;
  technician: string;
  metricTime: string;
  processTime: string;
  roType?: string;
  shopType?: string;
  isOverdue?: boolean;
  isUrgent?: boolean;
} => ({
  ...ro,
  priority: ro.p,
  indicator: ro.e,
  advisor: ro.adv,
  technician: ro.tech,
  metricTime: ro.mt,
  processTime: ro.pt,
  roType: ro.ro_type,
  shopType: ro.shop_type,
  isOverdue: ro.is_overdue,
  isUrgent: ro.is_urgent,
});
const statusConfig = {
  awaiting_dispatch: {
    label: 'I - ROs Awaiting Dispatch',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
  },
  in_inspection: {
    label: 'II - ROs in Inspection',
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
  },
  pending_approval: {
    label: 'III - ROs Pending Approval',
    bg: 'bg-orange-50',
    border: 'border-orange-200',
  },
  in_repair: {
    label: 'IV - ROs in Repair',
    bg: 'bg-purple-50',
    border: 'border-purple-200',
  },
  pending_review: {
    label: 'V - ROs Pending Review',
    bg: 'bg-green-50',
    border: 'border-green-200',
  },
};

export default function InspectPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [roTypeFilter, setRoTypeFilter] = useState('All');
  const [shopTypeFilter, setShopTypeFilter] = useState('All');
  const [waiterFilter, setWaiterFilter] = useState('All');
  const [selectedRO, setSelectedRO] = useState<string | null>(null);

  // Fetch repair orders from backend
  const { data: repairOrdersData, isLoading, error } = useQuery({
    queryKey: ['repairOrders', roTypeFilter, shopTypeFilter, waiterFilter, searchQuery],
    queryFn: () => inspectDashboardService.getRepairOrders({
      ro_type: roTypeFilter !== 'All' ? roTypeFilter : undefined,
      shop_type: shopTypeFilter !== 'All' ? shopTypeFilter : undefined,
      waiter: waiterFilter !== 'All' ? waiterFilter : undefined,
      search: searchQuery || undefined,
    }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const repairOrders = useMemo(() => {
    return (repairOrdersData?.repair_orders || []).map(transformRepairOrder);
  }, [repairOrdersData]);

  // Group ROs by status
  const rosByStatus = useMemo(() => {
    const grouped: Record<string, RepairOrder[]> = {
      awaiting_dispatch: [],
      in_inspection: [],
      pending_approval: [],
      in_repair: [],
      pending_review: [],
    };
    
    repairOrders.forEach((ro: RepairOrder) => {
      grouped[ro.status].push(ro);
    });
    
    return grouped;
  }, [repairOrders]);

  const totalROs = repairOrders.length;

  // Get unique filter values
  const roTypes = useMemo(() => {
    return Array.from(new Set(repairOrders.map((ro: RepairOrder) => ro.ro_type).filter(Boolean))) as string[];
  }, [repairOrders]);

  const shopTypes = useMemo(() => {
    return Array.from(new Set(repairOrders.map((ro: RepairOrder) => ro.shop_type).filter(Boolean))) as string[];
  }, [repairOrders]);

  const waiters = useMemo(() => {
    return Array.from(new Set(repairOrders.map((ro: RepairOrder) => ro.waiter).filter(Boolean))) as string[];
  }, [repairOrders]);

  const handleExport = (status: string) => {
    console.log(`Exporting ${status} ROs`);
    // TODO: Implement export functionality
  };

  const handleCloseOld = () => {
    console.log('Closing old ROs');
    // TODO: Implement close old ROs functionality
  };

  const handleCloseAll = () => {
    console.log('Closing all ROs in pending review');
    // TODO: Implement close all functionality
  };

  const handleGoToRO = () => {
    if (selectedRO) {
      console.log(`Navigating to RO: ${selectedRO}`);
      // TODO: Navigate to RO detail page
    }
  };

  // Prepare page context for the bot
  const pageContext = useMemo(() => {
    return {
      page: 'Inspect - Repair Orders',
      ros: {
        total: totalROs,
        byStatus: Object.entries(rosByStatus).map(([status, ros]) => ({
          status,
          count: ros.length,
          ros: ros.slice(0, 5).map((ro: RepairOrder) => ({
            id: ro.ro,
            customer: ro.customer,
            status: ro.status,
            promised: ro.promised,
            processTime: ro.pt,
          })),
        })),
      },
    };
  }, [totalROs, rosByStatus]);

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Repair Orders"
        subtitle="Cox Automotive • Vehicle inspection and repair order management"
      />
      
      <div className="flex-1 overflow-auto bg-gray-50">
        {/* Top Controls Bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left side */}
            <div className="flex items-center space-x-4">
              <button className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200">
                Legend
              </button>
              
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Go to RO..."
                  className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500 w-48"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
              
            </div>

            {/* Right side */}
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-gray-700">
                Total ROs: <span className="font-bold">{totalROs}</span>
              </span>
              
              <select
                value={roTypeFilter}
                onChange={(e) => setRoTypeFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              >
                <option value="All">RO TYPE: All</option>
                {roTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              
              <select
                value={shopTypeFilter}
                onChange={(e) => setShopTypeFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              >
                <option value="All">SHOP TYPE: All</option>
                {shopTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
              
              <select
                value={waiterFilter}
                onChange={(e) => setWaiterFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              >
                <option value="All">WAITER: All</option>
                {waiters.map(waiter => (
                  <option key={waiter} value={waiter}>{waiter}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Main Content - Status Panels */}
        <div className="p-6 space-y-6">
          {isLoading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cox-blue-600"></div>
              <p className="mt-4 text-gray-500">Loading repair orders...</p>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">Failed to load repair orders</p>
              <button 
                onClick={() => window.location.reload()}
                className="px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700"
              >
                Retry
              </button>
            </div>
          ) : (
            <>
          {/* Panel I - Awaiting Dispatch */}
          <div className={clsx('rounded-lg border-2 p-4', statusConfig.awaiting_dispatch.bg, statusConfig.awaiting_dispatch.border)}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {statusConfig.awaiting_dispatch.label} ({rosByStatus.awaiting_dispatch.length})
              </h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCloseOld}
                  className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  Close Old ROs
                </button>
                <button
                  onClick={() => handleExport('awaiting_dispatch')}
                  className="flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Export</span>
                </button>
              </div>
            </div>
            
            {rosByStatus.awaiting_dispatch.length > 0 ? (
              <div className="overflow-x-auto bg-white rounded border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">P</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">RO</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tag</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Promised</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">E</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Customer</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Adv</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tech</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">MT</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">PT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rosByStatus.awaiting_dispatch.map((ro, idx) => (
                      <tr
                        key={ro.id}
                        className={clsx(
                          'border-b border-gray-100 hover:bg-gray-50 cursor-pointer',
                          idx % 2 === 1 && 'bg-blue-50/30'
                        )}
                        onClick={() => setSelectedRO(ro.ro)}
                      >
                        <td className="px-3 py-2">{ro.p}</td>
                        <td className="px-3 py-2 font-medium">{ro.ro}</td>
                        <td className="px-3 py-2">{ro.tag}</td>
                        <td className="px-3 py-2">{ro.promised}</td>
                        <td className="px-3 py-2">{ro.e}</td>
                        <td className="px-3 py-2">{ro.customer}</td>
                        <td className="px-3 py-2">{ro.adv}</td>
                        <td className="px-3 py-2">{ro.tech}</td>
                        <td className="px-3 py-2">{ro.mt}</td>
                        <td className="px-3 py-2">{ro.pt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded border border-gray-200">
                No ROs in this status
              </div>
            )}
          </div>

          {/* Panel II - In Inspection */}
          <div className={clsx('rounded-lg border-2 p-4', statusConfig.in_inspection.bg, statusConfig.in_inspection.border)}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {statusConfig.in_inspection.label} ({rosByStatus.in_inspection.length})
              </h2>
              <button
                onClick={() => handleExport('in_inspection')}
                className="flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
            
            {rosByStatus.in_inspection.length > 0 ? (
              <div className="overflow-x-auto bg-white rounded border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">P</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">RO</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tag</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Promised</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">E</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Customer</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Adv</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tech</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">MT</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">PT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rosByStatus.in_inspection.map((ro, idx) => (
                      <tr
                        key={ro.id}
                        className={clsx(
                          'border-b border-gray-100 hover:bg-gray-50 cursor-pointer',
                          idx % 2 === 1 && 'bg-yellow-50/30'
                        )}
                        onClick={() => setSelectedRO(ro.ro)}
                      >
                        <td className="px-3 py-2">{ro.p}</td>
                        <td className="px-3 py-2 font-medium">{ro.ro}</td>
                        <td className="px-3 py-2">{ro.tag}</td>
                        <td className="px-3 py-2">{ro.promised}</td>
                        <td className="px-3 py-2">{ro.e}</td>
                        <td className="px-3 py-2">{ro.customer}</td>
                        <td className="px-3 py-2">{ro.adv}</td>
                        <td className="px-3 py-2">{ro.tech}</td>
                        <td className="px-3 py-2">{ro.mt}</td>
                        <td className="px-3 py-2">{ro.pt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded border border-gray-200">
                No ROs in this status
              </div>
            )}
          </div>

          {/* Panel III - Pending Approval */}
          <div className={clsx('rounded-lg border-2 p-4', statusConfig.pending_approval.bg, statusConfig.pending_approval.border)}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {statusConfig.pending_approval.label} ({rosByStatus.pending_approval.length})
              </h2>
              <button
                onClick={() => handleExport('pending_approval')}
                className="flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
            
            {rosByStatus.pending_approval.length > 0 ? (
              <div className="overflow-x-auto bg-white rounded border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">P</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">RO</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tag</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Promised</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">E</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Customed</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Adv</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tech</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">MT</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">PT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rosByStatus.pending_approval.map((ro, idx) => (
                      <tr
                        key={ro.id}
                        className={clsx(
                          'border-b border-gray-100 hover:bg-gray-50 cursor-pointer',
                          idx % 2 === 1 && 'bg-orange-50/30',
                        ro.is_urgent && 'bg-green-100',
                        ro.is_overdue && 'bg-red-100'
                        )}
                        onClick={() => setSelectedRO(ro.ro)}
                      >
                        <td className="px-3 py-2">{ro.p}</td>
                        <td className="px-3 py-2 font-medium">{ro.ro}</td>
                        <td className="px-3 py-2">{ro.tag}</td>
                        <td className="px-3 py-2">{ro.promised}</td>
                        <td className="px-3 py-2">{ro.e}</td>
                        <td className="px-3 py-2">{ro.customer}</td>
                        <td className="px-3 py-2">{ro.adv}</td>
                        <td className="px-3 py-2">{ro.tech}</td>
                        <td className="px-3 py-2">{ro.mt}</td>
                        <td className="px-3 py-2">{ro.pt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded border border-gray-200">
                No ROs in this status
              </div>
            )}
          </div>

          {/* Panel IV - In Repair */}
          <div className={clsx('rounded-lg border-2 p-4', statusConfig.in_repair.bg, statusConfig.in_repair.border)}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {statusConfig.in_repair.label} ({rosByStatus.in_repair.length})
              </h2>
              <button
                onClick={() => handleExport('in_repair')}
                className="flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
              >
                <DocumentArrowDownIcon className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
            
            {rosByStatus.in_repair.length > 0 ? (
              <div className="overflow-x-auto bg-white rounded border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">P</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">RO</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tag</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Promised</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">E</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Customer</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Adv</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tech</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">MT</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">PT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rosByStatus.in_repair.map((ro, idx) => (
                      <tr
                        key={ro.id}
                        className={clsx(
                          'border-b border-gray-100 hover:bg-gray-50 cursor-pointer',
                          idx % 2 === 1 && 'bg-purple-50/30'
                        )}
                        onClick={() => setSelectedRO(ro.ro)}
                      >
                        <td className="px-3 py-2">{ro.p}</td>
                        <td className="px-3 py-2 font-medium">{ro.ro}</td>
                        <td className="px-3 py-2">{ro.tag}</td>
                        <td className="px-3 py-2">{ro.promised}</td>
                        <td className="px-3 py-2">{ro.e}</td>
                        <td className="px-3 py-2">{ro.customer}</td>
                        <td className="px-3 py-2">{ro.adv}</td>
                        <td className="px-3 py-2">{ro.tech}</td>
                        <td className="px-3 py-2">{ro.mt}</td>
                        <td className="px-3 py-2">{ro.pt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded border border-gray-200">
                No ROs in this status
              </div>
            )}
          </div>

          {/* Panel V - Pending Review */}
          <div className={clsx('rounded-lg border-2 p-4', statusConfig.pending_review.bg, statusConfig.pending_review.border)}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">
                {statusConfig.pending_review.label} ({rosByStatus.pending_review.length})
              </h2>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleCloseAll}
                  className="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  Close All
                </button>
                <button
                  onClick={() => handleExport('pending_review')}
                  className="flex items-center space-x-1 px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  <DocumentArrowDownIcon className="w-4 h-4" />
                  <span>Export</span>
                </button>
              </div>
            </div>
            
            {rosByStatus.pending_review.length > 0 ? (
              <div className="overflow-x-auto bg-white rounded border border-gray-200">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">P</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">RO</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tag</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Promised</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">E</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Customer</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Adv</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">Tech</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">MT</th>
                      <th className="px-3 py-2 text-left font-semibold text-gray-600">PT</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rosByStatus.pending_review.map((ro, idx) => (
                      <tr
                        key={ro.id}
                        className={clsx(
                          'border-b border-gray-100 hover:bg-gray-50 cursor-pointer',
                          idx % 2 === 1 && 'bg-green-50/30'
                        )}
                        onClick={() => setSelectedRO(ro.ro)}
                      >
                        <td className="px-3 py-2">{ro.p}</td>
                        <td className="px-3 py-2 font-medium">{ro.ro}</td>
                        <td className="px-3 py-2">{ro.tag}</td>
                        <td className="px-3 py-2">{ro.promised}</td>
                        <td className="px-3 py-2">{ro.e}</td>
                        <td className="px-3 py-2">{ro.customer}</td>
                        <td className="px-3 py-2">{ro.adv}</td>
                        <td className="px-3 py-2">{ro.tech}</td>
                        <td className="px-3 py-2">{ro.mt}</td>
                        <td className="px-3 py-2">{ro.pt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-white rounded border border-gray-200">
                No ROs in this status
              </div>
            )}
          </div>
            </>
          )}
        </div>
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot pageContext={pageContext} />
    </div>
  );
}