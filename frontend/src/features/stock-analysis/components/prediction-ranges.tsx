import { chanceOf, rangePosition, RANGE_MAX, RANGE_MIN } from '../model/ranges';
import type { Prediction } from '../model/headline';
import { cn } from '@/shared/lib/cn';
import { formatPct, formatProbability } from '@/shared/lib/format-number';

interface PredictionRangesProps {
  predictions: Prediction[];
  selected: string;
  target: number;
  onSelect: (category: string) => void;
}

/** One selectable row per holding category: p10–p90 band, median dot, zero line, odds, CAGR. */
export function PredictionRanges({
  predictions,
  selected,
  target,
  onSelect,
}: PredictionRangesProps) {
  const zero = rangePosition(0);
  return (
    <div className="overflow-x-auto">
      <div className="min-w-[600px]" role="listbox" aria-label="Holding periods">
        <div className="grid grid-cols-[56px_minmax(0,1fr)_76px_76px_84px_84px] gap-3 px-4 pb-2 text-xs text-muted-foreground">
          <span>Hold</span>
          <span>
            Range {formatPct(RANGE_MIN, 0)} … {formatPct(RANGE_MAX, 0)}
          </span>
          <span className="text-right">Median</span>
          <span className="text-right">Chance up</span>
          <span className="text-right">Hits {formatPct(target, 0)}</span>
          <span className="text-right">CAGR</span>
        </div>
        {predictions.map((p, index) => {
          const isSelected = p.category === selected;
          return (
            <button
              key={p.category}
              type="button"
              role="option"
              aria-selected={isSelected}
              onClick={() => {
                onSelect(p.category);
              }}
              className={cn(
                'grid w-full grid-cols-[56px_minmax(0,1fr)_76px_76px_84px_84px] items-center gap-3 border-t px-4 py-3 text-left text-sm transition-colors duration-150 hover:bg-muted/60',
                isSelected && 'bg-accent hover:bg-accent',
              )}
            >
              <span className="font-semibold">{p.category}</span>
              <span className="relative block h-5">
                <span
                  className="absolute inset-y-0 w-px bg-muted-foreground/50"
                  style={{ left: `${String(zero)}%` }}
                />
                <span
                  className="absolute top-1.5 h-2 rounded-full bg-band motion-safe:animate-grow-x"
                  style={{
                    left: `${String(rangePosition(p.p10_pct))}%`,
                    width: `${String(rangePosition(p.p90_pct) - rangePosition(p.p10_pct))}%`,
                    animationDelay: `${String(index * 50)}ms`,
                  }}
                />
                <span
                  className="absolute top-0.5 -ml-2 size-4 rounded-full border-2 border-card bg-primary shadow-sm"
                  style={{ left: `${String(rangePosition(p.p50_pct))}%` }}
                />
              </span>
              <span
                className={cn(
                  'text-right font-semibold',
                  p.p50_pct >= 0 ? 'text-gain' : 'text-loss',
                )}
              >
                {formatPct(p.p50_pct)}
              </span>
              <span className="text-right">{formatProbability(p.prob_up)}</span>
              <span className="text-right">{formatProbability(chanceOf(p, target))}</span>
              <span className="text-right text-muted-foreground">
                {p.cagr_p50_pct === null ? '—' : `${formatPct(p.cagr_p50_pct)}/yr`}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
