import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import {
  useCreateTradePlan,
  useJournalSettings,
  usePlanPreview,
  type CreateTradePlan,
  type JournalSettings,
} from '../api/use-trade-plans';
import { chanceOf, TARGETS, type Prediction } from '@/features/stock-analysis';
import { cn } from '@/shared/lib/cn';
import { formatDate } from '@/shared/lib/format-date';
import { formatInr, formatPct, formatProbability } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Skeleton } from '@/shared/ui/skeleton';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet';

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
        {props.open && <StartPlanLoader {...props} />}
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

/** Waits for the settings so the form starts with the user's defaults (D2.4). */
function StartPlanLoader(props: StartPlanSheetProps) {
  const settings = useJournalSettings();
  if (!settings.data) {
    return (
      <div className="flex flex-col gap-3 p-4" aria-busy="true">
        <Skeleton className="h-6 w-2/3" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }
  return <StartPlanForm {...props} settings={settings.data} />;
}

function StartPlanForm({
  onOpenChange,
  symbol,
  lastClose,
  predictions,
  initialCategory,
  initialTarget,
  settings,
}: StartPlanSheetProps & { settings: JournalSettings }) {
  const createPlan = useCreateTradePlan();
  const navigate = useNavigate();
  const [category, setCategory] = useState(initialCategory);
  const [target, setTarget] = useState(String(initialTarget));
  const [entry, setEntry] = useState(String(lastClose.close));
  const [stop, setStop] = useState(String(settings.default_stop_pct));
  const [tolerance, setTolerance] = useState(String(settings.success_tolerance_pp));
  const prediction = predictions.find((p) => p.category === category);
  const targetPct = Number(target);
  const entryPrice = Number(entry);
  const isValid = targetPct > 0 && Number(stop) < 0 && Number(tolerance) >= 0 && entryPrice > 0;
  const body: CreateTradePlan = {
    symbol,
    category: category as Prediction['category'],
    start_date: lastClose.date,
    target_pct: targetPct,
    // Q29: send a price only when it differs from the close, so the server records MANUAL.
    entry_price: entryPrice === lastClose.close ? null : entryPrice,
    stop_pct: Number(stop),
    success_tolerance_pp: Number(tolerance),
  };
  const preview = usePlanPreview(body, isValid);
  const review = preview.data;
  const isOwnTarget =
    review?.predicted_pct !== null &&
    review?.predicted_pct !== undefined &&
    review.predicted_pct !== review.target_pct;

  const start = () => {
    createPlan.mutate(body, {
      onSuccess: (plan) => {
        toast.success(`Plan #${String(plan.id)} started for ${symbol}`, {
          description: `${plan.category} · target ${formatPct(plan.target_pct, 2)} · ends ${formatDate(plan.planned_end_date)}`,
          action: { label: 'Journal', onClick: () => void navigate('/journal') },
        });
        onOpenChange(false);
      },
      onError: (error) => toast.error(error.message),
    });
  };

  return (
    <>
      <SheetHeader>
        <SheetTitle>Start a plan · {symbol}</SheetTitle>
        <SheetDescription>
          Last close {formatInr(lastClose.close)} ({formatDate(lastClose.date)}). The prediction is
          locked when you start.
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
                'flex min-h-14 flex-col items-start rounded-lg border p-2 text-left text-xs transition-colors duration-150 hover:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
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
            <Label htmlFor="target">Your target %</Label>
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

      <Step index={3} title="Entry and risk">
        <div className="grid grid-cols-3 gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="entry">Entry ₹</Label>
            <Input
              id="entry"
              type="number"
              step="0.05"
              value={entry}
              onChange={(e) => {
                setEntry(e.target.value);
              }}
            />
          </div>
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
        </div>
        <p className="text-xs text-muted-foreground">
          Entry defaults to the close; type your actual buy price if it differs. Sizing uses{' '}
          {formatInr(settings.paper_capital)} at {settings.risk_pct}% risk ·{' '}
          <Link to="/settings" className="text-primary underline-offset-2 hover:underline">
            Settings
          </Link>
        </p>
      </Step>

      <Step index={4} title="Review">
        {!isValid ? (
          <p className="text-sm text-muted-foreground">Check the values above to see the plan.</p>
        ) : preview.isError ? (
          <p className="text-sm text-loss" role="alert">
            {preview.error.message}
          </p>
        ) : !review ? (
          <Skeleton className="h-28 w-full" />
        ) : (
          <dl className="grid grid-cols-2 gap-3 text-sm" aria-live="polite">
            <div>
              <dt className="text-xs text-muted-foreground">Target price</dt>
              <dd className="font-semibold text-gain">{formatInr(review.target_price)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Stop price</dt>
              <dd className="font-semibold text-loss">{formatInr(review.stop_price)}</dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Suggested position</dt>
              <dd className="font-semibold">
                {review.suggested_quantity} sh · {formatInr(review.suggested_amount)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-muted-foreground">Ends</dt>
              <dd className="font-semibold">{formatDate(review.planned_end_date)}</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-xs text-muted-foreground">Success when the return is</dt>
              <dd className="font-semibold">
                {formatPct(
                  (review.predicted_pct ?? review.target_pct) - review.success_tolerance_pp,
                  1,
                )}{' '}
                …{' '}
                {formatPct(
                  (review.predicted_pct ?? review.target_pct) + review.success_tolerance_pp,
                  1,
                )}
                {isOwnTarget && (
                  <span className="block text-xs font-normal text-muted-foreground">
                    Judged against the prediction ({formatPct(review.predicted_pct ?? 0, 2)}); your
                    own target is tracked separately.
                  </span>
                )}
              </dd>
            </div>
          </dl>
        )}
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
