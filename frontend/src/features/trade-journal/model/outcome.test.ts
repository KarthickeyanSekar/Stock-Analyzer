import { describe, expect, it } from 'vitest';

import { previewOutcome } from './outcome';

describe('previewOutcome (mirrors the backend rule, ±0.5 pp)', () => {
  it.each([
    [1100, 'SUCCESS'],
    [1095, 'SUCCESS'],
    [1105, 'SUCCESS'],
    [1106, 'PARTIAL'],
    [1150, 'PARTIAL'],
    [1094, 'FAILURE'],
    [950, 'FAILURE'],
  ])('exit %d on entry 1000 with target +10%% → %s', (exit, expected) => {
    expect(previewOutcome(1000, exit, 10, 0.5).outcome).toBe(expected);
  });

  it('reports the actual return', () => {
    expect(previewOutcome(4354.45, 4820.38, 10.487, 0.5).actualPct).toBeCloseTo(10.7, 2);
  });
});
