const INR = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

/** Format a rupee amount with Indian digit grouping, e.g. ₹1,04,250.50. */
export function formatInr(value: number): string {
  return INR.format(value);
}

/** Format percent points with an explicit sign, e.g. +9.5% or −6.2%. */
export function formatPct(value: number, digits = 1): string {
  const rounded = value.toFixed(digits);
  if (Number(rounded) === 0) return `${(0).toFixed(digits)}%`;
  return value > 0 ? `+${rounded}%` : `−${rounded.slice(1)}%`;
}

/** Format a difference between percentages in percentage points, e.g. +2.6 pp or −0.4 pp. */
export function formatPp(value: number, digits = 1): string {
  return formatPct(value, digits).replace('%', ' pp');
}

/** Format a 0–1 probability as a whole percentage, e.g. 0.41 → "41%". */
export function formatProbability(value: number): string {
  return `${Math.round(value * 100).toString()}%`;
}
