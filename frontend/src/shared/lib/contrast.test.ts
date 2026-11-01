// WCAG 2.1 AA audit of the design tokens: every text/background pair the UI uses must reach
// 4.5:1 (normal text) in both themes. Reads the real tokens from src/index.css.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { describe, expect, it } from 'vitest';

const css = readFileSync(resolve(__dirname, '../../index.css'), 'utf8');

function tokens(selector: string): Record<string, string> {
  const block = new RegExp(`${selector.replace('.', '\\.')}\\s*\\{([^}]*)\\}`).exec(css)?.[1] ?? '';
  const found: Record<string, string> = {};
  for (const match of block.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)) {
    found[match[1] ?? ''] = match[2] ?? '';
  }
  return found;
}

function luminance(hex: string): number {
  const linear = (i: number) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * linear(1) + 0.7152 * linear(3) + 0.0722 * linear(5);
}

function contrast(a: string, b: string): number {
  const [la, lb] = [luminance(a), luminance(b)];
  return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05);
}

// [text token, background token]
const PAIRS: [string, string][] = [
  ['foreground', 'background'],
  ['foreground', 'surface'],
  ['card-foreground', 'card'],
  ['popover-foreground', 'popover'],
  ['muted-foreground', 'background'],
  ['muted-foreground', 'surface'],
  ['muted-foreground', 'muted'],
  ['muted-foreground', 'card'],
  ['primary-foreground', 'primary'],
  ['primary', 'background'],
  ['primary', 'card'],
  ['secondary-foreground', 'secondary'],
  ['accent-foreground', 'accent'],
  ['gain', 'background'],
  ['gain', 'card'],
  ['gain', 'surface'],
  ['loss', 'background'],
  ['loss', 'card'],
  ['loss', 'surface'],
  ['warning', 'background'],
  ['warning', 'card'],
  ['synthetic', 'background'],
  ['synthetic', 'card'],
  ['destructive', 'background'],
  ['sidebar-foreground', 'sidebar'],
  ['sidebar-accent-foreground', 'sidebar-accent'],
];

describe.each([
  ['light', ':root'],
  ['dark', '.dark'],
])('%s theme contrast (WCAG 2.1 AA)', (_theme, selector) => {
  const palette = tokens(selector);

  it.each(PAIRS)('%s on %s ≥ 4.5:1', (text, background) => {
    expect(palette[text], `--${text}`).toBeDefined();
    expect(palette[background], `--${background}`).toBeDefined();
    expect(contrast(palette[text] ?? '', palette[background] ?? '')).toBeGreaterThanOrEqual(4.5);
  });
});

describe('contrast()', () => {
  it('matches the WCAG reference values', () => {
    expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5);
    expect(contrast('#777777', '#ffffff')).toBeCloseTo(4.48, 2);
  });
});
