import { describe, expect, it } from 'vitest';

import { predictionHeadline, type Prediction } from './headline';

const prediction: Prediction = {
  category: '50D',
  calendar_days: 50,
  as_of: '2026-10-30',
  p10_pct: -6.2,
  p50_pct: 9.4,
  p90_pct: 24.1,
  prob_up: 0.64,
  prob_hit: { '5': 0.7, '10': 0.55, '20': 0.41 },
  cagr_p50_pct: null,
  model_version: 'baseline-empirical-v1',
};

describe('predictionHeadline', () => {
  it('shows median, range and the chance of the target', () => {
    expect(predictionHeadline(prediction)).toBe('+9% (−6%…+24%) · 41% chance of +20%');
  });

  it('uses another target when asked', () => {
    expect(predictionHeadline(prediction, 10)).toContain('55% chance of +10%');
  });
});
