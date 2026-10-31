import type { components } from '@/shared/api/schema';
import { formatPct, formatProbability } from '@/shared/lib/format-number';

export type Prediction = components['schemas']['PredictionResponse'];

export const DEFAULT_TARGET_PCT = 20;

/** Headline format (Q4): "+9% (−6…+24%) · 41% chance of +20%". */
export function predictionHeadline(prediction: Prediction, targetPct = DEFAULT_TARGET_PCT): string {
  const range = `${formatPct(prediction.p10_pct, 0)}…${formatPct(prediction.p90_pct, 0)}`;
  const chance = prediction.prob_hit[String(targetPct)] ?? 0;
  return `${formatPct(prediction.p50_pct, 0)} (${range}) · ${formatProbability(chance)} chance of +${String(targetPct)}%`;
}
