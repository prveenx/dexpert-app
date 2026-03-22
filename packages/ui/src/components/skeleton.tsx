import React from 'react';
import { cn } from '../utils/cn';

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  ...props
}) => (
  <div
    className={cn('animate-pulse rounded-md bg-gray-200 dark:bg-gray-700', className)}
    {...props}
  />
);
Skeleton.displayName = 'Skeleton';
