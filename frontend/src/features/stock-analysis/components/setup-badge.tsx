import { Minus, TrendingDown, TrendingUp, type LucideIcon } from 'lucide-react';

import type { Prediction } from '../model/headline';
import { cn } from '@/shared/lib/cn';

type Setup = NonNullable<Prediction['setup']>;

const META: Record<Setup, { label: string; icon: LucideIcon; className: string }> = {
  FAVOURABLE: { label: 'Favourable', icon: TrendingUp, className: 'border-gain/40 text-gain' },
  NEUTRAL: { label: 'Neutral', icon: Minus, className: 'border-border text-muted-foreground' },
  UNFAVOURABLE: {
    label: 'Unfavourable',
    icon: TrendingDown,
    className: 'border-loss/40 text-loss',
  },
};

/** Short-term setup (Q77): statistics, not advice. Icon + text, never colour alone. */
export function SetupBadge({ setup }: { setup: Setup }) {
  const meta = META[setup];
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium',
        meta.className,
      )}
      title="Short-term setup from the predicted odds; statistics, not advice"
    >
      <meta.icon className="size-3.5" aria-hidden="true" />
      {meta.label}
    </span>
  );
}
