import { type ColumnDef } from '@tanstack/react-table';
import { Database, RefreshCw, Search } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { useDataSources, useSetRealSync, type DataSource } from '../api/use-data-sources';
import { DataTable } from '@/shared/components/data-table';
import { EmptyState, ErrorState, SkeletonRows } from '@/shared/components/data-states';
import { formatDate } from '@/shared/lib/format-date';
import { Badge } from '@/shared/ui/badge';
import { Input } from '@/shared/ui/input';
import { Toggle } from '@/shared/ui/toggle';

const right = { align: 'right' } as const;

function SourceBadge({ source }: { source: DataSource }) {
  if (source.latest_source === null) return <Badge variant="outline">No data</Badge>;
  return source.is_real ? (
    <Badge variant="outline" className="border-gain text-gain">
      Real · {source.latest_source}
    </Badge>
  ) : (
    <Badge variant="outline" className="border-synthetic text-synthetic">
      Synthetic
    </Badge>
  );
}

function SyncToggle({ source, isFull }: { source: DataSource; isFull: boolean }) {
  const setSync = useSetRealSync();
  const isBlocked = isFull && !source.is_real_sync_enabled;
  return (
    <Toggle
      variant="outline"
      size="sm"
      className="h-10 min-w-24"
      pressed={source.is_real_sync_enabled}
      disabled={setSync.isPending || isBlocked}
      title={isBlocked ? 'Limit reached: turn another stock off first' : undefined}
      aria-label={`Sync real data for ${source.symbol}`}
      onPressedChange={(pressed: boolean) => {
        setSync.mutate({ symbol: source.symbol, isEnabled: pressed });
      }}
    >
      <RefreshCw aria-hidden="true" />
      {source.is_real_sync_enabled ? 'Syncing' : 'Sync'}
    </Toggle>
  );
}

/** Admin > Data sources: real vs synthetic per stock, and the (limited) real-data sync picks. */
export function DataSourcesTable() {
  const sources = useDataSources();
  const [search, setSearch] = useState('');
  const rows = sources.data?.stocks ?? [];
  const max = sources.data?.max_real_sync ?? 0;
  const picked = rows.filter((s) => s.is_real_sync_enabled).length;
  const realCount = rows.filter((s) => s.is_real).length;
  const isFull = picked >= max;

  const columns = useMemo<ColumnDef<DataSource>[]>(
    () => [
      {
        id: 'symbol',
        header: 'Stock',
        accessorFn: (s) => s.symbol,
        cell: ({ row }) => (
          <span className="flex flex-col">
            <Link
              to={`/stocks/${encodeURIComponent(row.original.symbol)}`}
              className="font-semibold hover:underline"
            >
              {row.original.symbol}
            </Link>
            <span className="text-xs text-muted-foreground">{row.original.name}</span>
          </span>
        ),
      },
      {
        id: 'source',
        header: 'Data',
        accessorFn: (s) => (s.is_real ? 0 : 1),
        cell: ({ row }) => <SourceBadge source={row.original} />,
      },
      {
        id: 'last',
        header: 'Last candle',
        accessorFn: (s) => s.last_trade_date ?? '',
        cell: ({ row }) =>
          row.original.last_trade_date ? formatDate(row.original.last_trade_date) : '—',
      },
      {
        id: 'candles',
        header: 'Candles',
        accessorFn: (s) => s.candles,
        cell: ({ row }) => row.original.candles.toLocaleString('en-IN'),
        meta: right,
      },
      {
        id: 'sync',
        header: 'Real-data sync',
        accessorFn: (s) => (s.is_real_sync_enabled ? 0 : 1),
        cell: ({ row }) => <SyncToggle source={row.original} isFull={isFull} />,
        meta: right,
      },
    ],
    [isFull],
  );

  if (sources.isPending) return <SkeletonRows rows={8} />;
  if (sources.isError) {
    return (
      <ErrorState
        message="Data sources could not be loaded."
        onRetry={() => void sources.refetch()}
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative w-full max-w-xs">
          <Search
            className="absolute top-2.5 left-2.5 size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="h-9 pl-8"
            placeholder="Search symbol or name"
            aria-label="Search stocks"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
            }}
          />
        </div>
        <p className="text-sm text-muted-foreground tabular-nums">
          {realCount} of {rows.length} stocks have real data · {picked} / {max} picked for sync
        </p>
      </div>
      <DataTable
        label="Data sources"
        data={rows}
        columns={columns}
        initialSorting={[{ id: 'sync', desc: false }]}
        search={search}
        matches={(s, text) =>
          s.symbol.toLowerCase().includes(text) || s.name.toLowerCase().includes(text)
        }
        getRowId={(s) => s.symbol}
        empty={
          <EmptyState
            icon={Database}
            title="No stocks found"
            description="Load stocks first (make seed), or clear the search."
          />
        }
        renderCard={(row) => (
          <li key={row.id} className="flex flex-col gap-2 rounded-xl border bg-card p-3 text-sm">
            <span className="flex items-center justify-between gap-2">
              <Link
                to={`/stocks/${encodeURIComponent(row.original.symbol)}`}
                className="font-semibold hover:underline"
              >
                {row.original.symbol}
              </Link>
              <SourceBadge source={row.original} />
            </span>
            <span className="flex items-center justify-between gap-2 text-muted-foreground tabular-nums">
              {row.original.last_trade_date ? formatDate(row.original.last_trade_date) : 'No data'}
              <SyncToggle source={row.original} isFull={isFull} />
            </span>
          </li>
        )}
      />
    </div>
  );
}
