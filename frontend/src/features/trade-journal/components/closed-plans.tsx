import { type ColumnDef } from '@tanstack/react-table';
import { Archive, Search } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { type TradePlan } from '../api/use-trade-plans';
import { OUTCOME_META, type Outcome } from '../model/outcome';
import { OutcomeBadge } from './outcome-badge';
import { EmptyState } from '@/shared/components/data-states';
import { DataTable } from '@/shared/components/data-table';
import { formatDate } from '@/shared/lib/format-date';
import { formatPct, formatPp } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select';

const ALL = 'all';
const OUTCOMES: Outcome[] = ['SUCCESS', 'PARTIAL', 'FAILURE', 'EXITED_EARLY'];
const right = { align: 'right' as const };

/** Actual minus what the outcome was judged against (the locked prediction, Q31). */
const gap = (plan: TradePlan) => (plan.actual_return_pct ?? 0) - plan.benchmark_pct;

const COLUMNS: ColumnDef<TradePlan>[] = [
  {
    id: 'symbol',
    header: 'Plan',
    accessorFn: (plan) => plan.symbol,
    cell: ({ row }) => (
      <span className="flex flex-col">
        <Link
          to={`/stocks/${encodeURIComponent(row.original.symbol)}`}
          className="font-semibold hover:underline"
        >
          {row.original.symbol}
        </Link>
        <span className="text-xs text-muted-foreground">
          #{row.original.id} · {row.original.category}
        </span>
      </span>
    ),
  },
  {
    id: 'closed',
    header: 'Closed',
    accessorFn: (plan) => plan.exit_date ?? '',
    cell: ({ row }) =>
      row.original.exit_date ? formatDate(row.original.exit_date) : <span>—</span>,
  },
  {
    id: 'actual',
    header: 'Actual',
    accessorFn: (plan) => plan.actual_return_pct ?? 0,
    cell: ({ row }) => (
      <span className="font-semibold">{formatPct(row.original.actual_return_pct ?? 0, 2)}</span>
    ),
    meta: right,
  },
  {
    id: 'predicted',
    header: 'Predicted',
    accessorFn: (plan) => plan.benchmark_pct,
    cell: ({ row }) => formatPct(row.original.benchmark_pct, 2),
    meta: right,
  },
  {
    id: 'difference',
    header: 'Difference',
    accessorFn: gap,
    cell: ({ row }) => formatPp(gap(row.original), 2),
    meta: right,
  },
  {
    id: 'outcome',
    header: 'Outcome',
    accessorFn: (plan) => plan.outcome ?? '',
    cell: ({ row }) =>
      row.original.outcome ? <OutcomeBadge outcome={row.original.outcome} /> : null,
  },
];

/** Closed plans: actual vs predicted and the calculated outcome; sortable, searchable, paged. */
export function ClosedPlans({ plans }: { plans: TradePlan[] }) {
  const [search, setSearch] = useState('');
  const [outcome, setOutcome] = useState<string>(ALL);

  if (plans.length === 0) {
    return (
      <EmptyState
        icon={Archive}
        title="No closed plans yet"
        description="Closed plans and their outcomes appear here."
      />
    );
  }
  const rows = plans.filter((plan) => outcome === ALL || plan.outcome === outcome);
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-3">
        <div className="relative w-full max-w-xs">
          <Search
            className="absolute top-2.5 left-2.5 size-4 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            className="h-9 pl-8"
            placeholder="Search symbol"
            aria-label="Search closed plans"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
            }}
          />
        </div>
        <Select
          value={outcome}
          onValueChange={(value) => {
            setOutcome(value ?? ALL);
          }}
        >
          <SelectTrigger className="h-9 w-48" aria-label="Outcome">
            <SelectValue>
              {(value: string) =>
                value === ALL ? 'All outcomes' : OUTCOME_META[value as Outcome].label
              }
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>All outcomes</SelectItem>
            {OUTCOMES.map((o) => (
              <SelectItem key={o} value={o}>
                {OUTCOME_META[o].label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <DataTable
        label="Closed plans"
        data={rows}
        columns={COLUMNS}
        initialSorting={[{ id: 'closed', desc: true }]}
        search={search}
        matches={(plan, text) => plan.symbol.toLowerCase().includes(text)}
        getRowId={(plan) => String(plan.id)}
        empty={
          <EmptyState
            icon={Search}
            title="No closed plans match"
            description="Try another symbol or outcome."
            action={
              <Button
                variant="outline"
                onClick={() => {
                  setSearch('');
                  setOutcome(ALL);
                }}
              >
                Clear filters
              </Button>
            }
          />
        }
        renderCard={(row) => (
          <li key={row.id} className="flex flex-col gap-2 rounded-xl border bg-card p-3 text-sm">
            <span className="flex items-center justify-between gap-2">
              <Link
                to={`/stocks/${encodeURIComponent(row.original.symbol)}`}
                className="font-semibold hover:underline"
              >
                {row.original.symbol} · {row.original.category}
              </Link>
              {row.original.outcome && <OutcomeBadge outcome={row.original.outcome} />}
            </span>
            <span className="text-xs text-muted-foreground">
              Actual {formatPct(row.original.actual_return_pct ?? 0, 2)} vs predicted{' '}
              {formatPct(row.original.benchmark_pct, 2)} ·{' '}
              {row.original.exit_date ? formatDate(row.original.exit_date) : ''}
            </span>
          </li>
        )}
      />
    </div>
  );
}
