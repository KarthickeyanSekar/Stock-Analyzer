import { ArrowDownRight, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useStockOverview } from '@/features/stock-analysis';
import {
  ActivePlans,
  OutcomeBadge,
  useJournalSummary,
  useTradePlans,
} from '@/features/trade-journal';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct, formatPp, formatProbability } from '@/shared/lib/format-number';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';

function Kpi({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: string;
  hint: string;
  tone?: string;
}) {
  return (
    <Card className="motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-1">
      <CardContent className="flex flex-col gap-1">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className={cn('text-3xl font-semibold', tone)}>{value}</span>
        <span className="text-xs text-muted-foreground">{hint}</span>
      </CardContent>
    </Card>
  );
}

export function HomePage() {
  const summary = useJournalSummary();
  const plans = useTradePlans();
  const overview = useStockOverview();
  const prices = Object.fromEntries(
    (overview.data ?? []).map((r) => [r.stock.symbol, r.last_close ?? 0]),
  );
  const active = (plans.data ?? []).filter((p) => p.status === 'ACTIVE');
  const recent = (plans.data ?? []).filter((p) => p.status === 'CLOSED').slice(0, 4);
  const byMove = [...(overview.data ?? [])].sort(
    (a, b) => (b.day_change_pct ?? 0) - (a.day_change_pct ?? 0),
  );
  const movers = [...byMove.slice(0, 3), ...byMove.slice(-3).reverse()];
  const topMedian = [...(overview.data ?? [])]
    .sort((a, b) => (b.median_1y_pct ?? -999) - (a.median_1y_pct ?? -999))
    .slice(0, 5);
  const lastDate = overview.data?.[0]?.last_date;
  const s = summary.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          {lastDate ? `Prices as of ${formatDate(lastDate)} close` : 'Loading prices…'} · NIFTY 50
          universe
        </p>
      </div>

      {s ? (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi
            label="Active plans"
            value={String(s.active)}
            hint={s.active ? 'being tracked' : 'nothing tracked yet'}
          />
          <Kpi
            label="Closed plans"
            value={String(s.closed)}
            hint={`${String(s.outcomes.SUCCESS ?? 0)} success · ${String(s.outcomes.PARTIAL ?? 0)} partial · ${String(s.outcomes.FAILURE ?? 0)} failure`}
          />
          <Kpi
            label="Success rate"
            value={s.success_rate === null ? '—' : formatProbability(s.success_rate)}
            hint="within the tolerance of the prediction"
          />
          <Kpi
            label="Model bias"
            value={s.avg_bias_pp === null ? '—' : formatPp(s.avg_bias_pp)}
            hint="actual − predicted (positive = too cautious)"
            tone={
              s.avg_bias_pp === null ? undefined : s.avg_bias_pp >= 0 ? 'text-gain' : 'text-loss'
            }
          />
        </div>
      ) : summary.isError ? (
        <ErrorState
          message="Could not load the journal summary."
          onRetry={() => void summary.refetch()}
        />
      ) : (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Active plans</CardTitle>
          </CardHeader>
          <CardContent>
            {plans.isPending ? (
              <SkeletonRows rows={2} className="h-28" />
            ) : (
              <ActivePlans plans={active} prices={prices} />
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent outcomes</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col divide-y">
            {recent.length === 0 && (
              <p className="text-sm text-muted-foreground">No closed plans yet.</p>
            )}
            {recent.map((p) => (
              <div key={p.id} className="flex items-center justify-between gap-2 py-2.5 text-sm">
                <div>
                  <span className="font-semibold">{p.symbol}</span>{' '}
                  <span className="text-muted-foreground">· {p.category}</span>
                  <p className="text-xs text-muted-foreground">
                    {formatPct(p.actual_return_pct ?? 0, 2)} vs {formatPct(p.target_pct, 2)}
                  </p>
                </div>
                {p.outcome && <OutcomeBadge outcome={p.outcome} />}
              </div>
            ))}
            <Link to="/journal" className="pt-3 text-sm text-primary hover:underline">
              Open journal
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Today&apos;s movers</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col divide-y">
            {overview.isPending && <SkeletonRows rows={6} className="h-8" />}
            {movers.map((r) => {
              const up = (r.day_change_pct ?? 0) >= 0;
              return (
                <Link
                  key={r.stock.symbol}
                  to={`/stocks/${encodeURIComponent(r.stock.symbol)}`}
                  className="flex items-center justify-between py-2.5 text-sm hover:text-primary"
                >
                  <span>
                    <span className="font-semibold">{r.stock.symbol}</span>{' '}
                    <span className="text-muted-foreground">{formatInr(r.last_close ?? 0)}</span>
                  </span>
                  <span
                    className={cn(
                      'flex items-center gap-1 font-medium',
                      up ? 'text-gain' : 'text-loss',
                    )}
                  >
                    {up ? (
                      <ArrowUpRight className="size-4" />
                    ) : (
                      <ArrowDownRight className="size-4" />
                    )}
                    {formatPct(r.day_change_pct ?? 0, 2)}
                  </span>
                </Link>
              );
            })}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Highest 1Y median prediction</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col divide-y">
            {overview.isPending && <SkeletonRows rows={5} className="h-8" />}
            {topMedian.map((r) => (
              <Link
                key={r.stock.symbol}
                to={`/stocks/${encodeURIComponent(r.stock.symbol)}`}
                className="flex items-center justify-between py-2.5 text-sm hover:text-primary"
              >
                <span>
                  <span className="font-semibold">{r.stock.symbol}</span>{' '}
                  <span className="text-muted-foreground">
                    · chance up {formatProbability(r.prob_up_1y ?? 0)}
                  </span>
                </span>
                <span className="font-semibold text-gain">{formatPct(r.median_1y_pct ?? 0)}</span>
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
