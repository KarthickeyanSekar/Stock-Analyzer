import { describe, expect, it } from 'vitest';

import { formatDateTimeIst } from './format-date';

describe('formatDateTimeIst', () => {
  it('converts UTC to IST', () => {
    // Arrange
    const utc = '2026-01-02T09:15:00Z';

    // Act
    const result = formatDateTimeIst(utc);

    // Assert
    expect(result).toContain('2:45:00');
  });
});
