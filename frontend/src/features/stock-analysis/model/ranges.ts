import type { Prediction } from './headline';

/** Shared scale for range bars, in percent points. */
export const RANGE_MIN = -40;
export const RANGE_MAX = 80;
/** Short holds move less: a tighter scale keeps their bars readable. */
export const SHORT_RANGE: RangeScale = { min: -10, max: 15 };

export interface RangeScale {
  min: number;
  max: number;
}

/** Position of a value on the range-bar scale as a CSS percentage (clamped). */
export function rangePosition(
  value: number,
  scale: RangeScale = { min: RANGE_MIN, max: RANGE_MAX },
): number {
  const clamped = Math.min(Math.max(value, scale.min), scale.max);
  return ((clamped - scale.min) / (scale.max - scale.min)) * 100;
}

export const TARGETS = [5, 10, 15, 20, 25, 30, 40, 50] as const;
/** Targets for 1-10 session holds (Q76). */
export const SHORT_TARGETS = [1, 2, 3, 5] as const;

/** Target presets for a holding period. */
export function targetsFor(isShortTerm: boolean): readonly number[] {
  return isShortTerm ? SHORT_TARGETS : TARGETS;
}

/** Probability of reaching ``target`` before the stop, 0 when unknown. */
export function chanceOf(prediction: Prediction, target: number): number {
  return prediction.prob_hit[String(target)] ?? 0;
}
