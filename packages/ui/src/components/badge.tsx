import React from 'react';
import { cn } from '../utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'planner' | 'browser' | 'os';
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ className, variant = 'default', ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors',
          {
            'bg-dexpert-600 text-white': variant === 'default',
            'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200': variant === 'secondary',
            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200': variant === 'destructive',
            'border border-gray-300 text-gray-700 dark:border-gray-700 dark:text-gray-300': variant === 'outline',
            'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200': variant === 'planner',
            'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200': variant === 'browser',
            'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200': variant === 'os',
          },
          className,
        )}
        {...props}
      />
    );
  },
);
Badge.displayName = 'Badge';
