import type { Prediction } from '../model/headline';
import { SetupBadge } from './setup-badge';
import { cn } from '@/shared/lib/cn';
import { formatPct, formatProbability } from '@/shared/lib/format-number';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card';

const SHORT = '5D';
const LONG = '1Y';

function Column({ title, prediction }: { title: string; prediction: Prediction | undefined }) {
  if (!prediction) {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-xs text-muted-foreground">{title}</span>
        <span className="text-sm text-muted-foreground">No prediction yet</span>
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-muted-foreground">{title}</span>
      <span
        className={cn(
          'text-2xl font-semibold',
          prediction.p50_pct >= 0 ? 'text-gain' : 'text-loss',
        )}
      >
        {formatPct(prediction.p50_pct)}
      </span>
      <span className="text-xs text-muted-foreground">
        {formatPct(prediction.p10_pct)} … {formatPct(prediction.p90_pct)} · up{' '}
        {formatProbability(prediction.prob_up)}
      </span>
      {prediction.setup && (
        <span>
          <SetupBadge setup={prediction.setup} />
        </span>
      )}
    </div>
  );
}

/** Short and long term side by side: next 5 sessions vs 1 year. */
export function OutlookCard({ predictions }: { predictions: Prediction[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Outlook</CardTitle>
        <CardDescription>Median and 80% range; statistics, not advice.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4">
        <Column title="Next 5 days" prediction={predictions.find((p) => p.category === SHORT)} />
        <Column title="1 year" prediction={predictions.find((p) => p.category === LONG)} />
      </CardContent>
    </Card>
  );
}
