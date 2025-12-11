import { ExclamationCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function ErrorState({ 
  title = 'Something went wrong',
  message = 'There was an error loading the data.',
  onRetry,
  className,
  size = 'md'
}: ErrorStateProps) {
  const sizeClasses = {
    sm: {
      container: 'py-6',
      icon: 'w-8 h-8',
      title: 'text-sm font-medium',
      message: 'text-xs',
      button: 'px-3 py-1 text-xs'
    },
    md: {
      container: 'py-8',
      icon: 'w-10 h-10',
      title: 'text-base font-medium',
      message: 'text-sm',
      button: 'px-4 py-2 text-sm'
    },
    lg: {
      container: 'py-12',
      icon: 'w-12 h-12',
      title: 'text-lg font-medium',
      message: 'text-base',
      button: 'px-6 py-3 text-base'
    }
  };

  const classes = sizeClasses[size];

  return (
    <div className={clsx('text-center', classes.container, className)}>
      <ExclamationCircleIcon className={clsx(classes.icon, 'text-red-400 mx-auto mb-4')} />
      <h3 className={clsx(classes.title, 'text-gray-900 mb-2')}>{title}</h3>
      <p className={clsx(classes.message, 'text-gray-500 mb-4')}>{message}</p>
      {onRetry && (
        <button 
          onClick={onRetry}
          className={clsx(
            classes.button,
            'font-medium text-white bg-cox-blue-600 rounded-lg hover:bg-cox-blue-700 inline-flex items-center'
          )}
        >
          <ArrowPathIcon className="w-4 h-4 mr-2" />
          Retry
        </button>
      )}
    </div>
  );
}