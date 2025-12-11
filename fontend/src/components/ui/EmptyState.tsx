import { ReactNode } from 'react';
import clsx from 'clsx';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function EmptyState({ 
  icon,
  title,
  message,
  action,
  className,
  size = 'md'
}: EmptyStateProps) {
  const sizeClasses = {
    sm: {
      container: 'py-6',
      title: 'text-sm font-medium',
      message: 'text-xs'
    },
    md: {
      container: 'py-8',
      title: 'text-base font-medium',
      message: 'text-sm'
    },
    lg: {
      container: 'py-12',
      title: 'text-lg font-medium',
      message: 'text-base'
    }
  };

  const classes = sizeClasses[size];

  return (
    <div className={clsx('text-center', classes.container, className)}>
      {icon && <div className="mb-4">{icon}</div>}
      <h3 className={clsx(classes.title, 'text-gray-900 mb-2')}>{title}</h3>
      {message && <p className={clsx(classes.message, 'text-gray-500 mb-4')}>{message}</p>}
      {action && <div>{action}</div>}
    </div>
  );
}