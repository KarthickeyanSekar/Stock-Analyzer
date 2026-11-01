import { Archive } from 'lucide-react';
import { Link } from 'react-router-dom';

import { type TradePlan } from '../api/use-trade-plans';
import { OutcomeBadge } from './outcome-badge';
import { EmptyState } from '@/shared/components/data-states';
import { formatDate } from '@/shared/lib/format-date';
import { formatPct, formatPp } from '@/shared/lib/format-number';

/** Closed plans: actual vs predicted and the calculated outcome (rows on desktop, cards on phones). */
export function ClosedPlans({ plans }: { plans: TradePlan[] }) {
  if (plans.length === 0) {
    return (
      <EmptyState
        icon={Archive}
        title="No closed plans yet"
        description="Closed plans and their outcomes appear here."
      />
    );
  }
  return (
    <ul className="divide-y rounded-xl border bg-card">
      {plans.map((plan) => (
        <li
          key={plan.id}
          className="grid grid-cols-2 items-center gap-2 p-4 text-sm sm:grid-cols-[1.4fr_1fr_1fr_1fr_auto]"
        >
          <div>
            <Link
              to={`/stocks/${encodeURIComponent(plan.symbol)}`}
              className="font-semibold hover:underline"
            >
              {plan.symbol}
            </Link>
            <p className="text-xs text-muted-foreground">
              #{plan.id} · {plan.category} · {formatDate(plan.start_date)} →{' '}
              {plan.exit_date ? formatDate(plan.exit_date) : ''}
            </p>
          </div>
          <div className="text-right sm:text-left">
            <p className="text-xs text-muted-foreground">Actual</p>
            <p className="font-semibold">{formatPct(plan.actual_return_pct ?? 0, 2)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Predicted</p>
            <p>{formatPct(plan.target_pct, 2)}</p>
          </div>
          <div className="text-right sm:text-left">
            <p className="text-xs text-muted-foreground">Difference</p>
            <p>{formatPp((plan.actual_return_pct ?? 0) - plan.target_pct, 2)}</p>
          </div>
          <div className="col-span-2 sm:col-span-1">
            {plan.outcome && <OutcomeBadge outcome={plan.outcome} />}
          </div>
        </li>
      ))}
    </ul>
  );
}
