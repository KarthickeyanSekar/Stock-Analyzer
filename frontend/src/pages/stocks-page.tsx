import { ArrowDown, ArrowUp, ArrowUpDown, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { useStockOverview } from '@/features/stock-analysis';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { cn } from '@/shared/lib/cn';
import { formatInr, formatPct, formatProbability } from '@/shared/lib/format-number';
import { Card } from '@/shared/ui/card';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

type SortKey =
  'symbol' | 'last_close' | 'day_change_pct' | 'return_1y_pct' | 'median_1y_pct' | 'prob_up_1y';
const ALL = 'All sectors';
const COLUMNS: { key: SortKey; label: string; align?: 'right' }[] = [
  { key: 'symbol', label: 'Stock' },
  { key: 'last_close', label: 'Last', align: 'right' },
  { key: 'day_change_pct', label: 'Day', align: 'right' },
  { key: 'return_1y_pct', label: '1Y return', align: 'right' },
  { key: 'median_1y_pct', label: '1Y prediction', align: 'right' },
  { key: 'prob_up_1y', label: 'Chance up', align: 'right' },
];

function Signed({ value, digits = 2 }: { value: number | null; digits?: number }) {
  if (value === null) return <span className="text-muted-foreground">—</span>;
  return <span className={value >= 0 ? 'text-gain' : 'text-loss'}>{formatPct(value, digits)}</span>;
}

export function StocksPage() {
  const navigate = useNavigate();
  const { data = [], isPending, isError, refetch } = useStockOverview();
  const [query, setQuery] = useState('');
  const [sector, setSector] = useState(ALL);
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean }>({ key: 'symbol', desc: false });

  const sectors = useMemo(
    () => [ALL, ...[...new Set(data.map((r) => r.stock.sector ?? 'Other'))].sort()],
    [data],
  );
  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = data.filter(
      (r) =>
        (sector === ALL || r.stock.sector === sector) &&
        (!needle ||
          r.stock.symbol.toLowerCase().includes(needle) ||
          r.stock.name.toLowerCase().includes(needle)),
    );
    const value = (r: (typeof data)[number]) =>
      sort.key === 'symbol' ? r.stock.symbol : (r[sort.key] ?? -Infinity);
    return filtered.sort((a, b) => {
      const [x, y] = [value(a), value(b)];
      const order = x < y ? -1 : x > y ? 1 : 0;
      return sort.desc ? -order : order;
    });
  }, [data, query, sector, sort]);

  const toggleSort = (key: SortKey) => {
    setSort((current) => ({ key, desc: current.key === key ? !current.desc : key !== 'symbol' }));
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold">Stocks</h1>
        <p className="text-sm text-muted-foreground">
          {data.length} NIFTY 50 stocks · sort any column · open a stock for its predictions
        </p>
      </div>
      <div className="flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <Search
            className="absolute top-2.5 left-2.5 size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="h-9 pl-8"
            placeholder="Filter by symbol or name"
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
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {sectors.map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isError && <ErrorState message="Could not load stocks." onRetry={() => void refetch()} />}
      {isPending && <SkeletonRows rows={10} />}
      {!isPending && rows.length === 0 && (
        <EmptyState
          icon={Search}
          title="No stocks match"
          description="Try another name or sector."
        />
      )}

      {rows.length > 0 && (
        <Card className="overflow-hidden p-0">
          <table className="hidden w-full text-sm md:table">
            <thead className="border-b bg-muted/50 text-xs text-muted-foreground">
              <tr>
                {COLUMNS.map((column) => {
                  const active = sort.key === column.key;
                  const Icon = !active ? ArrowUpDown : sort.desc ? ArrowDown : ArrowUp;
                  return (
                    <th
                      key={column.key}
                      scope="col"
                      aria-sort={active ? (sort.desc ? 'descending' : 'ascending') : 'none'}
                      className={cn(
                        'px-4 py-2 text-left font-medium',
                        column.align === 'right' && 'text-right',
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          toggleSort(column.key);
                        }}
                        className={cn(
                          'inline-flex items-center gap-1 hover:text-foreground',
                          active && 'text-foreground',
                        )}
                      >
                        {column.label}
                        <Icon className="size-3.5" aria-hidden="true" />
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.stock.symbol}
                  onClick={() => void navigate(`/stocks/${encodeURIComponent(r.stock.symbol)}`)}
                  className="cursor-pointer border-b transition-colors duration-150 last:border-0 hover:bg-muted/50"
                >
                  <td className="px-4 py-2.5">
                    <Link
                      to={`/stocks/${encodeURIComponent(r.stock.symbol)}`}
                      className="font-semibold hover:underline"
                    >
                      {r.stock.symbol}
                    </Link>
                    <span className="block text-xs text-muted-foreground">
                      {r.stock.name} · {r.stock.sector}
                    </span>
                  </td>
                  <td className="px-4 text-right">
                    {r.last_close === null ? '—' : formatInr(r.last_close)}
                  </td>
                  <td className="px-4 text-right">
                    <Signed value={r.day_change_pct} />
                  </td>
                  <td className="px-4 text-right">
                    <Signed value={r.return_1y_pct} digits={1} />
                  </td>
                  <td className="px-4 text-right font-medium">
                    <Signed value={r.median_1y_pct} digits={1} />
                  </td>
                  <td className="px-4 text-right">
                    {r.prob_up_1y === null ? '—' : formatProbability(r.prob_up_1y)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <ul className="divide-y md:hidden">
            {rows.map((r) => (
              <li key={r.stock.symbol}>
                <Link
                  to={`/stocks/${encodeURIComponent(r.stock.symbol)}`}
                  className="flex items-center justify-between gap-3 p-4"
                >
                  <span>
                    <span className="font-semibold">{r.stock.symbol}</span>
                    <span className="block text-xs text-muted-foreground">
                      1Y prediction <Signed value={r.median_1y_pct} digits={1} />
                    </span>
                  </span>
                  <span className="text-right text-sm">
                    {r.last_close === null ? '—' : formatInr(r.last_close)}
                    <span className="block text-xs">
                      <Signed value={r.day_change_pct} />
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
