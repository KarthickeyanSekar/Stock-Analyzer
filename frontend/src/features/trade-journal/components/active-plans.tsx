import { BookOpen, CalendarCheck, ShieldAlert, Target, type LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';

import { type TradePlan } from '../api/use-trade-plans';
import { EmptyState } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';

interface ActivePlansProps {
  plans: TradePlan[];
  onClose?: (plan: TradePlan) => void;
}

interface Flag {
  icon: LucideIcon;
  label: string;
  className: string;
}

/** Tracking flags (D2.3): shown with icon + text, never colour alone. Plans are never auto-closed. */
function flagsOf(plan: TradePlan): Flag[] {
  const progress = plan.progress;
  if (!progress) return [];
  const flags: Flag[] = [];
  if (progress.target_reached_on) {
    flags.push({
      icon: Target,
      label: `Target reached ${formatDate(progress.target_reached_on)}`,
      className: 'border-gain/40 text-gain',
    });
  }
  if (progress.stop_hit_on) {
    flags.push({
      icon: ShieldAlert,
      label: `Stop-loss crossed ${formatDate(progress.stop_hit_on)}`,
      className: 'border-loss/40 text-loss',
    });
  }
  if (progress.is_end_date_reached) {
    flags.push({
      icon: CalendarCheck,
      label: 'End date reached',
      className: 'border-warning/40 text-warning',
    });
  }
  return flags;
}

/** Active plans as cards: day N of M, current return and a stop → entry → target progress bar. */
export function ActivePlans({ plans, onClose }: ActivePlansProps) {
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
        const progress = plan.progress;
        const flags = flagsOf(plan);
        // Where the entry sits on the stop (0) → target (100) bar: fixed by the plan's own values.
        const entryAt = (Math.abs(plan.stop_pct) / (plan.target_pct - plan.stop_pct)) * 100;
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
                  {progress &&
                    ` · day ${String(progress.day_number)} of ${String(progress.total_days)}`}
                </p>
              </div>
              {progress && (
                <span
                  className={cn(
                    'text-sm font-semibold',
                    progress.return_pct > 0
                      ? 'text-gain'
                      : progress.return_pct < 0
                        ? 'text-loss'
                        : 'text-muted-foreground',
                  )}
                >
                  {formatPct(progress.return_pct, 2)}
                </span>
              )}
            </div>
            <div
              className="relative mt-4 h-2 rounded-full bg-muted"
              role="progressbar"
              aria-label="Progress from stop to target"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={progress?.progress_pct ?? entryAt}
            >
              <span
                className="absolute inset-y-0 left-0 rounded-full bg-primary motion-safe:animate-grow-x"
                style={{ width: `${String(progress?.progress_pct ?? entryAt)}%` }}
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
            {flags.length > 0 && (
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {flags.map((flag) => (
                  <li
                    key={flag.label}
                    className={cn(
                      'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium',
                      flag.className,
                    )}
                  >
                    <flag.icon className="size-3.5" aria-hidden="true" />
                    {flag.label}
                  </li>
                ))}
              </ul>
            )}
            {onClose && (
              <Button
                size="sm"
                variant={flags.length > 0 ? 'default' : 'outline'}
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
