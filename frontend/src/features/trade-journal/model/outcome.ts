import { CircleCheck, CircleX, LogOut, TrendingUp, type LucideIcon } from 'lucide-react';

import type { TradePlan } from '../api/use-trade-plans';

export type Outcome = NonNullable<TradePlan['outcome']>;

/** Label, icon, colour token and meaning of each calculated outcome (docs/15-trade-journal.md). */
export const OUTCOME_META: Record<
  Outcome,
  { label: string; icon: LucideIcon; className: string; hint: string }
> = {
  SUCCESS: {
    label: 'Success',
    icon: CircleCheck,
    className: 'border-gain/40 bg-gain/10 text-gain',
    hint: 'Actual equals the prediction within the tolerance',
  },
  PARTIAL: {
    label: 'Partial · tune model',
    icon: TrendingUp,
    className: 'border-warning/40 bg-warning/10 text-warning',
    hint: 'Above the prediction: the model was too cautious',
  },
  FAILURE: {
    label: 'Failure',
    icon: CircleX,
    className: 'border-loss/40 bg-loss/10 text-loss',
    hint: 'Below the prediction: the model was too optimistic',
  },
  EXITED_EARLY: {
    label: 'Exited early',
    icon: LogOut,
    className: 'border-border bg-muted text-muted-foreground',
    hint: 'Closed before the plan ended',
  },
};

/**
 * Preview of the outcome the server will calculate (same rule as the domain):
 * |actual − predicted| ≤ tolerance → SUCCESS, above → PARTIAL, below → FAILURE.
 * Display only: the server's calculation is authoritative.
 */
export function previewOutcome(
  entryPrice: number,
  exitPrice: number,
  targetPct: number,
  tolerancePp: number,
): { actualPct: number; outcome: Outcome } {
  const actualPct = Math.round(((exitPrice - entryPrice) / entryPrice) * 100 * 10_000) / 10_000;
  const outcome: Outcome =
    Math.abs(actualPct - targetPct) <= tolerancePp
      ? 'SUCCESS'
      : actualPct > targetPct
        ? 'PARTIAL'
        : 'FAILURE';
  return { actualPct, outcome };
}

/** Where the current price sits between stop (0%) and target (100%), clamped. */
export function progressToTarget(plan: TradePlan, price: number): number {
  const span = plan.target_price - plan.stop_price;
  return span <= 0 ? 0 : Math.min(100, Math.max(0, ((price - plan.stop_price) / span) * 100));
}
