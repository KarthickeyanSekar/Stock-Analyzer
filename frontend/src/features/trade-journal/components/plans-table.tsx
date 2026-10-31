import { useState } from 'react';
import { Link } from 'react-router-dom';

import { useCloseTradePlan, useTradePlans, type TradePlan } from '../api/use-trade-plans';
import { OUTCOME_STYLE } from '../model/outcome';
import { cn } from '@/shared/lib/cn';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table';

/** Every plan with its locked target, status and calculated outcome; active plans can be closed. */
export function PlansTable() {
  const { data: plans = [], isPending, isError } = useTradePlans();

  if (isPending) return <p className="text-sm text-slate-500">Loading plans…</p>;
  if (isError) return <p className="text-sm text-red-600">Could not load plans.</p>;
  if (plans.length === 0) {
    return (
      <p className="text-sm text-slate-500">
        No plans yet. Open a stock and start one from its page.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>#</TableHead>
          <TableHead>Stock</TableHead>
          <TableHead>Hold</TableHead>
          <TableHead>Start → planned end</TableHead>
          <TableHead className="text-right">Entry</TableHead>
          <TableHead className="text-right">Target (± tol.)</TableHead>
          <TableHead className="text-right">Actual</TableHead>
          <TableHead>Outcome</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {plans.map((plan) => (
          <PlanRow key={plan.id} plan={plan} />
        ))}
      </TableBody>
    </Table>
  );
}

function PlanRow({ plan }: { plan: TradePlan }) {
  const outcome = plan.outcome ? OUTCOME_STYLE[plan.outcome] : null;
  return (
    <TableRow>
      <TableCell>{plan.id}</TableCell>
      <TableCell>
        <Link to={`/stocks/${encodeURIComponent(plan.symbol)}`} className="font-medium underline">
          {plan.symbol}
        </Link>
      </TableCell>
      <TableCell>{plan.category}</TableCell>
      <TableCell className="whitespace-nowrap text-xs">
        {plan.start_date} → {plan.planned_end_date}
      </TableCell>
      <TableCell className="text-right">{formatInr(plan.entry_price)}</TableCell>
      <TableCell className="text-right whitespace-nowrap">
        {formatPct(plan.target_pct, 2)} (±{plan.success_tolerance_pp})
      </TableCell>
      <TableCell className="text-right">
        {plan.actual_return_pct === null ? '—' : formatPct(plan.actual_return_pct, 2)}
      </TableCell>
      <TableCell>
        {outcome ? (
          <span
            className={cn('rounded-md px-2 py-1 text-xs whitespace-nowrap', outcome.className)}
            title={outcome.hint}
          >
            {outcome.label}
          </span>
        ) : (
          <ClosePlanForm plan={plan} />
        )}
      </TableCell>
    </TableRow>
  );
}

function ClosePlanForm({ plan }: { plan: TradePlan }) {
  const closePlan = useCloseTradePlan();
  const [exitDate, setExitDate] = useState(plan.planned_end_date);
  const [exitPrice, setExitPrice] = useState('');

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Input
        type="date"
        value={exitDate}
        onChange={(event) => {
          setExitDate(event.target.value);
        }}
        className="h-7 w-36"
        aria-label={`Exit date for plan ${String(plan.id)}`}
      />
      <Input
        type="number"
        step="any"
        placeholder="Exit ₹"
        value={exitPrice}
        onChange={(event) => {
          setExitPrice(event.target.value);
        }}
        className="h-7 w-24"
        aria-label={`Exit price for plan ${String(plan.id)}`}
      />
      <Button
        size="sm"
        disabled={!exitPrice || closePlan.isPending}
        onClick={() => {
          closePlan.mutate({
            planId: plan.id,
            body: { exit_date: exitDate, exit_price: Number(exitPrice), exited_early: false },
          });
        }}
      >
        Close
      </Button>
      {closePlan.isError && <span className="text-xs text-red-600">{closePlan.error.message}</span>}
    </div>
  );
}
