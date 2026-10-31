import { OUTCOME_META, type Outcome } from '../model/outcome';
import { cn } from '@/shared/lib/cn';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/shared/ui/tooltip';

/** Outcome as icon + text + colour (never colour alone), with its meaning on hover. */
export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const meta = OUTCOME_META[outcome];
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium whitespace-nowrap',
              meta.className,
            )}
          >
            <meta.icon className="size-3.5" aria-hidden="true" />
            {meta.label}
          </span>
        }
      />
      <TooltipContent>{meta.hint}</TooltipContent>
    </Tooltip>
  );
}
