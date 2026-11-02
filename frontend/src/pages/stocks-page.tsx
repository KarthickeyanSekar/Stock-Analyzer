import { type ColumnDef } from '@tanstack/react-table';
import { Search, Star } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useStockOverview } from '@/features/stock-analysis';
import { useWatchlist } from '@/features/watchlist';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { DataTable } from '@/shared/components/data-table';
import { formatInr, formatPct, formatProbability } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

type Row = NonNullable<ReturnType<typeof useStockOverview>['data']>[number];
const ALL = 'all';
const right = { align: 'right' as const };

function Signed({ value, digits = 2 }: { value: number | null; digits?: number }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  return <span className={value >= 0 ? 'text-gain' : 'text-loss'}>{formatPct(value, digits)}</span>;
}

const COLUMNS: ColumnDef<Row>[] = [
  {
    id: 'symbol',
    header: 'Stock',
    accessorFn: (row) => row.stock.symbol,
    cell: ({ row }) => (
      <Link
        to={`/stocks/${encodeURIComponent(row.original.stock.symbol)}`}
        className="flex flex-col hover:underline"
      >
        <span className="font-semibold">{row.original.stock.symbol}</span>
        <span className="text-xs text-muted-foreground">{row.original.stock.name}</span>
      </Link>
    ),
  },
  {
    id: 'sector',
    header: 'Sector',
    accessorFn: (row) => row.stock.sector ?? '',
    cell: ({ getValue }) => <span className="text-muted-foreground">{String(getValue())}</span>,
  },
  {
    id: 'last',
    header: 'Last',
    accessorFn: (row) => row.last_close ?? -1,
    cell: ({ row }) =>
      row.original.last_close === null ? '—' : formatInr(row.original.last_close),
    meta: right,
  },
  {
    id: 'day',
    header: 'Day',
    accessorFn: (row) => row.day_change_pct ?? -Infinity,
    cell: ({ row }) => <Signed value={row.original.day_change_pct} />,
    meta: right,
  },
  {
    id: 'return_1y',
    header: '1Y return',
    accessorFn: (row) => row.return_1y_pct ?? -Infinity,
    cell: ({ row }) => <Signed value={row.original.return_1y_pct} digits={1} />,
    meta: right,
  },
  {
    id: 'median_1y',
    header: '1Y prediction',
    accessorFn: (row) => row.median_1y_pct ?? -Infinity,
    cell: ({ row }) => <Signed value={row.original.median_1y_pct} digits={1} />,
    meta: right,
  },
  {
    id: 'chance_up',
    header: 'Chance up',
    accessorFn: (row) => row.prob_up_1y ?? -1,
    cell: ({ row }) =>
      row.original.prob_up_1y === null ? '—' : formatProbability(row.original.prob_up_1y),
    meta: right,
  },
];

function matches(row: Row, search: string): boolean {
  return (
    row.stock.symbol.toLowerCase().includes(search) || row.stock.name.toLowerCase().includes(search)
  );
}

export function StocksPage() {
  const { data = [], isPending, isError, refetch } = useStockOverview();
  const watchlist = useWatchlist();
  const [query, setQuery] = useState('');
  const [sector, setSector] = useState(ALL);
  const [watchedOnly, setWatchedOnly] = useState(false);
  const watched = new Set((watchlist.data ?? []).map((s) => s.symbol));

  const sectors = useMemo(
    () => [ALL, ...[...new Set(data.map((r) => r.stock.sector ?? 'Other'))].sort()],
    [data],
  );
  const rows = data.filter(
    (r) =>
      (sector === ALL || r.stock.sector === sector) &&
      (!watchedOnly || watched.has(r.stock.symbol)),
  );
  const reset = () => {
    setQuery('');
    setSector(ALL);
    setWatchedOnly(false);
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Stocks</h1>
        <p className="text-sm text-muted-foreground">
          {data.length} NIFTY 50 stocks · click a column to sort · open a stock for its predictions
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative w-full max-w-xs">
          <Search
            className="absolute top-2.5 left-2.5 size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="h-9 pl-8"
            placeholder="Search symbol or name"
            aria-label="Filter stocks"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
            }}
          />
        </div>
        <Select
          value={sector}
          onValueChange={(value) => {
            setSector(value ?? ALL);
          }}
        >
          <SelectTrigger className="h-9 w-56" aria-label="Sector">
            <SelectValue>{(value: string) => (value === ALL ? 'All sectors' : value)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {sectors.map((s) => (
              <SelectItem key={s} value={s}>
                {s === ALL ? 'All sectors' : s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Button
          variant={watchedOnly ? 'default' : 'outline'}
          size="sm"
          className="h-9"
          aria-pressed={watchedOnly}
          onClick={() => {
            setWatchedOnly(!watchedOnly);
          }}
        >
          <Star aria-hidden="true" /> Watchlist only ({watched.size})
        </Button>
      </div>

      {isError && <ErrorState message="Could not load stocks." onRetry={() => void refetch()} />}
      {isPending && <SkeletonRows rows={10} />}
      {!isPending && !isError && (
        <DataTable
          label="Stocks"
          data={rows}
          columns={COLUMNS}
          initialSorting={[{ id: 'symbol', desc: false }]}
          search={query}
          matches={matches}
          getRowId={(row) => row.stock.symbol}
          empty={
            <EmptyState
              icon={watchedOnly ? Star : Search}
              title={
                watchedOnly && watched.size === 0 ? 'Your watchlist is empty' : 'No stocks match'
              }
              description={
                watchedOnly && watched.size === 0
                  ? 'Open a stock and tap the star to add it.'
                  : 'Try another name or sector.'
              }
              action={
                <Button variant="outline" onClick={reset}>
                  Clear filters
                </Button>
              }
            />
          }
          renderCard={(row) => (
            <li key={row.id}>
              <Link
                to={`/stocks/${encodeURIComponent(row.original.stock.symbol)}`}
                className="flex items-center justify-between gap-3 rounded-xl border bg-card p-3"
              >
                <span className="min-w-0">
                  <span className="block font-semibold">{row.original.stock.symbol}</span>
                  <span className="block truncate text-xs text-muted-foreground">
                    {row.original.stock.name}
                  </span>
                </span>
                <span className="text-right text-sm">
                  <span className="block font-semibold">
                    {row.original.last_close === null ? '—' : formatInr(row.original.last_close)}
                  </span>
                  <Signed value={row.original.day_change_pct} />
                </span>
              </Link>
            </li>
          )}
        />
      )}
    </div>
  );
}
