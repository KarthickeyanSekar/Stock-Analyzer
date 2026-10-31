import { useTheme } from 'next-themes';
import { useMemo } from 'react';

/**
 * Read design-token colours (CSS variables) for canvas-based widgets such as charts.
 * Pass a module-level constant array; values are re-read whenever the theme changes.
 */
export function useCssVars<T extends string>(names: readonly T[]): Record<T, string> {
  const { resolvedTheme } = useTheme();
  return useMemo(() => {
    const styles = getComputedStyle(document.documentElement);
    return Object.fromEntries(
      names.map((name) => [name, styles.getPropertyValue(`--${name}`).trim()]),
    ) as Record<T, string>;
    // eslint-disable-next-line react-hooks/exhaustive-deps -- the CSS variables change with the theme class
  }, [resolvedTheme, names]);
}
