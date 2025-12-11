import clsx from 'clsx';

interface LoadingSkeletonProps {
  className?: string;
  rows?: number;
  variant?: 'card' | 'list' | 'table';
}

export default function LoadingSkeleton({ 
  className, 
  rows = 3, 
  variant = 'card' 
}: LoadingSkeletonProps) {
  if (variant === 'card') {
    return (
      <div className={clsx('space-y-4', className)}>
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="p-4 bg-white rounded-lg border border-gray-200 animate-pulse">
            <div className="flex items-start justify-between">
              <div className="flex items-start flex-1">
                <div className="w-6 h-6 bg-gray-300 rounded" />
                <div className="ml-4 flex-1">
                  <div className="h-5 bg-gray-300 rounded w-48 mb-2" />
                  <div className="h-4 bg-gray-300 rounded w-full mb-2" />
                  <div className="h-4 bg-gray-300 rounded w-3/4" />
                </div>
              </div>
              <div className="w-20 h-6 bg-gray-300 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className={clsx('space-y-2', className)}>
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="flex items-center p-3 animate-pulse">
            <div className="w-5 h-5 bg-gray-300 rounded mr-3" />
            <div className="flex-1">
              <div className="h-4 bg-gray-300 rounded w-32 mb-1" />
              <div className="h-3 bg-gray-300 rounded w-20" />
            </div>
            <div className="w-4 h-4 bg-gray-300 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'table') {
    return (
      <div className={clsx('space-y-2', className)}>
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="flex items-center p-3 border-b border-gray-100 animate-pulse">
            <div className="w-24 h-4 bg-gray-300 rounded mr-4" />
            <div className="w-20 h-4 bg-gray-300 rounded mr-4" />
            <div className="flex-1 h-4 bg-gray-300 rounded" />
          </div>
        ))}
      </div>
    );
  }

  return null;
}