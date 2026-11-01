const NSE_OPEN_MINUTES = 9 * 60 + 15;
const NSE_CLOSE_MINUTES = 15 * 60 + 30;

const IST_PARTS = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Kolkata',
  weekday: 'short',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

export interface MarketStatus {
  isOpen: boolean;
  timeIst: string;
}

/** NSE regular session: weekdays 09:15–15:30 IST (holidays are not known to the frontend). */
export function nseStatus(now: Date): MarketStatus {
  const parts = Object.fromEntries(IST_PARTS.formatToParts(now).map((p) => [p.type, p.value]));
  const minutes = Number(parts.hour) * 60 + Number(parts.minute);
  const isWeekday = !['Sat', 'Sun'].includes(parts.weekday ?? '');
  return {
    isOpen: isWeekday && minutes >= NSE_OPEN_MINUTES && minutes < NSE_CLOSE_MINUTES,
    timeIst: `${parts.hour ?? '00'}:${parts.minute ?? '00'}`,
  };
}
