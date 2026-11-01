import { BookOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

import { type TradePlan } from '../api/use-trade-plans';
import { progressToTarget } from '../model/outcome';
import { EmptyState } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';

interface ActivePlansProps {
  plans: TradePlan[];
  prices: Record<string, number>;
  onClose?: (plan: TradePlan) => void;
}

/** Active plans as cards: current return and a stop → entry → target progress bar. */
export function ActivePlans({ plans, prices, onClose }: ActivePlansProps) {
  if (plans.length === 0) {
    return (
      <EmptyState
        icon={BookOpen}
        title="No active plans"
        description="Pick a stock, choose a holding period and lock in its prediction."
        action={<Button render={<Link to="/stocks" />}>Find a stock</Button>}
      />
    );
  }
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {plans.map((plan, index) => {
        const price = prices[plan.symbol] ?? plan.entry_price;
        const current = ((price - plan.entry_price) / plan.entry_price) * 100;
        const entryAt = progressToTarget(plan, plan.entry_price);
        return (
          <li
            key={plan.id}
            className="rounded-xl border bg-card p-4 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1"
            style={{ animationDelay: `${String(index * 40)}ms` }}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <Link
                  to={`/stocks/${encodeURIComponent(plan.symbol)}`}
                  className="font-semibold hover:underline"
                >
                  {plan.symbol}
                </Link>
                <p className="text-xs text-muted-foreground">
                  {plan.category} · until {formatDate(plan.planned_end_date)}
                </p>
              </div>
              <span
                className={cn('text-sm font-semibold', current >= 0 ? 'text-gain' : 'text-loss')}
              >
                {formatPct(current, 2)}
              </span>
            </div>
            <div
              className="relative mt-4 h-2 rounded-full bg-muted"
              aria-label="Progress from stop to target"
            >
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-primary motion-safe:animate-grow-x"
                style={{ width: `${String(progressToTarget(plan, price))}%` }}
              />
              <span
                className="absolute -top-1 h-4 w-0.5 bg-foreground/60"
                style={{ left: `${String(entryAt)}%` }}
              />
            </div>
            <div className="mt-1 flex justify-between text-xs text-muted-foreground">
              <span>Stop {formatInr(plan.stop_price)}</span>
              <span>Target {formatInr(plan.target_price)}</span>
            </div>
            {onClose && (
              <Button
                size="sm"
                variant="outline"
                className="mt-3 w-full"
                onClick={() => {
                  onClose(plan);
                }}
              >
                Close plan
              </Button>
            )}
          </li>
        );
      })}
    </ul>
  );
}
