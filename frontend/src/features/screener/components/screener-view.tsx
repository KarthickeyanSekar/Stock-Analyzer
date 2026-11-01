import { SearchX } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useScreener, type ScreenQuery, type ScreenRow } from '../api/use-screener';
import { useStockOverview } from '@/features/stock-analysis';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatPct, formatProbability } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Label } from '@/shared/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';
import { ToggleGroup, ToggleGroupItem } from '@/shared/ui/toggle-group';

const CATEGORIES = ['50D', '100D', '200D', '300D', '1Y', '2Y', '3Y'] as const;
const TARGETS = [5, 10, 15, 20, 25, 30, 40, 50];
const ANY = 'any';
const PROBABILITIES = [ANY, '0.3', '0.4', '0.5', '0.6'];
const WORST = [ANY, '-5', '-10', '-15', '-20'];
const QUALITY = [ANY, '4', '6', '8'];
const ALL_SECTORS = 'all';

type Category = (typeof CATEGORIES)[number];

function FilterSelect({
  id,
  label,
  value,
  options,
  format,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: string[];
  format: (option: string) => string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id} className="text-xs text-muted-foreground">
        {label}
      </Label>
      <Select
        value={value}
        onValueChange={(next) => {
          onChange(next ?? options[0] ?? ANY);
        }}
      >
        <SelectTrigger id={id} className="h-9 w-40" aria-label={label}>
          <SelectValue>{(selected: string) => format(selected)}</SelectValue>
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {format(option)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}

/** "N days, X% → which stocks?": filters on top, ranked results below (cards on phones). */
export function ScreenerView() {
  const [category, setCategory] = useState<Category>('1Y');
  const [target, setTarget] = useState(10);
  const [probability, setProbability] = useState(ANY);
  const [worst, setWorst] = useState(ANY);
  const [quality, setQuality] = useState(ANY);
  const [sector, setSector] = useState(ALL_SECTORS);
  const overview = useStockOverview();
  const sectors = [
    ALL_SECTORS,
    ...new Set((overview.data ?? []).map((r) => r.stock.sector ?? '').filter(Boolean)),
  ].sort((a, b) => (a === ALL_SECTORS ? -1 : b === ALL_SECTORS ? 1 : a.localeCompare(b)));

  const query: ScreenQuery = {
    category,
    target_pct: target,
    min_probability: probability === ANY ? undefined : probability,
    min_worst_pct: worst === ANY ? undefined : worst,
    min_quality: quality === ANY ? undefined : Number(quality),
    sector: sector === ALL_SECTORS ? undefined : [sector],
  };
  const { data: rows = [], isPending, isError, refetch, isFetching } = useScreener(query);
  const reset = () => {
    setProbability(ANY);
    setWorst(ANY);
    setQuality(ANY);
    setSector(ALL_SECTORS);
  };

  return (
    <div className="flex flex-col gap-4">
      <section className="flex flex-col gap-4 rounded-xl border bg-card p-4" aria-label="Filters">
        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground">Hold for</span>
          <ToggleGroup
            value={[category]}
            onValueChange={(value: string[]) => {
              const next = value[0] as Category | undefined;
              if (next) setCategory(next);
            }}
            aria-label="Holding period"
            className="flex-wrap"
          >
            {CATEGORIES.map((c) => (
              <ToggleGroupItem key={c} value={c} size="sm">
                {c}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground">I want at least</span>
          <ToggleGroup
            value={[String(target)]}
            onValueChange={(value: string[]) => {
              if (value[0]) setTarget(Number(value[0]));
            }}
            aria-label="Target return"
            className="flex-wrap"
          >
            {TARGETS.map((t) => (
              <ToggleGroupItem key={t} value={String(t)} size="sm">
                +{t}%
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
        <div className="flex flex-wrap gap-3">
          <FilterSelect
            id="min-probability"
            label="Chance at least"
            value={probability}
            options={PROBABILITIES}
            format={(o) => (o === ANY ? 'Any' : formatProbability(Number(o)))}
            onChange={setProbability}
          />
          <FilterSelect
            id="min-worst"
            label="Worst likely (p10) at least"
            value={worst}
            options={WORST}
            format={(o) => (o === ANY ? 'Any' : formatPct(Number(o), 0))}
            onChange={setWorst}
          />
          <FilterSelect
            id="min-quality"
            label="Quality at least"
            value={quality}
            options={QUALITY}
            format={(o) => (o === ANY ? 'Any' : `${o}/10`)}
            onChange={setQuality}
          />
          <FilterSelect
            id="sector"
            label="Sector"
            value={sector}
            options={sectors}
            format={(o) => (o === ALL_SECTORS ? 'All sectors' : o)}
            onChange={setSector}
          />
        </div>
      </section>

      <p className="text-sm text-muted-foreground" aria-live="polite">
        {isPending
          ? 'Screening…'
          : `${String(rows.length)} stocks · hold ${category} · chance of ${formatPct(target, 0)} before a −7% stop`}
      </p>

      {isError && (
        <ErrorState message="Could not run the screener." onRetry={() => void refetch()} />
      )}
      {isPending && <SkeletonRows rows={8} />}
      {!isPending && !isError && rows.length === 0 && (
        <EmptyState
          icon={SearchX}
          title="No stocks match"
          description="Try a lower target, a lower chance or fewer filters."
          action={
            <Button variant="outline" onClick={reset}>
              Clear filters
            </Button>
          }
        />
      )}
      {rows.length > 0 && (
        <div className={cn('transition-opacity duration-150', isFetching && 'opacity-60')}>
          <ResultsTable rows={rows} target={target} />
          <ResultCards rows={rows} target={target} />
        </div>
      )}
    </div>
  );
}

function Median({ value }: { value: number }) {
  return (
    <span className={cn('font-semibold', value >= 0 ? 'text-gain' : 'text-loss')}>
      {formatPct(value)}
    </span>
  );
}

function ResultsTable({ rows, target }: { rows: ScreenRow[]; target: number }) {
  return (
    <table className="hidden w-full rounded-xl border bg-card text-sm md:table">
      <thead className="text-xs text-muted-foreground">
        <tr className="border-b">
          <th className="px-4 py-2 text-left font-medium">Stock</th>
          <th className="px-4 py-2 text-right font-medium">Chance of {formatPct(target, 0)}</th>
          <th className="px-4 py-2 text-right font-medium">Median</th>
          <th className="px-4 py-2 text-right font-medium">80% range</th>
          <th className="px-4 py-2 text-right font-medium">Chance up</th>
          <th className="px-4 py-2 text-right font-medium">Quality</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.stock.symbol} className="border-b last:border-0 hover:bg-muted/60">
            <td className="px-4 py-2">
              <Link
                to={`/stocks/${encodeURIComponent(row.stock.symbol)}`}
                className="font-semibold hover:underline"
              >
                {row.stock.symbol}
              </Link>{' '}
              <span className="text-muted-foreground">{row.stock.sector}</span>
            </td>
            <td className="px-4 py-2 text-right font-semibold">
              {row.probability === null ? '—' : formatProbability(row.probability)}
            </td>
            <td className="px-4 py-2 text-right">
              <Median value={row.prediction.p50_pct} />
            </td>
            <td className="px-4 py-2 text-right text-muted-foreground">
              {formatPct(row.prediction.p10_pct)} … {formatPct(row.prediction.p90_pct)}
            </td>
            <td className="px-4 py-2 text-right">{formatProbability(row.prediction.prob_up)}</td>
            <td className="px-4 py-2 text-right">
              {row.quality === null ? '—' : `${String(row.quality)}/10`}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ResultCards({ rows, target }: { rows: ScreenRow[]; target: number }) {
  return (
    <ul className="grid gap-2 md:hidden">
      {rows.map((row) => (
        <li key={row.stock.symbol}>
          <Link
            to={`/stocks/${encodeURIComponent(row.stock.symbol)}`}
            className="flex items-center justify-between gap-3 rounded-xl border bg-card p-3"
          >
            <span>
              <span className="block font-semibold">{row.stock.symbol}</span>
              <span className="text-xs text-muted-foreground">
                {formatPct(row.prediction.p10_pct)} … {formatPct(row.prediction.p90_pct)} ·{' '}
                {row.quality === null ? '—' : `${String(row.quality)}/10`}
              </span>
            </span>
            <span className="text-right text-sm">
              <span className="block font-semibold">
                {row.probability === null ? '—' : formatProbability(row.probability)}
              </span>
              <span className="text-xs text-muted-foreground">
                chance of {formatPct(target, 0)}
              </span>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
