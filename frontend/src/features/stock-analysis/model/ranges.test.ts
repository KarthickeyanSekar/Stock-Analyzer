import { describe, expect, it } from 'vitest';

import { rangePosition, SHORT_RANGE, targetsFor } from './ranges';

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

describe('short-term scale and targets', () => {
  it('uses a tighter scale and small targets for short holds', () => {
    expect(rangePosition(-10, SHORT_RANGE)).toBe(0);
    expect(rangePosition(15, SHORT_RANGE)).toBe(100);
    expect(targetsFor(true)).toEqual([1, 2, 3, 5]);
    expect(targetsFor(false)[0]).toBe(5);
  });
});
