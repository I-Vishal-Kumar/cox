'use client';

import clsx from 'clsx';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  format?: 'number' | 'currency' | 'percent';
  icon?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

export default function KPICard({
  title,
  value,
  change,
  changeLabel,
  format = 'number',
  icon,
  size = 'md',
}: KPICardProps) {
  const formatValue = (val: string | number): string => {
    if (typeof val === 'string') return val;
    switch (format) {
      case 'currency':
        return new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        }).format(val);
      case 'percent':
        return `${val.toFixed(1)}%`;
      default:
        return new Intl.NumberFormat('en-US').format(val);
    }
  };

  const isPositive = change !== undefined && change >= 0;
  const hasChange = change !== undefined;

  return (
    <div
      className={clsx('kpi-card', {
        'p-3': size === 'sm',
        'p-4': size === 'md',
        'p-6': size === 'lg',
      })}
    >
      <div className="flex items-start justify-between">
        <div>
          <p
            className={clsx('kpi-card-label', {
              'text-xs': size === 'sm',
              'text-sm': size === 'md',
              'text-base': size === 'lg',
            })}
          >
            {title}
          </p>
          <p
            className={clsx('kpi-card-value mt-1', {
              'text-xl': size === 'sm',
              'text-2xl': size === 'md',
              'text-3xl': size === 'lg',
            })}
          >
            {formatValue(value)}
          </p>
          {hasChange && (
            <div className="flex items-center mt-2">
              <span
                className={clsx('kpi-card-change flex items-center', {
                  positive: isPositive,
                  negative: !isPositive,
                })}
              >
                {isPositive ? (
                  <ArrowUpIcon className="w-3 h-3 mr-1" />
                ) : (
                  <ArrowDownIcon className="w-3 h-3 mr-1" />
                )}
                {Math.abs(change).toFixed(1)}%
              </span>
              {changeLabel && (
                <span className="text-xs text-gray-400 ml-2">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
    </div>
  );
}
