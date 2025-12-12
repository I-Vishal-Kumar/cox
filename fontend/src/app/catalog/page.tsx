'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/ui/Header';
import FloatingChatBot from '@/components/ui/FloatingChatBot';
import {
  TableCellsIcon,
  MagnifyingGlassIcon,
  ChevronRightIcon,
  CircleStackIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { useQuery } from '@tanstack/react-query';
import { dataCatalogService, transformTable } from '@/lib/api/dataCatalog';

export default function CatalogPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('All');

  // Use TanStack Query directly
  const { data: catalogData, isLoading, error } = useQuery({
    queryKey: ['dataCatalog'],
    queryFn: dataCatalogService.getTables,
  });

  const tables = useMemo(() => {
    return catalogData?.tables.map(transformTable) || [];
  }, [catalogData]);

  // Get unique categories from tables
  const categories = useMemo(() => {
    const cats = Array.from(new Set(tables.map(t => t.category)));
    return ['All', ...cats.sort()];
  }, [tables]);

  const filteredTables = tables.filter((table) => {
    const matchesSearch =
      table.name.toLowerCase().includes(search.toLowerCase()) ||
      table.description.toLowerCase().includes(search.toLowerCase()) ||
      table.columns.some((col) => col.name.toLowerCase().includes(search.toLowerCase()));
    const matchesCategory = categoryFilter === 'All' || table.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const selectedTableData = tables.find((t) => t.name === selectedTable);

  // Prepare page context for the bot
  const pageContext = useMemo(() => {
    const tablesByCategory = tables.reduce((acc, table) => {
      const cat = table.category || 'General';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push({
        name: table.name,
        description: table.description,
        rowCount: table.rowCount,
        columnCount: table.columns.length,
        columns: table.columns.map(c => c.name),
      });
      return acc;
    }, {} as Record<string, any[]>);

    return {
      page: 'Data Catalog',
      catalog: {
        totalTables: tables.length,
        regions: catalogData?.regions || [],
        kpiCategories: catalogData?.kpi_categories || [],
        tables: tables.map(t => ({
          name: t.name,
          description: t.description,
          rowCount: t.rowCount,
          columnCount: t.columns.length,
          columns: t.columns.map(c => ({
            name: c.name,
            type: c.type,
            description: c.description,
          })),
          category: t.category,
        })),
        tablesByCategory: Object.entries(tablesByCategory).map(([category, tableList]) => ({
          category,
          count: tableList.length,
          tables: tableList,
        })),
        selectedTable: selectedTableData ? {
          name: selectedTableData.name,
          description: selectedTableData.description,
          rowCount: selectedTableData.rowCount,
          columns: selectedTableData.columns.map(c => ({
            name: c.name,
            type: c.type,
            description: c.description,
          })),
          category: selectedTableData.category,
          sampleQuery: `SELECT * FROM ${selectedTableData.name} LIMIT 10;`,
        } : null,
      },
    };
  }, [tables, catalogData, selectedTableData]);

  return (
    <div className="flex flex-col h-screen">
      <Header
        title="Data Catalog"
        subtitle="Cox Automotive • Explore available datasets, tables, and columns"
      />
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Table List */}
        <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
          {/* Search */}
          <div className="p-4 border-b border-gray-200">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search tables or columns..."
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cox-blue-500"
              />
            </div>
          </div>

          {/* Category Filters */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex flex-wrap gap-2">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={clsx(
                    'px-3 py-1 text-xs font-medium rounded-full',
                    categoryFilter === cat
                      ? 'bg-cox-blue-100 text-cox-blue-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  )}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* Table List */}
          <div className="flex-1 overflow-auto">
            {isLoading ? (
              // Loading skeletons
              Array.from({ length: 6 }).map((_, idx) => (
                <div key={idx} className="px-4 py-3 border-b border-gray-100 animate-pulse">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="w-5 h-5 bg-gray-300 rounded mr-3" />
                      <div>
                        <div className="h-4 bg-gray-300 rounded w-24 mb-1" />
                        <div className="h-3 bg-gray-300 rounded w-16" />
                      </div>
                    </div>
                    <div className="w-4 h-4 bg-gray-300 rounded" />
                  </div>
                </div>
              ))
            ) : error ? (
              // Error state
              <div className="p-4 text-center">
                <ExclamationCircleIcon className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">Failed to load tables</p>
                <button 
                  onClick={() => window.location.reload()}
                  className="mt-2 text-xs text-cox-blue-600 hover:text-cox-blue-700"
                >
                  Retry
                </button>
              </div>
            ) : filteredTables.length === 0 ? (
              // Empty state
              <div className="p-4 text-center">
                <TableCellsIcon className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500">No tables found</p>
              </div>
            ) : (
              filteredTables.map((table) => (
                <button
                  key={table.name}
                  onClick={() => setSelectedTable(table.name)}
                  className={clsx(
                    'w-full px-4 py-3 text-left border-b border-gray-100 hover:bg-gray-50 transition-colors',
                    selectedTable === table.name && 'bg-cox-blue-50'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <TableCellsIcon className="w-5 h-5 text-gray-400 mr-3" />
                      <div>
                        <p className="font-medium text-gray-900">{table.name}</p>
                        <p className="text-xs text-gray-500">{table.rowCount} rows</p>
                      </div>
                    </div>
                    <ChevronRightIcon className="w-4 h-4 text-gray-400" />
                  </div>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Right Panel - Table Details */}
        <div className="flex-1 overflow-auto bg-gray-50 p-6">
          {selectedTableData ? (
            <div className="space-y-6">
              {/* Header */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center">
                    <CircleStackIcon className="w-8 h-8 text-cox-blue-600 mr-4" />
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">
                        {selectedTableData.name}
                      </h2>
                      <p className="text-sm text-gray-500 mt-1">
                        {selectedTableData.description}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-3 py-1 text-sm font-medium bg-cox-blue-100 text-cox-blue-700 rounded-full">
                      {selectedTableData.category}
                    </span>
                    <p className="text-xs text-gray-500 mt-2">
                      Updated: {selectedTableData.lastUpdated}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-200">
                  <div className="text-sm">
                    <span className="text-gray-500">Rows:</span>{' '}
                    <span className="font-medium">{selectedTableData.rowCount}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-gray-500">Columns:</span>{' '}
                    <span className="font-medium">{selectedTableData.columns.length}</span>
                  </div>
                </div>
              </div>

              {/* Columns */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Columns</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-600">
                          Column Name
                        </th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-600">
                          Type
                        </th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-600">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTableData.columns.map((col) => (
                        <tr key={col.name} className="border-b border-gray-100">
                          <td className="py-3 px-4">
                            <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                              {col.name}
                            </code>
                          </td>
                          <td className="py-3 px-4 text-gray-500 font-mono text-xs">
                            {col.type}
                          </td>
                          <td className="py-3 px-4 text-gray-600">{col.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Sample Query */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Sample Query
                </h3>
                <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm overflow-x-auto">
                  {`SELECT *
FROM ${selectedTableData.name}
LIMIT 10;`}
                </pre>
                <button 
                  onClick={() => {
                    const query = `Show me data from ${selectedTableData.name} table`;
                    router.push(`/?query=${encodeURIComponent(query)}`);
                  }}
                  className="mt-4 px-4 py-2 text-sm font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 transition-colors"
                >
                  Run in AI Chat
                </button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <CircleStackIcon className="w-16 h-16 text-gray-300 mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Select a table to view details
              </h3>
              <p className="text-gray-500 max-w-md">
                Browse the available tables and columns in the data catalog. You can
                search for specific data or filter by category.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Floating Chat Bot */}
      <FloatingChatBot 
        pageContext={pageContext}
      />
    </div>
  );
}
