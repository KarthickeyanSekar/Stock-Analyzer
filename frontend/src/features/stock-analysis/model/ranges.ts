import type { Prediction } from './headline';

/** Shared scale for range bars, in percent points. */
export const RANGE_MIN = -40;
export const RANGE_MAX = 80;

/** Position of a value on the range-bar scale as a CSS percentage (clamped). */
export function rangePosition(value: number): number {
  const clamped = Math.min(Math.max(value, RANGE_MIN), RANGE_MAX);
  return ((clamped - RANGE_MIN) / (RANGE_MAX - RANGE_MIN)) * 100;
}

export const TARGETS = [5, 10, 15, 20, 25, 30, 40, 50] as const;

/** Probability of reaching ``target`` before the stop, 0 when unknown. */
export function chanceOf(prediction: Prediction, target: number): number {
  return prediction.prob_hit[String(target)] ?? 0;
}
