import { ArrowRight } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import { useCloseTradePlan, type TradePlan } from '../api/use-trade-plans';
import { previewOutcome } from '../model/outcome';
import { OutcomeBadge } from './outcome-badge';
import { formatInr, formatPct } from '@/shared/lib/format-number';
import { Button } from '@/shared/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';

interface ClosePlanDialogProps {
  plan: TradePlan | null;
  onOpenChange: (open: boolean) => void;
}

/** Record the exit with a live preview of the outcome before confirming. */
export function ClosePlanDialog({ plan, onOpenChange }: ClosePlanDialogProps) {
  return (
    <Dialog open={plan !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        {plan && (
          <ClosePlanForm
            key={plan.id}
            plan={plan}
            onDone={() => {
              onOpenChange(false);
            }}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

function ClosePlanForm({ plan, onDone }: { plan: TradePlan; onDone: () => void }) {
  const closePlan = useCloseTradePlan();
  const [exitDate, setExitDate] = useState(plan.planned_end_date);
  const [exitPrice, setExitPrice] = useState(plan.benchmark_price.toFixed(2));
  const price = Number(exitPrice);
  const preview =
    price > 0
      ? previewOutcome(plan.entry_price, price, plan.benchmark_pct, plan.success_tolerance_pp)
      : null;

  const confirm = () => {
    closePlan.mutate(
      { planId: plan.id, body: { exit_date: exitDate, exit_price: price, exited_early: false } },
      {
        onSuccess: (closed) => {
          toast.success(`Plan #${String(closed.id)} closed: ${closed.outcome ?? ''}`, {
            description: `${plan.symbol} ${formatPct(closed.actual_return_pct ?? 0, 2)} vs ${formatPct(closed.benchmark_pct, 2)} predicted`,
          });
          onDone();
        },
        onError: (error) => toast.error(error.message),
      },
    );
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>
          Close plan #{plan.id} · {plan.symbol}
        </DialogTitle>
        <DialogDescription>
          Entry {formatInr(plan.entry_price)} · predicted {formatPct(plan.benchmark_pct, 2)} (±
          {plan.success_tolerance_pp} pp). The outcome is calculated, not chosen.
        </DialogDescription>
      </DialogHeader>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="exit-date">Exit date</Label>
          <Input
            id="exit-date"
            type="date"
            value={exitDate}
            min={plan.start_date}
            onChange={(event) => {
              setExitDate(event.target.value);
            }}
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="exit-price">Exit price (₹)</Label>
          <Input
            id="exit-price"
            type="number"
            step="0.05"
            min="0"
            value={exitPrice}
            onChange={(event) => {
              setExitPrice(event.target.value);
            }}
          />
        </div>
      </div>
      <div className="rounded-lg bg-muted p-3 text-sm" aria-live="polite">
        {preview ? (
          <div className="flex flex-wrap items-center gap-2">
            <span>
              Actual <strong>{formatPct(preview.actualPct, 2)}</strong> vs predicted{' '}
              {formatPct(plan.benchmark_pct, 2)}
            </span>
            <ArrowRight className="size-4 text-muted-foreground" aria-hidden="true" />
            <OutcomeBadge outcome={preview.outcome} />
          </div>
        ) : (
          <span className="text-muted-foreground">Enter an exit price to preview the outcome.</span>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button disabled={!preview || closePlan.isPending} onClick={confirm}>
          {closePlan.isPending ? 'Closing…' : 'Close plan'}
        </Button>
      </DialogFooter>
    </>
  );
}
