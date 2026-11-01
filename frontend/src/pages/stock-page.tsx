import { ArrowDownRight, ArrowUpRight, Plus } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  DEFAULT_TARGET_PCT,
  PredictionRanges,
  PriceChart,
  TARGETS,
  TargetOdds,
  useStockPredictions,
  useStockPrices,
  type PriceLine,
} from '@/features/stock-analysis';
import { OutcomeBadge, StartPlanSheet, useTradePlans } from '@/features/trade-journal';
import { ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import { Badge } from '@/shared/ui/badge';
import { Button } from '@/shared/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';
import { Skeleton } from '@/shared/ui/skeleton';
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group';

const RANGES = { '1M': 31, '6M': 183, '1Y': 366, '5Y': 1830, All: 100_000 } as const;
type RangeKey = keyof typeof RANGES;

export function StockPage() {
  const { symbol = '' } = useParams();
  const predictions = useStockPredictions(symbol);
  const prices = useStockPrices(symbol);
  const plans = useTradePlans();
  const [range, setRange] = useState<RangeKey>('1Y');
  const [category, setCategory] = useState('1Y');
  const [target, setTarget] = useState(DEFAULT_TARGET_PCT);
  const [isSheetOpen, setSheetOpen] = useState(false);

  const candles = useMemo(() => {
    const all = prices.data ?? [];
    const last = all.at(-1);
    if (!last) return [];
    const from = new Date(last.date);
    from.setDate(from.getDate() - RANGES[range]);
    const fromIso = from.toISOString().slice(0, 10);
    return all.filter((c) => c.date >= fromIso);
  }, [prices.data, range]);

  const stockPlans = (plans.data ?? []).filter((p) => p.symbol === symbol);
  const activePlan = stockPlans.find((p) => p.status === 'ACTIVE');
  const lines = useMemo<PriceLine[]>(() => {
    const plan = plans.data?.find((p) => p.symbol === symbol && p.status === 'ACTIVE');
    return plan
      ? [
          { price: plan.target_price, title: 'Target', tone: 'gain' },
          { price: plan.entry_price, title: 'Entry', tone: 'muted-foreground' },
          { price: plan.stop_price, title: 'Stop', tone: 'loss' },
        ]
      : [];
  }, [plans.data, symbol]);

  if (predictions.isError) {
    return (
      <ErrorState
        message={`Stock ${symbol} was not found or could not be loaded.`}
        onRetry={() => void predictions.refetch()}
      />
    );
  }
  const data = predictions.data;
  const all = prices.data ?? [];
  const last = all.at(-1);
  const previous = all.at(-2);
  const change = last && previous ? last.close - previous.close : null;
  const changePct = change !== null && previous ? (change / previous.close) * 100 : null;
  const selected = data?.predictions.find((p) => p.category === category) ?? data?.predictions[0];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end sm:gap-4">
        <div className="min-w-0 sm:flex-1">
          <div className="text-sm text-muted-foreground">
            {data ? (
              `${data.stock.exchange} · ${data.stock.sector ?? ''}`
            ) : (
              <Skeleton className="h-4 w-40" />
            )}
          </div>
          <h1 className="flex flex-wrap items-center gap-x-3 gap-y-1 text-2xl font-semibold">
            {symbol}
            <span className="text-base font-normal text-muted-foreground">{data?.stock.name}</span>
            {data?.stock.is_synthetic && (
              <Badge variant="outline" className="border-synthetic text-synthetic">
                SYNTHETIC
              </Badge>
            )}
          </h1>
        </div>
        <div className="sm:text-right">
          <div className="text-3xl font-semibold">
            {last ? formatInr(last.close) : <Skeleton className="h-9 w-36" />}
          </div>
          {change !== null && changePct !== null && last && (
            <p
              className={cn(
                'flex items-center gap-1 text-sm sm:justify-end',
                change >= 0 ? 'text-gain' : 'text-loss',
              )}
            >
              {change >= 0 ? (
                <ArrowUpRight className="size-4" />
              ) : (
                <ArrowDownRight className="size-4" />
              )}
              {change >= 0 ? '+' : '−'}
              {Math.abs(change).toFixed(2)} ({formatPct(changePct, 2)}) · {formatDate(last.date)}
            </p>
          )}
        </div>
        <Button
          size="lg"
          disabled={!data || !last}
          onClick={() => {
            setSheetOpen(true);
          }}
        >
          <Plus /> Start plan
        </Button>
      </header>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="flex min-w-0 flex-col gap-6">
          <Card>
            <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
              <CardTitle>Price</CardTitle>
              <ToggleGroup
                value={[range]}
                onValueChange={(value: string[]) => {
                  const next = value[0] as RangeKey | undefined;
                  if (next) setRange(next);
                }}
                aria-label="Chart range"
              >
                {(Object.keys(RANGES) as RangeKey[]).map((key) => (
                  <ToggleGroupItem key={key} value={key} size="sm">
                    {key}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </CardHeader>
            <CardContent>
              {prices.isPending ? (
                <Skeleton className="h-72 w-full sm:h-80" />
              ) : (
                <PriceChart candles={candles} lines={lines} />
              )}
              {activePlan && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Dashed lines: active plan #{activePlan.id} entry, target and stop.
                </p>
              )}
            </CardContent>
          </Card>

          <Card className="p-0 pt-4">
            <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>Predictions by holding period</CardTitle>
                <CardDescription>
                  Band = 80% of past outcomes (p10–p90) · dot = median · line = 0%
                </CardDescription>
              </div>
              <ToggleGroup
                value={[String(target)]}
                onValueChange={(value: string[]) => {
                  if (value[0]) setTarget(Number(value[0]));
                }}
                aria-label="Target"
                className="flex-wrap"
              >
                {TARGETS.map((t) => (
                  <ToggleGroupItem key={t} value={String(t)} size="sm">
                    +{t}%
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </CardHeader>
            <CardContent className="px-0">
              {data ? (
                <PredictionRanges
                  predictions={data.predictions}
                  selected={category}
                  target={target}
                  onSelect={setCategory}
                />
              ) : (
                <div className="px-4">
                  <SkeletonRows rows={7} />
                </div>
              )}
              <p className="border-t px-4 pt-3 text-xs text-muted-foreground">
                Baseline statistics from past prices (synthetic data). Not investment advice.
              </p>
            </CardContent>
          </Card>
        </div>

        <aside className="flex flex-col gap-6">
          <Card className="lg:sticky lg:top-20">
            <CardHeader>
              <CardDescription>Selected · hold {selected?.category ?? '—'}</CardDescription>
              {selected ? (
                <p className="flex items-baseline gap-2">
                  <span
                    className={cn(
                      'text-4xl font-semibold',
                      selected.p50_pct >= 0 ? 'text-gain' : 'text-loss',
                    )}
                  >
                    {formatPct(selected.p50_pct)}
                  </span>
                  <span className="text-sm text-muted-foreground">median</span>
                </p>
              ) : (
                <Skeleton className="h-10 w-32" />
              )}
              {selected && (
                <p className="text-sm text-muted-foreground">
                  80% range {formatPct(selected.p10_pct)} … {formatPct(selected.p90_pct)}
                  {selected.cagr_p50_pct !== null && ` · ${formatPct(selected.cagr_p50_pct)}/yr`}
                </p>
              )}
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="text-sm font-medium">
                Chance of reaching each target before a −7% stop
              </p>
              {selected ? (
                <TargetOdds prediction={selected} target={target} />
              ) : (
                <SkeletonRows rows={8} className="h-4" />
              )}
              <Button
                disabled={!data || !last}
                onClick={() => {
                  setSheetOpen(true);
                }}
              >
                Start {selected?.category ?? ''} plan at +{target}%
              </Button>
            </CardContent>
          </Card>

          {stockPlans.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Plans for {symbol}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col divide-y">
                {stockPlans.map((p) => (
                  <div key={p.id} className="flex items-center justify-between gap-2 py-2 text-sm">
                    <span>
                      #{p.id} · {p.category} · {formatPct(p.target_pct, 2)}
                    </span>
                    {p.outcome ? (
                      <OutcomeBadge outcome={p.outcome} />
                    ) : (
                      <Badge variant="secondary">Active</Badge>
                    )}
                  </div>
                ))}
                <Link to="/journal" className="pt-2 text-sm text-primary hover:underline">
                  Open journal
                </Link>
              </CardContent>
            </Card>
          )}
        </aside>
      </div>

      {data && last && (
        <StartPlanSheet
          open={isSheetOpen}
          onOpenChange={setSheetOpen}
          symbol={symbol}
          lastClose={{ close: last.close, date: last.date }}
          predictions={data.predictions}
          initialCategory={category}
          initialTarget={target}
        />
      )}
    </div>
  );
}
