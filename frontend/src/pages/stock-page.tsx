import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  DEFAULT_TARGET_PCT,
  PredictionTable,
  PriceChart,
  useStockPredictions,
  useStockPrices,
  type PriceLine,
} from '@/features/stock-analysis';
import { NewPlanForm, useTradePlans } from '@/features/trade-journal';
import { formatInr } from '@/shared/lib/format-number';
import { Badge } from '@/shared/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card';

const TARGETS = [5, 10, 15, 20, 25, 30, 40, 50];
const CHART_FROM = '2025-01-01';

export function StockPage() {
  const { symbol = '' } = useParams();
  const [targetPct, setTargetPct] = useState(DEFAULT_TARGET_PCT);
  const predictions = useStockPredictions(symbol);
  const prices = useStockPrices(symbol, CHART_FROM);
  const plans = useTradePlans();

  const activePlan = plans.data?.find((p) => p.symbol === symbol && p.status === 'ACTIVE');
  const lines = useMemo<PriceLine[]>(
    () =>
      activePlan
        ? [
            { price: activePlan.target_price, title: 'Target', color: '#16a34a' },
            { price: activePlan.entry_price, title: 'Entry', color: '#64748b' },
            { price: activePlan.stop_price, title: 'Stop', color: '#dc2626' },
          ]
        : [],
    [activePlan],
  );

  if (predictions.isError) {
    return (
      <p className="text-red-600">
        Stock {symbol} not found. <Link to="/stocks">Back to stocks</Link>
      </p>
    );
  }
  const stock = predictions.data?.stock;
  const lastClose = predictions.data?.last_close;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">
            {symbol} {stock?.is_synthetic && <Badge variant="destructive">SYNTHETIC DATA</Badge>}
          </h1>
          <p className="text-sm text-slate-500">
            {stock?.name} · {stock?.sector} · {stock?.exchange}
          </p>
        </div>
        {lastClose && (
          <p className="text-right">
            <span className="text-2xl font-semibold">{formatInr(lastClose.close)}</span>
            <span className="block text-xs text-slate-500">close {lastClose.date}</span>
          </p>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Price (daily)</CardTitle>
        </CardHeader>
        <CardContent>
          {prices.data ? (
            <PriceChart candles={prices.data} lines={lines} />
          ) : (
            <p className="text-sm text-slate-500">Loading chart…</p>
          )}
          {activePlan && (
            <p className="mt-2 text-xs text-slate-500">
              Lines show active plan #{activePlan.id}: entry, target and stop.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Predictions by holding period</CardTitle>
          <label className="text-sm text-slate-600">
            Target{' '}
            <select
              value={targetPct}
              onChange={(event) => {
                setTargetPct(Number(event.target.value));
              }}
              className="rounded-md border border-slate-200 px-1"
              aria-label="Target percent"
            >
              {TARGETS.map((t) => (
                <option key={t} value={t}>
                  +{t}%
                </option>
              ))}
            </select>
          </label>
        </CardHeader>
        <CardContent>
          <PredictionTable
            predictions={predictions.data?.predictions ?? []}
            targetPct={targetPct}
          />
          <p className="mt-2 text-xs text-slate-500">
            Median return (p10…p90 range) and the chance of reaching the target before a −7% stop.
            Baseline statistics from past price history, not advice.
          </p>
        </CardContent>
      </Card>

      {lastClose && (
        <Card>
          <CardHeader>
            <CardTitle>Start a plan</CardTitle>
          </CardHeader>
          <CardContent>
            <NewPlanForm symbol={symbol} defaultStartDate={lastClose.date} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
