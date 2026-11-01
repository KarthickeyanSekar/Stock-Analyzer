import { useState } from 'react';
import { toast } from 'sonner';

import {
  useJournalSettings,
  useSaveJournalSettings,
  type JournalSettings,
} from '../api/use-trade-plans';
import { ErrorState } from '@/shared/components/data-states';
import { Button } from '@/shared/ui/button';
import { Input } from '@/shared/ui/input';
import { Label } from '@/shared/ui/label';
import { Skeleton } from '@/shared/ui/skeleton';

const FIELDS: {
  key: keyof JournalSettings;
  label: string;
  hint: string;
  step: string;
}[] = [
  {
    key: 'paper_capital',
    label: 'Paper capital ₹',
    hint: 'Used to size positions; never moves real money.',
    step: '10000',
  },
  {
    key: 'risk_pct',
    label: 'Risk per plan %',
    hint: 'What a stop-out may lose, as a share of capital (0–10).',
    step: '0.25',
  },
  {
    key: 'success_tolerance_pp',
    label: 'Success tolerance ±pp',
    hint: 'Actual within this many points of the prediction counts as a success.',
    step: '0.1',
  },
  {
    key: 'default_stop_pct',
    label: 'Default stop-loss %',
    hint: 'Pre-filled when starting a plan; must be negative.',
    step: '0.5',
  },
];

/** Journal defaults (D2.4). Plans already started keep the values they were started with. */
export function JournalSettingsForm() {
  const settings = useJournalSettings();
  if (settings.isError) {
    return (
      <ErrorState message="Could not load settings." onRetry={() => void settings.refetch()} />
    );
  }
  if (!settings.data) return <Skeleton className="h-72 w-full max-w-xl" />;
  return <SettingsFields saved={settings.data} />;
}

function SettingsFields({ saved }: { saved: JournalSettings }) {
  const save = useSaveJournalSettings();
  const [values, setValues] = useState<Record<keyof JournalSettings, string>>({
    paper_capital: String(saved.paper_capital),
    risk_pct: String(saved.risk_pct),
    success_tolerance_pp: String(saved.success_tolerance_pp),
    default_stop_pct: String(saved.default_stop_pct),
  });
  const parsed: JournalSettings = {
    paper_capital: Number(values.paper_capital),
    risk_pct: Number(values.risk_pct),
    success_tolerance_pp: Number(values.success_tolerance_pp),
    default_stop_pct: Number(values.default_stop_pct),
  };
  const isValid =
    parsed.paper_capital > 0 &&
    parsed.risk_pct > 0 &&
    parsed.risk_pct <= 10 &&
    parsed.success_tolerance_pp >= 0 &&
    parsed.default_stop_pct < 0;
  const isDirty = FIELDS.some(({ key }) => parsed[key] !== saved[key]);

  return (
    <form
      className="flex max-w-xl flex-col gap-4 rounded-xl border bg-card p-4"
      onSubmit={(event) => {
        event.preventDefault();
        save.mutate(parsed, {
          onSuccess: () => toast.success('Settings saved. New plans use them from now on.'),
          onError: (error) => toast.error(error.message),
        });
      }}
    >
      {FIELDS.map((field) => (
        <div key={field.key} className="flex flex-col gap-1.5">
          <Label htmlFor={field.key}>{field.label}</Label>
          <Input
            id={field.key}
            type="number"
            step={field.step}
            value={values[field.key]}
            aria-describedby={`${field.key}-hint`}
            onChange={(event) => {
              setValues({ ...values, [field.key]: event.target.value });
            }}
          />
          <p id={`${field.key}-hint`} className="text-xs text-muted-foreground">
            {field.hint}
          </p>
        </div>
      ))}
      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!isValid || !isDirty || save.isPending}>
          {save.isPending ? 'Saving…' : 'Save settings'}
        </Button>
        {!isValid && (
          <p className="text-sm text-loss" role="alert">
            Check the values: capital &gt; 0, risk 0–10%, tolerance ≥ 0, stop &lt; 0.
          </p>
        )}
      </div>
    </form>
  );
}
