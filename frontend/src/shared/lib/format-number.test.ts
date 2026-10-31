import { describe, expect, it } from 'vitest';

import { formatInr, formatPct, formatPp, formatProbability } from './format-number';

describe('formatInr', () => {
  it('uses Indian digit grouping', () => {
    expect(formatInr(104250.5)).toBe('₹1,04,250.50');
  });
});

describe('formatPct', () => {
  it('adds a sign and uses a true minus', () => {
    expect(formatPct(9.46)).toBe('+9.5%');
    expect(formatPct(-6.24)).toBe('−6.2%');
    expect(formatPct(0.01)).toBe('0.0%');
  });
});

describe('formatProbability', () => {
  it('shows whole percentages', () => {
    expect(formatProbability(0.4149)).toBe('41%');
  });
});

describe('formatPp', () => {
  it('uses percentage points, not percent', () => {
    expect(formatPp(2.61)).toBe('+2.6 pp');
    expect(formatPp(-0.42, 2)).toBe('−0.42 pp');
  });
});
