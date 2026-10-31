const IST_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium',
  timeStyle: 'medium',
  timeZone: 'Asia/Kolkata',
});

/** Format an ISO timestamp in Indian Standard Time. */
export function formatDateTimeIst(iso: string): string {
  return IST_FORMATTER.format(new Date(iso));
}

const DATE_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

/** Format an ISO date (YYYY-MM-DD) as "30 Oct 2026" (date only, no timezone shift). */
export function formatDate(isoDate: string): string {
  const [year, month, day] = isoDate.split('-').map(Number);
  return DATE_FORMATTER.format(new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1));
}
