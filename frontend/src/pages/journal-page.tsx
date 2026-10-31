import { PlansTable } from '@/features/trade-journal';

export function JournalPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Trade journal</h1>
        <p className="text-sm text-slate-500">
          One start, one planned end, one exit. The outcome is calculated: equal to the prediction
          within the tolerance = success, above = partial (model needs tuning), below = failure.
        </p>
      </div>
      <PlansTable />
    </div>
  );
}
