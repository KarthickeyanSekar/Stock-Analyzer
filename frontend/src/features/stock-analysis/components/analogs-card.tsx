import { History } from 'lucide-react';

import { useStockAnalogs } from '../api/use-stocks';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatPct, formatProbability } from '@/shared/lib/format-number';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';

/** What happened after the past setups most similar to this stock's latest one. */
export function AnalogsCard({
  symbol,
  category,
  target,
}: {
  symbol: string;
  category: string;
  target: number;
}) {
  const { data, isPending, isError, refetch } = useStockAnalogs(symbol, category);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Similar past setups · {category}</CardTitle>
        <CardDescription>
          Closest matches across all stocks, only from holding periods that have already ended.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 text-sm">
        {isPending && <SkeletonRows rows={4} className="h-6" />}
        {isError && <ErrorState message="Could not load setups." onRetry={() => void refetch()} />}
        {data && data.cases.length === 0 && (
          <EmptyState
            icon={History}
            title="No similar setups yet"
            description="Not enough history for this holding period."
          />
        )}
        {data && data.cases.length > 0 && (
          <>
            <dl className="grid grid-cols-3 gap-2">
              <div>
                <dt className="text-xs text-muted-foreground">Median</dt>
                <dd
                  className={cn(
                    'font-semibold',
                    (data.median_return_pct ?? 0) >= 0 ? 'text-gain' : 'text-loss',
                  )}
                >
                  {data.median_return_pct === null ? '—' : formatPct(data.median_return_pct)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Ended up</dt>
                <dd className="font-semibold">
                  {data.share_up === null ? '—' : formatProbability(data.share_up)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Hit {formatPct(target, 0)}</dt>
                <dd className="font-semibold">
                  {formatProbability(data.hit_rates[String(target)] ?? 0)}
                </dd>
              </div>
            </dl>
            <ul className="flex flex-col">
              {data.cases.slice(0, 5).map((c) => (
                <li
                  key={`${c.symbol}-${c.as_of}`}
                  className="flex items-center justify-between border-t py-1.5"
                >
                  <span>
                    <span className="font-medium">{c.symbol}</span>{' '}
                    <span className="text-xs text-muted-foreground">{formatDate(c.as_of)}</span>
                  </span>
                  <span className={c.return_pct >= 0 ? 'text-gain' : 'text-loss'}>
                    {formatPct(c.return_pct)}
                  </span>
                </li>
              ))}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}
