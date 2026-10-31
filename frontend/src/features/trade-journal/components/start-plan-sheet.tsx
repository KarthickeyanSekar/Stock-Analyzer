import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useCreateTradePlan } from '../api/use-trade-plans';
import { chanceOf, TARGETS, type Prediction } from '@/features/stock-analysis';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct, formatProbability } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet';

const DEFAULT_CAPITAL = 100_000;
const DEFAULT_RISK_PCT = 1;

interface StartPlanSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  symbol: string;
  lastClose: { close: number; date: string };
  predictions: Prediction[];
  initialCategory: string;
  initialTarget: number;
}

/** Guided plan start: ① holding period ② target ③ risk ④ review; the prediction is locked on start. */
export function StartPlanSheet(props: StartPlanSheetProps) {
  return (
    <Sheet open={props.open} onOpenChange={props.onOpenChange}>
      <SheetContent side="right" className="w-full gap-0 overflow-y-auto sm:max-w-md">
        {props.open && <StartPlanForm {...props} />}
      </SheetContent>
    </Sheet>
  );
}

function Step({
  index,
  title,
  children,
}: {
  index: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3 border-t px-4 py-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <span className="flex size-6 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
          {index}
        </span>
        {title}
      </h3>
      {children}
    </section>
  );
}

function StartPlanForm({
  onOpenChange,
  symbol,
  lastClose,
  predictions,
  initialCategory,
  initialTarget,
}: StartPlanSheetProps) {
  const createPlan = useCreateTradePlan();
  const navigate = useNavigate();
  const [category, setCategory] = useState(initialCategory);
  const [target, setTarget] = useState(String(initialTarget));
  const [stop, setStop] = useState('-7');
  const [tolerance, setTolerance] = useState('0.5');
  const [capital, setCapital] = useState(String(DEFAULT_CAPITAL));
  const prediction = predictions.find((p) => p.category === category);
  const targetPct = Number(target);
  const stopPct = Number(stop);
  const targetPrice = lastClose.close * (1 + targetPct / 100);
  const stopPrice = lastClose.close * (1 + stopPct / 100);
  const suggested =
    stopPct < 0 ? (Number(capital) * DEFAULT_RISK_PCT) / 100 / (Math.abs(stopPct) / 100) : 0;
  const isValid = targetPct > 0 && stopPct < 0 && Number(tolerance) >= 0;

  const start = () => {
    createPlan.mutate(
      {
        symbol,
        category: category as Prediction['category'],
        start_date: lastClose.date,
        target_pct: targetPct,
        stop_pct: stopPct,
        success_tolerance_pp: Number(tolerance),
      },
      {
        onSuccess: (plan) => {
          toast.success(`Plan #${String(plan.id)} started for ${symbol}`, {
            description: `${plan.category} · target ${formatPct(plan.target_pct, 2)} · ends ${plan.planned_end_date}`,
            action: { label: 'Journal', onClick: () => void navigate('/journal') },
          });
          onOpenChange(false);
        },
        onError: (error) => toast.error(error.message),
      },
    );
  };

  return (
    <>
      <SheetHeader>
        <SheetTitle>Start a plan · {symbol}</SheetTitle>
        <SheetDescription>
          Entry at the last close {formatInr(lastClose.close)} ({formatDate(lastClose.date)}). The
          prediction is locked when you start.
        </SheetDescription>
      </SheetHeader>

      <Step index={1} title="Holding period">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {predictions.map((p) => (
            <button
              key={p.category}
              type="button"
              aria-pressed={p.category === category}
              onClick={() => {
                setCategory(p.category);
              }}
              className={cn(
                'flex min-h-14 flex-col items-start rounded-lg border p-2 text-left text-xs transition-colors duration-150 hover:border-ring',
                p.category === category && 'border-primary bg-accent',
              )}
            >
              <span className="text-sm font-semibold">{p.category}</span>
              <span className={p.p50_pct >= 0 ? 'text-gain' : 'text-loss'}>
                {formatPct(p.p50_pct)}
              </span>
            </button>
          ))}
        </div>
      </Step>

      <Step index={2} title="Target">
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Target presets">
          {TARGETS.map((t) => (
            <Button
              key={t}
              size="sm"
              variant={Number(target) === t ? 'default' : 'outline'}
              onClick={() => {
                setTarget(String(t));
              }}
            >
              +{t}%
            </Button>
          ))}
        </div>
        <div className="flex items-end gap-3">
          <div className="flex flex-1 flex-col gap-1.5">
            <Label htmlFor="target">Target %</Label>
            <Input
              id="target"
              type="number"
              step="0.1"
              value={target}
              onChange={(event) => {
                setTarget(event.target.value);
              }}
            />
          </div>
          {prediction && (
            <p className="pb-2 text-sm text-muted-foreground">
              {formatProbability(chanceOf(prediction, targetPct))} chance · median{' '}
              {formatPct(prediction.p50_pct)}
            </p>
          )}
        </div>
      </Step>

      <Step index={3} title="Risk">
        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="stop">Stop-loss %</Label>
            <Input
              id="stop"
              type="number"
              step="0.5"
              value={stop}
              onChange={(e) => {
                setStop(e.target.value);
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="tolerance">Tolerance ±pp</Label>
            <Input
              id="tolerance"
              type="number"
              step="0.1"
              value={tolerance}
              onChange={(e) => {
                setTolerance(e.target.value);
              }}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="capital">Capital ₹</Label>
            <Input
              id="capital"
              type="number"
              step="1000"
              value={capital}
              onChange={(e) => {
                setCapital(e.target.value);
              }}
            />
          </div>
        </div>
      </Step>

      <Step index={4} title="Review">
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-xs text-muted-foreground">Target price</dt>
            <dd className="font-semibold text-gain">{formatInr(targetPrice)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Stop price</dt>
            <dd className="font-semibold text-loss">{formatInr(stopPrice)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Suggested amount (1% risk)</dt>
            <dd className="font-semibold">{formatInr(suggested)}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted-foreground">Success when</dt>
            <dd className="font-semibold">
              {formatPct(targetPct - Number(tolerance), 1)} …{' '}
              {formatPct(targetPct + Number(tolerance), 1)}
            </dd>
          </div>
        </dl>
      </Step>

      <SheetFooter className="border-t">
        <Button disabled={!isValid || createPlan.isPending} onClick={start}>
          {createPlan.isPending ? 'Starting…' : `Start ${category} plan`}
        </Button>
        <Button variant="outline" render={<Link to="/journal" />}>
          Open journal
        </Button>
      </SheetFooter>
    </>
  );
}
