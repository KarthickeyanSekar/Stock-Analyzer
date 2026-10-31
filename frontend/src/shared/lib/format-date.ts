const IST_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium',
  timeStyle: 'medium',
  timeZone: 'Asia/Kolkata',
});

/** Format an ISO timestamp in Indian Standard Time. */
export function formatDateTimeIst(iso: string): string {
  return IST_FORMATTER.format(new Date(iso));
}
