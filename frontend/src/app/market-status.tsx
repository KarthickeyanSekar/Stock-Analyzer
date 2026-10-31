import { useEffect, useState } from 'react';

import { cn } from '@/shared/lib/cn';
import { nseStatus } from '@/shared/lib/market-hours';

/** "NSE open · 10:05 IST" with a live dot; updates every 30 seconds. */
export function MarketStatus() {
  const [status, setStatus] = useState(() => nseStatus(new Date()));
  useEffect(() => {
    const timer = setInterval(() => {
      setStatus(nseStatus(new Date()));
    }, 30_000);
    return () => {
      clearInterval(timer);
    };
  }, []);

  return (
    <span className="hidden items-center gap-2 text-sm text-muted-foreground sm:flex">
      <span className="relative flex size-2">
        {status.isOpen && (
          <span className="absolute inline-flex size-full rounded-full bg-gain opacity-60 motion-safe:animate-ping" />
        )}
        <span
          className={cn(
            'relative inline-flex size-2 rounded-full',
            status.isOpen ? 'bg-gain' : 'bg-muted-foreground',
          )}
        />
      </span>
      NSE {status.isOpen ? 'open' : 'closed'} · {status.timeIst} IST
    </span>
  );
}
