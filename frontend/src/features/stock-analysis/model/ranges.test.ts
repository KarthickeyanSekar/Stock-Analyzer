import { describe, expect, it } from 'vitest';

import { rangePosition } from './ranges';

describe('rangePosition', () => {
  it('maps the scale ends and zero', () => {
    expect(rangePosition(-40)).toBe(0);
    expect(rangePosition(80)).toBe(100);
    expect(rangePosition(0)).toBeCloseTo(33.33, 1);
  });

  it('clamps values outside the scale', () => {
    expect(rangePosition(-90)).toBe(0);
    expect(rangePosition(150)).toBe(100);
  });
});
