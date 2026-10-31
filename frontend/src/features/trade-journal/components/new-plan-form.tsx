import { useState, type SyntheticEvent } from 'react';

import { useCreateTradePlan } from '../api/use-trade-plans';
import type { components } from '@/shared/api/schema';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';

type HoldingCategory = components['schemas']['HoldingCategory'];

const CATEGORIES: HoldingCategory[] = ['50D', '100D', '200D', '300D', '1Y', '2Y', '3Y'];

interface NewPlanFormProps {
  symbol: string;
  defaultStartDate: string;
  onCreated?: (planId: number) => void;
}

const optionalNumber = (value: string): number | undefined =>
  value.trim() === '' ? undefined : Number(value);

/** Start a plan. Leave entry price / target empty to use the close and the predicted median. */
export function NewPlanForm({ symbol, defaultStartDate, onCreated }: NewPlanFormProps) {
  const createPlan = useCreateTradePlan();
  const [category, setCategory] = useState<HoldingCategory>('50D');
  const [startDate, setStartDate] = useState(defaultStartDate);
  const [entryPrice, setEntryPrice] = useState('');
  const [targetPct, setTargetPct] = useState('');
  const [stopPct, setStopPct] = useState('-7');
  const [tolerance, setTolerance] = useState('0.5');

  const submit = (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    createPlan.mutate(
      {
        symbol,
        category,
        start_date: startDate,
        entry_price: optionalNumber(entryPrice),
        target_pct: optionalNumber(targetPct),
        stop_pct: Number(stopPct),
        success_tolerance_pp: Number(tolerance),
      },
      { onSuccess: (plan) => onCreated?.(plan.id) },
    );
  };

  return (
    <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
      <div className="space-y-1">
        <Label htmlFor="category">Holding category</Label>
        <select
          id="category"
          value={category}
          onChange={(event) => {
            setCategory(event.target.value as HoldingCategory);
          }}
          className="h-8 w-full rounded-lg border border-slate-200 bg-white px-2 text-sm"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <Field id="start" label="Start date" type="date" value={startDate} onChange={setStartDate} />
      <Field
        id="entry"
        label="Entry price (₹, empty = close)"
        value={entryPrice}
        onChange={setEntryPrice}
      />
      <Field
        id="target"
        label="Target % (empty = predicted median)"
        value={targetPct}
        onChange={setTargetPct}
      />
      <Field id="stop" label="Stop-loss %" value={stopPct} onChange={setStopPct} />
      <Field
        id="tolerance"
        label="Success tolerance ± pp"
        value={tolerance}
        onChange={setTolerance}
      />
      <div className="flex items-center gap-3 sm:col-span-3">
        <Button type="submit" disabled={createPlan.isPending}>
          {createPlan.isPending ? 'Starting…' : 'Start plan'}
        </Button>
        {createPlan.isError && (
          <p className="text-sm text-red-600" role="alert">
            {createPlan.error.message}
          </p>
        )}
        {createPlan.isSuccess && (
          <p className="text-sm text-emerald-700">
            Plan #{createPlan.data.id} started: target {createPlan.data.target_pct.toFixed(2)}%,
            ends {createPlan.data.planned_end_date}. Prediction locked.
          </p>
        )}
      </div>
    </form>
  );
}

interface FieldProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}

function Field({ id, label, value, onChange, type = 'number' }: FieldProps) {
  return (
    <div className="space-y-1">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        step="any"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      />
    </div>
  );
}
