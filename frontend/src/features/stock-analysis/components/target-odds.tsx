import { chanceOf, TARGETS } from '../model/ranges';
import type { Prediction } from '../model/headline';
import { cn } from '@/shared/lib/cn';
import { formatPct, formatProbability } from '@/shared/lib/format-number';

/** Bars: chance of reaching each target before the −7% stop, for one holding category. */
export function TargetOdds({ prediction, target }: { prediction: Prediction; target: number }) {
  return (
    <ul className="flex flex-col gap-2" aria-label="Chance of reaching each target">
      {TARGETS.map((t, index) => {
        const chance = chanceOf(prediction, t);
        const isTarget = t === target;
        return (
          <li
            key={t}
            className="grid grid-cols-[44px_minmax(0,1fr)_40px] items-center gap-2 text-sm"
          >
            <span className={cn(isTarget && 'font-semibold text-primary')}>{formatPct(t, 0)}</span>
            <span className="h-2 overflow-hidden rounded-full bg-muted">
              <span
                className={cn(
                  'block h-2 rounded-full motion-safe:animate-grow-x',
                  isTarget ? 'bg-primary' : 'bg-band',
                )}
                style={{
                  width: `${String(chance * 100)}%`,
                  animationDelay: `${String(index * 40)}ms`,
                }}
              />
            </span>
            <span className="text-right">{formatProbability(chance)}</span>
          </li>
        );
      })}
    </ul>
  );
}
