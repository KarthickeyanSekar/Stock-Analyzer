import type { TradePlan } from '../api/use-trade-plans';

type Outcome = NonNullable<TradePlan['outcome']>;

/** Badge style and explanation for each calculated outcome (docs/15-trade-journal.md). */
export const OUTCOME_STYLE: Record<Outcome, { label: string; className: string; hint: string }> = {
  SUCCESS: {
    label: '✅ Success',
    className: 'bg-emerald-100 text-emerald-800',
    hint: 'Actual equals the prediction within the tolerance',
  },
  PARTIAL: {
    label: '🟡 Partial · tuning required',
    className: 'bg-amber-100 text-amber-800',
    hint: 'Above the prediction: the model was too cautious',
  },
  FAILURE: {
    label: '❌ Failure',
    className: 'bg-red-100 text-red-800',
    hint: 'Below the prediction: the model was too optimistic',
  },
  EXITED_EARLY: {
    label: '✋ Exited early',
    className: 'bg-slate-100 text-slate-700',
    hint: 'Closed before the plan ended',
  },
};
