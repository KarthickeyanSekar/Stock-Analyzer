import { CircleAlert, type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/shared/lib/cn';
import { Button } from '@/shared/ui/button';
import { Skeleton } from '@/shared/ui/skeleton';

/** Empty state: icon + one sentence + a primary action. */
export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  compact = false,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  /** Smaller padding and icon, for empty states inside dashboard cards. */
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center gap-2 px-4 text-center motion-safe:animate-in motion-safe:fade-in',
        compact ? 'py-4' : 'py-10',
      )}
    >
      <Icon
        className={cn('text-muted-foreground', compact ? 'size-6' : 'size-10')}
        aria-hidden="true"
      />
      <p className="font-medium">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

/** Error state: the message plus a retry button. */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm"
    >
      <CircleAlert className="size-4 text-destructive" aria-hidden="true" />
      <span className="flex-1">{message}</span>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

/** Skeleton rows shaped like a list or table while data loads. */
export function SkeletonRows({
  rows = 5,
  className = 'h-10',
}: {
  rows?: number;
  className?: string;
}) {
  return (
    <div className="flex flex-col gap-2" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className={className} />
      ))}
    </div>
  );
}
