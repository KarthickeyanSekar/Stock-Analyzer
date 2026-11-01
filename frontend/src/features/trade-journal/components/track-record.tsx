import { ChartBar, CircleCheck, CircleMinus } from 'lucide-react';

import { type TradePlan, type useJournalSummary } from '../api/use-trade-plans';
import { OUTCOME_META, type Outcome } from '../model/outcome';
import { EmptyState } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatPct, formatPp, formatProbability } from '@/shared/lib/format-number';

type Summary = NonNullable<ReturnType<typeof useJournalSummary>['data']>;
const ORDER: Outcome[] = ['SUCCESS', 'PARTIAL', 'FAILURE', 'EXITED_EARLY'];
const BAR: Record<Outcome, string> = {
  SUCCESS: 'bg-gain',
  PARTIAL: 'bg-warning',
  FAILURE: 'bg-loss',
  EXITED_EARLY: 'bg-muted-foreground',
};

const rate = (value: number | null) => (value === null ? '—' : formatProbability(value));

/**
 * Model accuracy per holding category (stacked outcomes, success rate, bias) and, per closed
 * plan, actual vs predicted plus whether your own target was reached (Q31).
 */
export function TrackRecord({ summary, plans }: { summary: Summary; plans: TradePlan[] }) {
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
      <dl className="grid grid-cols-3 gap-3 text-sm">
        <div>
          <dt className="text-xs text-muted-foreground">Model success rate</dt>
          <dd className="text-lg font-semibold">{rate(summary.success_rate)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Model bias (+ = too cautious)</dt>
          <dd className="text-lg font-semibold">
            {summary.avg_bias_pp === null ? '—' : formatPp(summary.avg_bias_pp, 2)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Your targets reached</dt>
          <dd className="text-lg font-semibold">{rate(summary.own_target_hit_rate)}</dd>
        </div>
      </dl>
      <ul className="flex flex-col gap-3">
        {summary.by_category.map((row) => (
          <li
            key={row.category}
            className="grid grid-cols-[48px_minmax(0,1fr)_150px] items-center gap-3 text-sm"
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
              {row.closed} closed · {rate(row.success_rate)} ·{' '}
              {row.avg_bias_pp === null ? '—' : formatPp(row.avg_bias_pp)}
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
      <section aria-labelledby="actual-vs-predicted">
        <h3 id="actual-vs-predicted" className="mb-2 text-sm font-semibold">
          Actual vs predicted
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted-foreground">
              <tr className="border-b">
                <th className="py-2 text-left font-medium">Plan</th>
                <th className="py-2 text-right font-medium">Predicted</th>
                <th className="py-2 text-right font-medium">Actual</th>
                <th className="py-2 text-right font-medium">Gap</th>
                <th className="py-2 text-right font-medium">Your target</th>
              </tr>
            </thead>
            <tbody>
              {plans.map((plan) => {
                const gap =
                  plan.actual_return_pct === null
                    ? null
                    : plan.actual_return_pct - plan.benchmark_pct;
                return (
                  <tr key={plan.id} className="border-b last:border-0">
                    <td className="py-2">
                      <span className="font-medium">{plan.symbol}</span>{' '}
                      <span className="text-muted-foreground">{plan.category}</span>
                    </td>
                    <td className="py-2 text-right">{formatPct(plan.benchmark_pct, 2)}</td>
                    <td className="py-2 text-right">
                      {plan.actual_return_pct === null ? '—' : formatPct(plan.actual_return_pct, 2)}
                    </td>
                    <td className="py-2 text-right">{gap === null ? '—' : formatPp(gap, 2)}</td>
                    <td className="py-2 text-right">
                      <span className="inline-flex items-center gap-1">
                        {plan.is_own_target_met ? (
                          <CircleCheck className="size-3.5 text-gain" aria-hidden="true" />
                        ) : (
                          <CircleMinus
                            className="size-3.5 text-muted-foreground"
                            aria-hidden="true"
                          />
                        )}
                        {formatPct(plan.target_pct, 1)}{' '}
                        {plan.is_own_target_met ? 'reached' : 'missed'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
