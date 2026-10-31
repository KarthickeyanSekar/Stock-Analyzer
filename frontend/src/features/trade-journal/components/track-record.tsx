import { ChartBar } from 'lucide-react';

import { type useJournalSummary } from '../api/use-trade-plans';
import { OUTCOME_META, type Outcome } from '../model/outcome';
import { EmptyState } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatPp, formatProbability } from '@/shared/lib/format-number';

type Summary = NonNullable<ReturnType<typeof useJournalSummary>['data']>;
const ORDER: Outcome[] = ['SUCCESS', 'PARTIAL', 'FAILURE', 'EXITED_EARLY'];
const BAR: Record<Outcome, string> = {
  SUCCESS: 'bg-gain',
  PARTIAL: 'bg-warning',
  FAILURE: 'bg-loss',
  EXITED_EARLY: 'bg-muted-foreground',
};

/** Per holding category: stacked outcome bar and model bias (actual − predicted). */
export function TrackRecord({ summary }: { summary: Summary }) {
  if (summary.closed === 0) {
    return (
      <EmptyState
        icon={ChartBar}
        title="No track record yet"
        description="Close plans to see how the predictions performed."
      />
    );
  }
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Success rate {summary.success_rate === null ? '—' : formatProbability(summary.success_rate)}{' '}
        · model bias {summary.avg_bias_pp === null ? '—' : formatPp(summary.avg_bias_pp, 2)}{' '}
        (positive = too cautious)
      </p>
      <ul className="flex flex-col gap-3">
        {summary.by_category.map((row) => (
          <li
            key={row.category}
            className="grid grid-cols-[48px_minmax(0,1fr)_96px] items-center gap-3 text-sm"
          >
            <span className="font-semibold">{row.category}</span>
            <span
              className="flex h-3 overflow-hidden rounded-full bg-muted"
              aria-label={`${row.category} outcomes`}
            >
              {ORDER.map((outcome) => {
                const count = row.outcomes[outcome] ?? 0;
                return count > 0 ? (
                  <span
                    key={outcome}
                    title={`${OUTCOME_META[outcome].label}: ${String(count)}`}
                    className={cn('h-3 motion-safe:animate-grow-x', BAR[outcome])}
                    style={{ width: `${String((count / row.closed) * 100)}%` }}
                  />
                ) : null;
              })}
            </span>
            <span className="text-right text-muted-foreground">
              {row.closed} closed · {row.avg_bias_pp === null ? '—' : formatPp(row.avg_bias_pp)}
            </span>
          </li>
        ))}
      </ul>
      <ul className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {ORDER.map((outcome) => (
          <li key={outcome} className="flex items-center gap-1.5">
            <span className={cn('size-2.5 rounded-sm', BAR[outcome])} />
            {OUTCOME_META[outcome].label}
          </li>
        ))}
      </ul>
    </div>
  );
}
