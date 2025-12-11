'use client';

import clsx from 'clsx';

interface Column {
  key: string;
  header: string;
  align?: 'left' | 'center' | 'right';
  format?: 'text' | 'number' | 'currency' | 'percent';
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

interface DataTableProps {
  columns: Column[];
  data: Record<string, unknown>[];
  compact?: boolean;
  striped?: boolean;
  highlightRow?: (row: Record<string, unknown>) => boolean;
}

export default function DataTable({
  columns,
  data,
  compact = false,
  striped = false,
  highlightRow,
}: DataTableProps) {
  const formatCell = (value: unknown, format?: string): string => {
    if (value === null || value === undefined) return '-';
    const numValue = Number(value);

    switch (format) {
      case 'currency':
        return isNaN(numValue)
          ? String(value)
          : new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 2,
            }).format(numValue);
      case 'percent':
        return isNaN(numValue) ? String(value) : `${numValue.toFixed(1)}%`;
      case 'number':
        return isNaN(numValue)
          ? String(value)
          : new Intl.NumberFormat('en-US').format(numValue);
      default:
        return String(value);
    }
  };

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={clsx({
                  'text-left': col.align === 'left' || !col.align,
                  'text-center': col.align === 'center',
                  'text-right': col.align === 'right',
                  'px-3 py-2': compact,
                })}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={idx}
              className={clsx({
                'bg-gray-50': striped && idx % 2 === 1,
                'bg-yellow-50': highlightRow?.(row),
              })}
            >
              {columns.map((col) => (
                <td
                  key={col.key}
                  className={clsx({
                    'text-left': col.align === 'left' || !col.align,
                    'text-center': col.align === 'center',
                    'text-right': col.align === 'right',
                    'px-3 py-2': compact,
                  })}
                >
                  {col.render
                    ? col.render(row[col.key], row)
                    : formatCell(row[col.key], col.format)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length === 0 && (
        <div className="text-center py-8 text-gray-500">No data available</div>
      )}
    </div>
  );
}
