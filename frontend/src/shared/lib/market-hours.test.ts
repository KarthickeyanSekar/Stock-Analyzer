import { describe, expect, it } from 'vitest';

import { nseStatus } from './market-hours';

describe('nseStatus', () => {
  it('is open on a weekday during the session (IST)', () => {
    // 2026-10-30 is a Friday; 10:00 IST = 04:30 UTC
    expect(nseStatus(new Date('2026-10-30T04:30:00Z'))).toEqual({ isOpen: true, timeIst: '10:00' });
  });

  it('is closed after 15:30 IST and at weekends', () => {
    expect(nseStatus(new Date('2026-10-30T10:01:00Z')).isOpen).toBe(false); // 15:31 IST
    expect(nseStatus(new Date('2026-10-31T05:00:00Z')).isOpen).toBe(false); // Saturday
  });
});
